## Example Docs
Last Updated: <!-- id:last-updated -->April 19, 2026 at 09:17 AM<!-- /id:last-updated -->

Browse the rendered and raw Markdown of the sections below to get an idea of what `mdexec` is capable of.

### Example API Call In Docs

The following block will be populated after running `mdexec`. Notice that this output block can be anywhere in the document, not just right after the Python block.

```json id=response
{
    "userId": 1,
    "id": 1,
    "title": "delectus aut autem",
    "completed": false
}












```

This code will perform the fetch and output the result above. The `exec` attribute marks it executable by `mdexec`, and the `output-id` to indicate where to send the stdout/stderr output.

```python exec output-id=response
import requests
import json
response = requests.get("https://jsonplaceholder.typicode.com/todos/1")
print(json.dumps(response.json(), indent=4))
```

### Last Updated Timestamp
Alternatively, instead of using `output-id` and stdout/stderr you can use the Python API:

```python exec
from datetime import datetime
now = datetime.now()
# Set the content of the block with id=last-updated
md.set('last-updated', f"{now:%B %d, %Y at %I:%M %p}")
```


### Shared Execution Context

Start in one code block,

```python exec ctx=calc
def add10(num: int) -> int:
    return num + 10
```

and continue in another:

```python exec ctx=calc
y = add10(5)
print(y)
```

Both code blocks have the same `ctx` attribute value (i.e. `ctx=calc`), so they use the same Python environment.

### Auto-updating "usage" text

A low effort README that stays up to date with the CLI:

```bash exec output-id=usage
mdexec --help
```
```output id=usage
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

Automatically generate lists, tables, or even HTML to inject between HTML comment blocks.

```python exec output-id=fruits-list
print()
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

### API Access

A global `md` API object for reading and updating markdown content.
```python exec
import json
input_data = md.get('foobar')
md.set('foobar2', json.dumps(json.loads(input_data.content), indent=2))
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
updated = mdexec.auto_format_markdown_table(out.content)
md.set('table', updated)
```
<!-- id:table -->| Fruit  |  Color  |
| :--- | :--- |
| Lemon  |  Yellow |
| Apple  |  Red    |<!-- /id:table -->
