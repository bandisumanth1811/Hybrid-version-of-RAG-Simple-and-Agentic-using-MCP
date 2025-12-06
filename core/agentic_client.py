import asyncio
import os
import sys
from typing import List, Dict, Any
from google import genai
from google.genai import types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

# Add parent dir
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.llm import GeminiClient

load_dotenv()

class AgenticClient:
    def __init__(self):
        self.llm_client = GeminiClient()
        self.model = self.llm_client.model_name
        self.chat_history = []
        
        # Path to the server script
        self.server_script = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "server",
            "tool_server.py"
        )

    def clear_history(self):
        self.chat_history = []

    def ask(self, query: str, repo_path: str, on_log=None) -> str:
        """
        Synchronous entry point for the async agentic flow.
        """
        return asyncio.run(self._run_agent(query, repo_path, on_log))

    async def _run_agent(self, query: str, repo_path: str, on_log=None) -> str:
        # 1. Setup MCP Connection
        if on_log: on_log("Initializing MCP Server...")
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[self.server_script],
            env=os.environ.copy()
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # 2. Get Tools
                mcp_tools_list = await session.list_tools()
                
                # 3. Convert to Gemini Tools
                gemini_tools = self._convert_tools(mcp_tools_list.tools)
                
                # 4. Prepare History
                if not self.chat_history:
                    initial_prompt = f"""
                    You are an expert coding assistant.
                    You have access to tools to explore a repository.
                    The repository is located at: {repo_path}
                    
                    IMPORTANT RULES:
                    1. ALWAYS use the 'repo_path' argument provided above for EVERY tool call.
                    2. When calling tools like 'read_file_segment' or 'list_symbols', the 'file_path' argument MUST be relative to the repository root (e.g., 'src/main.py', not just 'main.py').
                    3. If you are unsure where a file is, use 'list_files' first to find it. Do not guess paths.
                    4. If a user asks about a file, find its full relative path first before trying to read it or list its symbols.
                    
                    Plan your steps:
                    - If asked about a file's content or classes, first find the file path using 'list_files' or 'search_code'.
                    - Then use that exact path with 'list_symbols' or 'read_file_segment'.
                    """
                    self.chat_history.append(
                        types.Content(
                            role="user",
                            parts=[types.Part(text=initial_prompt)]
                        )
                    )
                
                # Append the NEW user query
                self.chat_history.append(
                    types.Content(
                        role="user",
                        parts=[types.Part(text=f"User Query: {query}")]
                    )
                )
                
                config = types.GenerateContentConfig(
                    tools=gemini_tools,
                    temperature=0.0
                )

                max_turns = 10
                for _ in range(max_turns):
                    response = self.llm_client.client.models.generate_content(
                        model=self.model,
                        contents=self.chat_history,
                        config=config
                    )
                    
                    # Check for function calls
                    if not response.function_calls:
                        # Final answer
                        # Append it to history so the model remembers what it said
                        self.chat_history.append(response.candidates[0].content)
                        return response.text
                    
                    # Execute tools
                    # We must append the model's response (with the function call) to history
                    self.chat_history.append(response.candidates[0].content)
                    
                    # Create parts for function responses
                    response_parts = []
                    
                    for fc in response.function_calls:
                        log_msg = f"[MCP] Calling {fc.name} with {fc.args}"
                        print(log_msg)
                        if on_log: on_log(log_msg)
                        
                        try:
                            # MCP call
                            result = await session.call_tool(fc.name, arguments=fc.args)
                            
                            # The result is a CallToolResult, usually has content list
                            tool_output = ""
                            if result.content:
                                for c in result.content:
                                    if c.type == "text":
                                        tool_output += c.text
                            
                            response_parts.append(
                                types.Part(
                                    function_response=types.FunctionResponse(
                                        name=fc.name,
                                        response={"result": tool_output}
                                    )
                                )
                            )
                        except Exception as e:
                            error_msg = f"Tool execution failed: {e}"
                            response_parts.append(
                                types.Part(
                                    function_response=types.FunctionResponse(
                                        name=fc.name,
                                        response={"error": error_msg}
                                    )
                                )
                            )
                    
                    # Append function responses to history
                    self.chat_history.append(types.Content(role="user", parts=response_parts))
                    
                return "Error: Maximum turns reached."

    def _convert_tools(self, mcp_tools) -> List[types.Tool]:
        """
        Converts MCP tool definitions to Gemini Tool format.
        """
        # Gemini expects a list of tools, where each tool is a function declaration
        declarations = []
        
        for tool in mcp_tools:
            # MCP tool.inputSchema is a JSON Schema dict
            # Gemini expects 'parameters' as a schema
            
            declarations.append(
                types.FunctionDeclaration(
                    name=tool.name,
                    description=tool.description,
                    parameters=tool.inputSchema
                )
            )
            
        return [types.Tool(function_declarations=declarations)]
