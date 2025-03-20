## Demonstration of Variables in Python

### Step 1: Execute Python Code

An AI agent wants to use a tool on the python-repl MCP server:

**Tool:** `execute_python`  
**Description:** Execute Python code and return the output. Variables persist between executions.

**Arguments:**
```json
{
  "code": "my_variable = \"Hello, world!\""
}
```

**Response:**
```json
{
  "output": [
    ">>> my_variable = \"Hello, world!\""
  ]
}
```

The variable `my_variable` has been created.

### Step 2: List Variables

An AI agent wants to use a tool on the python-repl MCP server:

**Tool:** `list_variables`  
**Description:** List all variables in the current session.

**Response:**
```json
{
  "Current session variables": [
    "names",
    "input",
    "exit",
    "my_variable"
  ]
}
```

The variables in the current session are `names`, `input`, `exit`, and `my_variable`. The `names()` function is the one that is used internally to generate the list of names. `my_variable` is the one the AI agent created.

### Step 3: Execute Python Code

An AI agent wants to use a tool on the python-repl MCP server:

**Tool:** `execute_python`  
**Description:** Execute Python code and return the output. Variables persist between executions.

**Arguments:**
```json
{
  "code": "print(my_variable)"
}
```

**Response:**
```json
{
  "output": [
    ">>> print(my_variable)",
    "Hello, world!"
  ]
}
```

The variable `my_variable` still has its value the AI agent set earlier.