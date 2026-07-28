import time

from loguru import logger

from system.window_controller import WindowController


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
            info = WindowController.get_active_window_info()
            window = str(info.get("window") or "").lower()
            active_app = str(info.get("app") or "").lower()

            if self.execution_context:
                self.execution_context.sync_from_system(
                    active_window=info.get("window"),
                    active_app=info.get("app"),
                )

            title_matches = not title or str(title).lower() in window
            app_matches = not app or str(app).lower() == active_app
            return title_matches and app_matches

        return self._wait_until(condition, timeout=timeout)

    def wait_for_element(self, target, timeout=10, control_type=None, window_title=None):
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

    def wait_until_enabled(self, target, timeout=10, control_type=None, window_title=None):
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

        analysis = (
            self.vision_manager.get_latest_analysis()
            if self.vision_manager is not None
            else {}
        ) or {}

        for key in ("text", "ocr_text", "screen_text"):
            value = analysis.get(key)

            if isinstance(value, str):
                parts.append(value)

        for element in analysis.get("ui_elements", []) or []:
            value = element.get("text")

            if value:
                parts.append(str(value))

        return "\n".join(parts)

    def _ui_signature(self, observation=None):
        if observation:
            elements = observation.get("ui_elements", [])
            window = observation.get("active_window")
            return window, tuple(self._element_signature(elements))

        info = WindowController.get_active_window_info()
        elements = []

        if self.ui_controller:
            elements = self.ui_controller.list_controls(limit=100)

        return info.get("window"), tuple(self._element_signature(elements))

    def _element_signature(self, elements):
        return sorted(
            (
                str(element.get("type", "")),
                str(element.get("text", "")),
                str(element.get("automation_id", "")),
            )
            for element in elements or []
        )
