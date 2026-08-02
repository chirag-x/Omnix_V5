import time

from loguru import logger


class WaitEngine:
    def __init__(
        self,
        vision_manager=None,
        ui_controller=None,
        execution_context=None,
        poll_interval=0.25,
    ):
        self.vision_manager = vision_manager
        self.ui_controller = ui_controller
        self.execution_context = execution_context
        self.poll_interval = poll_interval

    def wait_for_window(self, title=None, app=None, timeout=10):
        logger.info(f"[WaitEngine] Waiting for window title={title} app={app}")

        def condition():

            window = str(self._get_context_value("window", "")).lower()

            active_app = str(self._get_context_value("app", "")).lower()

            if self.execution_context:

                try:

                    self.execution_context.sync_from_system()

                except Exception as e:

                    logger.debug(f"[WaitEngine] Context sync failed: {e}")

            title_matches = not title or str(title).lower() in window

            app_matches = not app or str(app).lower() == active_app

            return title_matches and app_matches

        return self._wait_until(condition, timeout=timeout)

    def wait_for_element(
        self, target, timeout=10, control_type=None, window_title=None
    ):
        logger.info(f"[WaitEngine] Waiting for element: {target}")

        if not self.ui_controller:
            return "error"

        def condition():
            return (
                self.ui_controller.find_control(
                    target=target,
                    control_type=control_type,
                    window_title=window_title,
                )
                is not None
            )

        return self._wait_until(condition, timeout=timeout)

    def wait_for_text(self, text, timeout=10):
        logger.info(f"[WaitEngine] Waiting for text: {text}")

        def condition():
            return self._text_present(text)

        return self._wait_until(condition, timeout=timeout)

    def wait_for_loading_complete(self, timeout=15):
        logger.info("[WaitEngine] Waiting for loading to complete")

        loading_terms = {"loading", "please wait", "syncing", "connecting"}

        def condition():
            visible_text = self._visible_text().lower()
            return not any(term in visible_text for term in loading_terms)

        return self._wait_until(condition, timeout=timeout)

    def wait_for_ui_change(self, previous_observation=None, timeout=10):
        logger.info("[WaitEngine] Waiting for UI change")

        previous_signature = self._ui_signature(previous_observation)

        def condition():
            return self._ui_signature() != previous_signature

        return self._wait_until(condition, timeout=timeout)

    def wait_until_visible(self, target, timeout=10, **kwargs):
        return self.wait_for_element(target, timeout=timeout, **kwargs)

    def wait_until_enabled(
        self, target, timeout=10, control_type=None, window_title=None
    ):
        logger.info(f"[WaitEngine] Waiting until enabled: {target}")

        if not self.ui_controller:
            return "error"

        def condition():
            control = self.ui_controller.find_control(
                target=target,
                control_type=control_type,
                window_title=window_title,
            )

            if control is None:
                return False

            try:
                return control.is_enabled()
            except Exception:
                return True

        return self._wait_until(condition, timeout=timeout)

    def _wait_until(self, condition, timeout=10):
        deadline = time.time() + max(float(timeout), 0)

        while time.time() <= deadline:
            try:
                if condition():
                    return "success"
            except Exception as e:
                logger.debug(f"[WaitEngine] Poll failed: {e}")

            time.sleep(self.poll_interval)

        logger.warning("[WaitEngine] Timed out")
        return "error"

    def _text_present(self, text):
        target = str(text or "").lower().strip()

        if not target:
            return False

        return target in self._visible_text().lower()

    def _visible_text(self):
        parts = []

        if self.ui_controller:
            for control in self.ui_controller.list_controls(limit=200):
                value = control.get("text")

                if value:
                    parts.append(str(value))

        vision_frame = (
            self.vision_manager.get_latest_frame() if self.vision_manager else None
        )

        if vision_frame:

            if vision_frame.summary:
                parts.append(vision_frame.summary)

            if vision_frame.ui_tree:

                seen = set()

                for element in vision_frame.ui_tree.elements:

                    text = str(element.text or "").strip()

                    if text and text not in seen:
                        seen.add(text)
                        parts.append(text)

        return "\n".join(parts)

    def _ui_signature(self, observation=None):
        if observation:
            elements = observation.get("ui_elements", [])
            window = observation.get("active_window")
            return window, tuple(self._element_signature(elements))

        elements = []

        if self.ui_controller:

            elements = self.ui_controller.list_controls(limit=100)

        return (
            self._get_context_value("window", ""),
            tuple(self._element_signature(elements)),
        )

    def _element_signature(self, elements):
        return sorted(
            (
                str(element.get("type", "")),
                str(element.get("text", "")),
                str(element.get("automation_id", "")),
            )
            for element in elements or []
        )

    def _get_context_value(
        self,
        key,
        default=None,
    ):
        """
        Compatible reader for ExecutionContext.

        Supports:
        - V5 ExecutionContext object
        - old dictionary context
        """

        if not self.execution_context:
            return default

        # Old dict style support

        if isinstance(self.execution_context, dict):

            return self.execution_context.get(key, default)

        # V5 object style

        mapping = {
            "window": "current_window",
            "app": "current_app",
            "browser": "current_browser",
            "url": "current_url",
        }

        attribute = mapping.get(key, key)

        return getattr(self.execution_context, attribute, default)
