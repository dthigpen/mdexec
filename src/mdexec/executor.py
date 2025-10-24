from __future__ import annotations
import subprocess
import sys
import io
from contextlib import redirect_stdout, redirect_stderr
from typing import Any, Dict
from .types import CodeBlock
from mdexec.markdown_io import query_blocks


def execute_code_block(block: CodeBlock) -> str:
    """
    Execute a single mdexec code block and return its captured output.

    Currently supports:
      - Python (via `exec`)
      - Bash / sh (via subprocess)

    Args:
        block: The CodeBlock object containing code and metadata.

    Returns:
        Captured stdout + stderr as a single string.
    """
    lang = block.lang.lower()

    if not block.executable:
        raise ValueError(f'Block is not executable')
    if lang in ('python', 'py'):
        return _exec_python(block.content)

    elif lang in ('bash', 'sh'):
        return _exec_subprocess(block.content, shell=True)

    else:
        return f"⚠️ Unsupported language '{lang}' — skipping execution."


def _exec_python(code: str) -> str:
    """Execute Python code and return captured stdout/stderr."""
    stdout = io.StringIO()
    stderr = io.StringIO()

    try:
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exec(
                code,
                {'STARTING_CONTENT': 'TODO insert here', 'query_blocks': query_blocks},
            )
    except Exception as e:
        print(f'❌ Python error: {e}', file=stderr)

    out = stdout.getvalue()
    err = stderr.getvalue()
    return (out + err).strip()


def _exec_subprocess(code: str, shell: bool = True) -> str:
    """Execute shell code via subprocess and return its combined output."""
    try:
        result = subprocess.run(
            code,
            shell=shell,
            capture_output=True,
            text=True,
        )
        output = result.stdout + result.stderr
    except Exception as e:
        output = f'❌ Subprocess error: {e}'

    return output.strip()
