#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import sys
import time
import traceback
from pathlib import Path

import nbformat
from jupyter_client import KernelManager
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError

ROOT = Path(__file__).resolve().parent
NOTEBOOK_DIR = ROOT / "notebooks"


def discover(pattern: str) -> list[Path]:
    return sorted(path for path in NOTEBOOK_DIR.glob("*.ipynb") if fnmatch.fnmatch(path.name, pattern))


def validate(path: Path) -> list[str]:
    notebook = nbformat.read(path, as_version=4)
    problems: list[str] = []
    for cell_index, cell in enumerate(notebook.cells):
        if cell.cell_type != "code":
            continue
        for output in cell.get("outputs", []):
            if output.output_type == "error":
                problems.append(f"cell {cell_index}: {output.get('ename')}: {output.get('evalue')}")
    return problems


def reset_kernel_namespace(client: NotebookClient) -> None:
    """Clear user variables while keeping one kernel alive for the batch."""
    assert client.kc is not None
    message_id = client.kc.execute(
        "get_ipython().run_line_magic('reset', '-f')",
        silent=True,
        store_history=False,
    )
    client.wait_for_reply(message_id)


def cleanup_kernel(manager: KernelManager, client: NotebookClient | None) -> None:
    """Best-effort cleanup that never hides the original notebook error."""
    if client is not None and client.kc is not None:
        try:
            client.kc.stop_channels()
        except Exception:  # pragma: no cover - defensive cleanup
            traceback.print_exc(file=sys.stderr)
    try:
        if manager.has_kernel:
            manager.shutdown_kernel(now=True)
    except Exception:  # pragma: no cover - defensive cleanup
        traceback.print_exc(file=sys.stderr)
    try:
        manager.cleanup_resources()
    except Exception:  # pragma: no cover - defensive cleanup
        traceback.print_exc(file=sys.stderr)


def execute_all(notebooks: list[Path], timeout: int) -> bool:
    """Execute notebooks in order with one reusable Python kernel.

    Reusing a kernel makes the full repository run faster and avoids repeatedly
    allocating ZeroMQ ports. The user namespace is reset before every notebook,
    so notebook variables do not leak across chapters.
    """
    manager = KernelManager(kernel_name="python3")
    manager.start_kernel(cwd=str(ROOT))
    client: NotebookClient | None = None
    failed = False

    try:
        for index, path in enumerate(notebooks):
            relative = path.relative_to(ROOT)
            print(f"RUN  {relative}", flush=True)
            notebook = nbformat.read(path, as_version=4)

            if client is None:
                client = NotebookClient(
                    notebook,
                    km=manager,
                    timeout=timeout,
                    kernel_name="python3",
                    allow_errors=False,
                    resources={"metadata": {"path": str(ROOT)}},
                )
                client.start_new_kernel_client()
            else:
                reset_kernel_namespace(client)
                client.nb = notebook
                client.timeout = timeout
                client.reset_execution_trackers()

            started = time.perf_counter()
            try:
                client.execute()
            except CellExecutionError as error:
                failed = True
                print(f"FAIL {relative}: {error}", file=sys.stderr)
                break
            except Exception as error:
                failed = True
                print(f"FAIL {relative}: {type(error).__name__}: {error}", file=sys.stderr)
                break

            elapsed = time.perf_counter() - started
            nbformat.write(client.nb, path)
            problems = validate(path)
            if problems:
                failed = True
                print(f"FAIL {relative}: notebook contains error outputs", file=sys.stderr)
                for problem in problems:
                    print(f"  {problem}", file=sys.stderr)
                break
            print(f"OK   {relative} ({elapsed:.1f}s)")
    finally:
        cleanup_kernel(manager, client)

    return failed


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute or validate all project notebooks.")
    parser.add_argument("--pattern", default="*.ipynb", help="Notebook filename glob (default: *.ipynb)")
    parser.add_argument("--timeout", type=int, default=900, help="Per-cell timeout in seconds")
    parser.add_argument("--validate-only", action="store_true", help="Do not execute; only scan existing outputs")
    args = parser.parse_args()

    notebooks = discover(args.pattern)
    if not notebooks:
        print(f"No notebooks matched {args.pattern!r}", file=sys.stderr)
        return 2

    if args.validate_only:
        failed = False
        for path in notebooks:
            relative = path.relative_to(ROOT)
            problems = validate(path)
            if problems:
                failed = True
                print(f"FAIL {relative}")
                for problem in problems:
                    print(f"  {problem}")
            else:
                print(f"OK   {relative}")
        return 1 if failed else 0

    return 1 if execute_all(notebooks, args.timeout) else 0


if __name__ == "__main__":
    raise SystemExit(main())
