# MCP Bootstrap

A minimal, runnable project for learning the **Model Context Protocol (MCP)** — the open standard that lets AI apps discover and call tools from external servers.

You get both sides of the wire:

| File | Role | What it does |
|------|------|----------------|
| `research_server.py` | **MCP Server** | Exposes `search_papers` and `extract_info` tools |
| `mcp_chatbot.py` | **MCP Client / Host** | Starts the server, lists tools, lets Gemini call them |
| `main.py` | Helper | Prints a quick map of the project |

---

## How MCP fits together

```
┌─────────────────┐         stdio (JSON-RPC)        ┌──────────────────┐
│  Host / Client  │ ◄──────────────────────────────► │   MCP Server     │
│  mcp_chatbot.py │   list_tools / call_tool         │ research_server  │
│  + Gemini LLM   │                                  │  • search_papers │
└─────────────────┘                                  │  • extract_info  │
                                                     └──────────────────┘
```

1. The **host** starts the server as a subprocess (`stdio` transport).
2. It calls `list_tools` — the server returns schemas for each `@mcp.tool()`.
3. Those schemas are given to the **LLM** as function declarations.
4. When the model wants data, the host runs `call_tool` on the MCP session and feeds the result back.

Same server can also be plugged into **Cursor** or **Claude Desktop** — that’s the point of the protocol.

---

## Prerequisites

- Python **3.11+**
- [uv](https://docs.astral.sh/uv/) (recommended) **or** pip + venv
- A free [Gemini API key](https://aistudio.google.com/apikey)

### Install uv (if you don’t have it)

```bash
# macOS / Linux
brew install uv

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

---

## Setup

### 1. Clone the repo

```bash
git clone <your-repo-url>
cd mcp_project   # or whatever you named the folder
```

### 2. Configure your API key

```bash
cp .env.example .env
```

Open `.env` and set:

```bash
GEMINI_API_KEY=your_key_here
```

### 3. Install packages

**Option A — uv (recommended)**

```bash
uv sync
```

This creates a virtualenv (`.venv`) and installs everything from `pyproject.toml`:

| Package | Why it’s needed |
|---------|-----------------|
| `mcp` | MCP client + FastMCP server SDK |
| `google-genai` | Gemini API for the chatbot host |
| `arxiv` | Search papers in `search_papers` |
| `python-dotenv` | Load `.env` for the API key |

**Option B — pip + venv**

```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows
# .venv\Scripts\activate

pip install -U pip
pip install mcp google-genai arxiv python-dotenv
```

---

## Run the full demo (client + server)

**With uv:**

```bash
uv run mcp_chatbot.py
```

**With pip / activated venv:**

```bash
python mcp_chatbot.py
```

You’ll see lines like `→ MCP tool: search_papers(...)` when the LLM decides to use a tool.

### Try these questions

Copy-paste any of these after the chatbot starts:

**Search papers (`search_papers`)**
```text
Find 3 papers about transformers
Search for 5 papers on reinforcement learning
Find recent papers about quantum computing
Search arXiv for graph neural networks, max 2 results
What papers exist on attention mechanisms in NLP?
```

**Look up a paper (`extract_info`)**
```text
Tell me about paper 1706.03762
What is the summary of paper 1706.03762?
Who are the authors of paper 1706.03762?
Give me the title and PDF link for paper 1706.03762
```

**Combine both tools**
```text
Search for papers on transformers, then summarize the first one
Find 3 physics papers and tell me what the first paper is about
Search for algorithms papers and list their titles
```

> Tip: run a search first so papers are cached under `papers/`, then ask about a specific paper ID from the results.

Or just print the project map:

```bash
uv run main.py
# or: python main.py
```

---

## Run the server alone

Useful when connecting from Cursor / Claude Desktop:

```bash
uv run research_server.py
# or: python research_server.py
```

This process speaks MCP over **stdin/stdout**. Don’t type into it manually — a host drives it.

### Cursor / Claude Desktop config example

Add something like this to your MCP settings (adjust the path):

```json
{
  "mcpServers": {
    "research": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/mcp_project",
        "run",
        "research_server.py"
      ]
    }
  }
}
```

---

## Tools exposed by the server

### `search_papers(topic, max_results=5)`

Queries arXiv, caches metadata under `papers/<topic>/papers_info.json`, returns paper IDs.

### `extract_info(paper_id)`

Looks up a cached paper by ID across all topic folders.

---

## Project layout

```text
.
├── research_server.py   # MCP server (tools)
├── mcp_chatbot.py       # MCP client + Gemini tool loop
├── main.py              # Quick orientation
├── papers/              # Local cache created by search_papers
├── .env.example         # Copy → .env (never commit secrets)
├── mcp_config.example.json  # Sample Cursor / Claude Desktop MCP config
├── pyproject.toml
├── LICENSE
└── README.md
```

---

## Learning path

1. Read `research_server.py` — how FastMCP registers tools.
2. Read `mcp_chatbot.py` — connect → `list_tools` → LLM → `call_tool`.
3. Run the chatbot and watch tool calls print in the terminal.
4. Point Cursor at the same server and ask the same questions in the IDE.

---

## Notes

- Generated paper caches live in `papers/` (gitignored except `.gitkeep`).
- Keep secrets in `.env` only — `.env` is gitignored.
- Default model is `gemini-2.5-flash`; override with `GEMINI_MODEL` in `.env`.

---

## License

MIT — use this as a learning starter for your own MCP servers.
