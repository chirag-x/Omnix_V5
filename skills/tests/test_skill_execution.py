import asyncio

from skills.manager.skill_manager import SkillManager
from skills.core.skill_context import SkillContext


class TestLogger:

    def info(self, message):
        print("[INFO]", message)

    def error(self, message):
        print("[ERROR]", message)

    def warning(self, message):
        print("[WARNING]", message)


class MockSystem:

    async def get_information(self):

        return {
            "os": "Windows",
            "cpu": "Test CPU",
            "memory": "Test Memory",
            "status": "online",
        }


async def main():

    manager = SkillManager()

    await manager.initialize()

    print("Loaded skills:", manager.skill_count())

    context = SkillContext(
        command="get system information",
        intent="system_info",
        logger=TestLogger(),
        system=MockSystem(),
    )

    skill_id = "builtin.system.system_info"

    print("\nExecuting:", skill_id)

    try:

        result = await manager.execute(
            skill_id,
            context,
        )

        print("\nResult:")
        print(result)

    except Exception as error:

        print(
            "\n❌ Execution failed:",
            error,
        )

    await manager.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
