# Contributing

For bug reports, include the server version or commit, operating system, Python
version, configured Jupyter executable, kernel name and language, MCP client, and a
minimal reproduction. Include expected behavior, execution metadata, and relevant
logs. Remove credentials, private file contents, and other sensitive data before
sharing a report.

Discuss changes to the six-tool contract before implementing a large feature.
Keep pull requests focused and explain the user-visible behavior and validation.

## Local development

Use Python 3.12 or later and uv:

```bash
uv sync --locked --dev
uv run pre-commit install
uv run --locked ruff format --check
uv run --locked ruff check
uv run --locked ty check
uv run --locked pytest tests/ -v
uv build
```

Tests register an isolated Python kernelspec pointing to the test environment;
they do not need or alter your user kernelspec registration. Tests execute real
code and start kernel subprocesses. Linux is covered by CI on Python 3.12–3.14;
Windows, macOS, R, and Julia are not covered by that matrix.

## Use this checkout in an agent

Add this to your client's `mcp.json`, replacing the absolute paths with your
checkout and desired working directory:

```json
{
  "mcpServers": {
    "jupyter-python": {
      "command": "uv",
      "args": [
        "run",
        "--project", "/absolute/path/to/jupyter-kernel-mcp",
        "--locked",
        "--dev",
        "jupyter-kernel-mcp",
        "--jupyter", "/absolute/path/to/jupyter-kernel-mcp/.venv/bin/jupyter",
        "--kernel", "python3",
        "--cwd", "/absolute/path/to/project"
      ]
    }
  }
}
```

`--project` points to this checkout; `--cwd` sets the kernel's working directory.
`--locked` uses the committed lockfile, and `--dev` includes ipykernel and
Matplotlib. The example uses the checkout's Jupyter environment; you can select
another installation and kernel with `--jupyter` and `--kernel`.

For Claude Code, use [`.mcp.json`](examples/mcp.json); for Codex, use the
[TOML example](examples/codex-config.toml) in `.codex/config.toml`. Both local
configuration files are ignored by Git. Restart the MCP connection after changing
source code or launch arguments.

## Changes and dependencies

Add regression tests for changed behavior. Keep the README and usage examples
focused on human setup and workflows.
Document tool selection, output consumption, polling, and recovery in MCP server
instructions, tool descriptions, and response field descriptions; agents receive
these through discovery. Verify that metadata through a real MCP client.
Architecture and lifecycle invariants are documented in [AGENTS.md](AGENTS.md).

Commit `uv.lock` with dependency changes. FastMCP is deliberately pinned; review
its migration guidance before updating. CI and pre-commit use locked development
tools. Build dependencies and the uv executable are not pinned by `uv.lock`, so
this setup does not promise byte-for-byte reproducible distributions.
GitHub Actions are pinned to commit SHAs, with Dependabot proposing updates.

## Before a release

1. Finish the checks above and require a passing GitHub Actions run for the exact
   commit being released.
2. Update the version in `pyproject.toml`.
3. Build the source distribution and wheel. Inspect their contents for required
   documentation/license files and accidental local configuration or private data.
4. Smoke-test the wheel in an isolated environment with `uv run --isolated
   --no-project --with /absolute/path/to/package.whl jupyter-kernel-mcp --help`, then
   verify an MCP connection with an explicit Jupyter executable and kernel.
5. Tag the validated commit and describe changes and compatibility limitations
   in its GitHub release notes. Publishing is a separate maintainer action;
   the CI workflow does not publish packages or releases.

Repository settings such as required status checks, branch protection, secret
scanning, and private vulnerability reporting must be configured on GitHub;
they are not enabled by these files. If private vulnerability reporting is
available on the repository's Security tab, use it for sensitive security reports.
