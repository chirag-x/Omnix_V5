import time

from loguru import logger

from core.execution_context import ExecutionContext
from system.app_controller import AppController
from system.keyboard_mouse_controller import KeyboardMouseController


class BrowserSkill:
    name = "browser_action"

    def __init__(self, **_deps):
        self.hotkeys = {
            "back": ("alt", "left"),
            "forward": ("alt", "right"),
            "refresh": ("ctrl", "r"),
            "hard_refresh": ("ctrl", "shift", "r"),
            "new_tab": ("ctrl", "t"),
            "close_tab": ("ctrl", "w"),
            "next_tab": ("ctrl", "tab"),
            "previous_tab": ("ctrl", "shift", "tab"),
            "focus_address": ("ctrl", "l"),
        }

    def run(self, params):
        params = params or {}
        action = str(params.get("action", "open_browser")).lower()
        browser = self._browser_from_params(params)

        logger.info(f"[BrowserSkill] Running action={action} browser={browser}")

        if action in {"open", "open_browser"}:
            return self._open_browser(browser)

        if action in {"open_url", "navigate", "go_to"}:
            return self._open_url(browser, params.get("url"))

        if action == "search":
            return self._search(browser, params.get("query") or params.get("text"))

        if action in self.hotkeys:
            return self._hotkey_action(browser, action)

        logger.warning(f"[BrowserSkill] Unknown action: {action}")
        return "error"

    def _browser_from_params(self, params):
        browser = ExecutionContext.normalize_browser(params.get("browser"))
        return browser or ExecutionContext.DEFAULT_BROWSER

    def _open_browser(self, browser):
        logger.info(f"[BrowserSkill] Opening browser: {browser}")
        result = AppController.open_app(browser)
        time.sleep(1)
        return result

    def _search(self, browser, query):
        if not query:
            logger.warning("[BrowserSkill] Search requested without query")
            return "error"

        if self._open_browser(browser) == "error":
            return "error"

        self._focus_address_bar()
        KeyboardMouseController.type_text(str(query))
        KeyboardMouseController.press_key("enter")

        logger.info(f"[BrowserSkill] Search submitted")
        return "success"

    def _open_url(self, browser, url):
        url = ExecutionContext.normalize_url(url)

        if not url:
            logger.warning("[BrowserSkill] URL open requested without url")
            return "error"

        if self._open_browser(browser) == "error":
            return "error"

        self._focus_address_bar()
        KeyboardMouseController.type_text(url)
        KeyboardMouseController.press_key("enter")

        logger.info(f"[BrowserSkill] URL submitted: {url}")
        return "success"

    def _hotkey_action(self, browser, action):
        if self._open_browser(browser) == "error":
            return "error"

        keys = self.hotkeys.get(action)

        if not keys:
            return "error"

        KeyboardMouseController.hotkey(*keys)

        logger.info(f"[BrowserSkill] Hotkey sent for action={action}")
        return "success"

    def _focus_address_bar(self):
        KeyboardMouseController.hotkey("ctrl", "l")
        time.sleep(0.15)
