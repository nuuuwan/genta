<<<<<<< HEAD
=======
import os
>>>>>>> dfba8c6 (Add initial implementation of genta assistants and project structure)
from datetime import datetime
from typing import Optional

from src.genta.AbstractAssistant import AbstractAssistant

<<<<<<< HEAD

class DaynaAssistant(AbstractAssistant):
=======
DIR_DIARY = os.environ.get("DIR_DIARY")
if not DIR_DIARY:
    raise EnvironmentError("DIR_DIARY environment variable is not set.")

_N_RECENT = 1
_DATE_FILE_RE = __import__("re").compile(r"^\d{4}-\d{2}-\d{2}\.md$")


def _load_recent_entries(n: int = _N_RECENT):
    """Return (filenames, combined_content) for the most recent n entries."""
    if not os.path.isdir(DIR_DIARY):
        return [], ""
    files = sorted(f for f in os.listdir(DIR_DIARY) if _DATE_FILE_RE.match(f))
    recent = files[-n:] if len(files) >= n else files
    parts = []
    for fname in recent:
        path = os.path.join(DIR_DIARY, fname)
        with open(path, encoding="utf-8") as fh:
            parts.append(fh.read().strip())
    return recent, "\n\n---\n\n".join(parts)


class DaynaAssistant(AbstractAssistant):
    def __init__(self):
        super().__init__()
        self._recent_files, self._recent_entries = _load_recent_entries()

>>>>>>> dfba8c6 (Add initial implementation of genta assistants and project structure)
    @property
    def name(self) -> str:
        return "Dayna"

    @property
    def description(self) -> str:
<<<<<<< HEAD
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
=======
        return "Diary Assistant" " — reflect on your day through questions"

    @property
    def system_prompt(self) -> str:
        base = (
            "You are Dayna, a diary companion. "
            "Your ONLY role is to ask ONE insightful, "
            "open-ended question per turn to help "
            "the user reflect on their day. "
            "Never make statements, observations, "
            "compliments, or summaries. "
            "Never mirror the user's words back to them. "
            "Each question must be short, specific, "
            "and emotionally attuned. "
            "Rotate across: moments of joy or pride, "
            "struggles or frustrations, decisions made, "
            "interactions with others, and feelings "
            "that lingered. "
            "Start with a simple open question."
        )
        if not self._recent_entries:
            return base
        return (
            base + "\n\nFor context, here are the user's most recent "
            "diary entries:\n\n"
            + self._recent_entries
            + "\n\nUse these entries to notice patterns, growth, "
            "or unresolved threads — but ask about today, "
            "not the past."
        )

    @property
    def _opening_seed(self) -> str:
        if self._recent_entries:
            return (
                "The user's recent diary entries are in "
                "your system prompt. "
                "Briefly summarise the key themes or "
                "feelings from those entries in 2-3 "
                "sentences — no questions yet."
            )
        return "Hello"
>>>>>>> dfba8c6 (Add initial implementation of genta assistants and project structure)

    @property
    def _compile_instruction(self) -> Optional[str]:
        return (
            "Based on the conversation so far, "
<<<<<<< HEAD
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
=======
            "write a warm and authentic first-person "
            "diary entry as if written by the user. "
            "Capture their voice, key moments, feelings, "
            "and any lessons or gratitude expressed. "
            "Write in flowing paragraphs. "
            "Do not include a title "
            "— start directly with the entry text."
        )

    def run(self) -> None:
        self._print_welcome()
        if self._recent_files:
            names = ", ".join(self._recent_files)
            self.console.print(f"[dim]Context loaded from: {names}[/dim]\n")
        greeting = self._send(self._opening_seed)
        self._print_assistant(greeting)

        from rich.prompt import Prompt

        while True:
            user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]").strip()

            if not user_input:
                continue

            if user_input.lower() in ("q", "x", "quit", "exit"):
                self._on_quit()
                self.console.print("\n[dim]Goodbye.[/dim]\n")
                break

            if user_input.lower() in ("done", "finish"):
                self._handle_done()
                break

            reply = self._send(user_input)
            self._print_assistant(reply)

    def _append_diary_entry(self, content: str) -> str:
        os.makedirs(DIR_DIARY, exist_ok=True)
        date_str = datetime.today().strftime("%Y-%m-%d")
        time_str = datetime.now().strftime("%H:%M")
        filepath = os.path.join(DIR_DIARY, f"{date_str}.md")
        if not os.path.exists(filepath):
            header = f"# {date_str}\n\n"
        else:
            header = ""
        with open(filepath, "a", encoding="utf-8") as fh:
            fh.write(f"{header}## {time_str}\n\n{content}\n")
        return filepath

    def _on_quit(self) -> None:
        content = self.compile()
        if not content:
            return
        filepath = self._append_diary_entry(content)
        word_count = len(content.split())
        char_count = len(content)
        self.console.print(
            f"\n[bold green]Diary entry saved[/bold green] "
            f"[dim]→ {filepath}[/dim]"
        )
        self.console.print(
            f"[dim]{word_count} words · {char_count} characters[/dim]\n"
        )
>>>>>>> dfba8c6 (Add initial implementation of genta assistants and project structure)
