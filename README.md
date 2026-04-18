# `mdexec`

A zero-dependency, lightweight, runnable Markdown notebook. Easily execute Python and Bash code blocks and output results anywhere in the same file. Look at the examples in the source of [this README](https://github.com/dthigpen/mdexec/blob/main/README.md?plain=1) or the [examples](https://github.com/dthigpen/mdexec/blob/main/examples/) directory!

````markdown
## Example Docs
The current time is: <!-- id:last-updated --><!-- /id:last-updated -->

```python exec output-id=last-updated
from datetime import datetime
now = datetime.now()
print(f"{now:%B %d, %Y at %I:%M %p}")
```
````

## Installation

Install directly from the git repository with:
```
pip install git+https://github.com/dthigpen/mdexec.git
```

## Usage

1. Create a Markdown file with code blocks for the code you want to run, and optionally tag other elements for input/output.
2. Execute it with `mdexec notebook.md`

Example Markdown file:

````markdown
## Example Docs
Last Updated: <!-- id:last-updated -->DATE WILL BE OVERWRITTEN HERE<!-- /id:last-updated -->

### Example API Call In Docs

The following block will be populated after running `mdexec`. Notice that this output block can be anywhere in the document, not just right after the Python block.

```json id=response
```

This code will perform the fetch and output the result above. Notice the `exec` attribute to mark it executable by `mdexec`, and the `output-id` to indicate where to send the stdout/stderr output.

```python exec output-id=response
import requests
import json
response = requests.get("https://jsonplaceholder.typicode.com/todos/1")
print(json.dumps(response.json(), indent=4))
```

Alternatively, instead of using `output-id` and stdout/stderr you can use the Python API:

```python exec
from datetime import datetime
now = datetime.now()
# Set the content of the block with id=last-updated
md.set('last-updated', f"{now:%B %d, %Y at %I:%M %p}")
```
````

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

### Autoformatting Tables

Reformat markdown tables so that the cells line up in the source text for easier plain-text editing and viewing.

```python exec
import mdexec
out = md.get('table')
out.content= mdexec.auto_format_markdown_table(out.content)
```
<!-- id:table -->
| Fruit  |  Color  |
| :--- | :--- |
| Lemon  |  Yellow |
| Apple  |  Red    |
<!-- /id:table -->

## To Do

- Shared Python contexts across multiple code blocks. Each code block is isolated right now.
- File watcher to rerun on save. E.g. `mdexec --watch *.md`.
- More Markdown tests to ensure things like indented code blocks get handled properly.
- Better error handling and output for when Exceptions get raised during execution.
