"""TodoUI - Multi-project to-do application."""

import sys

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QStackedWidget,
    QHBoxLayout, QVBoxLayout, QStatusBar
)
from PyQt6.QtGui import QAction, QFont
from PyQt6.QtCore import Qt

from jframes import (
    TabSwitcher, get_colors, set_theme, FONT_FAMILY,
    register_theme_callback
)
from config import get_config, ConfigManager, APP_DIR
from database import DatabaseManager
from widgets import ProjectTaskWidget, SettingsWidget, CalendarWidget, HistoryWidget


class MainWindow(QMainWindow):
    """Main application window."""

    FRAME_WIDTH = 400  # Width per task frame
    TAB_NAMES = ["Tasks", "Settings", "Calendar", "History"]

    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db = db
        self.config = get_config()
        self.project_widgets: list[ProjectTaskWidget] = []

        self.setWindowTitle("Setado")
        from PyQt6.QtGui import QIcon
        self.setWindowIcon(QIcon(str(APP_DIR / "setado_ico.ico")))
        self._update_minimum_size()

        # Apply theme
        self._apply_theme()

        self._setup_menu()
        self._setup_central_widget()
        self._setup_status_bar()

        # Register for theme changes
        register_theme_callback(self._on_theme_changed)

    def _apply_theme(self):
        """Apply theme colors to the main window."""
        colors = get_colors()
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {colors['bg_dark']};
            }}
        """)

    def _on_theme_changed(self):
        """Handle theme change - restyle everything."""
        self._apply_theme()
        self._style_menu()
        self._style_status_bar()
        # Rebuild tabs to pick up new colors
        self._rebuild_tasks_tab()
        self._rebuild_calendar_tab()
        self._rebuild_history_tab()

    def _update_minimum_size(self):
        """Update minimum window size based on frame count."""
        min_width = self.FRAME_WIDTH * self.config.frame_count
        self.setMinimumSize(min_width, 600)

    def _setup_menu(self):
        """Set up the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        # Settings action
        settings_action = QAction("&Settings", self)
        settings_action.triggered.connect(self._show_settings)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        self._style_menu()

    def _style_menu(self):
        """Apply theme styling to the menu bar."""
        colors = get_colors()
        menubar = self.menuBar()
        menubar.setFont(QFont(FONT_FAMILY, 10))
        menubar.setStyleSheet(f"""
            QMenuBar {{
                background-color: {colors['bg_dark']};
                color: {colors['text_primary']};
                border-bottom: 1px solid {colors['separator']};
                padding: 2px;
            }}
            QMenuBar::item {{
                background-color: transparent;
                padding: 4px 12px;
                border-radius: 4px;
            }}
            QMenuBar::item:selected {{
                background-color: {colors['bg_light']};
            }}
            QMenu {{
                background-color: {colors['card_bg']};
                color: {colors['text_primary']};
                border: 1px solid {colors['separator']};
                border-radius: 6px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 24px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {colors['bg_light']};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {colors['separator']};
                margin: 4px 8px;
            }}
        """)

    def _show_settings(self):
        """Switch to the Settings tab."""
        self.tab_switcher.set_current_tab("Settings")
        self.stack.setCurrentIndex(1)

    def _setup_central_widget(self):
        """Set up the central widget with TabSwitcher + QStackedWidget."""
        colors = get_colors()

        central = QWidget()
        central.setStyleSheet(f"background-color: {colors['bg_dark']};")
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 4)
        main_layout.setSpacing(8)

        # Tab switcher at top
        self.tab_switcher = TabSwitcher(self.TAB_NAMES)
        self.tab_switcher.set_on_tab_change(self._on_tab_changed)
        main_layout.addWidget(self.tab_switcher)

        # Stacked widget for tab content
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent;")
        main_layout.addWidget(self.stack, 1)

        # Tasks tab (index 0)
        self.tasks_tab = self._create_tasks_tab()
        self.stack.addWidget(self.tasks_tab)

        # Settings tab (index 1)
        self.settings_widget = SettingsWidget()
        self.settings_widget.settings_changed.connect(self._on_settings_changed)
        self.stack.addWidget(self.settings_widget)

        # Calendar tab (index 2)
        self.calendar_widget = CalendarWidget(self.db)
        self.stack.addWidget(self.calendar_widget)

        # History tab (index 3)
        self.history_widget = HistoryWidget(self.db)
        self.stack.addWidget(self.history_widget)

    def _on_tab_changed(self, tab_name: str):
        """Handle tab switcher selection."""
        index = self.TAB_NAMES.index(tab_name)
        self.stack.setCurrentIndex(index)
        if tab_name == "Calendar":
            self.calendar_widget.refresh()
        elif tab_name == "History":
            self.history_widget.refresh()

    def _create_tasks_tab(self) -> QWidget:
        """Create the tasks tab with the configured number of frames."""
        tasks_tab = QWidget()
        tasks_tab.setStyleSheet("background: transparent;")
        tasks_layout = QHBoxLayout(tasks_tab)
        tasks_layout.setContentsMargins(0, 0, 0, 0)
        tasks_layout.setSpacing(8)

        # Clear existing widgets list
        self.project_widgets.clear()

        # Create ProjectTaskWidget columns based on config
        for _ in range(self.config.frame_count):
            widget = ProjectTaskWidget(self.db)
            widget.project_changed.connect(self._on_project_changed)
            widget.project_selected.connect(self._save_frame_projects)
            self.project_widgets.append(widget)
            tasks_layout.addWidget(widget)

        # Restore saved project selections
        saved = self.config.frame_projects
        for i, widget in enumerate(self.project_widgets):
            if i < len(saved) and saved[i] is not None:
                widget.set_project_by_id(saved[i])

        return tasks_tab

    def _rebuild_tasks_tab(self):
        """Rebuild the tasks tab with the new frame count."""
        # Remember current tab
        current_index = self.stack.currentIndex()

        # Remove old tasks tab
        old_tab = self.stack.widget(0)
        self.stack.removeWidget(old_tab)
        old_tab.deleteLater()

        # Create new tasks tab
        self.tasks_tab = self._create_tasks_tab()
        self.stack.insertWidget(0, self.tasks_tab)

        # Update window size
        self._update_minimum_size()

        # Resize window if it's smaller than the new minimum
        current_size = self.size()
        min_width = self.FRAME_WIDTH * self.config.frame_count
        if current_size.width() < min_width:
            self.resize(min_width, current_size.height())

        # Restore tab selection
        self.stack.setCurrentIndex(current_index)

    def _rebuild_calendar_tab(self):
        """Rebuild the calendar tab with new theme colors."""
        current_index = self.stack.currentIndex()

        old_widget = self.stack.widget(2)
        self.stack.removeWidget(old_widget)
        old_widget.deleteLater()

        self.calendar_widget = CalendarWidget(self.db)
        self.stack.insertWidget(2, self.calendar_widget)

        self.stack.setCurrentIndex(current_index)

    def _rebuild_history_tab(self):
        """Rebuild the history tab with new theme colors."""
        current_index = self.stack.currentIndex()

        old_widget = self.stack.widget(3)
        self.stack.removeWidget(old_widget)
        old_widget.deleteLater()

        self.history_widget = HistoryWidget(self.db)
        self.stack.insertWidget(3, self.history_widget)

        self.stack.setCurrentIndex(current_index)

    def _on_settings_changed(self, changes: dict):
        """Handle settings changes."""
        if 'frame_count' in changes:
            self.config = get_config()
            self._rebuild_tasks_tab()
            self._save_frame_projects()
            self.status_bar.showMessage(
                f"Task layout updated to {self.config.frame_count} frames", 3000
            )
        if 'theme' in changes:
            self.status_bar.showMessage(
                f"Theme changed to {changes['theme']}", 3000
            )

    def _setup_status_bar(self):
        """Set up the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self._style_status_bar()
        self.status_bar.showMessage("Ready")

    def _style_status_bar(self):
        """Apply theme styling to the status bar."""
        colors = get_colors()
        self.status_bar.setFont(QFont(FONT_FAMILY, 9))
        self.status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {colors['bg_dark']};
                color: {colors['text_secondary']};
                border-top: 1px solid {colors['separator']};
                padding: 2px 8px;
            }}
        """)

    def _save_frame_projects(self):
        """Save current project selections to config."""
        frame_projects = [w.current_project_id for w in self.project_widgets]
        ConfigManager().update(frame_projects=frame_projects)

    def _on_project_changed(self):
        """Handle project changes from any widget."""
        for widget in self.project_widgets:
            widget.refresh_from_external()
        self._save_frame_projects()
        self.status_bar.showMessage("Projects updated", 3000)

    def closeEvent(self, event):
        """Handle window close."""
        self._save_frame_projects()
        self.db.close()
        event.accept()


def main():
    """Application entry point."""
    # Initialize configuration
    ConfigManager()
    config = get_config()

    # Initialize database
    db = DatabaseManager(config)

    # Create and run application
    app = QApplication(sys.argv)
    app.setApplicationName("Setado")

    # Set application-wide Inter font
    app_font = QFont(FONT_FAMILY, 10)
    app.setFont(app_font)

    # Set theme from config
    try:
        set_theme(config.theme)
    except ValueError:
        set_theme("dark")

    window = MainWindow(db)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
