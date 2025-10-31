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
fruits = ['Apple', 'Banana', 'Cherry']
for i, fruit in enumerate(fruits):
	print(f'{i+1}. {fruit}') 
```

My favorite fruits are:
<!-- id:fruits-list -->
1. Apple
2. Banana
3. Cherry
<!-- /id:fruits-list -->

### Read, Transform, and Output to Markdown
```python exec
import json
b = get_block(id='foobar')
out = get_block(id='foobar2')
out.content = json.dumps(json.loads(b.content), indent=2)
```

Unformatted input:
 
```json id=foobar
{"foo": "bar","example": true}
```

Formatted output:

```jsonc id=foobar2
{
  "foo": "bar",
  "example": true
}
```
