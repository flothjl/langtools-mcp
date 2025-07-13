import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings

# XDG Base Directory paths with fallbacks per spec
XDG_CONFIG_HOME = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
XDG_DATA_HOME = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
XDG_CACHE_HOME = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
XDG_STATE_HOME = Path(
    os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state")
)
APP_NAME = "langtools_mcp"
BIN_DIR = XDG_DATA_HOME / "langtools_mcp" / "bin"


class Settings(BaseSettings):
    BIN_DIR: str = Field(
        description="Binary Directory to install any necessary tools",
        default=str(BIN_DIR),
    )


if __name__ == "__main__":
    settings = Settings()
    print(settings)
