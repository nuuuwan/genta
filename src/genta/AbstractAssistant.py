import os
from abc import ABC, abstractmethod
from typing import Optional

import anthropic
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt


class AbstractAssistant(ABC):
    MODEL = "claude-sonnet-4-5"

    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )
        self.console = Console()
        self.messages: list[dict] = []

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

    def _send(self, user_message: str) -> str:
        """Add a user turn, call the LLM, record the reply, and return it."""
        self.messages.append({"role": "user", "content": user_message})
        reply = self._call_llm()
        self.messages.append({"role": "assistant", "content": reply})
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

    def run(self) -> None:
        self._print_welcome()
        greeting = self._send("Hello")
        self._print_assistant(greeting)

        pending = ""
        while True:
            prompt = (
                "\n[bold cyan]   ...[/bold cyan]"
                if pending
                else "\n[bold cyan]You[/bold cyan]"
            )
            user_input = Prompt.ask(prompt).strip()

            if user_input == "//":
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
