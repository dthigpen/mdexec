# `mdexec`

A lightweight runnable Markdown notebook.

## Examples

### Auto-updating "usage" text

```bash exec output-id=help
mdexec --help
```
```output id=help
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

### Complex Markdown generation

```python exec output-id=fruits-list
fruits = ['apple', 'banana', 'cherry']
for fruit in fruits:
	print(f'- {fruit}') 
```

My favorite fruits are:
<!-- id:fruits-list -->
- apple
- banana
- cherry
<!-- /id:fruits-list -->
