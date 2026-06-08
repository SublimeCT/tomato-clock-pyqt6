# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

番茄专注 (Tomato Clock) — a PyQt6 Pomodoro timer desktop app for macOS with system tray integration, focus type management, and statistics tracking.

## Commands

```bash
uv sync                        # Install dependencies
uv run src/main.py             # Run the app
uv run pyinstaller TomatoClock.spec  # Build macOS .app bundle
```

Rebuilding Qt resources (after adding/modifying assets in `src/assets/`):
```bash
rcc -g python resources.qrc -o src/assets/reources_rc.py
```

No test suite exists yet.

## Mandatory Rules

- **Always use `uv`** — never `python`, `python3`, `pip`, or `pip3`
- **Always use PyQt6** — never PySide6, never QML; QWidget style only
- **All code must work in the packaged (PyInstaller) production environment**
- **Max 300 lines per file**
- Verify any uncertain Qt/PyQt API before using

## Architecture

```
src/main.py              → Entry point: wires up core, UI, and tray
src/core/                → Business logic (no Qt widget imports)
src/ui/                  → All QWidget-based UI components
src/tray/                → System tray (macOS native NSStatusItem via ctypes)
src/utils/               → Shared utilities (icon loading)
src/assets/              → Static resources + auto-generated resources_rc.py
```

### Wiring (main.py)

`SettingsStore` → `SessionStore` → `PomodoroEngine` → `MainWindow` + `TrayController`. All are created in `main.py` and receive dependencies via constructor injection.

### Core Layer (`src/core/`)

- **PomodoroEngine**: State machine (focus → short_break → long_break). Emits `state_changed` / `focus_completed` signals. Holds an immutable `EngineState` dataclass.
- **SessionStore**: Persists completed sessions as JSON in `AppDataLocation`. Provides query methods: `sessions_on()`, `sessions_between()`, `counts_by_day()`, `minutes_by_day()`.
- **SettingsStore**: Wraps QSettings for durations, focus types, colors, defaults.

### UI Layer (`src/ui/`)

- **MainWindow**: Container with `BottomNavBar`; hosts FocusPage, StatsPage, SettingsPage. Closing hides the window (app lives in tray).
- **FocusPage**: Timer display with start/pause/reset. ChevronRow selectors for focus type and duration.
- **StatsPage**: Day/week/month/year statistics using `stats_charts.py` (bar+line via PyQt6-Charts), `stats_calendar_views.py` (calendar grids), and `stats_contribution.py` (GitHub-style heatmap).
- **SettingsPage**: Duration config, focus type CRUD via `focus_type_dialog.py`.

### Tray (`src/tray/`)

- **TrayController**: Platform-aware tray; uses `MacStatusItem` on macOS (`sys.platform == "darwin"`), `QSystemTrayIcon` elsewhere.
- **MacStatusItem**: Direct ObjectiveC interop via ctypes for native NSStatusItem with template image support (dark mode compatible).

### Resources

Static assets go through Qt Resource System: add files to `src/assets/`, register in `resources.qrc`, run `rcc`, then import `reources_rc`. `IconLoader` tries Qt resources first (`:/` prefix), then filesystem, then PyInstaller's `sys._MEIPASS`.

## Key Patterns

- **Signal/slot** for all cross-component communication — no direct method calls between pages
- **Constructor injection** — components receive dependencies at creation, no global singletons
- **Platform branching** with `sys.platform` for macOS-specific behavior
- **Immutable state** via `EngineState` dataclass; engine emits new state on change
