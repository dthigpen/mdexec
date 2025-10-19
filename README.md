# `mdexec`

A lightweight runnable Markdown notebook.

## Example

The code block below shows the command to view the `mdexec` command usage. The next code block automatically gets updated with the result each time the notebook is run.

```bash mdexec id=help
mdexec --help
```
```output mdexec output-id=help
usage: mdexec [-h] [-o OUTPUT] input_file

Execute code blocks in a Markdown file and render results inline.

positional arguments:
  input_file            Path to the Markdown file to execute

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Optional path for the output Markdown file. If
                        omitted, outputs to the input file
```
