#!/usr/bin/env python
"""
Export restaurant reviews from a Confluence parent page to JSON.

IMPORTANT: This script is a helper that prints instructions for Claude Code.
It does NOT directly access Confluence - that requires MCP tools only available
to Claude Code.

Usage:
    python export_reviews_from_confluence.py --parent-id 99811341

This will print instructions that you can give to Claude Code to fetch and export
the reviews from the specified parent page.

For actual export, ask Claude Code:
    "Export reviews from Confluence parent page 99811341 to confluence_reviews_export.json"
"""

import argparse
from datetime import datetime


def main():
    parser = argparse.ArgumentParser(
        description='Generate export instructions for Confluence reviews'
    )
    parser.add_argument(
        '--parent-id',
        type=str,
        required=True,
        help='Confluence parent page ID (e.g., 99811341 for Toronto)'
    )
    parser.add_argument(
        '--cloud-id',
        type=str,
        default='https://gavinlu.atlassian.net',
        help='Atlassian cloud ID or site URL (default: https://gavinlu.atlassian.net)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='confluence_reviews_export.json',
        help='Output JSON file path (default: confluence_reviews_export.json)'
    )

    args = parser.parse_args()

    print("=" * 70)
    print("CONFLUENCE EXPORT INSTRUCTIONS FOR CLAUDE CODE")
    print("=" * 70)
    print()
    print("Copy and paste this request to Claude Code:")
    print()
    print(f"Export restaurant reviews from Confluence parent page {args.parent_id}")
    print(f"to {args.output}")
    print()
    print("Details:")
    print(f"  - Parent Page ID: {args.parent_id}")
    print(f"  - Cloud ID: {args.cloud_id}")
    print(f"  - Output File: {args.output}")
    print(f"  - Export Date: {datetime.now().strftime('%Y-%m-%d')}")
    print()
    print("=" * 70)
    print()
    print("What Claude Code will do:")
    print("1. Fetch the parent page information")
    print("2. Get all descendant pages (restaurant reviews)")
    print("3. Fetch full content for each review page")
    print("4. Build JSON export matching existing format")
    print(f"5. Save to {args.output}")
    print()
    print("After export completes, you can import with:")
    print(f"  python manage.py import_confluence_reviews --json-file {args.output}")
    print()


if __name__ == '__main__':
    main()
