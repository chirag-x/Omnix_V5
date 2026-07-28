
from utils.logger import setup_logger
from core.omnix_engine import OmnixEngine

def main():

    setup_logger()

    engine = OmnixEngine()

    engine.initialize()

    engine.start()

    engine.run()


if __name__ == "__main__":
    main()
