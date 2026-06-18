import asyncio
import copy
import sys
from pathlib import Path

import uvicorn


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


LOG_CONFIG = copy.deepcopy(uvicorn.config.LOGGING_CONFIG)
LOG_CONFIG["loggers"]["app"] = {
    "handlers": ["default"],
    "level": "INFO",
    "propagate": False,
}

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CERTS_DIR = PROJECT_ROOT / "certs"


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        ssl_keyfile=str(CERTS_DIR / "dev-key.pem"),
        ssl_certfile=str(CERTS_DIR / "dev-cert.pem"),
        log_level="info",
        log_config=LOG_CONFIG,
    )
