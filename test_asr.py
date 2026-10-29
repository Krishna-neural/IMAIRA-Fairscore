from faster_whisper import WhisperModel
import json
import time

# Start the timer
start_time = time.time()

print("Loading the model (this will download a few GBs the first time)...")
# Load the model exactly as the guide specifies
model = WhisperModel("large-v3", device="cuda", compute_type="int8_float16")

print("Transcribing audio...")
# Transcribe with word-level timestamps enabled
segments, info = model.transcribe("asr/test.wav", word_timestamps=True)

# Prepare the data to save as JSON
output_data = {"language": info.language, "words": []}

for segment in segments:
    for word in segment.words:
        print(f"[{word.start:.2f}s -> {word.end:.2f}s] {word.word}")
        output_data["words"].append({
            "word": word.word,
            "start": word.start,
            "end": word.end
        })

# Save to a JSON file
with open("test_output.json", "w") as f:
    json.dump(output_data, f, indent=4)

print(f"Done! Saved to test_output.json.")
print(f"Total time taken: {time.time() - start_time:.2f} seconds")