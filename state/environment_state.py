from loguru import logger


class EnvironmentState:

    def __init__(self):

        logger.info("Initializing Environment State")

        self.state = {
            "active_window": None,
            "active_app": None,
            "ui_elements": [],
            "last_action": None,
            "last_result": None,
        }

    def update(self, system_context, vision_frame):

        if system_context:

            self.state["active_window"] = system_context.get("active_window")
            self.state["active_app"] = system_context.get("active_app")

        if vision_frame is not None:

            self.state["ui_elements"] = (
                vision_frame.ui_tree.elements if vision_frame.ui_tree else []
            )

            # Keep these synchronized with the latest VisionFrame.
            self.state["active_window"] = vision_frame.active_window
            self.state["active_app"] = vision_frame.active_app

    def set_action_feedback(self, action, result):

        self.state["last_action"] = action
        self.state["last_result"] = result

    def get_state(self):

        return self.state
