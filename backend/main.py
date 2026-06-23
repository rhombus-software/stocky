from src.app import app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.app:app", host="127.0.0.1", port=5000, reload=True)
