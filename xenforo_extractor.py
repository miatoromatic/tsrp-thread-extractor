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

    def __init__(self, base_url: str, api_key: str):
        """
        Initialize the XenForo extractor.

        Args:
            base_url: Base URL of the XenForo forum (e.g., https://forum.example.com)
            api_key: XenForo API key
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'XF-Api-Key': api_key,
            'Content-Type': 'application/json'
        }
        # Cache for user data to avoid repeated API calls
        self.user_cache = {}

    def get_user_role(self, user_id: int) -> str:
        """
        Get the user's role based on their user_group_id and secondary_group_ids.

        Args:
            user_id: The user ID

        Returns:
            Role string (e.g., "(Admin)", "(Moderator)") or empty string
        """
        # Check cache first
        if user_id in self.user_cache:
            return self.user_cache[user_id]

        try:
            url = f"{self.base_url}/api/users/{user_id}"
            # Add parameters to access user group data
            # - api_bypass_permissions: Required to access internal profile data
            # - with: Request additional data relations
            params = {
                'api_bypass_permissions': 1,
                'with': 'profile'
            }
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()

            data = response.json()
            user_data = data.get('user', {})

            # Debug output - show full user data structure
            print(f"  Debug: User {user_id} API response:")
            print(f"    - user_group_id: {user_data.get('user_group_id')}")
            print(f"    - secondary_group_ids: {user_data.get('secondary_group_ids')} (type: {type(user_data.get('secondary_group_ids'))})")

            user_group_id = user_data.get('user_group_id')
            secondary_group_ids_raw = user_data.get('secondary_group_ids', [])

            # Handle secondary_group_ids as either list or comma-separated string
            if isinstance(secondary_group_ids_raw, str):
                # Convert comma-separated string to list of integers
                secondary_group_ids = [int(x.strip()) for x in secondary_group_ids_raw.split(',') if x.strip()]
            elif isinstance(secondary_group_ids_raw, list):
                # Already a list
                secondary_group_ids = secondary_group_ids_raw
            else:
                secondary_group_ids = []

            print(f"    - parsed secondary_group_ids: {secondary_group_ids}")

            # Determine role based on group IDs
            role = ""
            if user_group_id == 3:
                role = "(Admin)"
            elif user_group_id == 12:
                role = "(Narrator)"
            elif user_group_id == 4:
                role = "(Moderator)"
            elif user_group_id == 5:
                role = "(Character)"
            elif 21 in secondary_group_ids:
                role = "(DM)"

            print(f"    - detected role: {role if role else 'None'}")

            # Cache the result
            self.user_cache[user_id] = role
            return role

        except Exception as e:
            print(f"  Warning: Could not fetch user data for user {user_id}: {e}")
            # Print response text if available for debugging
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                print(f"    Response: {e.response.text[:200]}")
            # Cache empty string to avoid repeated failed requests
            self.user_cache[user_id] = ""
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
        user_data = post.get('User', {})
        author = user_data.get('username', 'Unknown')
        user_id = user_data.get('user_id')
        post_date = post.get('post_date', 0)
        post_id = post.get('post_id', 'unknown')
        message = post.get('message', '')

        # Get user role if user_id is available
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
    parser.add_argument('thread_id', type=int, help='Thread ID to extract')
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
    extractor = XenForoExtractor(base_url, api_key)

    # Extract and save thread
    try:
        extractor.save_thread_as_markdown(
            args.thread_id,
            output_dir=args.output_dir,
            single_file=args.single_file
        )
        print("\n✓ Extraction complete!")
        return 0
    except requests.exceptions.HTTPError as e:
        print(f"\n✗ HTTP Error: {e}")
        print(f"Response: {e.response.text if hasattr(e, 'response') else 'No response'}")
        return 1
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return 1


if __name__ == '__main__':
    main()
