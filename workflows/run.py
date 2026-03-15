"""
Run a genta assistant by name.

Usage:
    python workflows/run.py <assistant>

Examples:
    python workflows/run.py tara
    python workflows/run.py dayna
    python workflows/run.py ada
"""

import argparse
import sys

from genta.custom import AdaAssistant, DaynaAssistant, TaraAssistant

REGISTRY = {
    "ada": AdaAssistant,
    "dayna": DaynaAssistant,
    "tara": TaraAssistant,
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a genta assistant.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"Available assistants: {', '.join(sorted(REGISTRY))}",
    )
    parser.add_argument(
        "assistant",
        help="Name of the assistant to run (e.g. tara, dayna, ada)",
    )
    args = parser.parse_args()

    name = args.assistant.lower()
    assistant_cls = REGISTRY.get(name)

    if assistant_cls is None:
        print(
            f"Unknown assistant: '{name}'. "
            f"Available: {', '.join(sorted(REGISTRY))}",
            file=sys.stderr,
        )
        sys.exit(1)

    assistant_cls().run()


if __name__ == "__main__":
    main()
