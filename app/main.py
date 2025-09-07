from fastapi import FastAPI

app = FastAPI(title="User Service", version="1.0.0")


@app.get("/health")
def health():
    return {"status": "ok", "service": "users"}