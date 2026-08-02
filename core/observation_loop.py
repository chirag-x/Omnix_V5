from loguru import logger

from system.services.window_controller import WindowController


class ObservationLoop:
    def __init__(self, vision_manager=None, ui_controller=None, execution_context=None):
        self.vision_manager = vision_manager
        self.ui_controller = ui_controller
        self.execution_context = execution_context
        self.last_observation = None

    def observe(self, previous_observation=None):
        logger.info("[Observation] Capturing desktop state")

        active_info = {}

        if self.execution_context:
            active_info = {
                "app": self.execution_context.current_app,
                "window": self.execution_context.current_window,
            }
        vision_frame = self._latest_vision()

        ui_elements = self._collect_ui_elements(
            vision_frame,
        )

        if self.execution_context:
            self.execution_context.sync_from_system(
                active_window=active_info.get("window"),
                active_app=active_info.get("app"),
            )

        observation = {
            "active_window": active_info.get("window"),
            "active_app": active_info.get("app"),
            "focused_control": self._focused_control(ui_elements),
            "ui_elements": ui_elements,
            "ocr_text": self._visible_text(vision_frame, ui_elements),
            "application_state": self._application_state(),
            "vision": vision_frame,
            "screen_summary": (vision_frame.summary if vision_frame else ""),
        }

        previous = previous_observation or self.last_observation
        observation["changed"] = (
            self._signature(previous) != self._signature(observation)
            if previous
            else False
        )

        self.last_observation = observation
        return observation

    def compare(self, before, after):
        return {
            "changed": self._signature(before) != self._signature(after),
            "before": before,
            "after": after,
        }

    def _latest_vision(self):
        if self.vision_manager is None:
            return None

        return self.vision_manager.get_latest_frame()

    def _collect_ui_elements(self, vision_frame):

        elements = []

        if vision_frame and vision_frame.ui_tree:

            for element in vision_frame.ui_tree.elements:

                bbox = element.bbox

                elements.append(
                    {
                        "source": "vision",
                        "type": element.element_type,
                        "text": element.text,
                        "x": bbox.center_x if bbox else None,
                        "y": bbox.center_y if bbox else None,
                    }
                )

        seen = {
            (
                element.get("source", "vision"),
                str(element.get("type", "")),
                str(element.get("text", "")),
                element.get("x"),
                element.get("y"),
            )
            for element in elements
        }

        if self.ui_controller is None:
            return elements

        try:
            controls = self.ui_controller.list_controls(limit=120)
        except Exception as e:
            logger.debug(f"[Observation] UI Automation unavailable: {e}")
            return elements

        for control in controls:
            text = str(control.get("text") or "").strip()

            if not text:
                continue

            item = {
                "source": "uia",
                "type": control.get("type") or "control",
                "text": text,
                "automation_id": control.get("automation_id"),
                "rectangle": control.get("rectangle") or {},
            }
            rectangle = item["rectangle"]

            if rectangle:
                item["x"] = int((rectangle["left"] + rectangle["right"]) / 2)
                item["y"] = int((rectangle["top"] + rectangle["bottom"]) / 2)

            key = (
                item["source"],
                str(item.get("type", "")),
                item["text"],
                item.get("x"),
                item.get("y"),
            )

            if key not in seen:
                elements.append(item)
                seen.add(key)

        return elements

    def _focused_control(self, ui_elements):
        for element in ui_elements:
            if element.get("focused"):
                return element

        return None

    def _visible_text(
        self,
        vision_frame,
        ui_elements,
    ):
        parts = []

        if vision_frame and vision_frame.summary:
            parts.append(vision_frame.summary)

        seen = set()

        for element in ui_elements:

            text = str(element.get("text") or "").strip()

            if text and text not in seen:
                seen.add(text)
                parts.append(text)

        return "\n".join(parts)

    def _application_state(self):
        if not self.execution_context:
            return {}

        return self.execution_context.to_dict()

    def _signature(self, observation):
        if not observation:
            return None

        elements = observation.get("ui_elements", []) or []
        element_signature = sorted(
            (
                str(element.get("source", "")),
                str(element.get("type", "")),
                str(element.get("text", "")),
                str(element.get("automation_id", "")),
            )
            for element in elements
        )

        return (
            observation.get("active_window"),
            observation.get("active_app"),
            tuple(element_signature),
        )
