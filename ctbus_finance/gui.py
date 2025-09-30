import pathlib
import subprocess
from pathlib import Path
from typing import Sequence

__all__ = ["launch_fava"]


def launch_fava(
    beancount_file: pathlib.Path | str,
    *,
    host: str = "127.0.0.1",
    port: int = 5000,
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
        "fava",
        str(ledger_path),
        "--host",
        host,
        "--port",
        str(port),
    ]

    if extra_args:
        args.extend(extra_args)

    return subprocess.run(args, check=True)


if __name__ == "__main__":
    launch_fava(Path("all.beancount"))
