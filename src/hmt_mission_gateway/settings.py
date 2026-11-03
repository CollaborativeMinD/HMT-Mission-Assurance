"""Strict deployment settings and owner-provisioned secret admission."""

import stat
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="HMT_", extra="forbid", frozen=True)
    token_file: Path = Path("/run/secrets/mcp_token")
    metrics_token_file: Path = Path("/run/secrets/metrics_token")
    max_body_bytes: int = Field(default=1048576, ge=1024, le=1048576)
    max_active: int = Field(default=4, ge=1, le=32)
    request_seconds: float = Field(default=30, gt=0, le=120)
    allowed_hosts: list[str] = ["localhost", "127.0.0.1", "mcp"]


def read_secret(path: Path) -> SecretStr:
    if path.is_symlink():
        raise ValueError("SECRET_SYMLINK")
    info = path.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_size > 4096:
        raise ValueError("SECRET_FILE_INVALID")
    if info.st_mode & 0o022:
        raise ValueError("SECRET_WRITABLE_BY_OTHERS")
    value = path.read_text().strip()
    if len(value) < 32 or len(value) > 512 or not value.isascii() or any(c.isspace() for c in value):
        raise ValueError("SECRET_FORMAT_INVALID")
    return SecretStr(value)
