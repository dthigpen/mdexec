#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path
from .executor import execute_code_block
from .markdown import parse_document, apply_updates, CodeBlock


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

    input_md = args.input_file.read_text(encoding='utf-8')
    rendered_md = run_mdexec(input_md)
    output_path = args.output or args.input_file
    if rendered_md != input_md:
        output_path.write_text(rendered_md, encoding='utf-8')
    else:
        print('[info] No changes to save')


def get_line_number(text: str, idx: int) -> int:
    return text.count('\n', 0, idx) + 1


def run_mdexec(text: str) -> str:
    """
    Parse, execute, and update a Markdown document.
    """

    blocks = parse_document(text)

    for block in blocks:
        if not isinstance(block, CodeBlock):
            continue

        if not block.executable:
            continue

        try:
            output_id = block.get_option('output-id', None)

            info = []
            if block.id:
                info.append(f'id={block.id}')
            if output_id:
                info.append(f'output_id={output_id}')

            info_str = ' '.join(info) if info else '<anonymous>'
            line = get_line_number(text, block.start_idx)
            print(f'[info] Running code block on line {line + 1}: {info_str}')

            # --- Execute ---
            out, err = execute_code_block(block, all_blocks=blocks, line_start=line)

        except Exception as e:
            raise e

        # --- Route output ---
        if output_id:
            output_block = next((b for b in blocks if b.id == output_id), None)

            if not output_block:
                raise ValueError(f'Missing output block with id: {output_id}')

            output_block.content = out
        else:
            formatted_out = '\n'.join([f'[info] stdout: {l}' for l in out.splitlines()])
            formatted_err = '\n'.join([f'[info] stderr: {l}' for l in err.splitlines()])
            if out:
                print(formatted_out)
            if err:
                print(formatted_err)

    return apply_updates(text, blocks)


if __name__ == '__main__':
    main()
