from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QMainWindow, QStackedWidget, QVBoxLayout, QWidget

from src.core.pomodoro_engine import PomodoroEngine
from src.core.session_store import SessionStore
from src.core.settings_store import SettingsStore
from src.ui.bottom_nav import BottomNavBar
from src.ui.focus_page import FocusPage
from src.ui.settings_page import SettingsPage
from src.ui.stats_page import StatsPage
from src.ui.ui_theme import BG


class MainWindow(QMainWindow):
    def __init__(self, engine: PomodoroEngine, settings: SettingsStore, sessions: SessionStore):
        super().__init__()
        self._engine = engine
        self._settings = settings
        self._sessions = sessions

        self.setWindowTitle("番茄专注")
        self.setMinimumSize(680, 820)
        self.resize(680, 820)
        self.setStyleSheet(
            f"QMainWindow {{ background: {BG}; }}"
        )

        self.focus_page = FocusPage(
            engine=self._engine,
            settings=self._settings,
            on_open_focus_type_settings=self.open_focus_type_settings,
            on_open_focus_duration_settings=self.open_focus_duration_settings,
        )
        self.stats_page = StatsPage(sessions=self._sessions)
        self.settings_page = SettingsPage(engine=self._engine, settings=self._settings)

        self.pages = QStackedWidget(self)
        self.pages.setStyleSheet("QStackedWidget { background: transparent; }")
        self.pages.addWidget(self.focus_page)
        self.pages.addWidget(self.stats_page)
        self.pages.addWidget(self.settings_page)

        self.bottom_nav = BottomNavBar(self)
        self.bottom_nav.set_items(["专注", "统计", "设置"])
        self.bottom_nav.current_changed.connect(self.pages.setCurrentIndex)
        self.bottom_nav.set_current_index(0)

        container = QWidget(self)
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.pages, 1)
        layout.addWidget(self.bottom_nav, 0)

        self.setCentralWidget(container)

        self._engine.focus_completed.connect(self.stats_page.refresh)

    def show_focus(self) -> None:
        self.bottom_nav.set_current_index(0)
        self.pages.setCurrentIndex(0)
        self.show()
        self.raise_()
        self.activateWindow()

    def open_focus_type_settings(self) -> None:
        self.bottom_nav.set_current_index(2)
        self.pages.setCurrentIndex(2)
        self.show()
        self.raise_()
        self.activateWindow()
        self.settings_page.open_focus_type_manager()

    def open_focus_duration_settings(self) -> None:
        self.bottom_nav.set_current_index(2)
        self.pages.setCurrentIndex(2)
        self.show()
        self.raise_()
        self.activateWindow()
        self.settings_page.focus_durations()

    def closeEvent(self, event: QCloseEvent) -> None:
        event.ignore()
        self.hide()
