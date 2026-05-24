from .base import *  # noqa: F401, F403

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

LOGGING["formatters"]["colored"] = {  # type: ignore[index]  # noqa: F405
    "()": "colorlog.ColoredFormatter",
    "format": "%(log_color)s%(levelname)-8s%(reset)s %(asctime)s %(name)s %(funcName)s():%(lineno)d — %(message)s",
    "datefmt": "%Y-%m-%d %H:%M:%S",
    "log_colors": {
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold_red",
    },
}
LOGGING["handlers"]["console"]["formatter"] = "colored"  # type: ignore[index]  # noqa: F405
