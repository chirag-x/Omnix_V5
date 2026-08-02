import asyncio

from skills.manager.skill_manager import SkillManager


async def main():

    manager = SkillManager()

    await manager.initialize()

    print("Skill count:", manager.skill_count())

    print("\nLoaded skills:")

    for skill in manager.list_skills():
        print("-", skill)

    await manager.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
