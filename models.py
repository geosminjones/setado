"""Data models for TodoUI."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Project:
    """Project data model."""
    id: Optional[int]
    name: str
    description: Optional[str] = None
    is_archived: bool = False
    created_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class Task:
    """Task data model."""
    id: Optional[int]
    project_id: int
    title: str
    priority: int = 0
    due_date: Optional[datetime] = None
    is_completed: bool = False
    is_deleted: bool = False
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
