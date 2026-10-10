import logging.config
from copy import deepcopy
from typing import Any

import structlog
from structlog.stdlib import ProcessorFormatter
from uvicorn.config import LOGGING_CONFIG as UVICORN_LOGGING_CONFIG

from src.core.config import Environment, settings

JSON_ENVIRONMENTS = frozenset({"ci", "prod", "production"})


def _shared_processors() -> list[Any]:
    return [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]


def build_logging_config(environment: Environment, log_level: str) -> dict[str, Any]:
    """Build Uvicorn's logging configuration for the active environment."""
    config = deepcopy(UVICORN_LOGGING_CONFIG)

    for logger in config["loggers"].values():
        logger["level"] = log_level

    # Uvicorn configures only its own loggers. Add the root logger so that
    # application code can use logging.getLogger() without extra setup.
    config["root"] = {"handlers": ["default"], "level": log_level}

    if environment in JSON_ENVIRONMENTS:
        json_formatter = {
            "()": ProcessorFormatter,
            "processor": structlog.processors.JSONRenderer(),
            "foreign_pre_chain": _shared_processors(),
        }
        config["formatters"]["default"] = json_formatter
        config["formatters"]["access"] = deepcopy(json_formatter)

    return config


def configure_logging() -> None:
    """Configure structlog and standard-library logging for this application."""
    processors = _shared_processors()
    if settings.app.ENVIRONMENT in JSON_ENVIRONMENTS:
        processors.append(ProcessorFormatter.wrap_for_formatter)
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    logging.config.dictConfig(LOGGING_CONFIG)


LOGGING_CONFIG = build_logging_config(
    environment=settings.app.ENVIRONMENT,
    log_level=settings.app.LOGLEVEL,
)
