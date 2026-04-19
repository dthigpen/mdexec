# `mdexec`

A lightweight, zero-dependency way to turn Markdown into a **runnable notebook**.

Execute Python or Bash code blocks and write results **anywhere in the same file**, no hidden state, no UI, just plain text.

## Example

The current time is: <!-- id:last-updated -->April 19, 2026 at 08:29 AM<!-- /id:last-updated -->

```python exec output-id=last-updated
from datetime import datetime
now = datetime.now()
print(f"{now:%B %d, %Y at %I:%M %p}")
```

Run:

```
mdexec README.md
```

and the timestamp updates in-place.

## How it works

* Add `exec` to any code block you want executed
* Capture output with `output-id=...`
* Reference locations in Markdown using `<!-- id:... --> ... <!-- /id:... -->` or `id=...` in another code block
* `mdexec` rewrites only the parts that change

No hidden metadata. Just Markdown.

## Installation

Install directly from GitHub:

```
pip install git+https://github.com/dthigpen/mdexec.git
```

## Usage

1. Create a Markdown file
2. Add executable code blocks:

````markdown
```python exec
x = 1 + 1
```
````

3. (Optional) Capture output:

````markdown
<!-- id:result -->old<!-- /id:result -->

```python exec output-id=result
print(2 + 2)
```
````

4. Run:

```
mdexec notebook.md
```

## More Examples

For full examples, check out the source of [`example.md`](https://github.com/dthigpen/mdexec/tree/main/examples/example.md). Alternatively, see the snippets below for a quick overview.

### Inline Output Anywhere

````markdown
The result is: <!-- id:sum -->42<!-- /id:sum -->

```python exec output-id=sum
print(40 + 2)
```
````

### Output to Code Blocks

````markdown
```python exec output-id=result
import json
print(json.dumps({'foo': 'bar', 'hello': True}, indent=2))
```

```json id=result
{
  "foo": "bar",
  "hello": true
}
```
````

### Input From Markdown

A global `md` API object is injected into Python code blocks to programmatically read/write to the Markdown document.

````markdown

Given some input data:
```json id=data
{
  "value": 123,
  "hello": true
}
```

Perform some calculation with it:

```python exec
import json
data = json.loads(md.get('data').content)
x = data['value'] * 456
```
````

### Shared Execution Context (Coming Soon)

````
```python exec ctx=calc
x = 10
```

```python exec ctx=calc
y = x + 5
print(y)
```
````

### Bash Support

````
```bash exec
echo "Hello from bash"
```
````

### Dynamic Tables

A global `md` API object is injected into Python code blocks to programmatically read/write to the Markdown document. This can be used to update multiple references.

````
| Item | Price |
|------|-------|
| A    | <!-- id:a -->0<!-- /id:a --> |
| B    | <!-- id:b -->0<!-- /id:b --> |

```python exec
prices = {"a": 10, "b": 20}
for k, v in prices.items():
    md.set(k, v)
```
````

## Features

* Execute Python and Bash code blocks
* Write output anywhere in the document
* Shared execution context across blocks (Coming soon)
* Minimal, readable Markdown (no hidden formats)
* Line-preserving updates (no full rewrites)
* Zero dependencies

## Design Philosophy

* Markdown is the source of truth
* Execution should be **transparent and inspectable**
* Outputs should be **stable and version-control friendly**
* No hidden state, no magic files

## To Do

- Shared Python contexts across multiple code blocks. Each code block is isolated right now.
- File watcher to rerun on save. E.g. `mdexec --watch *.md`.
- More Markdown tests to ensure things like indented code blocks get handled properly.
