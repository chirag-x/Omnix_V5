from sys import executable

from loguru import logger
import asyncio
import subprocess
import shutil
import psutil
import inspect
import os
from pathlib import Path


class AutomationEngine:
    def __init__(
        self,
        executor,
        system_manager=None,
        input_service=None,
        browser_service=None,
        execution_context=None,
    ):
        logger.info("[Automation] Initializing engine")

        self.executor = executor
        self.system = system_manager
        self.input = input_service
        self.browser = browser_service
        self.execution_context = execution_context
        self.running = True

    def execute_plan(self, plan):
        logger.info("[Automation] Starting plan")

        for step in plan:
            if not self.running:
                logger.warning("[Automation] Stopped")
                break

            normalized_step = self._normalize_step(step)
            skill_name = normalized_step.get("skill")

            logger.info(f"[Automation] Executing step: {skill_name}")

            result = self._execute_step(normalized_step)

            if result == "error":
                logger.error(f"[Automation] Step failed: {skill_name}")

        logger.info("[Automation] Plan finished")

    def _normalize_step(self, step):
        params = (
            step.get("parameters", step.get("params", {}))
            if isinstance(step, dict)
            else {}
        )

        return {
            "skill": step.get("skill") if isinstance(step, dict) else None,
            "parameters": params if isinstance(params, dict) else {},
        }

    def _execute_step(self, step):
        if hasattr(self.executor, "execute_step"):
            return self.executor.execute_step(step)

        if hasattr(self.executor, "execute_skill"):
            return self.executor.execute_skill(step)

        skill = self.executor.get_skill(step.get("skill"))

        if not skill:
            logger.error(f"[Automation] Skill not found: {step.get('skill')}")
            return "error"

        params = step.get("parameters", {})

        if hasattr(skill, "run"):
            return skill.run(params) or "success"

        if hasattr(skill, "execute"):
            return skill.execute(**params) or "success"

        logger.error(
            f"[Automation] Skill has no executable entry point: {step.get('skill')}"
        )
        return "error"

    # --------------------------------------------------
    # Application Resolution
    # --------------------------------------------------

    @staticmethod
    def _normalize_application_name(app: str) -> str:
        """
        Normalize a user supplied application name.

        Examples:
            "Google Chrome" -> "chrome"
            "chrome.exe"    -> "chrome"
            "VS Code"       -> "vscode"
        """

        app = str(app or "").strip().lower()

        if app.endswith(".exe"):
            app = app[:-4]

        app = " ".join(app.split())

        aliases = {
            # Browsers
            "google chrome": "chrome",
            "chrome browser": "chrome",
            "microsoft edge": "edge",
            "edge browser": "edge",
            "mozilla firefox": "firefox",
            # Development
            "vs code": "vscode",
            "visual studio code": "vscode",
            "code": "vscode",
            # Windows applications
            "file explorer": "explorer",
            "windows explorer": "explorer",
            "command prompt": "cmd",
            "powershell": "powershell",
            "windows terminal": "terminal",
            "calculator": "calculator",
            # Common applications
            "discord app": "discord",
            "spotify app": "spotify",
        }

        return aliases.get(app, app)

    def _application_candidates(self, app: str) -> list[str]:
        """
        Return possible executable names for an application.
        """

        app = self._normalize_application_name(app)

        known = {
            # Browsers
            "chrome": ["chrome.exe"],
            "edge": ["msedge.exe"],
            "firefox": ["firefox.exe"],
            # Development
            "vscode": ["Code.exe", "code.exe"],
            "visualstudio": ["devenv.exe"],
            # Communication / media
            "discord": ["Discord.exe"],
            "spotify": ["Spotify.exe"],
            # Windows applications
            "notepad": ["notepad.exe"],
            "calculator": ["calc.exe"],
            "calc": ["calc.exe"],
            "paint": ["mspaint.exe"],
            "cmd": ["cmd.exe"],
            "powershell": ["powershell.exe"],
            "terminal": ["wt.exe"],
            "explorer": ["explorer.exe"],
        }

        candidates = list(known.get(app, []))

        if app:
            candidates.extend(
                [
                    app,
                    f"{app}.exe",
                ]
            )

        # Remove duplicates while preserving order.
        result = []
        seen = set()

        for candidate in candidates:

            key = candidate.lower()

            if key not in seen:
                seen.add(key)
                result.append(candidate)

        return result

    def _find_application_executable(
        self,
        app: str,
    ) -> str | None:
        """
        Find an installed Windows executable.

        Returns an absolute path or executable name when found.
        """

        raw_app = str(app or "").strip()

        if not raw_app:
            return None

        # --------------------------------------------------
        # 1. User supplied a direct executable path.
        # --------------------------------------------------

        direct_path = Path(raw_app).expanduser()

        if direct_path.is_file():

            return str(direct_path)

        normalized = self._normalize_application_name(raw_app)

        candidates = self._application_candidates(normalized)

        # --------------------------------------------------
        # 2. Search PATH.
        # --------------------------------------------------

        for candidate in candidates:

            path = shutil.which(candidate)

            if path:

                return path

        # --------------------------------------------------
        # 3. Common Windows installation directories.
        # --------------------------------------------------

        roots = []

        program_files = os.environ.get("PROGRAMFILES")

        if program_files:
            roots.append(Path(program_files))

        program_files_x86 = os.environ.get("PROGRAMFILES(X86)")

        if program_files_x86:
            roots.append(Path(program_files_x86))

        local_app_data = os.environ.get("LOCALAPPDATA")

        if local_app_data:
            roots.append(Path(local_app_data))

        app_data = os.environ.get("APPDATA")

        if app_data:
            roots.append(Path(app_data))

        # --------------------------------------------------
        # Known locations for common applications.
        # --------------------------------------------------

        known_paths = {
            "chrome": [
                Path("Google/Chrome/Application/chrome.exe"),
            ],
            "edge": [
                Path("Microsoft/Edge/Application/msedge.exe"),
            ],
            "firefox": [
                Path("Mozilla Firefox/firefox.exe"),
            ],
            "vscode": [
                Path("Programs/Microsoft VS Code/Code.exe"),
                Path("Microsoft VS Code/Code.exe"),
            ],
            "discord": [
                Path("Discord/Discord.exe"),
                Path("Programs/Discord/Discord.exe"),
            ],
            "spotify": [
                Path("Spotify/Spotify.exe"),
            ],
        }

        for root in roots:

            if not root.exists():
                continue

            # First check known paths.
            for relative_path in known_paths.get(normalized, []):

                candidate = root / relative_path

                if candidate.is_file():

                    return str(candidate)

        # --------------------------------------------------
        # 4. Search common executable names directly.
        #
        # We deliberately do not recursively scan the entire
        # drive because that would be slow.
        # --------------------------------------------------

        common_dirs = []

        for root in roots:

            if root.exists():
                common_dirs.append(root)

        for root in common_dirs:

            for candidate_name in candidates:

                try:

                    # Check only a shallow search.
                    matches = list(root.glob(f"*/{candidate_name}"))

                    for match in matches:

                        if match.is_file():

                            return str(match)

                except (OSError, PermissionError):
                    continue

        return None

    async def _launch_executable(
        self,
        executable: str,
        app_name: str,
    ) -> bool:
        """
        Launch an executable and verify that the application starts.
        """

        try:

            process = subprocess.Popen(executable)

            logger.info(
                "[Automation] Started application "
                f"pid={process.pid} executable={executable}"
            )

            await asyncio.sleep(0.8)

            normalized = self._normalize_application_name(app_name)

            if await self.is_running(normalized):

                logger.info(f"[Automation] Verified '{normalized}' is running.")

                return True

            # Some applications use a different process name.
            logger.info(
                "[Automation] Launch command completed successfully "
                f"for '{app_name}'."
            )

            return process.poll() is None

        except Exception as exc:

            logger.exception(f"[Automation] Failed to launch '{executable}': {exc}")

            return False

    # --------------------------------------------------
    # V5 Compatibility API
    # --------------------------------------------------

    async def open_application(
        self,
        app: str,
    ) -> bool:
        """
        Open an installed desktop application.

        Resolution order:

            1. ApplicationManager, if available
            2. Direct executable path
            3. PATH lookup
            4. Common Windows installation locations
        """

        raw_app = str(app or "").strip()

        if not raw_app:

            logger.warning("[Automation] No application name provided.")

            return False

        normalized = self._normalize_application_name(raw_app)

        logger.info(
            f"[Automation] Opening application: {raw_app} "
            f"(normalized: {normalized})"
        )

        # --------------------------------------------------
        # 1. Existing System ApplicationManager
        # --------------------------------------------------

        if (
            self.system is not None
            and getattr(
                self.system,
                "applications",
                None,
            )
            is not None
        ):

            try:

                logger.info("[Automation] Trying ApplicationManager: " f"{normalized}")

                launched = self.system.applications.launch(normalized)

                if asyncio.iscoroutine(launched):

                    launched = await launched

                if launched:

                    await asyncio.sleep(0.8)

                    if await self.is_running(normalized):

                        logger.info(
                            "[Automation] ApplicationManager " "launch verified."
                        )

                        return True

            except Exception as exc:

                logger.debug("[Automation] ApplicationManager failed: " f"{exc}")

        # --------------------------------------------------
        # 2. Resolve executable
        # --------------------------------------------------

        executable = self._find_application_executable(raw_app)

        if executable:

            logger.info(f"[Automation] Resolved '{raw_app}' " f"to: {executable}")

            return await self._launch_executable(
                executable,
                normalized,
            )

        logger.warning("[Automation] Application not found: " f"{raw_app}")

        return False

    async def close_application(self, app: str):
        logger.info(f"[Automation] Closing {app}")

        app = str(app or "").strip()
        image_name = app if app.lower().endswith(".exe") else f"{app}.exe"

        subprocess.run(
            ["taskkill", "/F", "/IM", image_name],
            capture_output=True,
        )

        return True

    async def focus_application(self, app: str):
        logger.info(f"[Automation] Focus application: {app}")

        if self.system is not None and self.system.windows is not None:
            try:
                windows = self.system.windows
                windows.refresh()
                matches = windows.by_application(app) + windows.by_title(app)

                for window in matches:
                    if windows.focus(window):
                        return True
            except Exception as e:
                logger.debug(f"[Automation] Window focus failed: {e}")

        return True

    async def is_running(self, app: str):
        app = str(app or "").lower().strip()

        if not app:
            return False

        process_names = {app, app if app.endswith(".exe") else f"{app}.exe"}

        for proc in psutil.process_iter(["name"]):
            try:
                if str(proc.info.get("name") or "").lower() in process_names:
                    return True
            except (psutil.Error, OSError):
                continue

        result = subprocess.run(
            ["tasklist"],
            capture_output=True,
            text=True,
        )

        return app.lower() in result.stdout.lower()

    # --------------------------------------------------
    # Browser API
    # --------------------------------------------------

    async def open_browser(self, browser: str = "chrome", url: str | None = None):
        if self.browser is None:
            return False

        if not await self.browser.is_running(browser):
            if not await self.browser.launch(browser):
                return False
        else:
            await self.browser.focus(browser)

        if url:
            return await self.browser.open_url(url, browser=browser)

        return True

    async def search_web(self, query: str, browser: str = "chrome"):
        if self.browser is None:
            return False

        return await self.browser.search(query=query, browser=browser)

    async def navigate(self, url: str, browser: str = "chrome"):
        if self.browser is None:
            return False

        return await self.browser.open_url(url=url, browser=browser)

    async def new_tab(self):
        return bool(self.browser and await self.browser.new_tab())

    async def close_tab(self):
        return bool(self.browser and await self.browser.close_tab())

    async def refresh_browser(self):
        return bool(self.browser and await self.browser.refresh())

    async def browser_back(self):
        return bool(self.browser and await self.browser.back())

    async def browser_forward(self):
        return bool(self.browser and await self.browser.forward())

    async def scroll_browser(self, direction: str = "down"):
        return bool(self.browser and await self.browser.scroll(direction=direction))

    async def focus_browser(self, browser: str = "chrome"):
        return bool(self.browser and await self.browser.focus(browser))

    async def browser_action(self, action: str, **parameters):
        action = str(action or "").lower()

        handlers = {
            "open": self.open_browser,
            "open_browser": self.open_browser,
            "focus": self.focus_browser,
            "focus_browser": self.focus_browser,
            "search": self.search_web,
            "open_url": self.navigate,
            "navigate": self.navigate,
            "go_to": self.navigate,
            "new_tab": self.new_tab,
            "close_tab": self.close_tab,
            "refresh": self.refresh_browser,
            "back": self.browser_back,
            "forward": self.browser_forward,
            "scroll": self.scroll_browser,
            "scroll_up": self.scroll_browser,
            "scroll_down": self.scroll_browser,
        }

        handler = handlers.get(action)
        if handler is None:
            logger.warning(f"[Automation] Unsupported browser action: {action}")
            return False

        if action == "scroll_up":
            parameters["direction"] = "up"
        elif action == "scroll_down":
            parameters["direction"] = "down"

        try:
            return await handler(**parameters)
        except TypeError:
            return await handler()

    # --------------------------------------------------
    # Input API
    # --------------------------------------------------

    async def move_mouse(self, x: int, y: int, **kwargs):
        return bool(self.input and await self.input.move_mouse(x, y, **kwargs))

    async def click(self, x=None, y=None, button="left", clicks=1, interval=0.1):
        return bool(
            self.input
            and await self.input.click(
                x=x,
                y=y,
                button=button,
                clicks=clicks,
                interval=interval,
            )
        )

    async def double_click(self, x: int, y: int):
        return bool(self.input and await self.input.double_click(x, y))

    async def right_click(self, x: int, y: int):
        return await self.click(x=x, y=y, button="right")

    async def middle_click(self, x: int, y: int):
        return await self.click(x=x, y=y, button="middle")

    async def drag(self, start_x: int, start_y: int, end_x: int, end_y: int, **kwargs):
        return bool(
            self.input
            and await self.input.drag(start_x, start_y, end_x, end_y, **kwargs)
        )

    async def type_text(self, text: str):
        return bool(self.input and await self.input.type_text(text))

    async def press_key(self, key: str):
        return bool(self.input and await self.input.press_key(key))

    async def hotkey(self, *keys: str):
        return bool(self.input and await self.input.hotkey(*keys))

    async def scroll(self, amount: int):
        return bool(self.input and await self.input.scroll(amount))

    # --------------------------------------------------
    # Clipboard API
    # --------------------------------------------------

    async def get_clipboard(self):
        if self.input is None:
            return ""

        return await self.input.get_clipboard()

    async def set_clipboard(self, text: str):
        return bool(self.input and await self.input.set_clipboard(text))

    # --------------------------------------------------
    # Window API
    # --------------------------------------------------

    async def focus_window(self, title: str):
        return self._window_action(title, "focus")

    async def close_window(self, title: str):
        return self._window_action(title, "close")

    async def minimize_window(self, title: str):
        return self._window_action(title, "minimize")

    async def maximize_window(self, title: str):
        return self._window_action(title, "maximize")

    def _window_action(self, title: str, action: str):
        if self.system is None or self.system.windows is None:
            return False

        try:
            windows = self.system.windows
            windows.refresh()

            for window in windows.by_title(title):
                handler = getattr(windows, action)
                if handler(window):
                    return True
        except Exception as e:
            logger.exception(f"[Automation] Window action failed: {e}")

        return False

    def stop(self):
        logger.warning("[Automation] Stopping")
        self.running = False
