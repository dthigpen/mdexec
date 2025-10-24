from dataclasses import dataclass
from typing import Optional, Any, Dict, Literal

from markdown_it.token import Token


@dataclass
class IoBlock:
    content: str
    id: Optional[str]
    # type: Literal['input', 'output']


@dataclass
class HtmlBlock(IoBlock):
    start_token: Token
    end_token: Token


@dataclass
class CodeBlock(IoBlock):
    """Represents a fenced code block processed by mdexec."""

    token: Token
    lang: str
    output_id: Optional[str]
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
