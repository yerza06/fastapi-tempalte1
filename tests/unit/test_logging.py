from structlog.stdlib import ProcessorFormatter
from uvicorn.config import LOGGING_CONFIG as UVICORN_LOGGING_CONFIG

from src.core.logging import build_logging_config


def test_local_logging_uses_uvicorn_formatters() -> None:
    config = build_logging_config("local", "DEBUG")

    assert config["formatters"] == UVICORN_LOGGING_CONFIG["formatters"]
    assert config["root"] == {"handlers": ["default"], "level": "DEBUG"}
    assert all(logger["level"] == "DEBUG" for logger in config["loggers"].values())


def test_ci_logging_uses_json_formatter() -> None:
    config = build_logging_config("ci", "INFO")

    assert config["formatters"]["default"]["()"] is ProcessorFormatter
    assert config["formatters"]["access"]["()"] is ProcessorFormatter
    assert (
        config["formatters"]["default"]["processor"](
            None, "info", {"event": "application started"}
        )
        == '{"event": "application started"}'
    )
