import os
import re
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional

import anthropic
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt


class AbstractAssistant(ABC):
    MODEL = "claude-sonnet-4-5"
    HISTORY_ROOT = Path("/tmp/genta")
    HISTORY_MAX_FILES = 25
    HISTORY_MAX_CHARS = 12_000
    HISTORY_TAIL_LINES = 300
    CONTEXT_CHAR_BUDGET = 24_000

    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )
        self.console = Console()
        self.messages: list[dict] = []
        self._history_loaded = False
        self._transcript_path = self._create_transcript_path()
        self._init_transcript()

    # ------------------------------------------------------------------
    # Abstract interface — subclasses must implement these
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def name(self) -> str:
        """Display name of the assistant."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """One-line description shown at session start."""
        ...

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """System prompt defining the assistant's persona and behaviour."""
        ...

    @property
    def _compile_instruction(self) -> Optional[str]:
        """
        Override in subclasses that produce a deliverable.
        Return a prompt fragment instructing the LLM how to compile
        the conversation into a final output.
        """
        return None

    @property
    def _history_enabled(self) -> bool:
        """Override to disable loading startup history."""
        return True

    @property
    def _custom_context_reserved_chars(self) -> int:
        """Override to reserve context budget for assistant-specific inputs."""
        return 0

    # ------------------------------------------------------------------
    # Session transcript + history
    # ------------------------------------------------------------------

    def _assistant_slug(self) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", self.name.lower()).strip("-")
        return slug or "assistant"

    def _create_transcript_path(self) -> Path:
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        directory = self.HISTORY_ROOT / self._assistant_slug()
        directory.mkdir(parents=True, exist_ok=True)
        return directory / f"{ts}.md"

    def _init_transcript(self) -> None:
        started_at = datetime.now().isoformat(timespec="seconds")
        header = f"# {self.name} Conversation\n\n" f"Started: {started_at}\n\n"
        with self._transcript_path.open("w", encoding="utf-8") as fh:
            fh.write(header)

    def _append_transcript(self, speaker: str, text: str) -> None:
        content = text.strip()
        if not content:
            return
        ts = datetime.now().strftime("%H:%M:%S")
        with self._transcript_path.open("a", encoding="utf-8") as fh:
            fh.write(f"## {speaker} ({ts})\n\n{content}\n\n")

    def _history_char_budget(self) -> int:
        system_chars = len(self.system_prompt)
        available = (
            self.CONTEXT_CHAR_BUDGET
            - system_chars
            - self._custom_context_reserved_chars
        )
        return max(0, min(self.HISTORY_MAX_CHARS, available))

    def _history_files(self) -> list[Path]:
        directory = self.HISTORY_ROOT / self._assistant_slug()
        if not directory.exists():
            return []
        files = sorted(directory.glob("*.md"))
        current = self._transcript_path.resolve()
        return [
            p
            for p in files[-self.HISTORY_MAX_FILES :]
            if p.resolve() != current
        ]

    def _build_history_context(
        self,
    ) -> tuple[Optional[str], list[str], bool]:
        files = self._history_files()
        names = [p.name for p in files]
        context: Optional[str] = None
        truncated = False
        if files:
            parts = []
            for path in files:
                try:
                    content = path.read_text(encoding="utf-8").strip()
                except OSError:
                    continue
                if content:
                    parts.append(f"### {path.name}\n\n{content}")

            if parts:
                combined = "\n\n---\n\n".join(parts)
                budget = self._history_char_budget()
                if budget > 0:
                    if len(combined) > budget:
                        lines = combined.splitlines()
                        if len(lines) > self.HISTORY_TAIL_LINES:
                            combined = "\n".join(
                                lines[-self.HISTORY_TAIL_LINES :]
                            )
                            truncated = True
                        if len(combined) > budget:
                            combined = combined[-budget:]
                            truncated = True
                        if truncated:
                            combined = (
                                "[history truncated to latest context]"
                                "\n\n" + combined
                            )
                    context = combined.strip()

        return context, names, truncated

    def _load_history_context(self) -> None:
        if self._history_loaded or not self._history_enabled:
            return
        self._history_loaded = True

        context, files_read, truncated = self._build_history_context()
        if files_read:
            joined = ", ".join(files_read)
            self.console.print(f"[dim]History files read: {joined}[/dim]")
        else:
            self.console.print("[dim]History files read: none[/dim]")

        if truncated:
            self.console.print(
                "[dim]History was long; loaded the latest "
                f"{self.HISTORY_TAIL_LINES} lines within context budget.[/dim]"
            )

        if not context:
            return

        self.messages.append(
            {
                "role": "user",
                "content": (
                    "Conversation history from earlier sessions follows. "
                    "Use it as optional context, prioritizing the current "
                    "conversation:\n\n"
                    f"{context}"
                ),
            }
        )
        self._append_transcript("System", "Loaded startup history context")

    # ------------------------------------------------------------------
    # LLM helpers
    # ------------------------------------------------------------------

    def _call_llm(self, extra_instruction: str = "") -> str:
        system = self.system_prompt
        if extra_instruction:
            system = f"{system}\n\n{extra_instruction}"
        response = self.client.messages.create(
            model=self.MODEL,
            max_tokens=8096,
            system=system,
            messages=self.messages,
        )
        if not response.content:
            return ""
        return response.content[0].text.strip()

    def _send(self, user_message: str, from_user: bool = True) -> str:
        """Add a user turn, call the LLM, record the reply, and return it."""
        self.messages.append({"role": "user", "content": user_message})
        speaker = "You" if from_user else "Seed"
        self._append_transcript(speaker, user_message)
        reply = self._call_llm()
        self.messages.append({"role": "assistant", "content": reply})
        self._append_transcript(self.name, reply)
        return reply

    # ------------------------------------------------------------------
    # Compile
    # ------------------------------------------------------------------

    def compile(self) -> Optional[str]:
        """
        Produce a compiled deliverable from the conversation.
        Returns None if this assistant has no deliverable.
        Subclasses can override to add file-saving or post-processing.
        """
        instruction = self._compile_instruction
        if not instruction or not self.messages:
            return None
        # Anthropic requires the last message to be a user turn.
        # Temporarily append the compile request without mutating history.
        compile_messages = self.messages + [
            {"role": "user", "content": instruction}
        ]
        system = self.system_prompt
        response = self.client.messages.create(
            model=self.MODEL,
            max_tokens=8096,
            system=system,
            messages=compile_messages,
        )
        if not response.content:
            return None
        return response.content[0].text.strip()

    def _save_output(self, content: str, subdir: str, filename: str) -> str:
        """Save content to output/<subdir>/<filename>; return the path."""
        output_dir = os.path.join(os.getcwd(), "output", subdir)
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as fh:
            fh.write(content)
        return filepath

    # ------------------------------------------------------------------
    # Console rendering
    # ------------------------------------------------------------------

    def _print_assistant(self, text: str) -> None:
        self.console.print(
            Panel(
                Markdown(text),
                title=f"[bold magenta]{self.name}[/bold magenta]",
                border_style="magenta",
                padding=(1, 2),
            )
        )

    # ------------------------------------------------------------------
    # Main conversation loop
    # ------------------------------------------------------------------

    def _print_welcome(self) -> None:
        suffix = (
            " and compile your deliverable"
            if self._compile_instruction
            else ""
        )
        self.console.print(
            Panel(
                f"[bold white]{self.name}[/bold white]\n"
                f"[dim]{self.description}[/dim]\n\n"
                "[italic dim]Type [bold]done[/bold] to finish"
                + suffix
                + ", or [bold]q[/bold] to exit"
                " without compiling.[/italic dim]",
                border_style="cyan",
                expand=False,
                padding=(1, 2),
            )
        )

    def _handle_done(self) -> None:
        compiled = self.compile()
        if compiled:
            self.console.print(
                Panel(
                    Markdown(compiled),
                    title="[bold green]Compiled Output[/bold green]",
                    border_style="green",
                    padding=(1, 2),
                )
            )
        else:
            self.console.print(
                "\n[dim]Session ended. "
                "No deliverable for this assistant.[/dim]\n"
            )

    def _on_quit(self) -> None:
        """Called on quit/exit. Override for cleanup or saving."""
        pass

    @property
    def _greeting_seed(self) -> str:
        """Opening message sent to the LLM. Override to customise."""
        return "Hello"

    def _pre_run(self) -> None:
        """Called before the greeting. Override for setup output."""
        pass

    def run(self) -> None:
        self._print_welcome()
        self._pre_run()
        self._load_history_context()
        greeting = self._send(self._greeting_seed, from_user=False)
        self._print_assistant(greeting)

        pending = ""
        while True:
            prompt = (
                "\n[bold cyan]You[/bold cyan]"
            )
            user_input = Prompt.ask(prompt).strip()

            if "\\\\" in user_input or "//" in user_input:
                pending += "\n\n"
                self.console.print()
                continue

            if not user_input:
                continue

            if user_input.lower() in ("q", "x", "quit", "exit"):
                self._on_quit()
                self.console.print("\n[dim]Goodbye.[/dim]\n")
                break

            if user_input.lower() in ("done", "finish"):
                self._handle_done()
                break

            full_message = (pending + user_input).strip()
            pending = ""
            reply = self._send(full_message)
            self._print_assistant(reply)
