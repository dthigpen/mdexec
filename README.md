# `mdexec`

A lightweight, zero-dependency way to turn Markdown into a runnable notebook.

Execute Python or Bash code blocks and write results **anywhere in the same file**, no hidden state, no UI, just plain text.

## Example

The following timestamp auto-updates when the notebook is run.

The current time is: <!-- id:last-updated -->**April 19, 2026 at 08:29 AM**<!-- /id:last-updated -->

```python exec output-id=last-updated
from datetime import datetime
now = datetime.now()
print(f"**{now:%B %d, %Y at %I:%M %p}**")
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

## Quick Start

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

## Concepts

### Executable Code Blocks

- Markdown code blocks can be marked as executable using the `exec` attribute.
- `exec` tells `mdexec` to run the block. Skip a code block by removing `exec` or setting it to `exec=false`.

````markdown
```python exec
print("Hello from Python")
```

```bash exec
echo Hello from Bash
```
````

### IDs: Connecting Input to Output

The `id` is the glue between blocks.

- A code block that gets executed (has `exec`) produces output. `stdout` can be captured and put back into the markdown document.
- Add `output-id=other-id` to an executable code block to redirect its output somewhere else, another code block, or an html tagged region.
- A code block is identified with the attribute `id=myid`.
- An HTML block is identified with special tags: `< !-- id:myid -->` and `< !-- /id:myid -->`.
- Any block that has an ID can be used as input to, or output from an executed code block.

For example, this code outputs to the html tagged region below it.

````markdown
```python exec output-id=report
print("Generated report")
```

```html
<!-- id:report -->
Generated report
<!-- /id:report -->
```
````

- One code block maps to one output target.
- Think of it as "write to this location".

### Output Targets

Output from a code block can optionally be written back to the markdown file with either HTML comment blocks or code blocks.

In both cases a code block must execute and produce some output. For example,

````markdown
```bash exec output-id=example
echo Hello
```
````

#### HTML Comment Blocks

Outputting between HTML comments allows for writing arbitrary markdown content.

Before execution:

````markdown
<!-- id:example -->
<!-- /id:example -->
````

After execution:

```markdown
<!-- id:example -->
Hello
<!-- /id:example -->
```

- The content between the comments is replaced.
- The `output-id` value in the source code block must match the ID in the comment.

#### Output to Code Blocks

Similarly, output can be written into another code block with matching IDs:

Before Execution:

````markdown
```id=example
```
````

After execution:

````markdown
```id=example
Hello
```
````

- For structured output like JSON, the ID should come somewhere after the language. E.g. `json id=example`.

### Formatting Behavior

`mdexec` tries to preserve formatting:
- If your output has newlines, they are kept
- If your block is multiline, output will match that style
- No extra whitespace is added unless needed for valid Markdown

This means:
```python
print("hello")
print()
print()
```
will produce:

```
hello


```
### Execution Order

Blocks are executed in the order they appear in the file.

- Later code blocks can depend on earlier ones (using a shared context, e.g. `ctx=something` in both code blocks)
- Output (code and HTML) blocks can appear in any order
- Keep this in mind when structuring notebooks


### Shared Execution Context

- By default, Python code blocks don't carry function definitions or variables to other code blocks.
- A shared context can be declared with the attribute `ctx=some-name`.

````markdown
```python exec ctx=calc
x = 10
```

```python exec ctx=calc
y = x + 5
print(y)
```
````

### Python API

- A global `md` API object is injected into Python code blocks to programmatically read and write to the Markdown document.
- Use `md.get('some-id').content` to reference old content within Python code.
- Use `md.set('some-id, 'new-content')` to rederence content within Python code.

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

Or even update cells of tables:

````markdown
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

### Live Reload (Optional)

`mdexec` is designed to be simple and composable. For auto-reloading, you can pair it with tools like `entr`:

```bash
ls notebook.md | entr mdexec notebook.md
```

## Features

* Execute Python and Bash code blocks
* Write output anywhere in the document
* Shared or isolated execution context across blocks
* Minimal, readable Markdown (no hidden formats)
* Line-preserving updates (no full rewrites)
* Zero dependencies

## Design Philosophy

* Markdown is the source of truth
* Execution should be **transparent and inspectable**
* Outputs should be **stable and version-control friendly**
* No hidden state, no magic files