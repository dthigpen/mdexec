## Example Docs
Last Updated: <!-- id:last-updated -->April 18, 2026 at 08:43 AM<!-- /id:last-updated -->

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
