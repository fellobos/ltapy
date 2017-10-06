# Default LightTools version.
VERSION = "LightTools(64) 8.5.0"

# Timeout for a connection attempt to LightTools.
TIMEOUT = 60

# Default logging configuration for LightTools.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[%(asctime)s] %(name)s %(levelname)s - %(message)s"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "verbose"
        },
    },
    "loggers": {
        "lighttools": {  # must match logger name, e.g. lighttools.ltapi
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,  # due to default logger in jupyter qtconsole
        },
    }
}
