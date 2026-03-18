#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clean up duplicate entries in Notion database
Removes duplicate Korean entries, keeping only one copy of each
"""

import os
import requests
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")


def format_db_id(db_id: str) -> str:
    """Format database ID with hyphens"""
    return f'{db_id[0:8]}-{db_id[8:12]}-{db_id[12:16]}-{db_id[16:20]}-{db_id[20:]}'


def delete_page(page_id: str) -> bool:
    """Delete a page from Notion"""
    url = f'https://api.notion.com/v1/pages/{page_id}'
    headers = {
        'Authorization': f'Bearer {NOTION_TOKEN}',
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json'
    }
    
    payload = {'archived': True}  # Archive instead of delete
    
    try:
        response = requests.patch(url, headers=headers, json=payload)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"  ✗ Failed to delete {page_id}: {e}")
        return False


def cleanup_duplicates():
    """Find and remove duplicate entries"""
    
    print("🔍 Scanning for duplicates...\n")
    
    formatted_id = format_db_id(DATABASE_ID)
    url = f'https://api.notion.com/v1/databases/{formatted_id}/query'
    headers = {
        'Authorization': f'Bearer {NOTION_TOKEN}',
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json'
    }
    
    # Map Korean text to list of page IDs
    korean_to_pages = {}
    has_more = True
    start_cursor = None
    total_pages = 0
    
    # Fetch all pages
    while has_more:
        payload = {'page_size': 100}
        if start_cursor:
            payload['start_cursor'] = start_cursor
        
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
        for page in data.get('results', []):
            total_pages += 1
            page_id = page['id']
            
            try:
                title_prop = page['properties'].get('Korean', {})
                title_content = title_prop.get('title', [])
                if title_content:
                    korean_text = title_content[0]['text']['content']
                    
                    if korean_text not in korean_to_pages:
                        korean_to_pages[korean_text] = []
                    korean_to_pages[korean_text].append(page_id)
            except Exception as e:
                print(f"  ⚠️  Error parsing page {page_id}: {e}")
        
        has_more = data.get('has_more', False)
        start_cursor = data.get('next_cursor')
    
    # Find duplicates
    duplicates = {k: v for k, v in korean_to_pages.items() if len(v) > 1}
    
    print(f"📊 Database Stats:")
    print(f"  Total pages: {total_pages}")
    print(f"  Unique Korean entries: {len(korean_to_pages)}")
    print(f"  Duplicate entries: {len(duplicates)}")
    print(f"  Total duplicates to remove: {sum(len(v) - 1 for v in duplicates.values())}\n")
    
    if not duplicates:
        print("✅ No duplicates found!")
        return
    
    # Show what will be deleted
    print("🗑️  Duplicates to remove:\n")
    total_to_delete = 0
    for korean, page_ids in sorted(duplicates.items()):
        print(f"  '{korean}'")
        print(f"    Found {len(page_ids)} copies, keeping 1, removing {len(page_ids)-1}")
        total_to_delete += len(page_ids) - 1
    
    # Confirm before deletion
    print(f"\n⚠️  This will archive {total_to_delete} pages from your Notion database")
    response = input("Continue? (y/n): ").strip().lower()
    
    if response != 'y':
        print("Cancelled.")
        return
    
    # Delete duplicates (keep first, delete rest)
    print("\n🧹 Removing duplicates...\n")
    deleted_count = 0
    
    for korean, page_ids in duplicates.items():
        # Keep first, delete rest
        for page_id_to_delete in page_ids[1:]:
            if delete_page(page_id_to_delete):
                deleted_count += 1
                print(f"  ✓ Archived duplicate: '{korean}'")
    
    print(f"\n✅ Complete! Archived {deleted_count} duplicate pages")
    print(f"   Remaining unique entries: {len(korean_to_pages)}")


if __name__ == "__main__":
    cleanup_duplicates()
