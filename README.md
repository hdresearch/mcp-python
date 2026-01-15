# Python REPL MCP Server

This MCP server provides a Python REPL (Read-Eval-Print Loop) as a tool. It allows execution of Python code through the MCP protocol with a persistent session.

<a href="https://glama.ai/mcp/servers/jsorljnhdl">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/jsorljnhdl/badge" alt="Python REPL Server MCP server" />
</a>

## Setup

### Prerequisites
- Install `uv` if you haven't already
- Clone this repository
```bash
git clone https://github.com/hdresearch/mcp-python
```
## Running the Server

Simply run:

```bash
cd mcp-python
uv run src/mcp_python/server.py
```

## Usage with Claude Desktop

Add this configuration to your Claude Desktop config file:

```json
{
  "mcpServers": {
    "python-repl": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/mcp-python",
        "run",
        "mcp_python"
      ]
    }
  }
}
```

- `/absolute/path/to/mcp-python` might look like `/Users/hdresearch/repos/mcp-python`
- if `mcp_python` is not working, substitute with `src/mcp_python/server.py`


The server provides three tools:

1. `execute_python`: Execute Python code with persistent variables

   - `code`: The Python code to execute
   - `reset`: Optional boolean to reset the session

2. `list_variables`: Show all variables in the current session

3. `install_package`: Install a package from pypi

## Examples

Set a variable:

```python
a = 42
```

Use the variable:

```python
print(f"The value is {a}")
```

List all variables:

```python
# Use the list_variables tool
```

Reset the session:

```python
# Use execute_python with reset=true
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. Here are some ways you can contribute:

- Report bugs
- Suggest new features
- Improve documentation
- Add test cases
- Submit code improvements

Before submitting a PR, please ensure:

1. Your code follows the existing style
2. You've updated documentation as needed
3. Maybe write some tests?

For major changes, please open an issue first to discuss what you would like to change.