# Repository Guidelines

## Project Structure & Module Organization
- `main.py` is the entry point that wires up the GUI.
- `main_window.py` contains the PyQt5 UI and interaction logic.
- `pyscrcpy.py` and `device_manager.py` hold app logic for device management and scrcpy/ADB integration.
- `pyscrcpy.json` stores persisted device/config state.
- `requirements.txt` defines Python dependencies.
- `build/`, `dist/`, and `pyscrcpy.spec` are PyInstaller build outputs/specs.
- Assets live at the repo root, e.g. `pyscrcpy.jpg`, `screenshot.jpg`.

## Build, Test, and Development Commands
- `pip install -r requirements.txt` installs dependencies.
- `python main.py` runs the app locally.
- `uv pip install -r requirements.txt` is an alternative install path if you use `uv`.
- `python -m PyInstaller --name pyscrcpy --onefile --noconsole --icon=pyscrcpy.jpg --noupx --clean main.py` builds a Windows executable (see `pyscrcpy.spec`).

## Coding Style & Naming Conventions

## Encoding & Localization
- All `.py` files must be saved as UTF-8 and include `# -*- coding: utf-8 -*-` at the top.
- GUI entrypoint should set a Chinese-capable font (e.g., `Microsoft YaHei`) to avoid missing glyphs in dialogs.
- When showing subprocess output in UI, decode explicitly (e.g., `utf-8` with `errors='ignore'` or `gbk` on Windows).
- If `pyscrcpy.json` contains garbled text, clean or migrate it to UTF-8 to prevent UI contamination.

- Use 4-space indentation and PEP 8 styling for Python.
- Prefer `snake_case` for functions/variables and `PascalCase` for classes.
- Keep UI-related logic in `main_window.py` and device/ADB logic in `device_manager.py` to avoid mixing concerns.
- No formatter or linter is configured; if you introduce one, document it here.

## Testing Guidelines
- No automated tests are present in this repository.
- If you add tests, place them under a new `tests/` directory and use a clear naming scheme like `test_device_manager.py`.
- Include manual testing notes for UI changes (e.g., device list add/remove, scrcpy launch, ADB shell).

## Refactor Status & Known Issues
- The project is under active refactor. UI layout is currently unclear, and some ADB command executions can hang.
- When touching UI layout, keep widgets grouped by workflow (device list, actions, logs) and document any new layout rules here.
- For ADB calls, prefer non-blocking execution (subprocess with timeouts or background threads) and surface timeouts in the UI.

## Commit & Pull Request Guidelines
- Commit history shows short, descriptive messages (often in Chinese) without a strict convention. Keep messages concise and action-oriented (e.g., “支持设备列表排序显示”).
- If relevant, include issue/PR references like `(#10)`.
- Pull requests should include a summary, testing notes, and screenshots for UI changes.

## Configuration & Environment Notes
- Requires Python 3.8+, ADB in `PATH`, and scrcpy 1.24+ in `PATH`.
- Verify ADB connectivity and USB debugging on first run.
