import os
import re
import subprocess
from datetime import datetime
from typing import Optional

from src.genta.AbstractAssistant import AbstractAssistant

DIR_DIARY = os.environ.get("DIR_DIARY")
if not DIR_DIARY:
    raise EnvironmentError("DIR_DIARY environment variable is not set.")

_N_RECENT = 3
_DATE_FILE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\.md$")


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

    @property
    def name(self) -> str:
        return "Dayna"

    @property
    def description(self) -> str:
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
    def _custom_context_reserved_chars(self) -> int:
        return len(self._recent_entries)

    @property
    def _opening_seed(self) -> str:
        if self._recent_entries:
            return (
                "The user's recent diary entries are in "
                "your system prompt. "
                "Summarise the key themes and feelings "
                "from those entries as 3-5 bullet points. "
                "Address the user directly as 'you'. "
                "Be concise and specific. No questions yet."
            )
        return "Hello"

    @property
    def _compile_instruction(self) -> Optional[str]:
        return (
            "Write a first-person diary entry using ONLY "
            "what the user actually said in this conversation. "
            "Do not invent emotions, events, or details "
            "they did not mention. "
            "Where a little context genuinely helps "
            "the sentence make sense, add it in square "
            "brackets, e.g. [a colleague] or [that morning]. "
            "Keep additions minimal and factual. "
            "Write in the user's own voice and natural "
            "phrasing. No title — start directly with "
            "the entry text."
        )

    @property
    def _greeting_seed(self) -> str:
        return self._opening_seed

    def _pre_run(self) -> None:
        if self._recent_files:
            names = ", ".join(self._recent_files)
            self.console.print(f"[dim]Context loaded from: {names}[/dim]\n")

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
        subprocess.Popen(["open", filepath])
