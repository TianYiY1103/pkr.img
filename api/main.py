from fastapi import FastAPI

app = FastAPI(title="pkr.img API")

@app.get("/health")
def health():
    return {"status": "ok"}
