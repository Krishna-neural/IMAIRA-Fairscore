import os
import sys

# Ensure CUDA/cuDNN DLLs in the virtual environment are discoverable on Windows
scripts_dir = os.path.dirname(sys.executable)
if os.path.isdir(scripts_dir):
    try:
        os.add_dll_directory(scripts_dir)
    except Exception:
        pass
    os.environ["PATH"] = scripts_dir + os.pathsep + os.environ.get("PATH", "")

# Also add torch/lib if present
torch_lib = os.path.join(os.path.dirname(scripts_dir), "Lib", "site-packages", "torch", "lib")
if os.path.isdir(torch_lib):
    try:
        os.add_dll_directory(torch_lib)
    except Exception:
        pass
    os.environ["PATH"] = torch_lib + os.pathsep + os.environ.get("PATH", "")

import time
import json
import wave
import platform
import threading
import subprocess
import ctypes
from ctypes import wintypes
from typing import Dict, Any, List

# Windows RAM measuring via psapi
class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
    _fields_ = [
        ('cb', wintypes.DWORD),
        ('PageFaultCount', wintypes.DWORD),
        ('PeakWorkingSetSize', ctypes.c_size_t),
        ('WorkingSetSize', ctypes.c_size_t),
        ('QuotaPeakPagedPoolUsage', ctypes.c_size_t),
        ('QuotaPagedPoolUsage', ctypes.c_size_t),
        ('QuotaPeakNonPagedPoolUsage', ctypes.c_size_t),
        ('QuotaNonPagedPoolUsage', ctypes.c_size_t),
        ('PagefileUsage', ctypes.c_size_t),
        ('PeakPagefileUsage', ctypes.c_size_t),
    ]

def get_process_memory_mb() -> Dict[str, float]:
    try:
        kernel32 = ctypes.windll.kernel32
        psapi = ctypes.windll.psapi
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESS_MEMORY_COUNTERS), wintypes.DWORD]
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL

        pmc = PROCESS_MEMORY_COUNTERS()
        pmc.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
        if psapi.GetProcessMemoryInfo(kernel32.GetCurrentProcess(), ctypes.byref(pmc), pmc.cb):
            return {
                "working_set_mb": round(pmc.WorkingSetSize / (1024 * 1024), 2),
                "peak_working_set_mb": round(pmc.PeakWorkingSetSize / (1024 * 1024), 2),
            }
    except Exception as e:
        return {"error": str(e)}
    return {"working_set_mb": 0.0, "peak_working_set_mb": 0.0}

def get_gpu_sample() -> Dict[str, float]:
    """Sample GPU metrics once using nvidia-smi."""
    try:
        cmd = [
            "nvidia-smi",
            "--query-gpu=memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu,power.draw",
            "--format=csv,noheader,nounits"
        ]
        out = subprocess.check_output(cmd, encoding="utf-8").strip()
        parts = [p.strip() for p in out.split(",")]
        return {
            "total_mb": float(parts[0]),
            "used_mb": float(parts[1]),
            "free_mb": float(parts[2]),
            "gpu_util_pct": float(parts[3]),
            "temp_c": float(parts[4]),
            "power_w": float(parts[5]),
        }
    except Exception:
        return {}

class GPUMonitor(threading.Thread):
    """Background sampler for GPU metrics at high frequency."""
    def __init__(self, sample_interval_sec: float = 0.05):
        super().__init__(daemon=True)
        self.interval = sample_interval_sec
        self.running = True
        self.samples: List[Dict[str, float]] = []

    def run(self):
        while self.running:
            s = get_gpu_sample()
            if s:
                self.samples.append(s)
            time.sleep(self.interval)

    def stop(self) -> Dict[str, Any]:
        self.running = False
        self.join(timeout=1.0)
        if not self.samples:
            return {}
        used = [s["used_mb"] for s in self.samples]
        util = [s["gpu_util_pct"] for s in self.samples]
        power = [s["power_w"] for s in self.samples]
        return {
            "sample_count": len(self.samples),
            "peak_vram_used_mb": max(used),
            "avg_vram_used_mb": round(sum(used) / len(used), 2),
            "peak_gpu_util_pct": max(util),
            "avg_gpu_util_pct": round(sum(util) / len(util), 2),
            "peak_power_w": max(power),
            "avg_power_w": round(sum(power) / len(power), 2),
            "last_sample": self.samples[-1]
        }

def get_audio_info(audio_path: str) -> Dict[str, Any]:
    with wave.open(audio_path, "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        duration = frames / float(rate)
        return {
            "path": audio_path,
            "duration_sec": round(duration, 3),
            "sample_rate_hz": rate,
            "channels": channels,
            "bits_per_sample": sampwidth * 8,
            "total_frames": frames,
            "file_size_bytes": os.path.getsize(audio_path),
        }

def run_baseline_profile(audio_path: str = "asr/test.wav", compute_type: str = "float16") -> Dict[str, Any]:
    from faster_whisper import WhisperModel
    import torch
    import ctranslate2

    print(f"\n=======================================================", flush=True)
    print(f"Starting Baseline ASR Profiling (compute_type={compute_type})", flush=True)
    print(f"Audio target: {audio_path}", flush=True)
    print(f"=======================================================", flush=True)

    audio_info = get_audio_info(audio_path)
    print(f"Audio Duration: {audio_info['duration_sec']}s ({audio_info['sample_rate_hz']}Hz, {audio_info['channels']}ch)", flush=True)

    # 1. Baseline Pre-Run State
    baseline_gpu = get_gpu_sample()
    baseline_ram = get_process_memory_mb()
    print(f"Baseline GPU VRAM: {baseline_gpu.get('used_mb', 'N/A')} MiB / {baseline_gpu.get('total_mb', 'N/A')} MiB", flush=True)
    print(f"Baseline Process RAM: {baseline_ram['working_set_mb']} MB", flush=True)

    # 2. Model Loading
    print("\n[Phase 1] Loading Whisper large-v3 on CUDA...", flush=True)
    t0_load_wall = time.perf_counter()
    t0_load_cpu = time.process_time()

    model = WhisperModel("large-v3", device="cuda", compute_type=compute_type)

    load_wall_sec = round(time.perf_counter() - t0_load_wall, 3)
    load_cpu_sec = round(time.process_time() - t0_load_cpu, 3)
    post_load_gpu = get_gpu_sample()
    post_load_ram = get_process_memory_mb()
    print(f"Model Load Time: {load_wall_sec}s (CPU: {load_cpu_sec}s)", flush=True)
    print(f"Post-Load GPU VRAM: {post_load_gpu.get('used_mb', 'N/A')} MiB (delta: +{round(post_load_gpu.get('used_mb', 0) - baseline_gpu.get('used_mb', 0), 2)} MiB)", flush=True)
    print(f"Post-Load Process RAM: {post_load_ram['working_set_mb']} MB", flush=True)

    # 3. Inference Profiling with continuous GPU sampling
    print("\n[Phase 2] Running ASR Inference with word_timestamps=True...", flush=True)
    monitor = GPUMonitor(sample_interval_sec=0.05)
    monitor.start()

    t0_inf_wall = time.perf_counter()
    t0_inf_cpu = time.process_time()

    segments, info = model.transcribe(audio_path, word_timestamps=True)

    words_extracted = []
    full_text = []
    word_confidences = []

    for seg in segments:
        full_text.append(seg.text)
        if seg.words:
            for w in seg.words:
                words_extracted.append({
                    "word": w.word,
                    "start": round(w.start, 2),
                    "end": round(w.end, 2),
                    "conf": round(w.probability, 4) if hasattr(w, "probability") else None
                })
                if hasattr(w, "probability") and w.probability is not None:
                    word_confidences.append(w.probability)

    inf_wall_sec = round(time.perf_counter() - t0_inf_wall, 3)
    inf_cpu_sec = round(time.process_time() - t0_inf_cpu, 3)
    gpu_stats = monitor.stop()

    post_inf_ram = get_process_memory_mb()
    rtf = round(inf_wall_sec / audio_info["duration_sec"], 4)
    throughput_x = round(audio_info["duration_sec"] / inf_wall_sec, 2)
    avg_conf = round(sum(word_confidences) / len(word_confidences), 4) if word_confidences else None
    min_conf = round(min(word_confidences), 4) if word_confidences else None

    # Print summary
    print(f"\nInference Completed in: {inf_wall_sec}s", flush=True)
    print(f"Audio Duration: {audio_info['duration_sec']}s", flush=True)
    print(f"Real-Time Factor (RTF): {rtf} ({throughput_x}x faster than real-time)", flush=True)
    print(f"Peak GPU VRAM Used: {gpu_stats.get('peak_vram_used_mb', 'N/A')} MiB", flush=True)
    print(f"Peak GPU Utilization: {gpu_stats.get('peak_gpu_util_pct', 'N/A')}%", flush=True)
    print(f"Avg GPU Utilization: {gpu_stats.get('avg_gpu_util_pct', 'N/A')}%", flush=True)
    print(f"Inference Process Peak RAM: {post_inf_ram['peak_working_set_mb']} MB", flush=True)
    print(f"Detected Language: {info.language} (p={round(info.language_probability, 4)})", flush=True)
    print(f"Total Words Extracted: {len(words_extracted)}", flush=True)
    print(f"Average Word Confidence: {avg_conf} (Min: {min_conf})", flush=True)
    print(f"\nTranscript:", flush=True)
    print(" ".join(full_text).strip(), flush=True)

    report = {
        "metadata": {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "os": f"{platform.system()} {platform.release()}",
            "python_version": sys.version.split()[0],
            "torch_version": torch.__version__,
            "ctranslate2_version": ctranslate2.__version__,
            "cuda_available": torch.cuda.is_available(),
            "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "Unknown",
            "compute_type": compute_type,
        },
        "audio": audio_info,
        "model_loading": {
            "wall_time_sec": load_wall_sec,
            "cpu_time_sec": load_cpu_sec,
            "vram_delta_mb": round(post_load_gpu.get("used_mb", 0) - baseline_gpu.get("used_mb", 0), 2),
            "post_load_vram_mb": post_load_gpu.get("used_mb", 0),
        },
        "inference": {
            "wall_time_sec": inf_wall_sec,
            "cpu_time_sec": inf_cpu_sec,
            "rtf": rtf,
            "throughput_ratio": throughput_x,
            "detected_language": info.language,
            "language_probability": round(info.language_probability, 4),
            "word_count": len(words_extracted),
            "avg_word_confidence": avg_conf,
            "min_word_confidence": min_conf,
        },
        "gpu_profiling": {
            "baseline_vram_mb": baseline_gpu.get("used_mb", 0),
            "total_vram_mb": baseline_gpu.get("total_mb", 0),
            "peak_vram_mb": gpu_stats.get("peak_vram_used_mb", 0),
            "avg_vram_mb": gpu_stats.get("avg_vram_used_mb", 0),
            "peak_gpu_util_pct": gpu_stats.get("peak_gpu_util_pct", 0),
            "avg_gpu_util_pct": gpu_stats.get("avg_gpu_util_pct", 0),
            "peak_power_w": gpu_stats.get("peak_power_w", 0),
            "avg_power_w": gpu_stats.get("avg_power_w", 0),
        },
        "system_ram_profiling": {
            "baseline_working_set_mb": baseline_ram.get("working_set_mb", 0),
            "post_load_working_set_mb": post_load_ram.get("working_set_mb", 0),
            "peak_working_set_mb": post_inf_ram.get("peak_working_set_mb", 0),
        },
        "transcript_text": " ".join(full_text).strip(),
        "words": words_extracted
    }

    return report

if __name__ == "__main__":
    audio_file = sys.argv[1] if len(sys.argv) > 1 else "asr/test.wav"
    compute_type = sys.argv[2] if len(sys.argv) > 2 else "float16"

    report = run_baseline_profile(audio_file, compute_type=compute_type)

    out_json = f"asr/baseline_profile_{compute_type}.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\n[Saved full profile report to {out_json}]", flush=True)
