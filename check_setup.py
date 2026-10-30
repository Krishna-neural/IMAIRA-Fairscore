#!/usr/bin/env python3
"""IMAIRA FairScore Pre-Flight System Diagnostic Checker.

Verifies Python version, essential dependencies, dataset files,
calibrator model weights, and compute hardware before startup.
"""

import os
import sys
from pathlib import Path

# Enable UTF-8 console output if available
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parent

def check_mark(status: bool) -> str:
    return "[PASS]" if status else "[FAIL]"

def run_diagnostics():
    print("=" * 70)
    print(" IMAIRA FairScore - Pre-Flight System Diagnostic Report")
    print("=" * 70)

    # 1. Python Version
    py_ver = sys.version.split()[0]
    py_ok = sys.version_info >= (3, 10)
    print(f"{check_mark(py_ok)} Python Version: {py_ver} (Minimum: 3.10+)")

    # 2. Core Python Dependencies
    deps = [
        ("fastapi", "FastAPI ASGI Web Framework"),
        ("uvicorn", "Uvicorn Async Server"),
        ("pydantic", "Pydantic Schema Validation"),
        ("rapidfuzz", "RapidFuzz Levenshtein Similarity"),
        ("jellyfish", "Jellyfish Metaphone/Soundex Phonetics"),
        ("sklearn", "Scikit-Learn Isotonic Calibration"),
        ("numpy", "NumPy Numerical Engine"),
        ("scipy", "SciPy Scientific Functions"),
        ("yaml", "PyYAML Configuration Parser"),
        ("pytest", "Pytest Automated Testing Suite")
    ]

    missing_deps = []
    for mod, desc in deps:
        try:
            __import__(mod)
            print(f"{check_mark(True)} Dependency: {desc} ({mod})")
        except ImportError:
            print(f"{check_mark(False)} Dependency: {desc} ({mod})")
            missing_deps.append(mod)

    # 3. Optional Hardware Dependencies
    try:
        import torch
        cuda_ok = torch.cuda.is_available()
        gpu_name = torch.cuda.get_device_name(0) if cuda_ok else "No GPU Detected"
        print(f"[INFO] PyTorch CUDA Acceleration: {'Available (' + gpu_name + ')' if cuda_ok else 'CPU Mode'}")
    except ImportError:
        print("[INFO] PyTorch not installed (Standard CPU/Browser Web Speech mode active)")

    try:
        import faster_whisper
        print("[INFO] Faster-Whisper GPU Engine: Installed")
    except ImportError:
        print("[INFO] Faster-Whisper: Not installed (Defensive fallback to Web Speech API / Bridge)")

    # 4. Critical Data Assets
    data_assets = [
        (REPO_ROOT / "data" / "glossary.csv", "2,000-Term Technical Glossary"),
        (REPO_ROOT / "data" / "QandA.json", "120-Question Reference Dataset"),
        (REPO_ROOT / "data" / "rubrics_120.json", "120-Question Semantic Rubrics"),
        (REPO_ROOT / "artifacts" / "calibrator_content.pkl", "Isotonic Content Calibrator"),
        (REPO_ROOT / "artifacts" / "calibrator_structure.pkl", "Isotonic Structure Calibrator"),
        (REPO_ROOT / "reports" / "scorer_robustness_report.json", "Fairness Robustness Benchmark"),
        (REPO_ROOT / "frontend" / "static" / "index.html", "Flagship Web Application")
    ]

    print("\n--- Critical Data & Model Assets ---")
    all_assets_ok = True
    for path, desc in data_assets:
        exists = path.exists()
        size_str = f"({path.stat().st_size:,} bytes)" if exists else ""
        print(f"{check_mark(exists)} Asset: {desc} {size_str}")
        if not exists:
            all_assets_ok = False

    # 5. Summary
    print("=" * 70)
    if not missing_deps and all_assets_ok:
        print("ALL PRE-FLIGHT CHECKS PASSED! System is fully operational.")
        print("Run 'python -m api.main' to start the web platform on http://localhost:8002")
    else:
        print("Some dependencies or assets are missing. Review output above.")
    print("=" * 70)

if __name__ == "__main__":
    run_diagnostics()
