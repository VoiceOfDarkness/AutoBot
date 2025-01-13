import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logger(
    name: str = "GameBot",
    level: int = logging.INFO,
    log_dir: str = "logs",
) -> logging.Logger:
    logger = logging.getLogger(name)

    if not logger.handlers:
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        main_log_file = os.path.join(log_dir, f"{name.lower()}.log")
        file_handler = RotatingFileHandler(
            main_log_file,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        api_log_file = os.path.join(log_dir, f"{name.lower()}_api.log")
        api_handler = RotatingFileHandler(
            api_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        api_handler.setFormatter(formatter)
        api_handler.addFilter(lambda record: getattr(record, "api_response", False))
        logger.addHandler(api_handler)

        logger.setLevel(level)

    return logger


def log_api_response(
    logger: logging.Logger, endpoint: str, response: str, status: str = "success"
):
    extra = {"api_response": True}
    logger.info(
        f"API Response - Endpoint: {endpoint}, Status: {status}, Response: {response}",
        extra=extra,
    )


logger = setup_logger()
