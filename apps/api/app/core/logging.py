import logging
import sys

from app.core.config import settings


def configure_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format=(
            '{"level":"%(levelname)s","logger":"%(name)s",'
            '"message":"%(message)s","time":"%(asctime)s"}'
        ),
        stream=sys.stdout,
        force=True,
    )

