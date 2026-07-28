import unittest

from core.command_processor import CommandProcessor
from core.task_planner import TaskPlanner


class FakeBrain:
    def __init__(self):
        self.calls = 0

    def ask(self, _prompt):
        self.calls += 1
        return "[]"


class WorkflowPlanTests(unittest.TestCase):
    def setUp(self):
        self.processor = CommandProcessor()

    def test_spotify_play_plan_finishes_with_double_click(self):
        plan = self.processor.create_simple_plan("omnix play beliver on spotify")

        self.assertEqual("spotify", plan[0]["parameters"]["app"])
        self.assertIn("wait_for_ui", [step["skill"] for step in plan])
        self.assertEqual("click_ui", plan[-1]["skill"])
        self.assertTrue(plan[-1]["parameters"]["double"])

    def test_bluetooth_plan_opens_specific_page_and_toggles_on(self):
        plan = self.processor.create_simple_plan("omnix turn on bluetooth")

        self.assertEqual(
            {"skill": "open_app", "parameters": {"app": "bluetooth settings"}},
            plan[0],
        )
        self.assertEqual("check", plan[-1]["parameters"]["action"])
        self.assertEqual("Bluetooth", plan[-1]["parameters"]["target"])

    def test_whatsapp_plan_waits_before_typing_message(self):
        plan = self.processor.create_simple_plan(
            "omnix send hii to gopal on whatsap"
        )

        self.assertEqual("whatsapp", plan[0]["parameters"]["app"])
        self.assertEqual("Search", plan[1]["parameters"]["target"])
        self.assertEqual("gopal", plan[2]["parameters"]["value"])
        self.assertEqual("Type a message", plan[-2]["parameters"]["target"])
        self.assertEqual("hii", plan[-2]["parameters"]["value"])

    def test_planner_uses_workflow_plan_without_ai(self):
        planner = TaskPlanner.__new__(TaskPlanner)
        planner.brain = FakeBrain()
        planner.command_processor = self.processor
        planner.allowed_skills = {
            "click_ui",
            "open_app",
            "press_key",
            "ui_control",
            "wait_for_ui",
        }
        planner.execution_context = None
        planner.max_plan_steps = 20

        plan = planner.create_plan("turn on bluetooth", {})

        self.assertEqual(0, planner.brain.calls)
        self.assertEqual("ui_control", plan[-1]["skill"])


if __name__ == "__main__":
    unittest.main()
