# XenForo Thread Extractor

A Python tool to extract posts from XenForo v2.2.8 Patch 1 forums and convert them to markdown files for LLM processing.

## Features

- Extract all posts from a XenForo thread via API
- Capture author, timestamp, and post content
- Convert BB code to Markdown format
- Handle pagination automatically
- Save as single file or individual post files
- Preserve post metadata (author, date, post ID)

## Requirements

- Python 3.7+
- XenForo forum with API access enabled
- Valid API key

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd tsrp-thread-extractor
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Create a configuration file:
```bash
cp config.example.json config.json
# Edit config.json with your forum URL and API key
```

## XenForo API Setup

### Obtaining an API Key

1. Log in to your XenForo admin panel
2. Navigate to **Setup** → **API keys**
3. Click **Add API key**
4. Set appropriate permissions (at minimum, need "Read threads" and "Read posts")
5. Save and copy the generated API key

### Required API Scopes

- `thread:read` - Read thread information
- `post:read` - Read posts

## Usage

### Command Line

Basic usage with command-line arguments:

```bash
python xenforo_extractor.py <thread_id> --base-url https://your-forum.com --api-key YOUR_API_KEY
```

### Options

- `thread_id` (required): The ID of the thread to extract
- `--base-url` (required): Base URL of your XenForo forum
- `--api-key` (required): Your XenForo API key
- `--output-dir`: Directory to save markdown files (default: `output`)
- `--single-file`: Save all posts in one file instead of separate files

### Examples

**Extract thread to separate files:**
```bash
python xenforo_extractor.py 12345 \
  --base-url https://forum.example.com \
  --api-key abc123xyz789 \
  --output-dir extracted_threads
```

**Extract thread to a single file:**
```bash
python xenforo_extractor.py 12345 \
  --base-url https://forum.example.com \
  --api-key abc123xyz789 \
  --single-file
```

## Output Format

### Single File Mode

Creates one markdown file containing all posts:

```
Thread_Title_12345.md
```

### Multiple Files Mode

Creates a directory with individual post files:

```
Thread_Title_12345/
├── README.md (index of all posts)
├── post_0001_67890.md
├── post_0002_67891.md
└── ...
```

### Post Format

Each post includes YAML frontmatter with metadata:

```markdown
---
author: username
date: 2024-01-15 14:30:00
post_id: 67890
thread: Thread Title
---

Post content in markdown format...
```

## BB Code Conversion

The tool automatically converts common BB codes to Markdown:

| BB Code | Markdown |
|---------|----------|
| `[b]text[/b]` | `**text**` |
| `[i]text[/i]` | `*text*` |
| `[u]text[/u]` | `_text_` |
| `[s]text[/s]` | `~~text~~` |
| `[code]code[/code]` | ` ```code``` ` |
| `[url=link]text[/url]` | `[text](link)` |
| `[img]url[/img]` | `![](url)` |
| `[quote]text[/quote]` | `> text` |

## Troubleshooting

### Authentication Errors

- Verify your API key is correct
- Check that the API key has necessary permissions
- Ensure API access is enabled in XenForo admin panel

### Thread Not Found

- Verify the thread ID is correct
- Check that the thread is accessible with your API key permissions
- Ensure the thread hasn't been deleted

### Rate Limiting

If you encounter rate limiting, the script will fail. You may need to:
- Add delays between requests
- Contact your forum administrator to adjust rate limits

## Advanced Usage

### Programmatic Usage

You can also use the `XenForoExtractor` class in your own Python scripts:

```python
from xenforo_extractor import XenForoExtractor

# Initialize extractor
extractor = XenForoExtractor(
    base_url="https://forum.example.com",
    api_key="your-api-key"
)

# Get all posts
posts = extractor.get_all_thread_posts(thread_id=12345)

# Process posts
for post in posts:
    author = post['User']['username']
    message = post['message']
    # ... do something with the post
```

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.