"""
MCP Server — Research Tools
===========================
This is the *server* half of MCP.

An MCP server exposes capabilities (tools, resources, prompts) that any
MCP-compatible *host* (Cursor, Claude Desktop, or our chatbot client)
can discover and call.

Transport: stdio — the host starts this process and talks over stdin/stdout.

Try it alone:
    uv run research_server.py

Or let the chatbot / Cursor launch it for you.
"""

from __future__ import annotations

import json
import os
from typing import List

import arxiv
from mcp.server.fastmcp import FastMCP

PAPER_DIR = "papers"

# Create the MCP server instance. The name shows up when hosts list servers.
mcp = FastMCP("research")


@mcp.tool()
def search_papers(topic: str, max_results: int = 5) -> List[str]:
    """
    Search arXiv for papers on a topic and cache their metadata locally.

    Args:
        topic: Topic to search for (e.g. "transformers", "quantum computing")
        max_results: Max number of papers to retrieve (default: 5)

    Returns:
        List of arXiv paper IDs found in the search
    """
    client = arxiv.Client()
    search = arxiv.Search(
        query=topic,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )
    papers = client.results(search)

    path = os.path.join(PAPER_DIR, topic.lower().replace(" ", "_"))
    os.makedirs(path, exist_ok=True)
    file_path = os.path.join(path, "papers_info.json")

    try:
        with open(file_path, "r") as json_file:
            papers_info = json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        papers_info = {}

    paper_ids: List[str] = []
    for paper in papers:
        paper_ids.append(paper.get_short_id())
        papers_info[paper.get_short_id()] = {
            "title": paper.title,
            "authors": [author.name for author in paper.authors],
            "summary": paper.summary,
            "pdf_url": paper.pdf_url,
            "published": str(paper.published.date()),
        }

    with open(file_path, "w") as json_file:
        json.dump(papers_info, json_file, indent=2)

    print(f"Results saved to: {file_path}")
    return paper_ids


@mcp.tool()
def extract_info(paper_id: str) -> str:
    """
    Look up cached details for a specific paper ID across all topic folders.

    Args:
        paper_id: arXiv paper ID (e.g. "1706.03762")

    Returns:
        JSON string with paper info, or an error message if not found
    """
    if not os.path.isdir(PAPER_DIR):
        return f"No papers directory yet. Search for a topic first."

    for item in os.listdir(PAPER_DIR):
        item_path = os.path.join(PAPER_DIR, item)
        if not os.path.isdir(item_path):
            continue

        file_path = os.path.join(item_path, "papers_info.json")
        if not os.path.isfile(file_path):
            continue

        try:
            with open(file_path, "r") as json_file:
                papers_info = json.load(json_file)
                if paper_id in papers_info:
                    return json.dumps(papers_info[paper_id], indent=2)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error reading {file_path}: {e}")
            continue

    return f"There's no saved information related to paper {paper_id}."


if __name__ == "__main__":
    # stdio = host owns the process lifetime and pipes JSON-RPC messages
    mcp.run(transport="stdio")
