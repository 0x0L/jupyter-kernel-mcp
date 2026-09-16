"""Check actual CLI exit paths, including exits that bypass Python cleanup."""

import asyncio
import json
import os
import signal
import sys
from pathlib import Path

import pytest


def alive(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


@pytest.mark.skipif(os.name == "nt", reason="POSIX process signals")
@pytest.mark.parametrize("exit_mode", ["eof", "terminate", "kill"])
@pytest.mark.parametrize("busy", [False, True])
async def test_server_exit_reaps_kernel(tmp_path, exit_mode, busy):
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "jupyter_kernel_mcp.server",
        "--jupyter",
        str(Path(sys.executable).with_name("jupyter")),
        "--kernel",
        "python3",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    pids = []
    pid_file = tmp_path / "pids.json"
    stdin, stdout = process.stdin, process.stdout
    assert stdin is not None and stdout is not None

    async def request(method, params, request_id):
        stdin.write(
            (
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "method": method,
                        "params": params,
                    }
                )
                + "\n"
            ).encode()
        )
        await stdin.drain()
        while True:
            line = await stdout.readline()
            assert line, "Server exited before responding"
            result = json.loads(line)
            if result.get("id") == request_id:
                assert "error" not in result, result
                return result

    try:
        async with asyncio.timeout(30):
            await request(
                "initialize",
                {
                    "protocolVersion": "2025-11-25",
                    "capabilities": {},
                    "clientInfo": {"name": "shutdown-test", "version": "1"},
                },
                1,
            )
            code = (
                "import os, json, time; from pathlib import Path; "
                f"Path({str(pid_file)!r}).write_text(json.dumps([os.getpid(), os.getppid()]))"
            )
            if busy:
                code += "; time.sleep(120)"
            await request(
                "tools/call",
                {
                    "name": "execute",
                    "arguments": {"code": code, "wait_seconds": 0},
                },
                2,
            )
            while not pid_file.exists():
                await asyncio.sleep(0.05)
            pids = json.loads(pid_file.read_text())
            assert all(alive(pid) for pid in pids)
        if exit_mode == "eof":
            stdin.close()
        else:
            getattr(process, exit_mode)()
        await asyncio.wait_for(process.wait(), 20)
        async with asyncio.timeout(15):
            while any(alive(pid) for pid in pids):
                await asyncio.sleep(0.1)
    finally:
        if process.returncode is None:
            process.kill()
            await process.wait()
        # Reap only the processes created by this test, including on regression.
        for pid in reversed(pids):
            if alive(pid):
                os.kill(pid, signal.SIGTERM)
