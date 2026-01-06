# XenForo Thread Extractor

A Python tool to extract posts from XenForo v2.2.8 Patch 1 forums and convert them to markdown files for LLM processing.

## Features

- Extract all posts from a XenForo thread via API
- Capture author, timestamp, and post content
- Automatic user role detection (Admin, Moderator, Character, Narrator, DM)
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

### Using Configuration File (Recommended)

To avoid entering your URL and API key every time, create a `config.json` file:

1. Copy the example configuration:
```bash
cp config.example.json config.json
```

2. Edit `config.json` with your credentials:
```json
{
  "base_url": "https://your-forum.com",
  "api_key": "your-api-key-here"
}
```

3. Run the extractor with just the thread ID:
```bash
python xenforo_extractor.py 12345
```

The script will automatically load credentials from `config.json`. You can still override them with command-line arguments if needed.

### Command Line

You can also provide credentials directly via command-line arguments:

```bash
python xenforo_extractor.py <thread_id> --base-url https://your-forum.com --api-key YOUR_API_KEY
```

### Options

- `thread_id` (required): The ID of the thread to extract
- `--base-url`: Base URL of your XenForo forum (optional if using config.json)
- `--api-key`: Your XenForo API key (optional if using config.json)
- `--config`: Path to config file (default: `config.json`)
- `--output-dir`: Directory to save markdown files (default: `output`)
- `--single-file`: Save all posts in one file instead of separate files

### Examples

**Using config.json (simplest):**
```bash
# Extract to separate files
python xenforo_extractor.py 12345

# Extract to single file
python xenforo_extractor.py 12345 --single-file

# Use custom config file
python xenforo_extractor.py 12345 --config my-config.json
```

**Using command-line arguments:**
```bash
# Extract thread to separate files
python xenforo_extractor.py 12345 \
  --base-url https://forum.example.com \
  --api-key abc123xyz789 \
  --output-dir extracted_threads

# Extract thread to a single file
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

Each post includes a header with metadata and optional role badge:

```markdown
## Post 1

**Author:** username (Admin)\
**Date:** 2024-01-15\
**Post_ID:** 67890

Post content in markdown format...
```

The tool automatically detects user roles from the XenForo API:
- **(Admin)** - Administrators (user_group_id = 3)
- **(Narrator)** - Narrators (user_group_id = 12)
- **(Moderator)** - Moderators (user_group_id = 4)
- **(Character)** - Characters (user_group_id = 5)
- **(DM)** - Dungeon Masters (secondary_group_id = 21)

## BB Code Conversion

The tool automatically converts common BB codes to Markdown:

| BB Code | Markdown | Notes |
|---------|----------|-------|
| `[b]text[/b]` | `**text**` | Bold |
| `[i]text[/i]` | `*text*` | Italic |
| `[u]text[/u]` | `_text_` | Underline |
| `[s]text[/s]` | `~~text~~` | Strikethrough |
| `[code]code[/code]` | ` ```code``` ` | Code block |
| `[url=link]text[/url]` | `text` | Link text only |
| `[img]url[/img]` | _(removed)_ | Images removed entirely |
| `[quote]text[/quote]` | `> text` | Quote |
| `[spoiler=title]text[/spoiler]` | `Spoiler-title: text` | Spoiler with title |
| `[spoiler]text[/spoiler]` | `Spoiler: text` | Spoiler without title |
| `[inlinespoiler]text[/inlinespoiler]` | `Spoiler: text` | Inline spoiler |

### Custom Forum Tags (Omitted)

The following custom BB codes are completely removed from output:
- `[side]...[/side]` - Sidebar content (omitted)
- `[ibanner]...[/ibanner]` - Image banners (omitted)
- `[fa]...[/fa]` - Font Awesome icons (omitted)
- `[bannericon]...[/bannericon]` - Banner icons (omitted)
- `[abbr=option]...[/abbr]` - Abbreviations (omitted)
- `[metertext=option]...[/metertext]` - Meter text (omitted)
- `[metercolor=option]...[/metercolor]` - Meter color (omitted)

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