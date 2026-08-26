import asyncio
import inspect
import threading
import time

import speech_recognition as sr
from loguru import logger

from voice.tts_engine import OfflineTTS
from voice.speech_recognizer import SpeechRecognizer
from voice.wake_listener import WakeListener


class VoiceManager:
    """
    Omnix V5 Voice Manager.

    VoiceManager handles only:

        - Wake word detection
        - Speech recognition
        - Voice output
        - Optional interruption
        - Forwarding recognized text to OmnixEngine

    It does NOT own:

        - AI
        - Agent execution
        - Planning
        - Skills
        - Automation

    Execution flow:

        WakeListener
            ↓
        SpeechRecognizer
            ↓
        VoiceManager
            ↓
        execute_callback
            ↓
        OmnixEngine.execute(...)
            ↓
        Result
            ↓
        VoiceManager
            ↓
        TTS
    """

    def __init__(
        self,
        execute_callback=None,
        command_processor=None,
    ):

        if execute_callback is not None and not callable(execute_callback):
            raise TypeError("execute_callback must be callable.")

        self.execute_callback = execute_callback

        # Real voice components.
        self.tts = OfflineTTS()

        self.recognizer = SpeechRecognizer()

        # IMPORTANT:
        #
        # VoiceManager must NEVER create its own
        # CommandProcessor.
        #
        # The engine injects the shared planning instance.
        self.command_processor = command_processor

        command_detector = self._get_command_detector()

        self.wake_listener = WakeListener(
            activation_callback=self._on_wake_detected,
            command_detector=command_detector,
        )

        self.running = False

        self._listening_for_command = False

        self._lock = threading.RLock()

        # ------------------------------------------------
        # Interrupt listener foundation
        # ------------------------------------------------

        self._interrupt_recognizer = sr.Recognizer()

        self._interrupt_recognizer.energy_threshold = 400

        self._interrupt_recognizer.dynamic_energy_threshold = True

        self._interrupt_thread = None

        self._interrupt_stop_fn = None

    # ====================================================================
    # ENGINE CONNECTION
    # ====================================================================

    def set_execute_callback(
        self,
        callback,
    ) -> None:

        if callback is not None and not callable(callback):
            raise TypeError("execute_callback must be callable.")

        self.execute_callback = callback

        logger.debug("VoiceManager execute callback updated.")

    def set_command_processor(
        self,
        command_processor,
    ) -> None:

        self.command_processor = command_processor

        command_detector = self._get_command_detector()

        if hasattr(
            self.wake_listener,
            "command_detector",
        ):
            self.wake_listener.command_detector = command_detector

        logger.debug("VoiceManager command processor updated.")

    def _get_command_detector(
        self,
    ):

        if self.command_processor is None:
            return None

        for attribute in (
            "looks_like_automation",
            "is_simple_automation",
        ):

            detector = getattr(
                self.command_processor,
                attribute,
                None,
            )

            if callable(detector):
                return detector

        return None

    # ====================================================================
    # START
    # ====================================================================

    def start(
        self,
    ):

        if self.running:

            logger.debug("VoiceManager already running.")

            return True

        logger.info("VoiceManager starting...")

        self.running = True

        self.wake_listener.start()

        logger.info("Omnix is waiting for wake word: " "'Hey Omnix'")

        print("[Omnix] Sleeping... " "Say 'Hey Omnix' to wake me up.")

        return True

    # ====================================================================
    # PAUSE / RESUME
    # ====================================================================

    def pause(
        self,
    ):

        try:

            self.wake_listener.paused = True

            self.wake_listener.stop(wait=False)

        except Exception as error:

            logger.debug(f"Voice pause error: {error}")

    def resume(
        self,
    ):

        if not self.running:
            return

        try:

            self.wake_listener.paused = False

            self.wake_listener.start()

        except Exception as error:

            logger.debug(f"Voice resume error: {error}")

    # ====================================================================
    # ENGINE EXECUTION
    # ====================================================================

    def _execute_command(
        self,
        text: str,
    ):

        text = str(text or "").strip()

        if not text:
            return None

        callback = self.execute_callback

        if callback is None:

            logger.error(
                "Voice command received but " "no execute_callback is configured."
            )

            return "My command system is " "not ready yet."

        try:

            result = callback(text)

            if inspect.isawaitable(result):

                result = self._resolve_awaitable(result)

            return result

        except Exception as error:

            logger.exception(f"Voice command execution failed: " f"{error}")

            return "Sorry, I had trouble processing " "that command."

    @staticmethod
    def _resolve_awaitable(
        awaitable,
    ):

        try:

            asyncio.get_running_loop()

        except RuntimeError:

            return asyncio.run(awaitable)

        result_holder = {
            "value": None,
            "error": None,
        }

        finished = threading.Event()

        def runner():

            try:

                result_holder["value"] = asyncio.run(awaitable)

            except Exception as error:

                result_holder["error"] = error

            finally:

                finished.set()

        thread = threading.Thread(
            target=runner,
            daemon=True,
        )

        thread.start()

        finished.wait()

        if result_holder["error"] is not None:

            raise result_holder["error"]

        return result_holder["value"]

    # ====================================================================
    # RESPONSE EXTRACTION
    # ====================================================================

    def _extract_response(
        self,
        result,
    ) -> str:

        if result is None:
            return ""

        if isinstance(
            result,
            str,
        ):
            return result.strip()

        if isinstance(
            result,
            dict,
        ):

            for key in (
                "response",
                "message",
                "text",
                "output",
                "answer",
                "content",
            ):

                value = result.get(key)

                if value:

                    return str(value).strip()

            if result.get("error"):

                return str(result["error"]).strip()

            value = result.get("value")

            if value is not None:

                return self._extract_response(value)

            return ""

        for attribute in (
            "response",
            "message",
            "text",
            "output",
            "answer",
            "content",
        ):

            value = getattr(
                result,
                attribute,
                None,
            )

            if value:

                return str(value).strip()

        value = getattr(
            result,
            "value",
            None,
        )

        if value is not None:

            return self._extract_response(value)

        error = getattr(
            result,
            "error",
            None,
        )

        if error:

            return str(error).strip()

        return str(result).strip()

    # ====================================================================
    # PROCESS RECOGNIZED COMMAND
    # ====================================================================

    def _process_and_respond(
        self,
        text: str,
        *,
        source: str = "voice",
    ):

        text = str(text or "").strip()

        if not text:
            return

        print(f"[User - {source}] {text}")

        logger.info(f"Voice command received: {text}")

        result = self._execute_command(text)

        response = self._extract_response(result)

        if response:

            print(f"[Omnix] {response}")

            self.speak(response)

    # ====================================================================
    # WAKE WORD CALLBACK
    # ====================================================================

    def _on_wake_detected(
        self,
        exit_requested=False,
        command_text=None,
    ):

        if exit_requested:

            logger.info("Exit command received.")

            self.speak("Goodbye! Shutting down.")

            self.shutdown()

            return

        with self._lock:

            if self._listening_for_command:

                logger.debug("Already listening. " "Ignoring duplicate wake.")

                return

            self._listening_for_command = True

        try:

            if command_text:

                logger.info("Direct voice command detected: " f"{command_text}")

            else:

                logger.info("Wake word detected. " "Listening for command...")

            try:

                self.wake_listener.paused = True

                self.wake_listener.stop(wait=True)

            except Exception as error:

                logger.debug(f"Wake listener stop error: " f"{error}")

            # --------------------------------------------
            # Direct command
            #
            # "Hey Omnix open Chrome"
            # --------------------------------------------

            if command_text:

                self.tts.stop_and_flush()

                self._process_and_respond(
                    command_text,
                    source="direct",
                )

                return

            # --------------------------------------------
            # Wake first
            #
            # "Hey Omnix"
            # "Open Chrome"
            # --------------------------------------------

            self.tts.stop_and_flush()

            time.sleep(0.3)

            self.speak("Yes, I'm listening.")

            self._wait_for_speech_to_finish()

            time.sleep(0.5)

            print("[VoiceManager] " "Listening for command...")

            text = self._listen_for_user_command()

            if not text:

                logger.info("No command heard after wake word.")

                self.speak("No command heard.")

                return

            self._process_and_respond(
                text,
                source="wake",
            )

        except Exception as error:

            logger.exception(f"Wake handler error: {error}")

        finally:

            try:

                self._wait_for_speech_to_finish()

                if self.running:

                    time.sleep(0.2)

                    self.wake_listener.paused = False

                    self.wake_listener.start()

            except Exception as error:

                logger.error("Failed to restart wake listener: " f"{error}")

            with self._lock:

                self._listening_for_command = False

    # ====================================================================
    # LISTEN
    # ====================================================================

    def _listen_for_user_command(
        self,
    ):

        for attempt in range(2):

            text = self.recognizer.listen_command()

            if not text:
                return None

            if self._looks_like_tts_echo(text):

                logger.info("Ignoring likely TTS echo: " f"{text}")

                if attempt == 0:
                    continue

                return None

            return text

        return None

    def listen_command(
        self,
    ):

        return self._listen_for_user_command()

    # ====================================================================
    # ECHO PROTECTION
    # ====================================================================

    @staticmethod
    def _looks_like_tts_echo(
        text,
    ):

        text = str(text or "").lower().strip(" .,!?:;")

        echo_phrases = {
            "yes i'm listening",
            "yes i am listening",
            "i'm listening",
            "i am listening",
            "listening",
        }

        return text in echo_phrases

    # ====================================================================
    # TTS
    # ====================================================================

    def speak(
        self,
        text: str,
    ):

        text = str(text or "").strip()

        if not text:
            return

        self.tts.speak(text)

    def say(
        self,
        text: str,
    ):

        return self.speak(text)

    # ====================================================================
    # STATUS
    # ====================================================================

    def status(
        self,
    ):

        return {
            "running": self.running,
            "listening_for_command": (self._listening_for_command),
            "tts_speaking": bool(
                getattr(
                    self.tts,
                    "speaking",
                    False,
                )
            ),
            "has_execute_callback": (self.execute_callback is not None),
            "has_command_processor": (self.command_processor is not None),
            "wake_listener": type(self.wake_listener).__name__,
            "recognizer": type(self.recognizer).__name__,
            "tts": type(self.tts).__name__,
        }

    # ====================================================================
    # HELPERS
    # ====================================================================

    def _wait_for_speech_to_finish(
        self,
        timeout: float = 30.0,
    ):

        start = time.monotonic()

        while bool(
            getattr(
                self.tts,
                "speaking",
                False,
            )
        ):

            if (time.monotonic() - start) >= timeout:

                logger.warning("Timed out waiting for TTS.")

                break

            time.sleep(0.1)

    # ====================================================================
    # SHUTDOWN
    # ====================================================================

    def shutdown(
        self,
    ):

        logger.info("VoiceManager shutting down.")

        self.running = False

        try:

            self.wake_listener.stop(wait=False)

        except Exception:
            pass

        if self._interrupt_stop_fn:

            try:

                self._interrupt_stop_fn(wait_for_stop=False)

            except Exception:
                pass

            self._interrupt_stop_fn = None

        try:

            self.tts.stop_and_flush()

        except Exception:
            pass

        try:

            self.tts.shutdown()

        except Exception as error:

            logger.debug(f"TTS shutdown error: {error}")

        return True

    stop = shutdown
