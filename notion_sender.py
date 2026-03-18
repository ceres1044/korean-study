#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notion Sender for Korean Learning Materials
===========================================
Sends analyzed materials to Notion database with English translations
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from notion_client import Client
import requests


def send_to_notion(analysis_path: Path, notion_token: str, database_id: str, 
                   skip_duplicates: bool = True, min_confidence: str = "medium") -> dict:
    """
    Send analysis results to Notion database with deduplication and filtering
    
    Args:
        analysis_path: Path to analysis JSON file
        notion_token: Notion API token
        database_id: Notion database ID
        skip_duplicates: Skip items already in Notion (default True)
        min_confidence: Minimum confidence level (high/medium/low, default medium)
        
    Returns:
        Dict with success stats
    """
    
    # Load analysis
    with open(analysis_path, 'r', encoding='utf-8') as f:
        analysis = json.load(f)
    
    notion = Client(auth=notion_token)
    session_date = analysis.get('session_date', '2026-02-05')
    
    materials = analysis.get('learning_materials', [])
    
    # Get existing Korean entries if deduplication enabled
    existing_korean = set()
    if skip_duplicates:
        print("🔍 Checking for existing entries...")
        try:
            # Format database_id with hyphens for API call
            db_id = database_id
            formatted_id = f'{db_id[0:8]}-{db_id[8:12]}-{db_id[12:16]}-{db_id[16:20]}-{db_id[20:]}'
            
            # Use direct API call to query database
            url = f'https://api.notion.com/v1/databases/{formatted_id}/query'
            headers = {
                'Authorization': f'Bearer {notion_token}',
                'Notion-Version': '2022-06-28',
                'Content-Type': 'application/json'
            }
            
            has_more = True
            start_cursor = None
            page_count = 0
            
            while has_more:
                payload = {'page_size': 100}
                if start_cursor:
                    payload['start_cursor'] = start_cursor
                
                response = requests.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                
                # Extract Korean text from all pages
                for page in data.get('results', []):
                    title_prop = page['properties'].get('Korean', {})
                    title_content = title_prop.get('title', [])
                    if title_content:
                        korean_text = title_content[0]['text']['content']
                        existing_korean.add(korean_text)
                
                has_more = data.get('has_more', False)
                start_cursor = data.get('next_cursor')
                page_count += len(data.get('results', []))
            
            print(f"   Found {len(existing_korean)} existing entries (scanned {page_count} pages)")
            
        except Exception as e:
            print(f"⚠️  Could not check for duplicates: {e}")
            existing_korean = set()
    
    # Filter materials
    confidence_levels = {"high": 2, "medium": 1, "low": 0}
    min_level = confidence_levels.get(min_confidence, 1)
    
    filtered_materials = []
    for item in materials:
        korean = item.get('korean', '')
        conf = item.get('confidence', 'medium')
        item_level = confidence_levels.get(conf, 0)
        
        # Skip duplicates
        if skip_duplicates and korean in existing_korean:
            continue
        
        # Skip low-confidence unless it's a correction
        if item_level < min_level and item.get('type') != 'correction':
            continue
        
        filtered_materials.append(item)
    
    stats = {
        "total": len(materials),
        "filtered": len(filtered_materials),
        "duplicates_skipped": len([m for m in materials if m.get('korean') in existing_korean]),
        "low_quality_skipped": len(materials) - len(filtered_materials) - len([m for m in materials if m.get('korean') in existing_korean]),
        "success": 0,
        "failed": 0,
        "errors": []
    }
    
    materials = filtered_materials
    
    print(f"\n📤 Sending {len(materials)} items to Notion...")
    print(f"📅 Session Date: {session_date}")
    print(f"🗄️  Database ID: {database_id[:8]}...")
    
    for i, item in enumerate(materials, 1):
        try:
            # Map types
            type_map = {
                "vocabulary": "Vocabulary",
                "phrase": "Phrase",
                "grammar": "Grammar Point",
                "correction": "Teacher Correction"
            }
            item_type = type_map.get(item.get('type', 'vocabulary'), "Vocabulary")
            
            # Map confidence
            conf_map = {
                "high": "High ✅",
                "medium": "Medium ⚠️",
                "low": "Low 🚫"
            }
            confidence = conf_map.get(item.get('confidence', 'medium'), "Medium ⚠️")
            
            # Build Korean text
            korean_text = item.get('korean', '')
            
            # Build English text
            english_text = item.get('english', '')
            
            # Build example text (combine both examples)
            examples = item.get('examples', [])
            example_lines = []
            for ex in examples:
                k = ex.get('korean', '')
                e = ex.get('english', '')
                if k and e:
                    example_lines.append(f"{k}\n→ {e}")
            example_text = "\n\n".join(example_lines)
            
            # Build notes (include correction details if present)
            notes_parts = []
            
            # Add context from class
            context = item.get('context_from_class', '')
            if context:
                notes_parts.append(f"From class: {context}")
            
            # Add correction details
            if item.get('type') == 'correction':
                corr = item.get('correction_details', {})
                if corr:
                    notes_parts.append(f"❌ Incorrect: {corr.get('incorrect', '')}")
                    notes_parts.append(f"✅ Correct: {corr.get('correct', '')}")
                    if corr.get('explanation'):
                        notes_parts.append(f"Why: {corr.get('explanation')}")
            
            # Add any additional notes
            if item.get('notes'):
                notes_parts.append(item['notes'])
            
            notes_text = "\n\n".join(notes_parts)
            
            # Create Notion page
            notion.pages.create(
                parent={"database_id": database_id},
                properties={
                    "Korean": {
                        "title": [{"text": {"content": korean_text[:2000]}}]
                    },
                    "English": {
                        "rich_text": [{"text": {"content": english_text[:2000]}}]
                    },
                    "Type": {
                        "select": {"name": item_type}
                    },
                    "Example": {
                        "rich_text": [{"text": {"content": example_text[:2000]}}]
                    },
                    "Confidence": {
                        "select": {"name": confidence}
                    },
                    "Session Date": {
                        "date": {"start": session_date}
                    },
                    "Status": {
                        "select": {"name": "To Review"}
                    },
                    "Notes": {
                        "rich_text": [{"text": {"content": notes_text[:2000]}}]
                    }
                }
            )
            
            stats["success"] += 1
            print(f"  ✅ [{i}/{len(materials)}] {item_type}: {korean_text[:40]}")
            
        except Exception as e:
            stats["failed"] += 1
            error_msg = f"{item.get('korean', 'unknown')}: {str(e)}"
            stats["errors"].append(error_msg)
            print(f"  ❌ [{i}/{len(materials)}] Failed: {error_msg}")
    
    print(f"\n📊 Results:")
    print(f"  📥 Analyzed: {stats['total']} items")
    if stats.get('duplicates_skipped', 0) > 0:
        print(f"  ⏭️  Skipped duplicates: {stats['duplicates_skipped']}")
    if stats.get('low_quality_skipped', 0) > 0:
        print(f"  🔽 Filtered low-quality: {stats['low_quality_skipped']}")
    print(f"  📤 Sent to Notion: {stats['filtered']}")
    print(f"  ✅ Success: {stats['success']}/{stats['filtered']}")
    if stats['failed'] > 0:
        print(f"  ❌ Failed: {stats['failed']}/{stats['filtered']}")
    
    if stats['errors']:
        print(f"\n⚠️  Errors:")
        for err in stats['errors'][:5]:  # Show first 5 errors
            print(f"    • {err}")
        if len(stats['errors']) > 5:
            print(f"    ... and {len(stats['errors']) - 5} more")
    
    return stats


def verify_database_connection(notion_token: str, database_id: str) -> tuple[bool, str]:
    """
    Verify connection to Notion database
    
    Returns:
        (success: bool, message: str)
    """
    try:
        notion = Client(auth=notion_token)
        
        # Try to retrieve the database
        db = notion.databases.retrieve(database_id=database_id)
        
        return True, f"✅ Connected! Found database"
        
    except Exception as e:
        error_str = str(e)
        
        if "object_not_found" in error_str.lower():
            return False, "❌ Database not found. Check your database ID in .env"
        elif "unauthorized" in error_str.lower():
            return False, "❌ Unauthorized. Check your Notion token and integration permissions"
        elif "could not find database" in error_str.lower():
            return False, "❌ Database not found. Make sure you've connected your integration to the database"
        else:
            return False, f"❌ Connection error: {error_str[:200]}"


def get_database_schema(notion_token: str, database_id: str) -> Optional[dict]:
    """
    Get database properties to verify schema
    
    Returns:
        Dict with property names and types, or None if failed
    """
    try:
        notion = Client(auth=notion_token)
        db = notion.databases.retrieve(database_id=database_id)
        
        properties = db.get('properties', {})
        schema = {}
        
        for prop_name, prop_data in properties.items():
            schema[prop_name] = prop_data.get('type', 'unknown')
        
        return schema
        
    except Exception as e:
        print(f"❌ Could not retrieve schema: {e}")
        return None
