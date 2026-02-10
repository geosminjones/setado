"""Configuration management for TodoUI."""

import json
import sys
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Optional


def _get_app_dir() -> Path:
    """Get the application directory, handling both script and frozen executable."""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable (PyInstaller, cx_Freeze, etc.)
        return Path(sys.executable).parent
    else:
        # Running as script
        return Path(__file__).parent


# Default paths relative to application directory
APP_DIR = _get_app_dir()
DEFAULT_DATA_DIR = APP_DIR / "data"
DEFAULT_DB_PATH = DEFAULT_DATA_DIR / "todoui.db"
DEFAULT_BACKUP_DIR = DEFAULT_DATA_DIR / "backups"
CONFIG_FILE = APP_DIR / "config.json"


@dataclass
class Config:
    """Application configuration."""
    database_path: str
    backup_path: str
    frame_count: int = 3
    default_priority: int = 0
    theme: str = "dark"
    frame_projects: list = field(default_factory=list)

    @classmethod
    def default(cls) -> "Config":
        """Create default configuration."""
        return cls(
            database_path=str(DEFAULT_DB_PATH),
            backup_path=str(DEFAULT_BACKUP_DIR),
            frame_count=3,
            default_priority=0
        )


class ConfigManager:
    """Singleton configuration manager."""

    _instance: Optional["ConfigManager"] = None

    def __new__(cls) -> "ConfigManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self._config: Optional[Config] = None
            self._load_or_create()

    def _load_or_create(self) -> None:
        """Load config from file or create defaults."""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._config = Config(**data)
            except Exception:
                # Any error loading config falls back to defaults
                self._config = Config.default()
                self._save()
        else:
            self._config = Config.default()
            self._ensure_directories()
            self._save()

    def _ensure_directories(self) -> None:
        """Create default directories if they don't exist."""
        Path(self._config.database_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self._config.backup_path).mkdir(parents=True, exist_ok=True)

    def _save(self) -> None:
        """Save configuration to file."""
        with open(CONFIG_FILE, "w") as f:
            json.dump(asdict(self._config), f, indent=2)

    @property
    def config(self) -> Config:
        """Get current configuration."""
        return self._config

    def update(self, **kwargs) -> None:
        """Update configuration values."""
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
        self._save()


def get_config() -> Config:
    """Get the application configuration."""
    return ConfigManager().config
