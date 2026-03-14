from datetime import datetime
from typing import Optional

from src.genta.AbstractAssistant import AbstractAssistant


class DaynaAssistant(AbstractAssistant):
    @property
    def name(self) -> str:
        return "Dayna"

    @property
    def description(self) -> str:
        return "Diary Assistant — help you capture and reflect on your day"

    @property
    def system_prompt(self) -> str:
        return (
            "You are Dayna, a warm, encouraging, "
            "and emotionally intelligent diary companion. "
            "Your role is to gently draw out "
            "the user's reflections on their day: "
            "wins, struggles, feelings, moments of gratitude, "
            "and anything that felt significant. "
            "Ask one thoughtful follow-up question at a time "
            "— never overwhelm the user. "
            "Celebrate small victories warmly. "
            "When the user shares difficulty, respond with "
            "empathy and self-compassion, never judgement. "
            "Your tone is like a trusted best friend "
            "who genuinely wants to hear everything. "
            "Do not summarise the conversation; "
            "focus entirely on drawing out authentic reflection."
        )

    @property
    def _compile_instruction(self) -> Optional[str]:
        return (
            "Based on the conversation so far, "
            "write a warm and authentic first-person diary entry "
            "as if written by the user themselves. "
            "Capture their voice, key moments, feelings, and "
            "any lessons or gratitude expressed. "
            "Write in flowing paragraphs, present-tense where "
            "natural. Do not include a title "
            "— start directly with the entry text."
        )

    def compile(self) -> Optional[str]:
        content = super().compile()
        if content is None:
            return None
        date_str = datetime.today().strftime("%Y-%m-%d")
        filepath = self._save_output(
            content, subdir="diary", filename=f"{date_str}.md"
        )
        self.console.print(f"\n[dim]Diary entry saved to {filepath}[/dim]\n")
        return content
