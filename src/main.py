import signal
import sys

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from src.core.pomodoro_engine import PomodoroEngine
from src.core.session_store import SessionStore
from src.core.settings_store import SettingsStore
from src.tray.tray_controller import TrayController
from src.ui.main_window import MainWindow
from src.utils.icon_loader import load_app_icon

from src.assets import resources_rc

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    app_icon = load_app_icon("app-icon-44.png")
    app.setWindowIcon(app_icon)

    signal.signal(signal.SIGINT, lambda *_: app.quit())
    signal.signal(signal.SIGTERM, lambda *_: app.quit())
    sig_timer = QTimer()
    sig_timer.timeout.connect(lambda: None)
    sig_timer.start(200)

    settings = SettingsStore()
    sessions = SessionStore()
    engine = PomodoroEngine(settings=settings, sessions=sessions)
    window = MainWindow(engine=engine, settings=settings, sessions=sessions)
    controller = TrayController(engine=engine, settings=settings, main_window=window, app_icon=app_icon)

    sys.exit(app.exec())
