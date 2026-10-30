import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from interviewer.questions import load_questions, get_question_by_id

AUDIO_DIR = BASE_DIR / "static" / "audio" / "questions"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_VOICE = "en-US-AriaNeural"
VOICES = {
    "US Female (Aria)": "en-US-AriaNeural",
    "US Male (Guy)": "en-US-GuyNeural",
    "Indian Female (Neerja)": "en-IN-NeerjaNeural",
    "Indian Male (Prabhat)": "en-IN-PrabhatNeural"
}

def get_voice_options() -> Dict[str, str]:
    return VOICES

async def _synthesize_async(text: str, output_path: Path, voice: str) -> bool:
    try:
        import edge_tts
        communicator = edge_tts.Communicate(text=text, voice=voice)
        await communicator.save(str(output_path))
        return output_path.exists() and output_path.stat().st_size > 0
    except Exception:
        return False

def synthesize_speech(text: str, output_path: str, voice: str = DEFAULT_VOICE) -> str:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(lambda: asyncio.run(_synthesize_async(text, out, voice)))
            success = future.result()
    else:
        success = loop.run_until_complete(_synthesize_async(text, out, voice))

    if not success or not out.exists():
        # Minimal valid silent MP3 frame stub if offline
        with open(out, "wb") as f:
            f.write(b"\xff\xfb\x90\x44" + b"\x00" * 414)
    return str(out)

def get_question_audio(question_id: str, voice: str = DEFAULT_VOICE) -> str:
    clean_voice = voice.replace("-", "_")
    audio_file = AUDIO_DIR / f"{question_id}_{clean_voice}.mp3"
    if audio_file.exists() and audio_file.stat().st_size > 1000:
        return str(audio_file)

    q = get_question_by_id(question_id)
    if not q:
        raise ValueError(f"Question with ID '{question_id}' not found.")

    spoken_text = q.get("spoken_question", q.get("display_title", ""))
    return synthesize_speech(spoken_text, str(audio_file), voice=voice)

def generate_all_question_audio(voice: str = DEFAULT_VOICE) -> Dict[str, str]:
    questions = load_questions()
    result = {}
    for q in questions:
        q_id = q["id"]
        path = get_question_audio(q_id, voice=voice)
        result[q_id] = path
    return result

if __name__ == "__main__":
    audio_path = get_question_audio("q_db_01")
    print(f"Generated question audio for q_db_01 at: {audio_path} (Size: {os.path.getsize(audio_path)} bytes)")
