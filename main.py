"""
MCP Bootstrap — quick entry helper
==================================
Prints how this project fits together. Prefer the commands below for real use.

  uv run mcp_chatbot.py      # client + LLM + MCP server (full demo)
  uv run research_server.py  # MCP server only (stdio; for Cursor / Claude Desktop)
"""


def main() -> None:
    print(
        """
╔══════════════════════════════════════════════════════════╗
║           MCP Bootstrap — Learn by Running               ║
╚══════════════════════════════════════════════════════════╝

  What is MCP?
    Model Context Protocol — a standard so AI hosts can discover
    and call tools exposed by MCP servers (over stdio, SSE, etc.).

  This repo has two pieces:
    research_server.py  → MCP SERVER  (exposes search_papers, extract_info)
    mcp_chatbot.py      → MCP CLIENT  (Gemini + tool loop over MCP)

  Quick start:
    1. cp .env.example .env   # add GEMINI_API_KEY
    2. uv sync
    3. uv run mcp_chatbot.py

  Then try questions like:
    • Find 3 papers about transformers
    • Tell me about paper 1706.03762
    • Search for reinforcement learning, then summarize the first paper

  More sample questions → README.md
"""
    )


if __name__ == "__main__":
    main()
