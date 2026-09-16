# jupyter-kernel-mcp

Give your AI agent a persistent Jupyter kernel for calculations, data analysis,
and plots. Variables, data, and functions stay available across follow-up requests.

Use an MCP-compatible client and a Jupyter installation with your chosen kernel.

See also [example conversations](docs/usage.md) and [development setup](CONTRIBUTING.md).

## Quick setup with [uvx](https://docs.astral.sh/uv/)

Add this to your client's `mcp.json`, replacing the paths with absolute paths
on your machine:

```json
{
  "mcpServers": {
    "jupyter-python": {
      "command": "uvx",
      "args": [
        "--from", "git+https://github.com/0x0L/jupyter-kernel-mcp",
        "jupyter-kernel-mcp",
        "--jupyter", "/path/to/project/.venv/bin/jupyter",
        "--kernel", "python3",
        "--cwd", "/path/to/project"
      ]
    }
  }
}
```

`--jupyter` and `--kernel` are required. Choose a kernel listed by your Jupyter
executable's `kernelspec list` command. `--cwd` is optional and defaults to the
server's working directory. Install analysis libraries in the kernel's environment.
