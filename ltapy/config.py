"""
This module holds the available configuration options for the package.
"""

#: Default LightTools version.
LT_VERSION = "8.5.0"

#: Timeout in seconds after that a connection attempt to LightTools is
#: aborted.
TIMEOUT = 60

#: Default version of the JumpStart macro function library.
JS_VERSION = "LTCOM64.JSNET"

# Default logging configuration for LightTools.
_LOGGING = {
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
