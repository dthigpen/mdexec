from dataclasses import dataclass
from typing import Optional, Any, Dict

from markdown_it.token import Token


@dataclass
class CodeBlock:
    """Represents a fenced code block processed by mdexec."""

    token: Token
    lang: str
    code: str
    id: Optional[str]
    output_id: Optional[str]
    type: str  # "input" or "output" or "executable"
    vars: Dict[str, str]
    executable: bool = False

    @property
    def is_input(self) -> bool:
        """Whether this code block should be executed."""
        return self.type == 'input'

    @property
    def is_output(self) -> bool:
        """Whether this code block is meant to hold execution output."""
        return self.type == 'output'
