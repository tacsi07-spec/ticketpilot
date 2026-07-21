from fastapi import FastAPI

from backend.api.analyze import router as analyze_router


app = FastAPI(
    title="Brand Intelligence API",
    version="1.0.0",
)

app.include_router(analyze_router)


@app.get("/")
def root():
    return {
        "message": "Brand Intelligence API is running 🚀"
    }