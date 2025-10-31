from __future__ import annotations
import subprocess
import sys
import io
from contextlib import redirect_stdout, redirect_stderr
from typing import Any, Dict
from .types import CodeBlock
from .markdown_io import DocumentContext


def execute_code_block(block: CodeBlock, doc_context: DocumentContext = None) -> str:
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
    lang = block.language.lower()

    if not block.executable:
        raise ValueError(f'Block is not executable')
    if lang in ('python', 'py'):
        return _exec_python(
            block.content,
            env={
                'get_blocks': doc_context.get_blocks,
                'get_block': doc_context.get_block,
            },
        )

    elif lang in ('bash', 'sh'):
        return _exec_subprocess(block.content, shell=True)

    else:
        return f"Unsupported language '{lang}' — skipping execution."


def _exec_python(code: str, env: dict = None) -> str:
    """Execute Python code and return captured stdout/stderr."""
    stdout = io.StringIO()
    stderr = io.StringIO()
    env = env or {}
    try:
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exec(
                code,
                env,
            )
    except Exception as e:
        print(f'Python error: {e}', file=stderr)

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
        output = f'Subprocess error: {e}'

    return output.strip()
