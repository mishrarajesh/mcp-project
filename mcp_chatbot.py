"""
MCP Client — Chatbot Host
=========================
This is the *client / host* half of MCP.

Flow:
  1. Start the research MCP server as a subprocess (stdio)
  2. Discover the tools it exposes (search_papers, extract_info)
  3. Hand those tool schemas to Gemini so the LLM can choose when to call them
  4. When Gemini requests a tool call, execute it via MCP and feed the result back

Run:
    uv run mcp_chatbot.py

Requires GEMINI_API_KEY in .env (see .env.example).
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import List

from dotenv import load_dotenv
from google import genai
from google.genai import types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


class MCP_ChatBot:
    """Minimal host that wires an LLM to an MCP server over stdio."""

    def __init__(self):
        self.session: ClientSession | None = None
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "Set GEMINI_API_KEY (or GOOGLE_API_KEY) in your .env file. "
                "Get a free key at https://aistudio.google.com/apikey"
            )
        self.client = genai.Client(api_key=api_key)
        self.available_tools: List[types.Tool] = []

    def _mcp_tools_to_gemini(self, mcp_tools) -> List[types.Tool]:
        """Adapt MCP tool schemas into Gemini function declarations."""
        declarations = []
        for tool in mcp_tools:
            schema = tool.inputSchema or {"type": "object", "properties": {}}
            parameters = {
                "type": schema.get("type", "object"),
                "properties": schema.get("properties", {}),
            }
            if "required" in schema:
                parameters["required"] = schema["required"]

            declarations.append(
                types.FunctionDeclaration(
                    name=tool.name,
                    description=tool.description or "",
                    parameters=parameters,
                )
            )
        return [types.Tool(function_declarations=declarations)]

    def _tool_result_to_text(self, result) -> str:
        """Flatten MCP CallToolResult content into a string for Gemini."""
        parts = []
        for item in result.content:
            text = getattr(item, "text", None)
            if text is not None:
                parts.append(text)
            else:
                parts.append(str(item))
        return "\n".join(parts) if parts else json.dumps({"status": "ok"})

    async def process_query(self, query: str) -> None:
        """One user turn: LLM ↔ optional MCP tool calls ↔ final answer."""
        assert self.session is not None

        contents = [types.Content(role="user", parts=[types.Part(text=query)])]
        config = types.GenerateContentConfig(
            tools=self.available_tools,
            # We drive the tool loop ourselves so you can see MCP in action
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=True
            ),
        )

        while True:
            response = self.client.models.generate_content(
                model=MODEL,
                contents=contents,
                config=config,
            )

            candidate = response.candidates[0]
            model_content = candidate.content
            function_calls = [
                part.function_call
                for part in (model_content.parts or [])
                if part.function_call
            ]

            if not function_calls:
                if response.text:
                    print(response.text)
                break

            # Model asked for tools — keep that turn, then run MCP calls
            contents.append(model_content)

            response_parts = []
            for function_call in function_calls:
                tool_name = function_call.name
                tool_args = dict(function_call.args or {})
                print(f"→ MCP tool: {tool_name}({tool_args})")

                result = await self.session.call_tool(tool_name, arguments=tool_args)
                result_text = self._tool_result_to_text(result)

                response_parts.append(
                    types.Part.from_function_response(
                        name=tool_name,
                        response={"result": result_text},
                    )
                )

            contents.append(types.Content(role="user", parts=response_parts))

    async def chat_loop(self) -> None:
        print("\nMCP Chatbot ready (Google Gemini)")
        print(f"Model: {MODEL}")
        print("Type 'quit' to exit.\n")
        print("Try asking:")
        print("  • Find 3 papers about transformers")
        print("  • Tell me about paper 1706.03762")
        print("  • Search for reinforcement learning, then summarize the first paper")
        print()

        while True:
            try:
                query = input("Query: ").strip()
                if query.lower() == "quit":
                    break
                await self.process_query(query)
                print()
            except Exception as e:
                print(f"\nError: {e}")

    async def connect_to_server_and_run(self) -> None:
        # Host launches the MCP server as a child process over stdio
        server_params = StdioServerParameters(
            command="uv",
            args=["run", "research_server.py"],
            env=None,
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                self.session = session
                await session.initialize()

                response = await session.list_tools()
                tools = response.tools
                print("Connected. Tools from MCP server:", [t.name for t in tools])

                self.available_tools = self._mcp_tools_to_gemini(tools)
                await self.chat_loop()


async def main() -> None:
    chatbot = MCP_ChatBot()
    await chatbot.connect_to_server_and_run()


if __name__ == "__main__":
    asyncio.run(main())
