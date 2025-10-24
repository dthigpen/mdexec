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


```csv id=mycsv
aaa,bb,cc
111,22,33
xxx,yy,zz
```

```python exec output-id=test

b = list(query_blocks(id='mycsv'))[0]
print(b.content)
```

```output id=test
❌ Python error: query_blocks() missing 1 required positional argument: 'md_text'
```