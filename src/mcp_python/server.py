import asyncio
import io
import subprocess
import re
import traceback
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types
from mcp_python.repl import ReplProcess
import json
from pydantic import AnyUrl
from pathlib import Path


fixed_resources = {
    "examples/input.md": {
        "name": "Input Example",
        "description": "An example of sending user input to a REPL session.",
    },
    "examples/variables.md": {
        "name": "Variables Example",
        "description": "An example of using peristent variables in a Python REPL session.",
    }
}

class PythonREPLServer:
    def __init__(self):
        self.server = Server("python-repl")
        # Shared namespace for all executions # probably delete this later
        self.global_namespace = {
            "__builtins__": __builtins__,
        }
        # Start repl process
        self.repl = ReplProcess()
        # Set up handlers using decorators
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            return await self.handle_list_tools()
            
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
            return await self.handle_call_tool(name, arguments)
        
        @self.server.list_resources()
        async def handle_list_resources() -> list[types.Resource]:
            return await self.handle_list_resources()
        
        @self.server.read_resource()
        async def handle_read_resource(uri: AnyUrl) -> str:
            return await self.handle_read_resource(uri)
        
    async def handle_list_tools(self) -> list[types.Tool]:
        """List available tools"""
        return [
            types.Tool(
                name="execute_python",
                description="Execute Python code and return the output. Variables persist between executions, allowing you to build upon previous commands.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Python code to execute",
                        },
                        "reset": {
                            "type": "boolean",
                            "description": "Reset the Python session (clear all variables)",
                            "default": False
                        }
                    },
                    "required": ["code"],
                },
            ),
            types.Tool(
                name="user_input",
                description="Send a message to a program that is waiting for user input and return the output. Variables persist between executions",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Message to send to the program as user input",
                        }
                    },
                    "required": ["message"],
                },
            ),
            types.Tool(
                name="list_variables",
                description="List all variables in the current session.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            types.Tool(
                name="install_package",
                description="Install a Python package using uv. This package will then be immediately available for import in the REPL.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "package": {
                            "type": "string",
                            "description": "Package name to install (e.g., 'pandas')",
                        }
                    },
                    "required": ["package"],
                },
            )
        ]

    async def handle_call_tool(
        self, name: str, arguments: dict | None
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        """Handle tool execution requests"""
        tool = next((t for t in await self.handle_list_tools() if t.name == name), None)
        if not tool:
            raise ValueError(f"Unknown tool: {name}")

        if tool.inputSchema.get("required") and not arguments:
            raise ValueError("Missing required arguments")
        
        results = {}
        if name == "execute_python":
            if self.repl.paused_for_input:
                return [
                    types.TextContent(
                        type="text",
                        text="Error sending code. The REPL is currently waiting for user input."
                    )
                ]
            
            code = arguments.get("code")
            if not code:
                raise ValueError("Missing code parameter")

            # Check if we should reset the session
            if arguments.get("reset", False):
                self.repl.uninit()
                self.repl.__init__()
                results["reset"]=True
            
            try:
                # Execute code in REPL
                output, errors = self.repl.send_code(code)
                    
            except Exception as e:  # noqa: F841
                # Capture and format any exceptions
                error_msg = f"Error executing code:\n{traceback.format_exc()}"
                return [
                    types.TextContent(
                        type="text",
                        text=error_msg
                    )
                ]
        elif name == "user_input":
            if not self.repl.paused_for_input:
                return [
                    types.TextContent(
                        type="text",
                        text="Error sending message. The REPL is not currently waiting for user input."
                    )
                ]
            
            message = arguments.get("message")
            if not message:
                raise ValueError("Missing message parameter")
            try:
                # Execute code in REPL
                self.repl.paused_for_input = False
                output, errors = self.repl.send_input(message)
                    
            except Exception as e:  # noqa: F841
                # Capture and format any exceptions
                error_msg = f"Error sending message:\n{traceback.format_exc()}"
                return [
                    types.TextContent(
                        type="text",
                        text=error_msg
                    )
                ]
        
        if name == "user_input" or name == "execute_python":
                # Format response
                if output:
                    results["output"]=output.split("\n")
                if errors:
                    results["errors"]=errors.split("\n")
                if self.repl.paused_for_input:
                    results["status"]="Waiting for user input."
                if self.repl.shutting_down:
                    results["status"]="Successfully shut down (requires restart)."
                if not results:
                    results["status"]="Code executed successfully (no output)."
                result=json.dumps(results, indent=2)
                return [
                    types.TextContent(
                        type="text",
                        text=result
                    )
                ]

        elif name == "install_package":
            package = arguments.get("package")
            if not package:
                raise ValueError("Missing package name")
                
            # Basic package name validation
            if not re.match("^[A-Za-z0-9][A-Za-z0-9._-]*$", package):
                return [
                    types.TextContent(
                        type="text",
                        text=f"Invalid package name: {package}"
                    )
                ]
            
            try:
                # Install package using uv
                process = subprocess.run(
                    ["uv", "pip", "install", package],
                    capture_output=True,
                    text=True,
                    check=True
                )

                if process.returncode != 0:
                    return [
                        types.TextContent(
                            type="text",
                            text=f"Failed to install package: {process.stderr}"
                        )
                    ]
                
                # Import the package to make it available in the REPL
                try:
                    exec(f"import {package.split('[')[0]}", self.global_namespace)
                    return [
                        types.TextContent(
                            type="text",
                            text=f"Successfully installed and imported {package}"
                        )
                    ]
                except ImportError as e:
                    return [
                        types.TextContent(
                            type="text",
                            text=f"Package installed but import failed: {str(e)}"
                        )
                    ]
                    
            except subprocess.CalledProcessError as e:
                return [
                    types.TextContent(
                        type="text",
                        text=f"Failed to install package:\n{e.stderr}"
                    )
                ]
                
        elif name == "list_variables":
            if self.repl.paused_for_input:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: Cannot check variabled because the REPL is waiting for user input."
                    )
                ]
            try:
                output, errors = self.repl.get_names()
                vars_list=json.loads(output)
                if not vars_list:
                    return [
                        types.TextContent(
                            type="text",
                            text="No variables in current session."
                        )
                    ]
                
                # Format variables list
                vars_string = json.dumps({"Current session variables": vars_list}, indent=0)
                return [
                    types.TextContent(
                        type="text",
                        text=vars_string
                    )
                ]
            except Exception as e:  # noqa: F841
                # Capture and format any exceptions
                error_msg = f"Error checking variables:\n{traceback.format_exc()}"
                return [
                    types.TextContent(
                        type="text",
                        text=error_msg
                    )
                ]
        else:
            raise ValueError(f"Unknown tool: {name}")
        
    async def handle_list_resources(self) -> list[types.Resource]:
        return [
            types.Resource(
                uri=AnyUrl(f"file://{key}"),
                name=fixed_resources[key]["name"],
                description=fixed_resources[key]["description"],
                mimeType="text/plain",
            )
            for key in fixed_resources.keys()
        ]
    
    async def handle_read_resource(self, uri: AnyUrl) -> str:
        if not uri:
            raise ValueError("Missing resource_name parameter")
        if uri.scheme != "file":
            raise ValueError(f"Unsupported URI scheme: {uri.scheme}")
        resource_name = str(uri).replace("file://", "")
        if resource_name in list(fixed_resources.keys()):
            file_path = Path(__file__).resolve().parent / resource_name
            with open(file_path, "r") as file:
                return file.read()
        else:
            return "Resource not found."
    
    async def run(self):
        """Run the server"""
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="python-repl",
                    server_version="0.1.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )

async def main():
    server = PythonREPLServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
