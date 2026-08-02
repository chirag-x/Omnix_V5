import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(PROJECT_ROOT))

from core.intent_classifier import IntentClassifier
from core.command_processor import CommandProcessor
from core.task_planner import TaskPlanner

# -----------------------
# Fake Brain
# -----------------------


class FakeBrain:

    def ask(self, prompt):

        lower_prompt = prompt.lower()

        command = lower_prompt.split("user command:")[-1].strip()

        print("\nCOMMAND:", repr(command), "\n")

        if command.startswith("open"):
            return """
[
{"skill":"open_app","parameters":{"app":"chrome"}}
]
"""

        elif command.startswith("search"):
            return """
[
{"skill":"browser_action","parameters":{"action":"search","query":"AI agents"}}
]
"""

        elif command.startswith("type"):
            return """
[
{"skill":"type_text","parameters":{"text":"Hello World"}}
]
"""

        elif command.startswith("click"):
            return """
[
{"skill":"click_ui","parameters":{"target":"Login"}}
]
"""

        return "[]"


brain = FakeBrain()

processor = CommandProcessor()

classifier = IntentClassifier(
    brain,
    command_processor=processor,
)

planner = TaskPlanner(
    brain_manager=brain,
    command_processor=processor,
)

command = "Search AI agents"

print("=" * 50)

print("INPUT")

print(command)

print("=" * 50)

intent = classifier.classify(command)

print("INTENT")

print(intent)

print("=" * 50)

structured = processor.process(command)

print("STRUCTURED COMMAND")

print(structured)

print("=" * 50)

plan = planner.create_plan(command)

print("PLAN")

for step in plan:

    print(step)

print("=" * 50)
