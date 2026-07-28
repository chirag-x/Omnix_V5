from dataclasses import dataclass, field
from typing import Any, ClassVar
from urllib.parse import urlparse

from loguru import logger

_UNSET = object()


@dataclass
class ExecutionContext:
    """
    Runtime state shared by the entire AI system.

    This stores what Omnix currently knows about the desktop,
    browser and workflow so every module has the same context.
    """

    SUPPORTED_BROWSERS: ClassVar[frozenset[str]] = frozenset(
        {
            "chrome",
            "edge",
            "firefox",
            "brave",
        }
    )
    DEFAULT_BROWSER: ClassVar[str] = "chrome"
    BROWSER_ALIASES: ClassVar[dict[str, str]] = {
        "brave browser": "brave",
        "google chrome": "chrome",
        "microsoft edge": "edge",
        "mozilla firefox": "firefox",
    }
    # -----------------------------
    # Desktop
    # -----------------------------

    current_app: str | None = None
    current_window: str | None = None

    # -----------------------------
    # Browser
    # -----------------------------

    current_browser: str | None = None
    current_url: str | None = None
    current_website: str | None = None
    current_tab: int | None = None

    # -----------------------------
    # UI
    # -----------------------------

    focused_element: str | None = None
    selected_element: str | None = None

    # -----------------------------
    # Workflow
    # -----------------------------

    last_action: str | None = None
    last_skill: str | None = None
    last_result: str | None = None

    # -----------------------------
    # Search
    # -----------------------------

    last_search: str | None = None

    # -----------------------------
    # Misc
    # -----------------------------

    workflow_name: str | None = None

    metadata: dict[str, Any] = field(default_factory=dict)

    # ==========================================================
    # Helpers
    # ==========================================================

    def reset(self):

        self.current_app = None
        self.current_window = None

        self.current_browser = None
        self.current_url = None
        self.current_website = None
        self.current_tab = None

        self.focused_element = None
        self.selected_element = None

        self.last_action = None
        self.last_skill = None
        self.last_result = None

        self.last_search = None

        self.workflow_name = None

        self.metadata.clear()

    def update(self, **kwargs):

        for key, value in kwargs.items():

            if hasattr(self, key):

                setattr(self, key, value)

    @classmethod
    def normalize_browser(cls, browser: str | None) -> str | None:
        if browser is None:
            return None

        normalized = str(browser).lower().strip()

        if not normalized:
            return None

        normalized = cls.BROWSER_ALIASES.get(normalized, normalized)
        return normalized if normalized in cls.SUPPORTED_BROWSERS else None

    @classmethod
    def is_supported_browser(cls, browser: str | None) -> bool:
        return cls.normalize_browser(browser) is not None

    @classmethod
    def browser_from_text(cls, text: str | None) -> str | None:
        value = str(text or "").lower()

        if not value:
            return None

        for alias, browser in cls.BROWSER_ALIASES.items():
            if alias in value:
                return browser

        for browser in sorted(cls.SUPPORTED_BROWSERS, key=len, reverse=True):
            if browser in value:
                return browser

        return None

    @staticmethod
    def normalize_url(url: str | None) -> str | None:
        value = str(url or "").strip()

        if not value:
            return None

        if "://" in value or value.startswith("about:"):
            return value

        return f"https://{value}"

    def sync_from_system(
        self,
        active_window=_UNSET,
        active_app=_UNSET,
    ):

        if active_window is not _UNSET:
            self.current_window = active_window

        if active_app is not _UNSET:
            browser = self.normalize_browser(active_app)
            self.current_app = browser or active_app
            self.set_browser(browser)

        logger.info(
            "[ExecutionContext] Synced system state: "
            f"app={self.current_app}, "
            f"window={self.current_window}, "
            f"browser={self.current_browser}"
        )

    def to_dict(self):

        return {
            "current_app": self.current_app,
            "current_window": self.current_window,
            "current_browser": self.current_browser,
            "current_url": self.current_url,
            "current_website": self.current_website,
            "current_tab": self.current_tab,
            "focused_element": self.focused_element,
            "selected_element": self.selected_element,
            "last_action": self.last_action,
            "last_skill": self.last_skill,
            "last_result": self.last_result,
            "last_search": self.last_search,
            "workflow_name": self.workflow_name,
            "metadata": self.metadata,
        }

    def is_app_active(self, app: str | None):

        if not app:
            return False

        if self.current_app is None:
            return False

        current_app = self.normalize_browser(self.current_app) or self.current_app
        target_app = self.normalize_browser(app) or app

        return str(current_app).lower() == str(target_app).lower()

    def is_browser_active(self, browser: str | None = None):

        if self.current_browser is None:
            return False

        if browser is None:
            return True

        return self.current_browser == self.normalize_browser(browser)

    def set_browser(self, browser: str | None):

        previous_browser = self.current_browser
        self.current_browser = self.normalize_browser(browser)

        if self.current_browser is None or self.current_browser != previous_browser:
            self.current_url = None
            self.current_website = None
            self.current_tab = None

    def set_current_url(self, url: str | None):

        self.current_url = self.normalize_url(url)

        if not self.current_url:
            self.current_website = None
            return

        try:
            parsed = urlparse(self.current_url)
            self.current_website = parsed.netloc or parsed.path.split("/")[0]
        except Exception:
            self.current_website = None
