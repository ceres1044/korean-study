from notion_client import Client
import os
from dotenv import load_dotenv

load_dotenv('/Users/jingchen/code/koreanlearning/.env')

notion = Client(auth=os.getenv('NOTION_TOKEN'))
db_id = os.getenv('NOTION_DATABASE_ID')

print(f"Testing databases.query() on DB: {db_id}")
print(f"Method exists: {hasattr(notion.databases, 'query')}")

try:
    response = notion.databases.query(
        database_id=db_id,
        page_size=5
    )
    
    results = response.get('results', [])
    print(f"\n✅ Success! Found {len(results)} pages (limited to 5)")
    print(f"Has more: {response.get('has_more', False)}")
    
    # Show first page's Korean title if exists
    if results:
        first_page = results[0]
        korean_prop = first_page['properties'].get('Korean', {})
        korean_title = korean_prop.get('title', [])
        if korean_title:
            print(f"First entry: {korean_title[0]['text']['content']}")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print(f"Error type: {type(e).__name__}")
