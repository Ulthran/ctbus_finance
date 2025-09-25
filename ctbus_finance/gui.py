"""Convenience helpers for running the Fava Beancount web interface."""

from __future__ import annotations

import pathlib
import subprocess
import sys
from typing import Sequence

__all__ = ["launch_fava"]


def launch_fava(
    beancount_file: pathlib.Path | str,
    *,
    host: str = "127.0.0.1",
    port: int = 5000,
    open_browser: bool = True,
    extra_args: Sequence[str] | None = None,
) -> subprocess.CompletedProcess[bytes]:
    """Start the Fava web UI pointing at ``beancount_file``.

    Parameters
    ----------
    beancount_file:
        Path to the Beancount ledger file that Fava should open.
    host:
        Host interface that the Fava server should bind to.
    port:
        TCP port that the Fava server should listen on.
    open_browser:
        Whether Fava should attempt to open a browser window automatically.
    extra_args:
        Additional command-line arguments to pass to the ``fava`` CLI.

    Returns
    -------
    subprocess.CompletedProcess
        The completed subprocess invocation for the launched Fava server.
    """

    ledger_path = pathlib.Path(beancount_file).expanduser().resolve()
    if not ledger_path.exists():
        raise FileNotFoundError(f"No Beancount file found at: {ledger_path}")

    args: list[str] = [
        sys.executable,
        "-m",
        "fava",
        str(ledger_path),
        "--host",
        host,
        "--port",
        str(port),
    ]

    if not open_browser:
        args.append("--no-browser")

    if extra_args:
        args.extend(extra_args)

    return subprocess.run(args, check=True)
