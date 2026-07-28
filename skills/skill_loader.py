import os
import importlib
import inspect
from loguru import logger


class SkillLoader:

    def __init__(self, dependencies=None):

        self.skill_folders = [
            "skills/built_in",
            "skills/generated"
        ]

        self.dependencies = dependencies or {}

    def load_skills(self):

        skills = {}

        for folder in self.skill_folders:

            if not os.path.exists(folder):
                continue

            for file in os.listdir(folder):

                if not file.endswith(".py"):
                    continue

                module_name = file[:-3]
                module_path = folder.replace("/", ".") + "." + module_name

                try:

                    module = importlib.import_module(module_path)
                    # importlib.reload(module)

                    for name, obj in inspect.getmembers(module):

                        if inspect.isclass(obj) and name.endswith("Skill"):

                            skill_instance = self._create_skill(obj)

                            if skill_instance.name in skills:
                                logger.warning(
                                    f"[SkillLoader] Skipping duplicate skill: {skill_instance.name}"
                                )
                                continue

                            skills[skill_instance.name] = skill_instance

                            logger.info(f"[SkillLoader] Loaded skill: {skill_instance.name}")

                except Exception as e:
                    logger.error(f"[SkillLoader] Failed loading skill {module_path}: {e}")

        return skills

    def _create_skill(self, skill_class):
        signature = inspect.signature(skill_class)
        parameters = signature.parameters

        accepts_kwargs = any(
            parameter.kind == inspect.Parameter.VAR_KEYWORD
            for parameter in parameters.values()
        )

        if accepts_kwargs:
            return skill_class(**self.dependencies)

        filtered_dependencies = {
            name: value
            for name, value in self.dependencies.items()
            if name in parameters
        }

        return skill_class(**filtered_dependencies)
