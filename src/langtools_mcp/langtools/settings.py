import os
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

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
    model_config = SettingsConfigDict(env_prefix="LANGTOOLS_")
    BIN_DIR: str = Field(
        description="Binary Directory to install any necessary tools",
        default=str(BIN_DIR),
    )


class PythonToolSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LANGTOOLS_PYTHON")
    TOOLS: list[Literal["ruff", "pyright"]] = Field(
        description="Python tools to use. To see supported tools refer to documentation",
        default=["ruff", "pyright"],
    )

    BIN_DIR: str = Field(
        description="Bin directory for python tools",
        default=str(BIN_DIR),
    )


class GoToolSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LANGTOOLS_GO")
    GO_TOOLS: list[Literal["vet"]] = Field(
        description="Go tools to use on your project. To see supported tools refer to documentation",
        default=["vet"],
    )

    BIN_DIR: str = Field(
        description="Bin directory for go tools",
        default=str(BIN_DIR),
    )


if __name__ == "__main__":
    os.environ["LANGTOOLS_PYTHON_TOOLS"] = '["ruff"]'
    settings = Settings()
    print(settings)
