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
        if not block.executable:
            continue
        try:
            own_id = block.id
            output_id = block.output_id
            if output_id is None:
                print(
                    f'[warning] Executable code block did not contain an output-id. Output will be printed to the console.'
                )
            info_str = ''
            if own_id:
                info_str += f'id={own_id}'
            if output_id:
                info_str += f'output_id={output_id}'
            if not info_str:
                info_str = '<anonymous>'
            print(f'[info] Running code block: {info_str}')

            result = execute_code_block(block)
        except Exception as e:
            result = f'Error: {e}'

        if output_id:
            # Replace or insert the output block in the markdown
            rendered_text = replace_output_block(
                rendered_text,
                output_id,
                result,
                match_indent=False,
            )
        else:
            print(result)

    return rendered_text


if __name__ == '__main__':
    main()
