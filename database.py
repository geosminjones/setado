"""Database operations for TodoUI."""

import sqlite3
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import Config
from models import Project, Task


class DatabaseManager:
    """Manages SQLite database operations."""

    def __init__(self, config: Config):
        self.db_path = Path(config.database_path)
        self.backup_path = Path(config.backup_path)

        # Ensure directories exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.backup_path.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                is_archived INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                archived_at TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                priority INTEGER DEFAULT 0,
                due_date TEXT,
                is_completed INTEGER DEFAULT 0,
                is_deleted INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                deleted_at TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        """)

        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")

        self.conn.commit()

    def _backup(self) -> None:
        """Create a timestamped backup of the database."""
        if not self.db_path.exists():
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_path / f"todoui_{timestamp}.db"

        # Close connection temporarily for clean backup
        self.conn.close()
        shutil.copy2(self.db_path, backup_file)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row

    def close(self) -> None:
        """Close database connection."""
        self.conn.close()

    # Project operations

    def create_project(self, name: str, description: Optional[str] = None) -> Project:
        """Create a new project."""
        now = datetime.now().isoformat()
        cursor = self.conn.cursor()

        cursor.execute(
            "INSERT INTO projects (name, description, created_at) VALUES (?, ?, ?)",
            (name, description, now)
        )
        self.conn.commit()
        self._backup()

        return Project(
            id=cursor.lastrowid,
            name=name,
            description=description,
            is_archived=False,
            created_at=datetime.fromisoformat(now)
        )

    def get_projects(self, include_archived: bool = False) -> list[Project]:
        """Get all projects, optionally including archived ones."""
        cursor = self.conn.cursor()

        if include_archived:
            cursor.execute("SELECT * FROM projects ORDER BY name")
        else:
            cursor.execute("SELECT * FROM projects WHERE is_archived = 0 ORDER BY name")

        projects = []
        for row in cursor.fetchall():
            projects.append(Project(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                is_archived=bool(row["is_archived"]),
                created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
                archived_at=datetime.fromisoformat(row["archived_at"]) if row["archived_at"] else None
            ))

        return projects

    def archive_project(self, project_id: int) -> None:
        """Archive a project."""
        now = datetime.now().isoformat()
        cursor = self.conn.cursor()

        cursor.execute(
            "UPDATE projects SET is_archived = 1, archived_at = ? WHERE id = ?",
            (now, project_id)
        )
        self.conn.commit()
        self._backup()

    def delete_project(self, project_id: int) -> None:
        """Hard delete a project and all its tasks."""
        cursor = self.conn.cursor()

        # Delete tasks first (or rely on CASCADE)
        cursor.execute("DELETE FROM tasks WHERE project_id = ?", (project_id,))
        cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))

        self.conn.commit()
        self._backup()

    # Task operations

    def create_task(
        self,
        project_id: int,
        title: str,
        priority: int = 0,
        due_date: Optional[datetime] = None
    ) -> Task:
        """Create a new task."""
        now = datetime.now().isoformat()
        due_str = due_date.isoformat() if due_date else None
        cursor = self.conn.cursor()

        cursor.execute(
            """INSERT INTO tasks (project_id, title, priority, due_date, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (project_id, title, priority, due_str, now)
        )
        self.conn.commit()
        self._backup()

        return Task(
            id=cursor.lastrowid,
            project_id=project_id,
            title=title,
            priority=priority,
            due_date=due_date,
            is_completed=False,
            is_deleted=False,
            created_at=datetime.fromisoformat(now)
        )

    def get_tasks(self, project_id: int, include_deleted: bool = False) -> list[Task]:
        """Get all tasks for a project."""
        cursor = self.conn.cursor()

        if include_deleted:
            cursor.execute(
                "SELECT * FROM tasks WHERE project_id = ? ORDER BY priority, created_at",
                (project_id,)
            )
        else:
            cursor.execute(
                """SELECT * FROM tasks
                   WHERE project_id = ? AND is_deleted = 0
                   ORDER BY priority, created_at""",
                (project_id,)
            )

        tasks = []
        for row in cursor.fetchall():
            tasks.append(Task(
                id=row["id"],
                project_id=row["project_id"],
                title=row["title"],
                priority=row["priority"],
                due_date=datetime.fromisoformat(row["due_date"]) if row["due_date"] else None,
                is_completed=bool(row["is_completed"]),
                is_deleted=bool(row["is_deleted"]),
                created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
                completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
                deleted_at=datetime.fromisoformat(row["deleted_at"]) if row["deleted_at"] else None
            ))

        return tasks

    def get_tasks_with_due_dates(self, project_id: Optional[int] = None) -> list[Task]:
        """Get active tasks with due dates, sorted nearest-first.

        When project_id is None, returns tasks from all non-archived projects.
        When project_id is provided, returns tasks from that project only.
        """
        cursor = self.conn.cursor()

        if project_id is None:
            cursor.execute(
                """SELECT t.* FROM tasks t
                   JOIN projects p ON t.project_id = p.id
                   WHERE t.due_date IS NOT NULL
                     AND t.is_completed = 0
                     AND t.is_deleted = 0
                     AND p.is_archived = 0
                   ORDER BY t.due_date ASC"""
            )
        else:
            cursor.execute(
                """SELECT * FROM tasks
                   WHERE project_id = ?
                     AND due_date IS NOT NULL
                     AND is_completed = 0
                     AND is_deleted = 0
                   ORDER BY due_date ASC""",
                (project_id,)
            )

        tasks = []
        for row in cursor.fetchall():
            tasks.append(Task(
                id=row["id"],
                project_id=row["project_id"],
                title=row["title"],
                priority=row["priority"],
                due_date=datetime.fromisoformat(row["due_date"]) if row["due_date"] else None,
                is_completed=bool(row["is_completed"]),
                is_deleted=bool(row["is_deleted"]),
                created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
                completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
                deleted_at=datetime.fromisoformat(row["deleted_at"]) if row["deleted_at"] else None
            ))

        return tasks

    def get_completed_tasks(self, project_id: Optional[int] = None) -> list[Task]:
        """Get completed tasks, sorted most-recently-completed first.

        When project_id is None, returns tasks from all non-archived projects.
        When project_id is provided, returns tasks from that project only.
        """
        cursor = self.conn.cursor()

        if project_id is None:
            cursor.execute(
                """SELECT t.* FROM tasks t
                   JOIN projects p ON t.project_id = p.id
                   WHERE t.is_completed = 1
                     AND t.is_deleted = 0
                     AND p.is_archived = 0
                   ORDER BY t.completed_at DESC"""
            )
        else:
            cursor.execute(
                """SELECT * FROM tasks
                   WHERE project_id = ?
                     AND is_completed = 1
                     AND is_deleted = 0
                   ORDER BY completed_at DESC""",
                (project_id,)
            )

        tasks = []
        for row in cursor.fetchall():
            tasks.append(Task(
                id=row["id"],
                project_id=row["project_id"],
                title=row["title"],
                priority=row["priority"],
                due_date=datetime.fromisoformat(row["due_date"]) if row["due_date"] else None,
                is_completed=bool(row["is_completed"]),
                is_deleted=bool(row["is_deleted"]),
                created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
                completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
                deleted_at=datetime.fromisoformat(row["deleted_at"]) if row["deleted_at"] else None
            ))

        return tasks

    def complete_task(self, task_id: int) -> None:
        """Mark a task as completed."""
        now = datetime.now().isoformat()
        cursor = self.conn.cursor()

        cursor.execute(
            "UPDATE tasks SET is_completed = 1, completed_at = ? WHERE id = ?",
            (now, task_id)
        )
        self.conn.commit()
        self._backup()

    def uncomplete_task(self, task_id: int) -> None:
        """Mark a task as not completed."""
        cursor = self.conn.cursor()

        cursor.execute(
            "UPDATE tasks SET is_completed = 0, completed_at = NULL WHERE id = ?",
            (task_id,)
        )
        self.conn.commit()
        self._backup()

    def delete_task(self, task_id: int) -> None:
        """Soft delete a task."""
        now = datetime.now().isoformat()
        cursor = self.conn.cursor()

        cursor.execute(
            "UPDATE tasks SET is_deleted = 1, deleted_at = ? WHERE id = ?",
            (now, task_id)
        )
        self.conn.commit()
        self._backup()

    def update_task(self, task_id: int, **kwargs) -> None:
        """Update task fields."""
        if not kwargs:
            return

        # Build update query
        allowed_fields = {"title", "priority", "due_date", "is_completed", "is_deleted"}
        updates = []
        values = []

        for key, value in kwargs.items():
            if key in allowed_fields:
                updates.append(f"{key} = ?")
                if key == "due_date" and value is not None:
                    values.append(value.isoformat() if isinstance(value, datetime) else value)
                else:
                    values.append(value)

        if not updates:
            return

        values.append(task_id)
        query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"

        cursor = self.conn.cursor()
        cursor.execute(query, values)
        self.conn.commit()
        self._backup()
