from __future__ import annotations
import subprocess
import io
from contextlib import redirect_stdout, redirect_stderr
from .markdown import CodeBlock, Block
import copy


class MdApi:
    def __init__(self, blocks: list[Block]):
        self._blocks = blocks
        self._id_map = {b.id: b for b in blocks if b.id is not None}

    def __getitem__(self, block_id: str):
        return self.get(block_id)

    def get(self, block_id: str) -> Block | None:
        block = self._id_map.get(block_id)
        return copy.deepcopy(block) if block else None

    def set(self, block_id: str, content: str) -> None:
        block = self._id_map.get(block_id)
        if not block:
            raise ValueError(f"No block with id '{block_id}'")
        block.content = content

    def find(self, predicate=None) -> list[Block]:
        results = self._blocks
        if predicate:
            results = [b for b in results if predicate(b)]
        return [copy.deepcopy(b) for b in results]


def execute_code_block(block: CodeBlock, all_blocks: list[Block] = None) -> str:
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
    if lang in ('python', 'py', 'python3'):
        # TODO handle ctx so that vars can be shared across code blocks
        env = {}
        env['md'] = MdApi(all_blocks)
        return _exec_python(
            block.content,
            env=env,
        )

    elif lang in ('bash', 'sh'):
        return _exec_subprocess(block.content, shell=True)

    else:
        return f"Unsupported language '{lang}' - skipping execution."


def _exec_python(code: str, env: dict = None) -> str:
    """Execute Python code and return captured stdout/stderr."""
    stdout = io.StringIO()
    stderr = io.StringIO()
    env = env or {}
    try:
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exec(
                code,
                env,  # By only providing the globals env, locals will also go into here
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
