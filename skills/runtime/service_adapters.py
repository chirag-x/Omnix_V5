"""
Runtime service adapters for skill execution.

The V5 system managers expose mostly synchronous desktop APIs, while built-in
skills use an async service contract through SkillContext. These adapters keep
that boundary explicit without changing the managers themselves.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import webbrowser
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

import psutil
from loguru import logger

from core.planning.execution_context import ExecutionContext


class AsyncInputAdapter:
    """Async facade over the synchronous input subsystem."""

    def __init__(self, input_manager=None):
        self.input_manager = input_manager

    async def move_mouse(self, x: int, y: int, duration: float = 0.0) -> bool:
        try:
            if self.input_manager and hasattr(self.input_manager, "mouse"):
                self.input_manager.mouse.move_to(int(x), int(y), duration=duration)
            elif self.input_manager and hasattr(self.input_manager, "move_mouse"):
                self.input_manager.move_mouse(int(x), int(y), duration=duration)
            else:
                return False
            return True
        except Exception as exc:
            logger.exception(f"[InputAdapter] move_mouse failed: {exc}")
            return False

    async def click(
        self,
        x: int | None = None,
        y: int | None = None,
        button: str = "left",
        clicks: int = 1,
        interval: float = 0.1,
    ) -> bool:
        try:
            if self.input_manager and hasattr(self.input_manager, "mouse"):
                self.input_manager.mouse.click(
                    x=None if x is None else int(x),
                    y=None if y is None else int(y),
                    button=button,
                    clicks=int(clicks),
                    interval=float(interval),
                )
            elif self.input_manager and hasattr(self.input_manager, "click"):
                if x is not None and y is not None:
                    await self.move_mouse(int(x), int(y))
                self.input_manager.click()
            else:
                return False
            return True
        except Exception as exc:
            logger.exception(f"[InputAdapter] click failed: {exc}")
            return False

    async def double_click(self, x: int, y: int) -> bool:
        return await self.click(x=x, y=y, clicks=2)

    async def drag(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        duration: float = 0.2,
        button: str = "left",
    ) -> bool:
        try:
            if not self.input_manager or not hasattr(self.input_manager, "mouse"):
                return False

            mouse = self.input_manager.mouse
            mouse.move_to(int(start_x), int(start_y), duration=0)
            mouse.drag_to(int(end_x), int(end_y), duration=duration, button=button)
            return True
        except Exception as exc:
            logger.exception(f"[InputAdapter] drag failed: {exc}")
            return False

    async def type_text(self, text: str) -> bool:
        try:
            if self.input_manager and hasattr(self.input_manager, "typing"):
                self.input_manager.typing.type_text(str(text))
            elif self.input_manager and hasattr(self.input_manager, "type_text"):
                self.input_manager.type_text(str(text))
            else:
                return False
            return True
        except Exception as exc:
            logger.exception(f"[InputAdapter] type_text failed: {exc}")
            return False

    async def press_key(self, key: str) -> bool:
        try:
            if self.input_manager and hasattr(self.input_manager, "keyboard"):
                self.input_manager.keyboard.press(str(key))
            else:
                return False
            return True
        except Exception as exc:
            logger.exception(f"[InputAdapter] press_key failed: {exc}")
            return False

    async def hotkey(self, *keys: str) -> bool:
        try:
            keys = tuple(str(key) for key in keys if str(key).strip())
            if not keys:
                return False

            if self.input_manager and hasattr(self.input_manager, "keyboard"):
                self.input_manager.keyboard.hotkey(*keys)
            elif self.input_manager and hasattr(self.input_manager, "hotkey"):
                self.input_manager.hotkey(*keys)
            else:
                return False
            return True
        except Exception as exc:
            logger.exception(f"[InputAdapter] hotkey failed: {exc}")
            return False

    async def scroll(self, amount: int) -> bool:
        try:
            if self.input_manager and hasattr(self.input_manager, "mouse"):
                self.input_manager.mouse.scroll(int(amount))
            else:
                return False
            return True
        except Exception as exc:
            logger.exception(f"[InputAdapter] scroll failed: {exc}")
            return False

    async def get_clipboard(self) -> str:
        if not self.input_manager or not hasattr(self.input_manager, "get_clipboard"):
            return ""
        try:
            return self.input_manager.get_clipboard()
        except Exception as exc:
            logger.exception(f"[InputAdapter] get_clipboard failed: {exc}")
            return ""

    async def set_clipboard(self, text: str) -> bool:
        if not self.input_manager or not hasattr(self.input_manager, "set_clipboard"):
            return False
        try:
            self.input_manager.set_clipboard(str(text))
            return True
        except Exception as exc:
            logger.exception(f"[InputAdapter] set_clipboard failed: {exc}")
            return False


class AsyncFileAdapter:
    """Async facade over FileManager with the contract used by file skills."""

    def __init__(self, file_manager=None):
        self.file_manager = file_manager

    async def create_file(self, path: str, content: str = "") -> dict[str, Any]:
        if self.file_manager is None:
            raise RuntimeError("File manager is unavailable.")

        file_path = Path(path)
        if content:
            created = self.file_manager.files.write_text(file_path, str(content))
        else:
            created = self.file_manager.create_file(file_path)

        return {
            "path": str(created),
            "created": True,
        }

    async def open_file(self, path: str) -> bool:
        if self.file_manager is None:
            raise RuntimeError("File manager is unavailable.")

        if hasattr(self.file_manager, "launch_file"):
            return bool(self.file_manager.launch_file(path))

        try:
            os.startfile(str(path))
            return True
        except Exception as exc:
            logger.exception(f"[FileAdapter] open_file failed: {exc}")
            return False

    async def search(self, query: str, path: str | None = None) -> list[dict[str, str]]:
        if self.file_manager is None:
            raise RuntimeError("File manager is unavailable.")

        root = Path(path or os.getcwd())
        pattern = str(query or "*")
        if not any(ch in pattern for ch in "*?[]"):
            pattern = f"*{pattern}*"

        results = self.file_manager.search(root, pattern=pattern)
        return [
            {
                "name": result.name,
                "path": str(result),
            }
            for result in results
        ]


class AsyncSystemAdapter:
    """Async skill-facing facade over SystemManager."""

    def __init__(self, system_manager=None):
        self.system_manager = system_manager

    def __getattr__(self, name: str) -> Any:
        if self.system_manager is not None:
            return getattr(self.system_manager, name)
        raise AttributeError(name)

    async def get_information(self) -> dict[str, Any]:
        stats = {}
        if self.system_manager is not None:
            try:
                stats = self.system_manager.statistics()
            except Exception as exc:
                logger.debug(f"[SystemAdapter] statistics unavailable: {exc}")

        return {
            "os": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python": platform.python_version(),
            "status": "online",
            "system": stats,
        }

    async def lock(self) -> bool:
        return self._power_action("lock")

    async def sleep(self) -> bool:
        return self._power_action("sleep")

    async def restart(self) -> bool:
        return self._power_action("restart")

    async def shutdown(self) -> bool:
        return self._power_action("shutdown")

    def _power_action(self, action: str) -> bool:
        if self.system_manager is None or self.system_manager.power is None:
            return False

        handler = getattr(self.system_manager.power, action, None)
        if handler is None:
            return False

        return bool(handler())


class BrowserController:
    """Best-effort browser control service used by browser skills."""

    EXECUTABLES = {
        "chrome": ("chrome", "chrome.exe", "Google Chrome"),
        "edge": ("msedge", "msedge.exe", "Microsoft Edge"),
        "firefox": ("firefox", "firefox.exe", "Mozilla Firefox"),
        "brave": ("brave", "brave.exe", "Brave"),
    }

    PROCESS_NAMES = {
        "chrome": {"chrome", "chrome.exe"},
        "edge": {"msedge", "msedge.exe"},
        "firefox": {"firefox", "firefox.exe"},
        "brave": {"brave", "brave.exe", "brave-browser", "brave-browser.exe"},
    }

    def __init__(
        self,
        system_manager=None,
        input_service: AsyncInputAdapter | None = None,
        execution_context: ExecutionContext | None = None,
    ):
        self.system_manager = system_manager
        self.input_service = input_service
        self.execution_context = execution_context

    async def is_running(self, browser: str | None = None) -> bool:
        browser = self._browser(browser)
        names = self.PROCESS_NAMES.get(browser, {browser, f"{browser}.exe"})

        for proc in psutil.process_iter(["name"]):
            try:
                if str(proc.info.get("name") or "").lower() in names:
                    return True
            except (psutil.Error, OSError):
                continue

        return False

    async def launch(self, browser: str | None = None) -> bool:
        browser = self._browser(browser)
        command = self._resolve_executable(browser)

        if command is None:
            logger.warning(f"[Browser] Browser executable not found: {browser}")
            return False

        try:
            subprocess.Popen([command], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self._set_browser(browser)
            return True
        except Exception as exc:
            logger.exception(f"[Browser] launch failed: {exc}")
            return False

    async def focus(self, browser: str | None = None) -> bool:
        browser = self._browser(browser)

        if self.system_manager is not None and self.system_manager.windows is not None:
            try:
                windows = self.system_manager.windows
                windows.refresh()
                for window in windows.by_process_name(browser) + windows.by_title(browser):
                    if windows.focus(window):
                        self._set_browser(browser)
                        return True
            except Exception as exc:
                logger.debug(f"[Browser] window focus failed: {exc}")

        if self.input_service:
            await self.input_service.hotkey("alt", "tab")

        self._set_browser(browser)
        return True

    async def open_url(self, url: str, browser: str | None = None) -> bool:
        browser = self._browser(browser)
        url = ExecutionContext.normalize_url(url)
        if not url:
            return False

        command = self._resolve_executable(browser)
        try:
            if command:
                subprocess.Popen(
                    [command, url],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            elif self.system_manager and self.system_manager.applications:
                if not self.system_manager.applications.launch_url(url):
                    webbrowser.open(url)
            else:
                webbrowser.open(url)

            self._set_browser(browser)
            if self.execution_context:
                self.execution_context.set_current_url(url)
            return True
        except Exception as exc:
            logger.exception(f"[Browser] open_url failed: {exc}")
            return False

    async def search(self, query: str, browser: str | None = None) -> bool:
        if not query:
            return False

        url = f"https://www.google.com/search?q={quote_plus(str(query))}"
        success = await self.open_url(url, browser=browser)
        if success and self.execution_context:
            self.execution_context.last_search = str(query)
        return success

    async def current_url(self) -> str | None:
        if self.execution_context:
            return self.execution_context.current_url
        return None

    async def new_tab(self) -> bool:
        return await self._hotkey("ctrl", "t")

    async def close_tab(self) -> bool:
        return await self._hotkey("ctrl", "w")

    async def refresh(self) -> bool:
        return await self._hotkey("ctrl", "r")

    async def back(self) -> bool:
        return await self._hotkey("alt", "left")

    async def forward(self) -> bool:
        return await self._hotkey("alt", "right")

    async def scroll(self, direction: str = "down") -> bool:
        amount = -5 if str(direction).lower() == "down" else 5
        if self.input_service is None:
            return False
        return await self.input_service.scroll(amount)

    async def click(
        self,
        _element: str,
        button: str = "left",
        clicks: int = 1,
        interval: float = 0.1,
    ) -> bool:
        if self.input_service is None:
            return False
        return await self.input_service.click(
            button=button,
            clicks=clicks,
            interval=interval,
        )

    async def _hotkey(self, *keys: str) -> bool:
        if self.input_service is None:
            return False
        return await self.input_service.hotkey(*keys)

    def _browser(self, browser: str | None) -> str:
        if self.execution_context:
            normalized = self.execution_context.normalize_browser(browser)
            if normalized:
                return normalized
            if self.execution_context.current_browser:
                return self.execution_context.current_browser
            return self.execution_context.DEFAULT_BROWSER

        return ExecutionContext.normalize_browser(browser) or ExecutionContext.DEFAULT_BROWSER

    def _set_browser(self, browser: str | None) -> None:
        if self.execution_context:
            self.execution_context.set_browser(browser)
            self.execution_context.current_app = self.execution_context.current_browser

    def _resolve_executable(self, browser: str) -> str | None:
        for candidate in self.EXECUTABLES.get(browser, (browser,)):
            path = shutil.which(candidate)
            if path:
                return path

        common_paths = {
            "chrome": [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            ],
            "edge": [
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            ],
            "firefox": [
                r"C:\Program Files\Mozilla Firefox\firefox.exe",
                r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
            ],
            "brave": [
                r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
                r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
            ],
        }

        for path in common_paths.get(browser, []):
            if Path(path).exists():
                return path

        return None
