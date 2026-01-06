#!/usr/bin/env python3
"""
XenForo Thread Extractor
Extracts posts from XenForo forums and converts them to markdown files.
"""

import requests
import json
import os
import re
from datetime import datetime
from typing import List, Dict, Optional
import argparse
from pathlib import Path


class XenForoExtractor:
    """Extract posts from XenForo forums using the API."""

    def __init__(self, base_url: str, api_key: str, user_roles_file: str = 'user_roles.json'):
        """
        Initialize the XenForo extractor.

        Args:
            base_url: Base URL of the XenForo forum (e.g., https://forum.example.com)
            api_key: XenForo API key
            user_roles_file: Path to JSON file containing user_id -> role mappings
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'XF-Api-Key': api_key,
            'Content-Type': 'application/json'
        }
        # Load user role mappings from JSON file
        self.user_roles = self._load_user_roles(user_roles_file)

    def _load_user_roles(self, file_path: str) -> Dict[str, str]:
        """Load user role mappings from JSON file."""
        try:
            with open(file_path, 'r') as f:
                roles = json.load(f)
            print(f"✓ Loaded {len(roles)} user role mappings from {file_path}")
            return roles
        except FileNotFoundError:
            print(f"Note: {file_path} not found, role badges will not be displayed")
            return {}
        except json.JSONDecodeError as e:
            print(f"Warning: Error parsing {file_path}: {e}")
            return {}

    def get_user_role(self, user_id: int) -> str:
        """
        Get the user's role from the user_roles mapping.

        Args:
            user_id: The user ID

        Returns:
            Role string (e.g., "(Admin)", "(Moderator)") or empty string
        """
        user_id_str = str(user_id)
        if user_id_str in self.user_roles:
            role_name = self.user_roles[user_id_str]
            return f"({role_name})"
        return ""

    def get_thread_posts(self, thread_id: int, page: int = 1) -> Dict:
        """
        Fetch posts from a thread.

        Args:
            thread_id: The thread ID to extract posts from
            page: Page number for pagination (default: 1)

        Returns:
            Dictionary containing posts and pagination info
        """
        url = f"{self.base_url}/api/threads/{thread_id}/posts"
        params = {'page': page}

        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()

        return response.json()

    def get_all_thread_posts(self, thread_id: int) -> List[Dict]:
        """
        Fetch all posts from a thread, handling pagination.

        Args:
            thread_id: The thread ID to extract posts from

        Returns:
            List of all posts in the thread
        """
        all_posts = []
        page = 1

        while True:
            print(f"Fetching page {page}...")
            data = self.get_thread_posts(thread_id, page)

            posts = data.get('posts', [])
            if not posts:
                break

            all_posts.extend(posts)

            # Check if there are more pages
            pagination = data.get('pagination', {})
            if page >= pagination.get('last_page', 1):
                break

            page += 1

        print(f"Fetched {len(all_posts)} posts total")
        return all_posts

    def get_thread_info(self, thread_id: int) -> Dict:
        """
        Fetch thread information.

        Args:
            thread_id: The thread ID

        Returns:
            Dictionary containing thread information
        """
        url = f"{self.base_url}/api/threads/{thread_id}"

        response = requests.get(url, headers=self.headers)
        response.raise_for_status()

        return response.json()

    def bb_code_to_markdown(self, bb_code: str) -> str:
        """
        Convert BB code to markdown (basic conversion).

        Args:
            bb_code: BB code string

        Returns:
            Markdown formatted string
        """
        # Remove or convert common BB codes
        text = bb_code

        # CUSTOM: Remove [side]...[/side] tags entirely (omit content)
        text = re.sub(r'\[side\].*?\[/side\]', '', text, flags=re.IGNORECASE | re.DOTALL)

        # CUSTOM: Remove custom forum tags entirely (omit content and tags)
        text = re.sub(r'\[ibanner\].*?\[/ibanner\]', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'\[fa\].*?\[/fa\]', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'\[bannericon\].*?\[/bannericon\]', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'\[abbr=.*?\].*?\[/abbr\]', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'\[metertext=.*?\].*?\[/metertext\]', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'\[metercolor=.*?\].*?\[/metercolor\]', '', text, flags=re.IGNORECASE | re.DOTALL)

        # CUSTOM: Handle spoilers - keep content but mark as spoiler
        # [spoiler=Title]content[/spoiler] -> Spoiler-Title: content
        text = re.sub(
            r'\[spoiler=(.*?)\](.*?)\[/spoiler\]',
            r'Spoiler-\1: \2',
            text,
            flags=re.IGNORECASE | re.DOTALL
        )
        # [spoiler]content[/spoiler] -> Spoiler: content
        text = re.sub(
            r'\[spoiler\](.*?)\[/spoiler\]',
            r'Spoiler: \1',
            text,
            flags=re.IGNORECASE | re.DOTALL
        )
        # [inlinespoiler]content[/inlinespoiler] -> Spoiler: content
        text = re.sub(
            r'\[inlinespoiler\](.*?)\[/inlinespoiler\]',
            r'Spoiler: \1',
            text,
            flags=re.IGNORECASE | re.DOTALL
        )

        # Bold
        text = re.sub(r'\[b\](.*?)\[/b\]', r'**\1**', text, flags=re.IGNORECASE | re.DOTALL)

        # Italic
        text = re.sub(r'\[i\](.*?)\[/i\]', r'*\1*', text, flags=re.IGNORECASE | re.DOTALL)

        # Underline (markdown doesn't have native underline, use emphasis)
        text = re.sub(r'\[u\](.*?)\[/u\]', r'_\1_', text, flags=re.IGNORECASE | re.DOTALL)

        # Strikethrough
        text = re.sub(r'\[s\](.*?)\[/s\]', r'~~\1~~', text, flags=re.IGNORECASE | re.DOTALL)

        # Code blocks
        text = re.sub(r'\[code\](.*?)\[/code\]', r'```\n\1\n```', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'\[code=(.*?)\](.*?)\[/code\]', r'```\1\n\2\n```', text, flags=re.IGNORECASE | re.DOTALL)

        # Inline code
        text = re.sub(r'\[icode\](.*?)\[/icode\]', r'`\1`', text, flags=re.IGNORECASE | re.DOTALL)

        # URLs - keep only the text part
        text = re.sub(r'\[url=(.*?)\](.*?)\[/url\]', r'\2', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'\[url\](.*?)\[/url\]', r'\1', text, flags=re.IGNORECASE | re.DOTALL)

        # Images - remove entirely
        text = re.sub(r'\[img\].*?\[/img\]', '', text, flags=re.IGNORECASE | re.DOTALL)

        # Quotes
        text = re.sub(r'\[quote\](.*?)\[/quote\]', r'> \1', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'\[quote=(.*?)\](.*?)\[/quote\]', r'> **\1 wrote:**\n> \2', text, flags=re.IGNORECASE | re.DOTALL)

        # Lists
        text = re.sub(r'\[list\](.*?)\[/list\]', r'\1', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'\[\*\](.*?)(?=\[\*\]|\[/list\]|$)', r'- \1\n', text, flags=re.IGNORECASE | re.DOTALL)

        # Headers
        text = re.sub(r'\[h1\](.*?)\[/h1\]', r'# \1', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'\[h2\](.*?)\[/h2\]', r'## \1', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'\[h3\](.*?)\[/h3\]', r'### \1', text, flags=re.IGNORECASE | re.DOTALL)

        # Clean up any remaining BB codes (simple approach)
        text = re.sub(r'\[.*?\]', '', text)

        return text.strip()

    def format_post_markdown(self, post: Dict, thread_title: str = "", post_number: int = 1) -> str:
        """
        Format a single post as markdown.

        Args:
            post: Post dictionary from API
            thread_title: Optional thread title for context (not used in output per user request)
            post_number: The post number in the thread

        Returns:
            Markdown formatted post
        """
        # Debug: Check if post is None
        if post is None:
            print(f"  Warning: Post {post_number} is None, skipping...")
            return ""

        # Debug: Check if post is a dict
        if not isinstance(post, dict):
            print(f"  Warning: Post {post_number} is not a dict (type: {type(post)}), skipping...")
            return ""

        try:
            user_data = post.get('User', {})
            if user_data is None:
                user_data = {}

            author = user_data.get('username', 'Unknown')
            user_id = user_data.get('user_id')
            post_date = post.get('post_date', 0)
            post_id = post.get('post_id', 'unknown')
            message = post.get('message', '')

            # Get user role from mapping
            role = ""
            if user_id:
                role = self.get_user_role(user_id)
                if role:
                    role = f" {role}"

            # Convert timestamp to readable format (date only, no time)
            if post_date:
                date_str = datetime.fromtimestamp(post_date).strftime('%Y-%m-%d')
            else:
                date_str = 'Unknown date'

            # Convert BB code to markdown
            message_md = self.bb_code_to_markdown(message)

            # Format the post with new header format (bold with backslash line breaks)
            markdown = f"""**Author:** {author}{role}\\
**Date:** {date_str}\\
**Post_ID:** {post_id}

{message_md}
"""

            return markdown

        except Exception as e:
            print(f"  Error formatting post {post_number}: {e}")
            print(f"  Post data keys: {list(post.keys()) if isinstance(post, dict) else 'Not a dict'}")
            print(f"  Post data: {post}")
            # Return a placeholder so we can continue
            return f"**Error:** Could not format post {post_number} - {str(e)}\n\n"

    def save_thread_as_markdown(self, thread_id: int, output_dir: str = "output",
                                 single_file: bool = False):
        """
        Extract a thread and save as markdown file(s).

        Args:
            thread_id: The thread ID to extract
            output_dir: Directory to save markdown files
            single_file: If True, save all posts in one file; if False, save each post separately
        """
        # Get thread info
        print(f"Fetching thread info for thread {thread_id}...")
        thread_info = self.get_thread_info(thread_id)
        thread_data = thread_info.get('thread', {})
        thread_title = thread_data.get('title', f'Thread_{thread_id}')

        # Sanitize thread title for filename
        safe_title = re.sub(r'[^\w\s-]', '', thread_title)
        safe_title = re.sub(r'[-\s]+', '_', safe_title)

        # Get all posts
        posts = self.get_all_thread_posts(thread_id)

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        if single_file:
            # Save all posts in one file
            filename = output_path / f"{safe_title}_{thread_id}.md"
            print(f"Saving all posts to {filename}...")

            with open(filename, 'w', encoding='utf-8') as f:
                # Write thread header
                f.write(f"# {thread_title}\n\n")
                f.write(f"**Thread ID:** {thread_id}\n")
                f.write(f"**Total Posts:** {len(posts)}\n\n")
                f.write("---\n\n")

                # Write each post
                for i, post in enumerate(posts, 1):
                    f.write(f"## Post {i}\n\n")
                    post_md = self.format_post_markdown(post, thread_title, post_number=i)
                    f.write(post_md)
                    f.write("\n\n")

            print(f"✓ Saved {len(posts)} posts to {filename}")
        else:
            # Save each post as a separate file
            thread_dir = output_path / f"{safe_title}_{thread_id}"
            thread_dir.mkdir(parents=True, exist_ok=True)

            print(f"Saving posts to {thread_dir}/...")

            # Create an index file
            index_file = thread_dir / "README.md"
            with open(index_file, 'w', encoding='utf-8') as f:
                f.write(f"# {thread_title}\n\n")
                f.write(f"**Thread ID:** {thread_id}\n")
                f.write(f"**Total Posts:** {len(posts)}\n\n")
                f.write("## Posts\n\n")

            for i, post in enumerate(posts, 1):
                post_id = post.get('post_id', i)
                filename = thread_dir / f"post_{i:04d}_{post_id}.md"

                with open(filename, 'w', encoding='utf-8') as f:
                    # Add post header
                    f.write(f"## Post {i}\n\n")
                    post_md = self.format_post_markdown(post, thread_title, post_number=i)
                    f.write(post_md)

                # Add to index
                author = post.get('User', {}).get('username', 'Unknown')
                with open(index_file, 'a', encoding='utf-8') as f:
                    f.write(f"{i}. [Post by {author}](post_{i:04d}_{post_id}.md)\n")

            print(f"✓ Saved {len(posts)} posts to {thread_dir}/")


def load_config(config_path: str) -> Dict:
    """
    Load configuration from JSON file.

    Args:
        config_path: Path to config file

    Returns:
        Dictionary with configuration values
    """
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as e:
        print(f"Warning: Error parsing config file {config_path}: {e}")
        return {}


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Extract posts from XenForo threads and convert to markdown'
    )
    parser.add_argument('thread_ids', type=int, nargs='+',
                        help='Thread ID(s) to extract (space-separated for multiple threads)')
    parser.add_argument('--base-url', help='Base URL of XenForo forum')
    parser.add_argument('--api-key', help='XenForo API key')
    parser.add_argument('--config', default='config.json', help='Path to config file (default: config.json)')
    parser.add_argument('--output-dir', default='output', help='Output directory (default: output)')
    parser.add_argument('--single-file', action='store_true',
                        help='Save all posts in a single file instead of separate files')

    args = parser.parse_args()

    # Load config file
    config = load_config(args.config)

    # Get base_url and api_key (command line args override config file)
    base_url = args.base_url or config.get('base_url')
    api_key = args.api_key or config.get('api_key')

    # Validate required parameters
    if not base_url:
        print("✗ Error: --base-url is required (either via command line or config.json)")
        return 1
    if not api_key:
        print("✗ Error: --api-key is required (either via command line or config.json)")
        return 1

    # Create extractor instance
    extractor = XenForoExtractor(base_url, api_key, user_roles_file='user_roles.json')

    # Extract and save threads
    total_threads = len(args.thread_ids)
    successful = 0
    failed = 0

    for idx, thread_id in enumerate(args.thread_ids, 1):
        if total_threads > 1:
            print(f"\n{'='*60}")
            print(f"Processing thread {idx}/{total_threads}: Thread ID {thread_id}")
            print(f"{'='*60}")

        try:
            extractor.save_thread_as_markdown(
                thread_id,
                output_dir=args.output_dir,
                single_file=args.single_file
            )
            successful += 1
        except requests.exceptions.HTTPError as e:
            print(f"\n✗ HTTP Error for thread {thread_id}: {e}")
            print(f"Response: {e.response.text if hasattr(e, 'response') else 'No response'}")
            failed += 1
        except Exception as e:
            print(f"\n✗ Error for thread {thread_id}: {e}")
            failed += 1

    # Summary
    print(f"\n{'='*60}")
    print(f"✓ Extraction complete!")
    print(f"  Successful: {successful}/{total_threads}")
    if failed > 0:
        print(f"  Failed: {failed}/{total_threads}")
    print(f"{'='*60}")

    return 0 if failed == 0 else 1


if __name__ == '__main__':
    main()
