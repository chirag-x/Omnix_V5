class IntentClassifier:

    def __init__(
        self,
        brain_manager,
        command_processor=None,
        available_skills=None,
    ):

        self.brain = brain_manager
        self.command_processor = command_processor
        self.available_skills = sorted(available_skills or [])

    def classify_intent(
        self,
        text,
    ):
        """
        Backward-compatible wrapper.
        """

        return self.classify(text)["intent"]

    def classify(self, text):

        text = str(text).strip()

        if not text:

            return {
                "intent": "chat",
                "confidence": 0.0,
            }

        # -----------------------------------
        # Fast rule-based classification
        # -----------------------------------

        if self.command_processor:

            if self.command_processor.looks_like_automation(text):

                return {
                    "intent": "automation",
                    "confidence": 0.98,
                }

        skill_text = ", ".join(self.available_skills) or "desktop control skills"

        prompt = f"""
You are the intent router for Omnix, a conversational Windows AI assistant.

Classify whether the user wants Omnix to perform an action on the PC or is
having a conversation.

Return ONLY one word: automation or chat.

Choose automation when the user asks Omnix to operate the computer, apps,
files, media, keyboard, mouse, windows, browser, or visible screen.

Choose chat when the user asks for an explanation, opinion, factual answer,
or talks socially without requesting a PC action.

Questions about how to do something are chat unless the user explicitly asks
Omnix to do it.

Available automation skills:
{skill_text}

Examples:
"Open Chrome" -> automation
"Scroll down and click Downloads" -> automation
"Turn the volume up" -> automation
"How do I open Chrome?" -> chat
"What do you think about Spotify?" -> chat
"Can you explain what is on my screen?" -> chat

User input:
{text}
"""

        response = self.brain.ask(prompt)

        if not response:
            return {
                "intent": "chat",
                "confidence": 0.90,
            }

        response = response.lower().strip()

        if "automation" in response:

            return {
                "intent": "automation",
                "confidence": 0.85,
            }

        return {
            "intent": "chat",
            "confidence": 0.80,
        }
