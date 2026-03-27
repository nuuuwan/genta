import os
import re
import subprocess
from typing import Optional

from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

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
    def __init__(self):
        super().__init__()
        self._essay_version = 0
        self._latest_essay: Optional[str] = None

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
            "You are Ada, a sharp thinking partner for essays and short-form "
            "articles. "
            "In the initial discussion phase, inspire ideas: probe for gaps, "
            "challenge assumptions, and suggest stronger framings. "
            "Ask one focused question per turn. "
            "After a draft exists, switch to editing discussion mode: "
            "help the user improve clarity, structure, voice, and "
            "argument quality with "
            "specific revision suggestions. "
            "Keep normal chat replies concise."
        )

    @property
    def _compile_instruction(self) -> Optional[str]:
        return (
            "Based on our conversation, write or revise a focused essay "
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

    def _call_llm(self, extra_instruction: str = "") -> str:
        phase_instruction = (
            "You are in the initial discussion phase. Keep pushing toward a "
            "clear thesis and strong supporting arguments."
            if not self._latest_essay
            else "You are in the editing discussion phase. Treat the existing "
            "draft as editable, and focus your advice on concrete revisions."
        )
        if extra_instruction:
            phase_instruction = f"{phase_instruction}\n\n{extra_instruction}"
        return super()._call_llm(phase_instruction)

    def _build_write_instruction(self) -> str:
        base = self._compile_instruction
        if not base:
            return "Write an essay based on our conversation in Markdown."
        if not self._latest_essay:
            return (
                f"{base}\n\n"
                "This is the first draft. Use the conversation only."
            )
        return (
            f"{base}\n\n"
            "Revise the existing draft using the latest editing discussion. "
            "Keep what is strong, improve what is weak, and return the full "
            "updated essay."
        )

    def _write_essay(self) -> str:
        instruction = self._build_write_instruction()
        write_messages = self.messages + [
            {"role": "user", "content": instruction}
        ]
        response = self.client.messages.create(
            model=self.MODEL,
            max_tokens=8096,
            system=self.system_prompt,
            messages=write_messages,
        )
        if not response.content:
            essay = ""
        else:
            essay = response.content[0].text.strip()

        self._essay_version += 1
        self._latest_essay = essay
        self.messages.append(
            {
                "role": "assistant",
                "content": (
                    f"Essay draft v{self._essay_version}:\n\n{essay}"
                    if essay
                    else f"Essay draft v{self._essay_version}: [empty output]"
                ),
            }
        )
        if essay:
            self._append_transcript(self.name, essay)
        return essay

    def _save_essay(self, content: str) -> str:
        slug = _title_to_kebab(_extract_title(content))
        suffix = f"-v{self._essay_version}" if self._essay_version > 1 else ""
        filename = f"{slug}{suffix}.md"
        filepath = os.path.join(_DIR_DESKTOP, filename)
        os.makedirs(_DIR_DESKTOP, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as fh:
            fh.write(content)
        return filepath

    def compile(self) -> Optional[str]:
        if self._latest_essay:
            content = self._latest_essay
        else:
            content = super().compile()
        if content is None:
            return None
        filepath = self._save_essay(content)
        self.console.print(f"\n[dim]Essay saved to {filepath}[/dim]\n")
        subprocess.Popen(["open", filepath])
        return content

    def _print_essay(self, content: str) -> None:
        title = (
            f"[bold green]Draft Essay v{self._essay_version}[/bold green]"
            if self._essay_version == 1
            else (
                f"[bold green]Revised Essay v"
                f"{self._essay_version}[/bold green]"
            )
        )
        self.console.print(
            Panel(
                Markdown(content),
                title=title,
                border_style="green",
                padding=(1, 2),
            )
        )

    def run(self) -> None:
        self._print_welcome()
        self._pre_run()
        self._load_history_context()
        greeting = self._send(self._greeting_seed, from_user=False)
        self._print_assistant(greeting)

        pending = ""
        while True:
            prompt = "\n[bold cyan]You[/bold cyan]"
            user_input = Prompt.ask(prompt).strip()

            if "\\\\" in user_input or "//" in user_input:
                pending += "\n\n"
                self.console.print()
                continue

            if not user_input:
                continue

            lowered = user_input.lower()

            if lowered in ("q", "x", "quit", "exit"):
                self._on_quit()
                self.console.print("\n[dim]Goodbye.[/dim]\n")
                break

            if lowered in ("done", "finish"):
                self._handle_done()
                break

            if lowered == "write essay":
                self._append_transcript("You", user_input)
                essay = self._write_essay()
                if not essay:
                    self.console.print(
                        "\n[red]Ada returned an empty draft.[/red]\n"
                    )
                    continue
                self._print_essay(essay)
                self.console.print(
                    "\n[dim]Now in editing discussion mode. "
                    "Discuss edits, then type 'write essay' again "
                    "to produce a revised version.[/dim]\n"
                )
                continue

            full_message = (pending + user_input).strip()
            pending = ""
            reply = self._send(full_message)
            self._print_assistant(reply)

    def _on_quit(self) -> None:
        if self._latest_essay:
            self.compile()
