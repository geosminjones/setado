"""Custom PyQt6 widgets for TodoUI - themed with jframes."""

import os
import tempfile
from datetime import datetime
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton,
    QLineEdit, QSpinBox, QDateEdit, QLabel, QDialog,
    QTextEdit, QCheckBox, QFrame, QFileDialog, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QTimer
from PyQt6.QtGui import QFont

from jframes import (
    get_colors, get_dropdown_arrow_path, get_scrollbar_qss,
    batch_update, MessageBox, ConfirmDialog, FONT_FAMILY,
    set_theme, get_available_themes, get_current_theme
)
from database import DatabaseManager
from models import Task
from config import get_config, ConfigManager


def _input_qss(colors: dict) -> str:
    """Common QSS for input fields (QLineEdit, QSpinBox, QDateEdit)."""
    return f"""
        background-color: {colors['bg_medium']};
        color: {colors['text_primary']};
        border: 1px solid {colors['separator']};
        border-radius: 6px;
        padding: 4px 8px;
        font-family: {FONT_FAMILY};
        font-size: 12px;
    """


def _combo_qss(colors: dict) -> str:
    """Common QSS for QComboBox with themed dropdown arrow."""
    arrow_path = get_dropdown_arrow_path(colors['text_primary'])
    return f"""
        QComboBox {{
            background-color: {colors['bg_medium']};
            color: {colors['text_primary']};
            border: 1px solid {colors['separator']};
            border-radius: 6px;
            padding: 4px 28px 4px 8px;
            font-family: {FONT_FAMILY};
            font-size: 12px;
        }}
        QComboBox:hover {{
            border-color: {colors['text_secondary']};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 24px;
        }}
        QComboBox::down-arrow {{
            image: url({arrow_path});
            width: 10px;
            height: 7px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {colors['card_bg']};
            color: {colors['text_primary']};
            border: 1px solid {colors['separator']};
            border-radius: 6px;
            selection-background-color: {colors['bg_light']};
            selection-color: {colors['text_primary']};
            outline: 0;
            padding: 4px;
        }}
    """


def _btn_success(colors: dict) -> str:
    """QSS for success/primary action buttons."""
    return f"""
        QPushButton {{
            background-color: {colors['success']};
            color: #ffffff;
            border: none;
            border-radius: 6px;
            padding: 6px 14px;
            font-family: {FONT_FAMILY};
            font-size: 12px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: #2ecc71;
        }}
    """


def _btn_danger(colors: dict) -> str:
    """QSS for danger/destructive action buttons."""
    return f"""
        QPushButton {{
            background-color: {colors['danger']};
            color: #ffffff;
            border: none;
            border-radius: 6px;
            padding: 6px 14px;
            font-family: {FONT_FAMILY};
            font-size: 12px;
        }}
        QPushButton:hover {{
            background-color: {colors['danger_hover']};
        }}
    """


def _btn_neutral(colors: dict) -> str:
    """QSS for neutral/secondary buttons."""
    return f"""
        QPushButton {{
            background-color: {colors['bg_light']};
            color: {colors['text_primary']};
            border: none;
            border-radius: 6px;
            padding: 6px 14px;
            font-family: {FONT_FAMILY};
            font-size: 12px;
        }}
        QPushButton:hover {{
            background-color: {colors['separator']};
        }}
    """


def _checkbox_qss(colors: dict) -> str:
    """QSS for themed checkboxes."""
    return f"""
        QCheckBox {{
            color: {colors['text_primary']};
            spacing: 6px;
            font-family: {FONT_FAMILY};
            font-size: 12px;
        }}
        QCheckBox::indicator {{
            width: 16px;
            height: 16px;
            border: 2px solid {colors['separator']};
            border-radius: 4px;
            background-color: {colors['bg_medium']};
        }}
        QCheckBox::indicator:hover {{
            border-color: {colors['text_secondary']};
        }}
        QCheckBox::indicator:checked {{
            background-color: {colors['success']};
            border-color: {colors['success']};
        }}
    """


def _get_spinbox_arrow_paths(color: str) -> tuple[str, str]:
    """Generate up and down arrow SVG images for spinbox buttons.

    Returns (up_path, down_path) with forward slashes for QSS url().
    """
    up_svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="6" viewBox="0 0 10 6">'
        f'<polygon points="5,0 10,6 0,6" fill="{color}"/>'
        '</svg>'
    )
    down_svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="6" viewBox="0 0 10 6">'
        f'<polygon points="5,6 0,0 10,0" fill="{color}"/>'
        '</svg>'
    )
    tmp_dir = tempfile.gettempdir()
    up_path = os.path.join(tmp_dir, 'todoui_spin_up.svg')
    down_path = os.path.join(tmp_dir, 'todoui_spin_down.svg')

    with open(up_path, 'w') as f:
        f.write(up_svg)
    with open(down_path, 'w') as f:
        f.write(down_svg)

    return up_path.replace('\\', '/'), down_path.replace('\\', '/')


def _spinbox_qss(colors: dict) -> str:
    """QSS for themed spinboxes with visible arrow indicators."""
    up_path, down_path = _get_spinbox_arrow_paths(colors['text_primary'])
    return f"""
        QSpinBox {{
            background-color: {colors['bg_medium']};
            color: {colors['text_primary']};
            border: 1px solid {colors['separator']};
            border-radius: 6px;
            padding: 4px 4px 4px 8px;
            font-family: {FONT_FAMILY};
            font-size: 12px;
        }}
        QSpinBox::up-button, QSpinBox::down-button {{
            background-color: {colors['bg_light']};
            border: none;
            width: 18px;
        }}
        QSpinBox::up-button {{
            border-top-right-radius: 6px;
            border-bottom: 1px solid {colors['separator']};
        }}
        QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
            background-color: {colors['separator']};
        }}
        QSpinBox::down-button {{
            border-bottom-right-radius: 6px;
        }}
        QSpinBox::up-arrow {{
            image: url({up_path});
            width: 10px;
            height: 6px;
        }}
        QSpinBox::down-arrow {{
            image: url({down_path});
            width: 10px;
            height: 6px;
        }}
    """


def _dateedit_qss(colors: dict) -> str:
    """QSS for themed date edits."""
    return f"""
        QDateEdit {{
            background-color: {colors['bg_medium']};
            color: {colors['text_primary']};
            border: 1px solid {colors['separator']};
            border-radius: 6px;
            padding: 4px 8px;
            font-family: {FONT_FAMILY};
            font-size: 12px;
        }}
        QDateEdit::drop-down {{
            border: none;
            width: 20px;
        }}
        QDateEdit QCalendarWidget {{
            background-color: {colors['card_bg']};
            color: {colors['text_primary']};
        }}
    """


class NewProjectDialog(QDialog):
    """Themed dialog for creating a new project."""

    def __init__(self, parent=None):
        super().__init__(parent)
        colors = get_colors()

        self.setWindowTitle("New Project")
        self.setMinimumWidth(350)
        self.setStyleSheet(f"background-color: {colors['bg_dark']};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Name field
        name_label = QLabel("Project Name:")
        name_label.setFont(QFont(FONT_FAMILY, 11))
        name_label.setStyleSheet(f"color: {colors['text_primary']};")
        layout.addWidget(name_label)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter project name")
        self.name_edit.setStyleSheet(_input_qss(colors))
        self.name_edit.setFont(QFont(FONT_FAMILY, 12))
        self.name_edit.setMinimumHeight(32)
        layout.addWidget(self.name_edit)

        # Description field
        desc_label = QLabel("Description (optional):")
        desc_label.setFont(QFont(FONT_FAMILY, 11))
        desc_label.setStyleSheet(f"color: {colors['text_primary']};")
        layout.addWidget(desc_label)

        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText("Enter project description")
        self.desc_edit.setMaximumHeight(100)
        self.desc_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {colors['bg_medium']};
                color: {colors['text_primary']};
                border: 1px solid {colors['separator']};
                border-radius: 6px;
                padding: 6px;
                font-family: {FONT_FAMILY};
                font-size: 12px;
            }}
        """)
        layout.addWidget(self.desc_edit)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        ok_btn = QPushButton("Create")
        ok_btn.setStyleSheet(_btn_success(colors))
        ok_btn.setMinimumHeight(32)
        ok_btn.clicked.connect(self.accept)
        btn_row.addWidget(ok_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(_btn_neutral(colors))
        cancel_btn.setMinimumHeight(32)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        layout.addLayout(btn_row)

    def get_data(self) -> tuple[str, Optional[str]]:
        """Get the entered project data."""
        name = self.name_edit.text().strip()
        desc = self.desc_edit.toPlainText().strip() or None
        return name, desc


class DueDateDialog(QDialog):
    """Themed dialog for setting a due date on an existing task."""

    def __init__(self, current_date: Optional[datetime] = None, parent=None):
        super().__init__(parent)
        colors = get_colors()

        self.setWindowTitle("Set Due Date")
        self.setMinimumWidth(280)
        self.setStyleSheet(f"background-color: {colors['bg_dark']};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self.use_date_check = QCheckBox("Set due date")
        self.use_date_check.setChecked(current_date is not None)
        self.use_date_check.setStyleSheet(_checkbox_qss(colors))
        layout.addWidget(self.use_date_check)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setStyleSheet(_dateedit_qss(colors))
        self.date_edit.setMinimumHeight(32)
        if current_date:
            self.date_edit.setDate(QDate(current_date.year, current_date.month, current_date.day))
        else:
            self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setEnabled(current_date is not None)
        self.use_date_check.toggled.connect(self.date_edit.setEnabled)
        layout.addWidget(self.date_edit)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        ok_btn = QPushButton("OK")
        ok_btn.setStyleSheet(_btn_success(colors))
        ok_btn.setMinimumHeight(32)
        ok_btn.clicked.connect(self.accept)
        btn_row.addWidget(ok_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(_btn_neutral(colors))
        cancel_btn.setMinimumHeight(32)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        layout.addLayout(btn_row)

    def get_date(self) -> Optional[datetime]:
        """Get the selected date, or None if unchecked."""
        if self.use_date_check.isChecked():
            qdate = self.date_edit.date()
            return datetime(qdate.year(), qdate.month(), qdate.day())
        return None


class TaskListItem(QFrame):
    """Themed task row widget displayed in scroll area."""

    toggled = pyqtSignal(int, bool)  # task_id, is_completed
    deleted = pyqtSignal(int)  # task_id
    priority_changed = pyqtSignal(int, int)  # task_id, new_priority
    due_date_changed = pyqtSignal(int, object)  # task_id, new_due_date

    def __init__(self, task: Task, parent=None):
        super().__init__(parent)
        self.task = task
        colors = get_colors()

        # Style the frame as a themed row
        self.setStyleSheet(f"""
            TaskListItem {{
                background-color: {colors['bg_medium']};
                border-radius: 6px;
            }}
        """)
        self.setMinimumHeight(38)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        # Checkbox for completion
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(task.is_completed)
        self.checkbox.setStyleSheet(_checkbox_qss(colors))
        self.checkbox.stateChanged.connect(self._on_toggle)
        layout.addWidget(self.checkbox)

        # Priority spinbox
        self.priority_spin = QSpinBox()
        self.priority_spin.setRange(-999, 999)
        self.priority_spin.setValue(task.priority)
        self.priority_spin.setMaximumWidth(60)
        self.priority_spin.setToolTip("Priority (higher = lower urgency)")
        self.priority_spin.setStyleSheet(_spinbox_qss(colors))
        self.priority_spin.setKeyboardTracking(False)
        if task.is_completed:
            self.priority_spin.setEnabled(False)
        self.priority_spin.valueChanged.connect(self._on_priority_changed)
        layout.addWidget(self.priority_spin)

        # Title label
        self.title_label = QLabel(task.title)
        self.title_label.setWordWrap(True)
        self.title_label.setFont(QFont(FONT_FAMILY, 12))
        if task.is_completed:
            self.title_label.setStyleSheet(
                f"color: {colors['text_secondary']}; text-decoration: line-through; background: transparent;"
            )
        else:
            self.title_label.setStyleSheet(
                f"color: {colors['text_primary']}; background: transparent;"
            )
        layout.addWidget(self.title_label, 1)

        # Due date button
        due_text = task.due_date.strftime("%m/%d") if task.due_date else "..."
        self.due_btn = QPushButton(due_text)
        self.due_btn.setMaximumWidth(50)
        self.due_btn.setToolTip("Click to set/change due date")
        self.due_btn.setFont(QFont(FONT_FAMILY, 10))
        self.due_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {colors['text_secondary']};
                border: 1px solid {colors['separator']};
                border-radius: 4px;
                padding: 2px 6px;
            }}
            QPushButton:hover {{
                background-color: {colors['bg_light']};
            }}
        """)
        if task.is_completed:
            self.due_btn.setEnabled(False)
        self.due_btn.clicked.connect(self._on_due_date_clicked)
        layout.addWidget(self.due_btn)

        # Delete button
        delete_btn = QPushButton("X")
        delete_btn.setFixedSize(38, 28)
        delete_btn.setFont(QFont(FONT_FAMILY, 10, QFont.Weight.Bold))
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['danger']};
                color: #ffffff;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {colors['danger_hover']};
            }}
        """)
        delete_btn.clicked.connect(lambda: self.deleted.emit(task.id))
        layout.addWidget(delete_btn)

    def _on_toggle(self, state):
        """Handle checkbox toggle."""
        is_completed = state == Qt.CheckState.Checked.value
        self.toggled.emit(self.task.id, is_completed)

    def _on_priority_changed(self, value):
        """Handle priority spinbox change."""
        self.priority_changed.emit(self.task.id, value)

    def highlight(self):
        """Briefly highlight this task row to indicate it was repositioned."""
        colors = get_colors()
        self.setStyleSheet(f"""
            TaskListItem {{
                background-color: {colors['bg_light']};
                border: 1px solid {colors['success']};
                border-radius: 6px;
            }}
        """)
        QTimer.singleShot(1500, self._remove_highlight)

    def _remove_highlight(self):
        """Remove the highlight styling."""
        colors = get_colors()
        self.setStyleSheet(f"""
            TaskListItem {{
                background-color: {colors['bg_medium']};
                border-radius: 6px;
            }}
        """)

    def _on_due_date_clicked(self):
        """Open due date dialog."""
        dialog = DueDateDialog(self.task.due_date, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_date = dialog.get_date()
            self.due_date_changed.emit(self.task.id, new_date)


class ProjectTaskWidget(QFrame):
    """Themed widget for managing tasks within a project."""

    project_changed = pyqtSignal()
    project_selected = pyqtSignal()

    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.current_project_id: Optional[int] = None
        colors = get_colors()

        # Outer container styling
        self.setStyleSheet(f"""
            ProjectTaskWidget {{
                background-color: {colors['container_bg']};
                border-radius: 10px;
            }}
        """)

        self._setup_ui()
        self._refresh_projects()

    def _setup_ui(self):
        """Set up the widget UI with theme styling."""
        colors = get_colors()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # ── Project selection area (card) ──
        project_card = QFrame()
        project_card.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['card_bg']};
                border-radius: 8px;
            }}
        """)
        project_card_layout = QHBoxLayout(project_card)
        project_card_layout.setContentsMargins(10, 8, 10, 8)
        project_card_layout.setSpacing(8)

        self.project_combo = QComboBox()
        self.project_combo.setStyleSheet(_combo_qss(colors))
        self.project_combo.setMinimumHeight(32)
        self.project_combo.currentIndexChanged.connect(self._on_project_selected)
        project_card_layout.addWidget(self.project_combo, 1)

        new_project_btn = QPushButton("+ New Project")
        new_project_btn.setStyleSheet(_btn_success(colors))
        new_project_btn.setMinimumHeight(32)
        new_project_btn.clicked.connect(self._create_project)
        project_card_layout.addWidget(new_project_btn)

        layout.addWidget(project_card)

        # ── Active Tasks section ──
        active_header = QLabel("Active Tasks")
        active_header.setFont(QFont(FONT_FAMILY, 11, QFont.Weight.Bold))
        active_header.setStyleSheet(f"color: {colors['text_primary']}; background: transparent;")
        layout.addWidget(active_header)

        # Active tasks scroll area
        self.active_scroll = QScrollArea()
        self.active_scroll.setWidgetResizable(True)
        self.active_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.active_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scrollbar_qss = get_scrollbar_qss(vertical=True, transparent_track=True, width=10)
        self.active_scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            {scrollbar_qss}
        """)

        self.active_container = QWidget()
        self.active_container.setStyleSheet("background: transparent;")
        self.active_layout = QVBoxLayout(self.active_container)
        self.active_layout.setContentsMargins(0, 0, 0, 0)
        self.active_layout.setSpacing(4)
        self.active_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.active_scroll.setWidget(self.active_container)
        layout.addWidget(self.active_scroll, 2)

        # ── Completed Tasks section ──
        completed_header = QLabel("Completed")
        completed_header.setFont(QFont(FONT_FAMILY, 11, QFont.Weight.Bold))
        completed_header.setStyleSheet(f"color: {colors['text_secondary']}; background: transparent;")
        layout.addWidget(completed_header)

        # Completed tasks scroll area
        self.completed_scroll = QScrollArea()
        self.completed_scroll.setWidgetResizable(True)
        self.completed_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.completed_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.completed_scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            {scrollbar_qss}
        """)

        self.completed_container = QWidget()
        self.completed_container.setStyleSheet("background: transparent;")
        self.completed_layout = QVBoxLayout(self.completed_container)
        self.completed_layout.setContentsMargins(0, 0, 0, 0)
        self.completed_layout.setSpacing(4)
        self.completed_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.completed_scroll.setWidget(self.completed_container)
        layout.addWidget(self.completed_scroll, 1)

        # ── Add task row (card) ──
        add_card = QFrame()
        add_card.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['card_bg']};
                border-radius: 8px;
            }}
        """)
        add_card_layout = QHBoxLayout(add_card)
        add_card_layout.setContentsMargins(10, 8, 10, 8)
        add_card_layout.setSpacing(6)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Task title")
        self.title_edit.setStyleSheet(_input_qss(colors))
        self.title_edit.setMinimumHeight(30)
        self.title_edit.returnPressed.connect(self._add_task)
        add_card_layout.addWidget(self.title_edit, 2)

        self.priority_spin = QSpinBox()
        self.priority_spin.setRange(-999, 999)
        self.priority_spin.setValue(get_config().default_priority)
        self.priority_spin.setToolTip("Priority")
        self.priority_spin.setMaximumWidth(65)
        self.priority_spin.setStyleSheet(_spinbox_qss(colors))
        self.priority_spin.setMinimumHeight(30)
        add_card_layout.addWidget(self.priority_spin)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setSpecialValueText("No date")
        self.date_edit.setMinimumDate(QDate(2000, 1, 1))
        self.date_edit.setStyleSheet(_dateedit_qss(colors))
        self.date_edit.setMinimumHeight(30)
        add_card_layout.addWidget(self.date_edit)

        self.use_date_check = QCheckBox("Due")
        self.use_date_check.setStyleSheet(_checkbox_qss(colors))
        add_card_layout.addWidget(self.use_date_check)

        add_btn = QPushButton("+ Add")
        add_btn.setStyleSheet(_btn_success(colors))
        add_btn.setMinimumHeight(30)
        add_btn.clicked.connect(self._add_task)
        add_card_layout.addWidget(add_btn)

        layout.addWidget(add_card)

        # ── Management buttons ──
        mgmt_row = QHBoxLayout()
        mgmt_row.setSpacing(8)

        archive_btn = QPushButton("Archive Project")
        archive_btn.setStyleSheet(_btn_neutral(colors))
        archive_btn.clicked.connect(self._archive_project)
        mgmt_row.addWidget(archive_btn)

        delete_btn = QPushButton("Delete Project")
        delete_btn.setStyleSheet(_btn_danger(colors))
        delete_btn.clicked.connect(self._delete_project)
        mgmt_row.addWidget(delete_btn)

        layout.addLayout(mgmt_row)

    def _refresh_projects(self):
        """Refresh the project dropdown."""
        self.project_combo.blockSignals(True)
        current_id = self.current_project_id

        self.project_combo.clear()
        self.project_combo.addItem("-- Select Project --", None)

        projects = self.db.get_projects(include_archived=False)
        selected_index = 0

        for i, project in enumerate(projects):
            self.project_combo.addItem(project.name, project.id)
            if project.id == current_id:
                selected_index = i + 1

        self.project_combo.setCurrentIndex(selected_index)
        self.project_combo.blockSignals(False)

        if selected_index > 0:
            self._on_project_selected(selected_index)
        else:
            self.current_project_id = None
            self._clear_tasks()

    def _on_project_selected(self, index: int):
        """Handle project selection change."""
        project_id = self.project_combo.itemData(index)
        self.current_project_id = project_id
        self._refresh_tasks()
        self.project_selected.emit()

    def _refresh_tasks(self):
        """Refresh the task lists using scroll area layout."""
        self._clear_tasks()

        if self.current_project_id is None:
            return

        tasks = self.db.get_tasks(self.current_project_id)

        with batch_update(self.active_container):
            with batch_update(self.completed_container):
                for task in tasks:
                    widget = TaskListItem(task)
                    widget.toggled.connect(self._on_task_toggled)
                    widget.deleted.connect(self._on_task_deleted)
                    widget.priority_changed.connect(self._on_task_priority_changed)
                    widget.due_date_changed.connect(self._on_task_due_date_changed)

                    if task.is_completed:
                        self.completed_layout.addWidget(widget)
                    else:
                        self.active_layout.addWidget(widget)

    def _clear_tasks(self):
        """Clear both task scroll areas."""
        # Clear active tasks
        while self.active_layout.count():
            item = self.active_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        # Clear completed tasks
        while self.completed_layout.count():
            item = self.completed_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

    def _create_project(self):
        """Open dialog to create a new project."""
        dialog = NewProjectDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name, desc = dialog.get_data()
            if name:
                project = self.db.create_project(name, desc)
                self.current_project_id = project.id
                self.project_changed.emit()

    def _add_task(self):
        """Add a new task to the current project."""
        if self.current_project_id is None:
            MessageBox(self, "No Project", "Please select a project first.", "warning")
            return

        title = self.title_edit.text().strip()
        if not title:
            return

        priority = self.priority_spin.value()

        due_date = None
        if self.use_date_check.isChecked():
            qdate = self.date_edit.date()
            due_date = datetime(qdate.year(), qdate.month(), qdate.day())

        self.db.create_task(self.current_project_id, title, priority, due_date)

        # Reset inputs
        self.title_edit.clear()
        self.priority_spin.setValue(get_config().default_priority)
        self.use_date_check.setChecked(False)

        self._refresh_tasks()

    def _on_task_toggled(self, task_id: int, is_completed: bool):
        """Handle task completion toggle."""
        if is_completed:
            self.db.complete_task(task_id)
        else:
            self.db.uncomplete_task(task_id)
        self._refresh_tasks()

    def _on_task_deleted(self, task_id: int):
        """Handle task deletion."""
        self.db.delete_task(task_id)
        self._refresh_tasks()

    def _on_task_priority_changed(self, task_id: int, new_priority: int):
        """Handle task priority change - update DB, reposition, and highlight."""
        self.db.update_task(task_id, priority=new_priority)
        self._refresh_tasks()

        # Find the repositioned task widget and highlight it
        for i in range(self.active_layout.count()):
            item = self.active_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), TaskListItem):
                if item.widget().task.id == task_id:
                    item.widget().highlight()
                    self.active_scroll.ensureWidgetVisible(item.widget())
                    break

    def _on_task_due_date_changed(self, task_id: int, new_due_date):
        """Handle task due date change."""
        self.db.update_task(task_id, due_date=new_due_date)
        self._refresh_tasks()

    def _archive_project(self):
        """Archive the current project."""
        if self.current_project_id is None:
            return

        dialog = ConfirmDialog(
            self, "Archive Project",
            "Are you sure you want to archive this project?"
        )
        if dialog.get_result():
            self.db.archive_project(self.current_project_id)
            self.current_project_id = None
            self.project_changed.emit()

    def _delete_project(self):
        """Delete the current project."""
        if self.current_project_id is None:
            return

        dialog = ConfirmDialog(
            self, "Delete Project",
            "Are you sure you want to permanently delete this project and all its tasks?"
        )
        if dialog.get_result():
            self.db.delete_project(self.current_project_id)
            self.current_project_id = None
            self.project_changed.emit()

    def set_project_by_id(self, project_id: int):
        """Select a project by its ID. Falls back to '-- Select Project --' if not found."""
        for i in range(self.project_combo.count()):
            if self.project_combo.itemData(i) == project_id:
                self.project_combo.setCurrentIndex(i)
                return
        self.project_combo.setCurrentIndex(0)

    def refresh_from_external(self):
        """Refresh widget data (called when other widgets modify data)."""
        self._refresh_projects()


class SettingsWidget(QWidget):
    """Themed widget for application settings."""

    settings_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = get_config()
        self.config_manager = ConfigManager()
        self._setup_ui()

    def _setup_ui(self):
        """Set up the settings UI with theme styling."""
        colors = get_colors()

        self.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # ── Theme selector ──
        theme_frame, theme_content = self._styled_group("Theme")
        theme_layout = QHBoxLayout(theme_content)
        theme_layout.setContentsMargins(16, 16, 16, 16)
        theme_layout.setSpacing(8)

        theme_label = QLabel("Color theme:")
        theme_label.setFont(QFont(FONT_FAMILY, 11))
        theme_label.setStyleSheet(f"color: {colors['text_primary']}; background: transparent;")
        theme_layout.addWidget(theme_label)

        self.theme_combo = QComboBox()
        self.theme_combo.setStyleSheet(_combo_qss(colors))
        self.theme_combo.setMinimumHeight(32)
        themes = get_available_themes()
        current_theme = get_current_theme()
        for name, display_name in themes:
            self.theme_combo.addItem(display_name, name)
            if name == current_theme.name:
                self.theme_combo.setCurrentIndex(self.theme_combo.count() - 1)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()

        layout.addWidget(theme_frame)

        # ── Frame count settings ──
        frame_frame, frame_content = self._styled_group("Task Panel Layout")
        frame_layout = QHBoxLayout(frame_content)
        frame_layout.setContentsMargins(16, 16, 16, 16)
        frame_layout.setSpacing(8)

        frame_label = QLabel("Number of task frames:")
        frame_label.setFont(QFont(FONT_FAMILY, 11))
        frame_label.setStyleSheet(f"color: {colors['text_primary']}; background: transparent;")
        frame_layout.addWidget(frame_label)

        self.frame_spin = QSpinBox()
        self.frame_spin.setRange(1, 4)
        self.frame_spin.setValue(self.config.frame_count)
        self.frame_spin.setToolTip("Number of task columns displayed (1-4)")
        self.frame_spin.setStyleSheet(_spinbox_qss(colors))
        self.frame_spin.setMinimumHeight(32)
        frame_layout.addWidget(self.frame_spin)
        frame_layout.addStretch()

        layout.addWidget(frame_frame)

        # ── Default priority settings ──
        priority_frame, priority_content = self._styled_group("Task Defaults")
        priority_layout = QHBoxLayout(priority_content)
        priority_layout.setContentsMargins(16, 16, 16, 16)
        priority_layout.setSpacing(8)

        priority_label = QLabel("Default priority:")
        priority_label.setFont(QFont(FONT_FAMILY, 11))
        priority_label.setStyleSheet(f"color: {colors['text_primary']}; background: transparent;")
        priority_layout.addWidget(priority_label)

        self.default_priority_spin = QSpinBox()
        self.default_priority_spin.setRange(-999, 999)
        self.default_priority_spin.setValue(self.config.default_priority)
        self.default_priority_spin.setToolTip("Default priority for new tasks (-999 to 999)")
        self.default_priority_spin.setStyleSheet(_spinbox_qss(colors))
        self.default_priority_spin.setMinimumHeight(32)
        priority_layout.addWidget(self.default_priority_spin)
        priority_layout.addStretch()

        layout.addWidget(priority_frame)

        # ── Database path settings ──
        db_frame, db_content = self._styled_group("Database Settings")
        db_layout = QVBoxLayout(db_content)
        db_layout.setContentsMargins(16, 16, 16, 16)
        db_layout.setSpacing(8)

        # Database path row
        db_path_row = QHBoxLayout()
        db_path_label = QLabel("Database path:")
        db_path_label.setFont(QFont(FONT_FAMILY, 11))
        db_path_label.setStyleSheet(f"color: {colors['text_primary']}; background: transparent;")
        db_path_row.addWidget(db_path_label)

        self.db_path_edit = QLineEdit()
        self.db_path_edit.setText(self.config.database_path)
        self.db_path_edit.setToolTip("Path to the SQLite database file")
        self.db_path_edit.setStyleSheet(_input_qss(colors))
        self.db_path_edit.setMinimumHeight(30)
        db_path_row.addWidget(self.db_path_edit, 1)

        db_browse_btn = QPushButton("Browse...")
        db_browse_btn.setStyleSheet(_btn_neutral(colors))
        db_browse_btn.clicked.connect(self._browse_database)
        db_path_row.addWidget(db_browse_btn)
        db_layout.addLayout(db_path_row)

        # Backup path row
        backup_path_row = QHBoxLayout()
        backup_label = QLabel("Backup path:")
        backup_label.setFont(QFont(FONT_FAMILY, 11))
        backup_label.setStyleSheet(f"color: {colors['text_primary']}; background: transparent;")
        backup_path_row.addWidget(backup_label)

        self.backup_path_edit = QLineEdit()
        self.backup_path_edit.setText(self.config.backup_path)
        self.backup_path_edit.setToolTip("Directory for database backups")
        self.backup_path_edit.setStyleSheet(_input_qss(colors))
        self.backup_path_edit.setMinimumHeight(30)
        backup_path_row.addWidget(self.backup_path_edit, 1)

        backup_browse_btn = QPushButton("Browse...")
        backup_browse_btn.setStyleSheet(_btn_neutral(colors))
        backup_browse_btn.clicked.connect(self._browse_backup)
        backup_path_row.addWidget(backup_browse_btn)
        db_layout.addLayout(backup_path_row)

        layout.addWidget(db_frame)

        # Note about restart
        note_label = QLabel("Note: Database and backup path changes require application restart.")
        note_label.setFont(QFont(FONT_FAMILY, 10))
        note_label.setStyleSheet(f"color: {colors['text_secondary']}; font-style: italic; background: transparent;")
        layout.addWidget(note_label)

        # Apply button
        button_row = QHBoxLayout()
        button_row.addStretch()
        apply_btn = QPushButton("Apply")
        apply_btn.setStyleSheet(_btn_success(colors))
        apply_btn.setMinimumSize(100, 34)
        apply_btn.clicked.connect(self._apply_settings)
        button_row.addWidget(apply_btn)
        layout.addLayout(button_row)

        # Push everything to the top
        layout.addStretch()

    def _styled_group(self, title: str) -> tuple[QFrame, QWidget]:
        """Create a themed group container (replaces QGroupBox).

        Returns (outer_frame, content_widget) - add outer_frame to parent layout,
        set your layout on content_widget.
        """
        colors = get_colors()

        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['card_bg']};
                border-radius: 8px;
            }}
        """)

        outer_layout = QVBoxLayout(frame)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        title_label = QLabel(f"  {title}")
        title_label.setFont(QFont(FONT_FAMILY, 10, QFont.Weight.Bold))
        title_label.setStyleSheet(f"""
            color: {colors['text_secondary']};
            background-color: {colors['bg_light']};
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            padding: 6px 10px;
        """)
        outer_layout.addWidget(title_label)

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        outer_layout.addWidget(content)

        return frame, content

    def _browse_database(self):
        """Open file dialog for database path."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Database File",
            self.db_path_edit.text(),
            "SQLite Database (*.db);;All Files (*)"
        )
        if path:
            self.db_path_edit.setText(path)

    def _browse_backup(self):
        """Open directory dialog for backup path."""
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Backup Directory",
            self.backup_path_edit.text()
        )
        if path:
            self.backup_path_edit.setText(path)

    def _apply_settings(self):
        """Apply and save settings changes."""
        new_frame_count = self.frame_spin.value()
        new_db_path = self.db_path_edit.text().strip()
        new_backup_path = self.backup_path_edit.text().strip()
        new_default_priority = self.default_priority_spin.value()
        new_theme = self.theme_combo.currentData()

        changes = {}
        needs_restart = False

        # Check what changed
        if new_frame_count != self.config.frame_count:
            changes['frame_count'] = new_frame_count

        if new_default_priority != self.config.default_priority:
            changes['default_priority'] = new_default_priority

        if new_db_path != self.config.database_path:
            changes['database_path'] = new_db_path
            needs_restart = True

        if new_backup_path != self.config.backup_path:
            changes['backup_path'] = new_backup_path
            needs_restart = True

        if new_theme != self.config.theme:
            changes['theme'] = new_theme

        if not changes:
            MessageBox(self, "Settings", "No changes to apply.")
            return

        # Confirm path changes
        if needs_restart:
            dialog = ConfirmDialog(
                self, "Confirm Path Changes",
                "Changing database or backup paths requires an application restart.\n\n"
                "The new paths will be used after you restart the application.\n\n"
                "Do you want to save these changes?"
            )
            if not dialog.get_result():
                return

        # Apply theme change immediately
        if 'theme' in changes:
            set_theme(changes['theme'])

        # Save changes
        self.config_manager.update(**changes)

        # Emit signal with changes
        self.settings_changed.emit(changes)

        if needs_restart:
            MessageBox(
                self, "Settings Saved",
                "Settings saved. Please restart the application for path changes to take effect."
            )
        else:
            MessageBox(self, "Settings Saved", "Settings applied successfully.")


class CalendarTaskItem(QFrame):
    """Read-only task row for the Calendar view."""

    def __init__(self, task: Task, project_name: str, parent=None):
        super().__init__(parent)
        colors = get_colors()

        self.setStyleSheet(f"""
            CalendarTaskItem {{
                background-color: {colors['bg_medium']};
                border-radius: 6px;
            }}
        """)
        self.setMinimumHeight(38)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        # Due date label
        due_text = task.due_date.strftime("%m/%d/%Y") if task.due_date else ""
        due_label = QLabel(due_text)
        due_label.setFixedWidth(80)
        due_label.setFont(QFont(FONT_FAMILY, 11))
        # Red if overdue
        if task.due_date and task.due_date.date() < datetime.now().date():
            due_label.setStyleSheet(
                f"color: {colors['danger']}; background: transparent;"
            )
        else:
            due_label.setStyleSheet(
                f"color: {colors['text_primary']}; background: transparent;"
            )
        layout.addWidget(due_label)

        # Project name label
        proj_label = QLabel(project_name)
        proj_label.setFixedWidth(120)
        proj_label.setFont(QFont(FONT_FAMILY, 11, QFont.Weight.Bold))
        proj_label.setStyleSheet(
            f"color: {colors['text_secondary']}; background: transparent;"
        )
        layout.addWidget(proj_label)

        # Priority label
        pri_label = QLabel(str(task.priority))
        pri_label.setFixedWidth(45)
        pri_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pri_label.setFont(QFont(FONT_FAMILY, 11))
        pri_label.setStyleSheet(
            f"color: {colors['text_secondary']}; background: transparent;"
        )
        layout.addWidget(pri_label)

        # Title label
        title_label = QLabel(task.title)
        title_label.setWordWrap(True)
        title_label.setFont(QFont(FONT_FAMILY, 12))
        title_label.setStyleSheet(
            f"color: {colors['text_primary']}; background: transparent;"
        )
        layout.addWidget(title_label, 1)


class CalendarWidget(QWidget):
    """Calendar view showing all tasks with due dates sorted chronologically."""

    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self._setup_ui()

    def _setup_ui(self):
        colors = get_colors()
        self.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Filter card
        filter_card = QFrame()
        filter_card.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['card_bg']};
                border-radius: 8px;
            }}
        """)
        filter_card.setMaximumHeight(42)
        filter_layout = QHBoxLayout(filter_card)
        filter_layout.setContentsMargins(10, 4, 10, 4)
        filter_layout.setSpacing(8)

        filter_label = QLabel("Project:")
        filter_label.setFont(QFont(FONT_FAMILY, 11))
        filter_label.setStyleSheet(
            f"color: {colors['text_primary']}; background: transparent;"
        )
        filter_layout.addWidget(filter_label)

        self.filter_combo = QComboBox()
        self.filter_combo.setStyleSheet(_combo_qss(colors))
        self.filter_combo.setMinimumHeight(28)
        self.filter_combo.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.filter_combo, 1)
        filter_layout.addStretch()

        layout.addWidget(filter_card)

        # Column header row
        header_frame = QFrame()
        header_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['bg_light']};
                border-radius: 6px;
            }}
        """)
        header_frame.setFixedHeight(28)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(8, 2, 8, 2)
        header_layout.setSpacing(6)

        for text, width, stretch in [
            ("Due Date", 80, 0), ("Project", 120, 0),
            ("Priority", 45, 0), ("Title", 0, 1)
        ]:
            lbl = QLabel(text)
            lbl.setFont(QFont(FONT_FAMILY, 10, QFont.Weight.Bold))
            lbl.setStyleSheet(
                f"color: {colors['text_secondary']}; background: transparent;"
            )
            if width:
                lbl.setFixedWidth(width)
            if text == "Pri":
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header_layout.addWidget(lbl, stretch)

        layout.addWidget(header_frame)

        # Scroll area for task list
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        scrollbar_qss = get_scrollbar_qss(
            vertical=True, transparent_track=True, width=10
        )
        self.scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            {scrollbar_qss}
        """)

        self.list_container = QWidget()
        self.list_container.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(4)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.list_container)
        layout.addWidget(self.scroll, 1)

        # Empty state label (hidden by default)
        self.empty_label = QLabel("No tasks with due dates")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setFont(QFont(FONT_FAMILY, 13))
        self.empty_label.setStyleSheet(
            f"color: {colors['text_secondary']}; background: transparent;"
        )
        self.empty_label.setVisible(False)
        layout.addWidget(self.empty_label)

    def refresh(self):
        """Rebuild filter dropdown (preserving selection) and task list."""
        # Remember current filter selection
        current_data = self.filter_combo.currentData()

        self.filter_combo.blockSignals(True)
        self.filter_combo.clear()
        self.filter_combo.addItem("All Projects", None)

        projects = self.db.get_projects(include_archived=False)
        selected_index = 0
        for i, project in enumerate(projects):
            self.filter_combo.addItem(project.name, project.id)
            if project.id == current_data:
                selected_index = i + 1

        self.filter_combo.setCurrentIndex(selected_index)
        self.filter_combo.blockSignals(False)

        self._refresh_tasks()

    def _on_filter_changed(self, _index: int):
        self._refresh_tasks()

    def _refresh_tasks(self):
        """Clear and repopulate the task list from DB."""
        # Clear existing items
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        project_id = self.filter_combo.currentData()
        tasks = self.db.get_tasks_with_due_dates(project_id)

        if not tasks:
            self.empty_label.setVisible(True)
            self.scroll.setVisible(False)
            return

        self.empty_label.setVisible(False)
        self.scroll.setVisible(True)

        # Build project name lookup
        projects = self.db.get_projects(include_archived=False)
        proj_names = {p.id: p.name for p in projects}

        with batch_update(self.list_container):
            for task in tasks:
                name = proj_names.get(task.project_id, "?")
                item = CalendarTaskItem(task, name)
                self.list_layout.addWidget(item)


class HistoryTaskItem(QFrame):
    """Read-only task row for the History view."""

    def __init__(self, task: Task, project_name: str, parent=None):
        super().__init__(parent)
        colors = get_colors()

        self.setStyleSheet(f"""
            HistoryTaskItem {{
                background-color: {colors['bg_medium']};
                border-radius: 6px;
            }}
        """)
        self.setMinimumHeight(38)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        # Completed date label
        completed_text = (
            task.completed_at.strftime("%m/%d/%Y")
            if task.completed_at else "—"
        )
        date_label = QLabel(completed_text)
        date_label.setFixedWidth(80)
        date_label.setFont(QFont(FONT_FAMILY, 11))
        date_label.setStyleSheet(
            f"color: {colors['text_secondary']}; background: transparent;"
        )
        layout.addWidget(date_label)

        # Project name label
        proj_label = QLabel(project_name)
        proj_label.setFixedWidth(120)
        proj_label.setFont(QFont(FONT_FAMILY, 11, QFont.Weight.Bold))
        proj_label.setStyleSheet(
            f"color: {colors['text_secondary']}; background: transparent;"
        )
        layout.addWidget(proj_label)

        # Priority label
        pri_label = QLabel(str(task.priority))
        pri_label.setFixedWidth(45)
        pri_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pri_label.setFont(QFont(FONT_FAMILY, 11))
        pri_label.setStyleSheet(
            f"color: {colors['text_secondary']}; background: transparent;"
        )
        layout.addWidget(pri_label)

        # Title label
        title_label = QLabel(task.title)
        title_label.setWordWrap(True)
        title_label.setFont(QFont(FONT_FAMILY, 12))
        title_label.setStyleSheet(
            f"color: {colors['text_secondary']}; background: transparent;"
        )
        layout.addWidget(title_label, 1)


class HistoryWidget(QWidget):
    """History view showing completed tasks sorted by completion date."""

    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self._setup_ui()

    def _setup_ui(self):
        colors = get_colors()
        self.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Filter card
        filter_card = QFrame()
        filter_card.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['card_bg']};
                border-radius: 8px;
            }}
        """)
        filter_card.setMaximumHeight(42)
        filter_layout = QHBoxLayout(filter_card)
        filter_layout.setContentsMargins(10, 4, 10, 4)
        filter_layout.setSpacing(8)

        filter_label = QLabel("Project:")
        filter_label.setFont(QFont(FONT_FAMILY, 11))
        filter_label.setStyleSheet(
            f"color: {colors['text_primary']}; background: transparent;"
        )
        filter_layout.addWidget(filter_label)

        self.filter_combo = QComboBox()
        self.filter_combo.setStyleSheet(_combo_qss(colors))
        self.filter_combo.setMinimumHeight(28)
        self.filter_combo.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.filter_combo, 1)
        filter_layout.addStretch()

        layout.addWidget(filter_card)

        # Column header row
        header_frame = QFrame()
        header_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['bg_light']};
                border-radius: 6px;
            }}
        """)
        header_frame.setFixedHeight(28)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(8, 2, 8, 2)
        header_layout.setSpacing(6)

        for text, width, stretch in [
            ("Completed", 80, 0), ("Project", 120, 0),
            ("Priority", 45, 0), ("Title", 0, 1)
        ]:
            lbl = QLabel(text)
            lbl.setFont(QFont(FONT_FAMILY, 10, QFont.Weight.Bold))
            lbl.setStyleSheet(
                f"color: {colors['text_secondary']}; background: transparent;"
            )
            if width:
                lbl.setFixedWidth(width)
            if text == "Priority":
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header_layout.addWidget(lbl, stretch)

        layout.addWidget(header_frame)

        # Scroll area for task list
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        scrollbar_qss = get_scrollbar_qss(
            vertical=True, transparent_track=True, width=10
        )
        self.scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            {scrollbar_qss}
        """)

        self.list_container = QWidget()
        self.list_container.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(4)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.list_container)
        layout.addWidget(self.scroll, 1)

        # Empty state label
        self.empty_label = QLabel("No completed tasks")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setFont(QFont(FONT_FAMILY, 13))
        self.empty_label.setStyleSheet(
            f"color: {colors['text_secondary']}; background: transparent;"
        )
        self.empty_label.setVisible(False)
        layout.addWidget(self.empty_label)

    def refresh(self):
        """Rebuild filter dropdown (preserving selection) and task list."""
        current_data = self.filter_combo.currentData()

        self.filter_combo.blockSignals(True)
        self.filter_combo.clear()
        self.filter_combo.addItem("All Projects", None)

        projects = self.db.get_projects(include_archived=False)
        selected_index = 0
        for i, project in enumerate(projects):
            self.filter_combo.addItem(project.name, project.id)
            if project.id == current_data:
                selected_index = i + 1

        self.filter_combo.setCurrentIndex(selected_index)
        self.filter_combo.blockSignals(False)

        self._refresh_tasks()

    def _on_filter_changed(self, _index: int):
        self._refresh_tasks()

    def _refresh_tasks(self):
        """Clear and repopulate the task list from DB."""
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        project_id = self.filter_combo.currentData()
        tasks = self.db.get_completed_tasks(project_id)

        if not tasks:
            self.empty_label.setVisible(True)
            self.scroll.setVisible(False)
            return

        self.empty_label.setVisible(False)
        self.scroll.setVisible(True)

        projects = self.db.get_projects(include_archived=False)
        proj_names = {p.id: p.name for p in projects}

        with batch_update(self.list_container):
            for task in tasks:
                name = proj_names.get(task.project_id, "?")
                item = HistoryTaskItem(task, name)
                self.list_layout.addWidget(item)
