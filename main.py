from utils.logger import setup_logger
import asyncio

from core.omnix_engine import OmnixEngine


async def main():

    setup_logger()
    engine = OmnixEngine()

    await engine.initialize()

    await engine.start()

    engine.run()


if __name__ == "__main__":

    asyncio.run(main())
