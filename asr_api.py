from fastapi import FastAPI, UploadFile, File
from faster_whisper import WhisperModel
import os
import tempfile
from pathlib import Path

app = FastAPI()

# Load the model into the RTX 4050's GPU
print("Loading Whisper Model...")
model = WhisperModel("large-v3", device="cuda", compute_type="float16")
print("Model Loaded!")

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix
    temp_file = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
            temp_file = temp.name
            temp.write(await file.read())

        segments, _ = model.transcribe(temp_file, word_timestamps=True)

        transcript_data = []
        for segment in segments:
            for word in segment.words:
                transcript_data.append({
                    "word": word.word.strip(),
                    "start": word.start,
                    "end": word.end
                })

        return {"transcript": transcript_data}
    finally:
        if temp_file:
            try:
                os.remove(temp_file)
            except FileNotFoundError:
                pass