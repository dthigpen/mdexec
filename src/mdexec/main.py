#!/usr/bin/env python3

import argparse
from pathlib import Path
from typing import Any
from markdown_it import MarkdownIt
from .executor import execute_code_block
from .markdown_io import replace_output_block, extract_mdexec_blocks


def main():
    parser = argparse.ArgumentParser(
        description='Execute code blocks in a Markdown file and render results inline.'
    )
    parser.add_argument(
        'input_file', type=Path, help='Path to the Markdown file to execute'
    )
    parser.add_argument(
        '-o',
        '--output',
        type=Path,
        help='Optional path for the output Markdown file. If omitted, outputs to the input file',
    )

    args = parser.parse_args()

    # Call our core processor (we’ll implement this next)
    input_md = args.input_file.read_text(encoding='utf-8')
    rendered_md = run_mdexec(input_md)

    output_path = args.output or args.input_file
    output_path.write_text(rendered_md, encoding='utf-8')


def run_mdexec(text: str) -> str:
    """
    Process a Markdown file, execute code blocks marked with 'mdexec',
    and inject or update output blocks in the Markdown.

    Args:
        path: Path to the input Markdown file.

    Returns:
        The rendered Markdown with code outputs inserted.
    """

    # Extract all mdexec blocks (code blocks with mdexec directives)
    code_blocks = extract_mdexec_blocks(text)

    rendered_text = text
    for block in code_blocks:
        if not block.is_input:
            continue
        try:
            if block.id is None:
                print(
                    f'[warning] Expected code block lang string to contain id=foo. Output will only be printed to the console.'
                )
            result = execute_code_block(block)
        except Exception as e:
            result = f'⚠️ Error: {e}'

        if block.id is not None:
            # Replace or insert the output block in the markdown
            rendered_text = replace_output_block(
                rendered_text,
                block.id,
                result,
                match_indent=False,
            )

    return rendered_text


if __name__ == '__main__':
    main()
