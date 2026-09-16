"""Private Jupyter CLI config, executed in the selected launcher's environment.

Only Jupyter and Python's standard library are required here. File requests keep
interrupts separate from launcher termination and work without POSIX signals.
The server holds a private stdin pipe open; EOF makes the relay shut down even
after an abrupt server exit. The server normally removes the private directory;
the relay removes it if its owner has died.
"""

import os
import shutil
import signal
import sys
import threading
from pathlib import Path

from jupyter_client.kernelapp import KernelApp
from tornado.ioloop import PeriodicCallback

_runtime = Path(os.environ["KERNEL_MCP_RUNTIME_DIR"])
_app = KernelApp.instance()
_owner_gone = threading.Event()


def _watch_owner():
    # Use an OS read rather than a buffered Python read: this daemon must not
    # hold a buffered stdin lock when the launcher exits normally.
    while os.read(sys.stdin.fileno(), 1):
        pass
    _owner_gone.set()


threading.Thread(target=_watch_owner, daemon=True).start()


def _poll_requests():
    if _owner_gone.is_set():
        _relay.stop()
        _app.shutdown(signal.SIGTERM)
        # The dead owner cannot remove its temporary connection/request files.
        shutil.rmtree(_runtime, ignore_errors=True)
        return
    (_runtime / "ready").touch(exist_ok=True)
    if (_runtime / "shutdown").exists():
        _relay.stop()
        _app.shutdown(signal.SIGTERM)
    elif not _app.km.is_alive():
        _relay.stop()
        _app.loop.stop()
    elif (_runtime / "interrupt").exists():
        _app.km.interrupt_kernel()
        (_runtime / "interrupt").unlink()


_relay = PeriodicCallback(_poll_requests, 100)
_relay.start()
