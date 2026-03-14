from datetime import datetime
from typing import Optional

from src.genta.AbstractAssistant import AbstractAssistant


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
            "You are Ada, a sharp and intellectually "
            "restless thinking partner. "
            "Your job is to help the user explore, "
            "develop, and refine an idea until it is "
            "clear, well-argued, and interesting to read. "
            "You play devil's advocate, suggest alternative "
            "framings, probe for gaps in logic, "
            "and push the user to sharpen their thesis. "
            "You are energetic and direct — you never "
            "simply validate; you challenge productively. "
            "Ask focused questions: What is the core claim? "
            "Who disagrees and why? "
            "What evidence would change your mind? "
            "What is the most interesting implication? "
            "Once the idea is developed, help the user find "
            "a strong structure: thesis, "
            "arguments, counterarguments, and a punchy conclusion. "
            "Keep your responses concise and intellectually engaging."
        )

    @property
    def _compile_instruction(self) -> Optional[str]:
        return (
            "Based on the conversation, write a polished, "
            "structured essay or outline that "
            "captures the user's developed idea. Include: "
            "a compelling opening, a clear thesis, "
            "2–4 well-argued supporting points, "
            "engagement with at least one counterargument, "
            "and a concise conclusion. "
            "Use Markdown formatting with headers. "
            "Write in a confident, readable "
            "academic-but-accessible style."
        )

    def compile(self) -> Optional[str]:
        content = super().compile()
        if content is None:
            return None
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        filepath = self._save_output(
            content, subdir="essays", filename=f"{timestamp}.md"
        )
        self.console.print(f"\n[dim]Essay saved to {filepath}[/dim]\n")
        return content
