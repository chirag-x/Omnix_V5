from loguru import logger


class RecoveryEngine:
    def __init__(self, max_attempts=2):
        self.max_attempts = max_attempts
        self.attempt_counts = {}

    def can_recover(self, step, verification):
        return self._attempt_count(step, verification) < self.max_attempts

    def recovery_steps(self, step, verification):
        self._record_attempt(step, verification)

        skill = step.get("skill")
        params = dict(step.get("parameters", {}) or {})
        reason = getattr(verification, "reason", "")
        retry = getattr(verification, "retry", False)
        status = getattr(verification, "status", None)

        logger.info(f"[Recovery] Building recovery for skill={skill} reason={reason}")
        logger.info(f"[Recovery] Building retry steps for skill={skill} reason={reason} retry={retry} status={status}")

        if skill == "wait_for_ui":
            longer = dict(params)
            longer["timeout"] = max(float(longer.get("timeout", 10)) * 1.5, 5)
            return [{"skill": "wait_for_ui", "parameters": longer}]

        if skill == "click_ui":
            target = params.get("text") or params.get("target")
            steps = []

            if target and not params.get("double"):
                double_params = dict(params)
                double_params["double"] = True
                steps.append({"skill": "click_ui", "parameters": double_params})

            steps.append({"skill": "press_key", "parameters": {"key": "enter"}})
            return steps

        if skill == "ui_control":
            action = str(params.get("action", "")).lower()
            target = params.get("target") or params.get("text")

            if action == "click" and target:
                return [
                    {
                        "skill": "ui_control",
                        "parameters": {**params, "action": "invoke"},
                    },
                    {"skill": "press_key", "parameters": {"key": "enter"}},
                ]

            if action in {"check", "uncheck"}:
                steps = [
                    {"skill": "wait_for_ui", "parameters": {"target": target, "timeout": 5}},
                    {"skill": "ui_control", "parameters": params},
                ]

                if "mismatch" in reason:
                    steps.append({"skill": "press_key", "parameters": {"key": "space"}})

                return steps

            if action in {"set_text", "type"} and target:
                return [
                    {"skill": "click_ui", "parameters": {"text": target}},
                    {"skill": "ui_control", "parameters": params},
                ]

        if skill == "open_app":
            app = params.get("app")

            if app:
                return [
                    {"skill": "open_app", "parameters": params},
                    {"skill": "wait_for_ui", "parameters": {"target": app, "timeout": 5}},
                ]

        if skill in {"press_key", "hotkey", "type_text"}:
            return [{"skill": "press_key", "parameters": {"key": "enter"}}]

        return []

    def _attempt_count(self, step, verification):
        return self.attempt_counts.get(self._key(step, verification), 0)

    def _record_attempt(self, step, verification):
        key = self._key(step, verification)
        self.attempt_counts[key] = self.attempt_counts.get(key, 0) + 1

    def _key(self, step, verification):
        params = step.get("parameters", {}) or {}

        reason = getattr(verification, "reason", "")

        return (
            step.get("skill"),
            tuple(sorted((str(key), str(value)) for key, value in params.items())),
            reason,
        )
