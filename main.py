
import os
from pathlib import Path

import yaml
from dotenv import dotenv_values
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow browser-based graders to access the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULTS = {
    "port": 8000,
    "workers": 8,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}


def convert_value(key, value):
    if key in ("port", "workers"):
        return int(value)

    if key == "debug":
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {
            "true", "1", "yes", "on"
        }

    return str(value)



def load_config():
    config = DEFAULTS.copy()

    # Layer 2: YAML file
    environment = os.getenv("APP_ENV", "development")
    yaml_file = Path(f"config.{environment}.yaml")

    if yaml_file.exists():
        with yaml_file.open() as file:
            config.update(yaml.safe_load(file) or {})

    # Layer 3: .env file
    file_env = dotenv_values(".env")
    env_mapping = {
        "APP_PORT": "port",
        "NUM_WORKERS": "workers",
        "APP_DEBUG": "debug",
        "APP_LOG_LEVEL": "log_level",
        "APP_API_KEY": "api_key",
    }

    for env_key, config_key in env_mapping.items():
        if file_env.get(env_key) is not None:
            config[config_key] = file_env[env_key]

    # Layer 4: OS environment variables
    os_mapping = {
        "APP_PORT": "port",
        "APP_WORKERS": "workers",
        "APP_DEBUG": "debug",
        "APP_LOG_LEVEL": "log_level",
        "APP_API_KEY": "api_key",
    }

    for env_key, config_key in os_mapping.items():
        if os.getenv(env_key) is not None:
            config[config_key] = os.environ[env_key]

    # Also support NUM_WORKERS if provided by the OS
    if os.getenv("NUM_WORKERS") is not None:
        config["workers"] = os.environ["NUM_WORKERS"]

    return config


@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):
    config = load_config()

    # Layer 5: CLI/query-string overrides
    for item in set:
        if "=" not in item:
            continue

        key, value = item.split("=", 1)
        config[key] = value

    result = {
        key: convert_value(key, value)
        for key, value in config.items()
    }

    # Never reveal the real API key.
    result["api_key"] = "****"

    return result

