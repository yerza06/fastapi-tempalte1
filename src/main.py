from fastapi import FastAPI

app = FastAPI()

@app.get('/')
async def home():
    return {"message": "Hellow World!"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app)
