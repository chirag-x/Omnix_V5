from core.omnix_engine import OmnixEngine


def print_result(result):
    """
    Safely print different Omnix result types.

    Omnix can return:
    - AIResult for conversation / questions
    - AgentResult for automation / agent tasks
    """

    print()
    print("Omnix:")

    # ---------------------------------------------------------
    # AI RESULT
    # ---------------------------------------------------------

    if type(result).__name__ == "AIResult":

        if result.success:
            value = getattr(result, "value", None)

            if value is not None:
                print(value)
            else:
                print("AI completed the request.")

        else:
            error = getattr(result, "error", None)
            print(f"Error: {error or 'Unknown AI error'}")

        print()
        return

    # ---------------------------------------------------------
    # AGENT RESULT
    # ---------------------------------------------------------

    if hasattr(result, "success"):
        print(f"Success: {result.success}")

    if hasattr(result, "status"):
        print(f"Status: {result.status}")

    if getattr(result, "success", False):

        output = getattr(result, "output", None)

        if output is not None:
            print(f"Output: {output}")

    else:

        error = getattr(result, "error", None)

        if error:
            print(f"Error: {error}")
        else:
            print("Error: Command failed.")

    print()


def main():

    engine = None

    try:

        # -----------------------------------------------------
        # START OMNIX
        # -----------------------------------------------------

        engine = OmnixEngine(auto_start=True)

        print()
        print("=" * 60)
        print("              OMNIX V5 IS READY")
        print("=" * 60)
        print("Talk naturally with Omnix.")
        print()
        print("Examples:")
        print("  - hello")
        print("  - What is artificial intelligence?")
        print("  - Tell me a joke")
        print("  - Open Chrome")
        print("  - Open Notepad")
        print("  - Open Calculator")
        print()
        print("Type 'exit', 'quit', or 'shutdown' to close.")
        print()

        # -----------------------------------------------------
        # MAIN CONVERSATION LOOP
        # -----------------------------------------------------

        while True:

            try:
                command = input("You: ").strip()

            except KeyboardInterrupt:
                print("\n")
                break

            except EOFError:
                print("\n")
                break

            # Ignore empty commands

            if not command:
                continue

            # -------------------------------------------------
            # EXIT COMMANDS
            # -------------------------------------------------

            if command.lower() in {"exit", "quit", "shutdown"}:

                print()
                print("Omnix: Shutting down. Goodbye!")
                print()

                break

            # -------------------------------------------------
            # EXECUTE COMMAND
            # -------------------------------------------------

            try:

                result = engine.execute(command)

                print_result(result)

            except Exception as exc:

                print()
                print("Omnix:")
                print(f"Command execution error: {exc}")
                print()

    except Exception as exc:

        print()
        print("=" * 60)
        print("OMNIX STARTUP FAILED")
        print("=" * 60)
        print(f"Error: {exc}")
        print()

    finally:

        # -----------------------------------------------------
        # SAFE SHUTDOWN
        # -----------------------------------------------------

        if engine is not None:

            try:

                engine.shutdown()

            except Exception as exc:

                print(f"Warning: shutdown encountered an error: {exc}")


if __name__ == "__main__":
    main()
