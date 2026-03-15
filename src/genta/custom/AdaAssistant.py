import os
import re
import subprocess
from typing import Optional

from src.genta.AbstractAssistant import AbstractAssistant

_DIR_DESKTOP = os.environ.get("DIR_DESKTOP")
if not _DIR_DESKTOP:
    raise EnvironmentError("DIR_DESKTOP environment variable is not set.")


def _title_to_kebab(title: str, max_len: int = 32) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug[:max_len].rstrip("-")


def _extract_title(content: str) -> str:
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return "essay"


class AdaAssistant(AbstractAssistant):
    @property
    def name(self) -> str:
        return "Ada"

    @property
    def description(self) -> str:
        return (
            "Essay & Ideas Assistant"
            " — stress-test your ideas and shape them into writing"
        )

    @property
    def system_prompt(self) -> str:
        return (
            "You are Ada, a sharp thinking partner. "
            "Help the user explore and refine an idea "
            "until it is clear and well-argued. "
            "Challenge productively: probe for gaps, "
            "push back, suggest alternative framings. "
            "Ask one focused question per turn. "
            "Keep every response under 200 characters. "
            "Be concise."
        )

    @property
    def _compile_instruction(self) -> Optional[str]:
        return (
            "Based on our conversation, write a focused essay "
            "of around 800 words. "
            "Structure it exactly as follows:\n\n"
            "1. **Title** — clear and direct.\n"
            "2. **Subtitle** — one sentence that sharpens "
            "the title.\n"
            "3. **Introduction** — under 200 characters. "
            "Punchy enough to stop someone scrolling on "
            "social media. No fluff.\n"
            "4. **Five sections**, each with a short "
            "subheading. Make each section earn its place: "
            "one tight argument or insight per section.\n"
            "5. **Conclusion** — engaging and memorable. "
            "Leave the reader with something to think about.\n"
            "6. **Appendix: References** — only if there are "
            "real, specific sources worth citing. "
            "Omit if not applicable.\n\n"
            "Style rules:\n"
            "- Succinct, informative, well-informed.\n"
            "- No MBA jargon. No filler phrases like "
            "'it is worth noting' or 'in conclusion'.\n"
            "- Short sentences. Plain words. "
            "If a simpler word exists, use it.\n"
            "- Write in Markdown."
        )

    def compile(self) -> Optional[str]:
        content = super().compile()
        if content is None:
            return None
        slug = _title_to_kebab(_extract_title(content))
        filepath = os.path.join(_DIR_DESKTOP, f"{slug}.md")
        os.makedirs(_DIR_DESKTOP, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as fh:
            fh.write(content)
        self.console.print(f"\n[dim]Essay saved to {filepath}[/dim]\n")
        subprocess.Popen(["open", filepath])
        return content

    def _on_quit(self) -> None:
        self.compile()
