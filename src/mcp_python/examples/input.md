## Demonstration of `input()` Function in Python

### Step 1: Execute Python Code

An AI agent wants to use a tool on the python-repl MCP server:

**Tool:** `execute_python`  
**Description:** Execute Python code and return the output. Variables persist between executions.

**Arguments:**
```json
{
  "code": "while True:\n  text=input(\"break?\")\n  if text==\"break\":\n    break"
}
```

**Response:**
```json
{
  "output": [
    ">>> while True:",
    "...   text=input(\"break?\")",
    "...   if text==\"break\":",
    "...     break",
    "... ",
    "break?"
  ],
  "status": "Waiting for user input."
}
```

The Python REPL process is now paused for user input. It can't execute any more code until some user input is provided.

### Step 2: Send User Input

An AI agent wants to use a tool on the python-repl MCP server:

**Tool:** `user_input`  
**Description:** Send a message to program requesting user input and return the output. Variables persist between executions.

**Arguments:**
```json
{
  "message": "break"
}
```

**Response:**
```json
{
  "status": "Code executed successfully (no output)."
}

The AI agent decided to stop the loop after 1 iteration. 