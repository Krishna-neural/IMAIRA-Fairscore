from fastapi import FastAPI, UploadFile, File
from faster_whisper import WhisperModel
import os

app = FastAPI()

# Load the model into the RTX 4050's GPU
print("Loading Whisper Model...")
model = WhisperModel("large-v3", device="cuda", compute_type="float16")
print("Model Loaded!")

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    # Save the incoming audio file temporarily
    temp_file = f"temp_{file.filename}"
    with open(temp_file, "wb") as f:
        f.write(await file.read())
    
    # Transcribe the audio and extract word-level timestamps
    segments, _ = model.transcribe(temp_file, word_timestamps=True)
    
    # Format the data
    transcript_data = []
    for segment in segments:
        for word in segment.words:
            transcript_data.append({
                "word": word.word.strip(),
                "start": word.start,
                "end": word.end
            })
            
    # Delete temporary file to save space
    os.remove(temp_file)
    
    return {"transcript": transcript_data}