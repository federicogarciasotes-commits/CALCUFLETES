import asyncio
import copy
import sys

import uvicorn


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


LOG_CONFIG = copy.deepcopy(uvicorn.config.LOGGING_CONFIG)
LOG_CONFIG["loggers"]["app"] = {
    "handlers": ["default"],
    "level": "INFO",
    "propagate": False,
}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        ssl_keyfile="certs/dev-key.pem",
        ssl_certfile="certs/dev-cert.pem",
        log_level="info",
        log_config=LOG_CONFIG,
    )
