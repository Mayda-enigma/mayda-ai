from fastapi import FastAPI, UploadFile, File
import whisper

app = FastAPI(title="Mayda Voice Service")

model = whisper.load_model("base")

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    audio = await file.read()
    with open("/tmp/audio.wav", "wb") as f:
        f.write(audio)
    result = model.transcribe("/tmp/audio.wav")
    return {"text": result["text"], "language": result.get("language", "en")}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
