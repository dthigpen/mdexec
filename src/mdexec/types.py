from dataclasses import dataclass, field
from typing import Optional, Any, Dict, Literal

from markdown_it.token import Token


@dataclass
class Block:
    pre_content: str = ''
    content: str = ''
    post_content: str = ''
    id: Optional[str] = None

    @property
    def full_content(self):
        return self.pre_content + self.content + self.post_content


@dataclass
class TextBlock(Block):
    pass


@dataclass
class HtmlCommentBlock(Block):
    start_token: Optional[Token] = None
    end_token: Optional[Token] = None
    options: Dict[str, str] = field(default_factory=dict)


@dataclass
class CodeBlock(Block):
    """Represents a fenced code block processed by mdexec."""

    token: Optional[Token] = None
    language: str = None
    output_id: Optional[str] = None
    options: Dict[str, str] = field(default_factory=dict)
    executable: bool = False
