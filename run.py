import os

import uvicorn
from uvicorn.config import LOGGING_CONFIG


def env_flag(name: str, default: str = "true") -> bool:
    return os.getenv(name, default).lower() in {"1", "true", "yes", "on"}


if __name__ == "__main__":
    # 修改默认日志配置
    LOGGING_CONFIG["formatters"]["default"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
    LOGGING_CONFIG["formatters"]["default"]["datefmt"] = "%Y-%m-%d %H:%M:%S"
    LOGGING_CONFIG["formatters"]["access"][
        "fmt"
    ] = '%(asctime)s - %(levelname)s - %(client_addr)s - "%(request_line)s" %(status_code)s'
    LOGGING_CONFIG["formatters"]["access"]["datefmt"] = "%Y-%m-%d %H:%M:%S"

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.getenv("APP_PORT", "9999")),
        reload=env_flag("UVICORN_RELOAD", "true"),
        log_config=LOGGING_CONFIG,
    )
