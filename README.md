# genta

A collection of LLM-powered conversational assistants, each with a distinct personality and purpose.

---

## Design

### Common Behaviour — `AbstractAssistant`

All assistants share a common foundation implemented in `AbstractAssistant`:

- **Rich console UI** — conversations rendered with [`rich`](https://github.com/Textualize/rich) for a polished terminal experience
- **Chat loop** — a structured, open-ended back-and-forth conversation with the user
- **LLM backend** — powered by OpenAI GPT-4o via the `openai` Python SDK
- **Session history** — all messages are tracked so the LLM has full context throughout the conversation
- **Compile step** — at the end of a session (when the user types `done`), an optional deliverable is produced

### How Assistants Differ

Each assistant differs along two axes:

| Axis | What it controls |
|---|---|
| **Persona / reaction style** | How the assistant responds — its tone, what it draws out, which questions it asks |
| **Compile action** | Whether a structured deliverable (diary entry, essay) is produced and saved at end of session |

---

## Assistants

### `TaraAssistant` — Buddhist Philosophy Guide

> *"Let us sit with what was."*

- **Persona**: Compassionate, contemplative, rooted in Buddhist teachings — impermanence (*anicca*), non-self (*anatta*), mindfulness (*sati*), loving-kindness (*metta*)
- **Goal**: Help the user reflect on the day's passings through a Buddhist lens; invite stillness and clarity
- **Deliverable**: None — Tara is purely contemplative, with no side-effects

---

### `Dayna` — Diary Assistant

> *"Tell me about your day."*

- **Persona**: Warm, encouraging, emotionally intelligent
- **Goal**: Gently draw out reflections on wins, struggles, feelings, and moments of gratitude; motivate honesty and self-compassion
- **Deliverable**: A heartfelt diary entry compiled from the conversation, saved to `output/diary/YYYY-MM-DD.md`

---

### `Ada` — Essay & Ideas Assistant

> *"What's the idea? Let's stress-test it."*

- **Persona**: Sharp, intellectually curious, energetic — plays devil's advocate, suggests framings, pushes for clarity
- **Goal**: Help the user explore, develop, and refine ideas; find a thesis, arguments, and counterarguments
- **Deliverable**: A structured essay or outline compiled from the discussion, saved to `output/essays/YYYY-MM-DD-HHmmss.md`

---

## Class Hierarchy

```
AbstractAssistant        (src/abstract_assistant.py)
├── TaraAssistant        (src/tara_assistant.py)
├── Dayna                (src/dayna_assistant.py)
└── Ada                  (src/ada_assistant.py)
```

---

## Usage

```bash
python workflows/pipeline.py
```

Select an assistant when prompted. During the conversation:

- Type anything to chat normally
- Type `done` to end the session — deliverable assistants will compile and save their output
- Type `quit` to exit without compiling

---

## Setup

```bash
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...
python workflows/pipeline.py
```
