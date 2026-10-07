from fastapi import FastAPI

from src.core.config import settings
from src.modules import modules_router

app = FastAPI()
app.include_router(modules_router)


@app.get("/")
async def home():
    return {"message": "Hellow World!"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.run.HOST,
        port=settings.run.PORT,
        reload=settings.run.RELOAD,
    )
