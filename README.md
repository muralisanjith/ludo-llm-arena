# 🎲 4-Player Ludo LLM Arena

An extension of Ed Donner's `connect` (Connect Four Arena) repository into a **4-Player Ludo Arena** where LLMs compete head-to-head in real time.

## 🌟 Features
- **4-Player Rules Engine (`arena/board.py`)**: Full implementation of 4-player Ludo rules including base exit on 6, outer track movement, safe squares (start and star squares), token captures with extra turns, consecutive 6s forfeit, exact finish requirements, and automatic turn skipping.
- **LLM Provider Factory (`arena/llm.py`)**: Unified interface supporting:
  - **Gemini**: `gemini-2.5-flash` (`GOOGLE_API_KEY`)
  - **Groq**: `openai/gpt-oss-20b` and `openai/gpt-oss-120b` (`GROQ_API_KEY`)
  - **OpenRouter**: `openai/gpt-oss-120b` (`OPENROUTER_API_KEY`)
- **JSON Prompting & Failure Recovery (`arena/player.py`)**: Prompt design featuring two worked examples for format compliance, single retry on invalid output, and soft random choice fallback to preserve 4-player game continuity.
- **Animated SVG View (`arena/board_view.py`)**: 15x15 cross-shaped board rendering with token stack offsets and smooth `@keyframes dropPiece` highlight animations for the latest moved token.
- **4-Column Gradio Interface (`arena/ludo.py`)**: Interactive UI with 4 model dropdown selectors, live inner thoughts panels, step/run/reset controls, game history, and model leaderboard.

---

## 🛠️ Environment Setup

Create a `.env` file in the root directory:

```env
GOOGLE_API_KEY=your_google_api_key_here
GROQ_API_KEY=your_groq_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🚀 Running the Ludo Arena

Start the 4-Player Gradio web interface:

```bash
python arena/ludo.py
```

Open the local URL provided by Gradio (typically `http://127.0.0.1:7860`) in your browser.

---

## 🧪 Running Unit Tests

Run the full test suite across all 4 components:

```bash
python -m unittest discover tests
```
