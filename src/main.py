from fastapi import FastAPI

from src.core.config import settings
from src.core.logging import LOGGING_CONFIG, configure_logging
from src.modules import modules_router

configure_logging()

app = FastAPI(
    title=settings.app.TITLE,
    debug=settings.app.DEBUG,
    summary=settings.app.SUMMARY,
    description=settings.app.DESCRIPTION,
    version=settings.app.VERSION
)
app.include_router(modules_router)


@app.get("/")
async def home():
    return {"message": "Hello World!"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.run.HOST,
        port=settings.run.PORT,
        reload=settings.run.RELOAD,
        log_config=LOGGING_CONFIG,
        log_level=settings.app.LOGLEVEL.lower(),
    )
