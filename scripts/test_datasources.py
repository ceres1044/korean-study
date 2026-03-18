from notion_client import Client
import os
from dotenv import load_dotenv

load_dotenv('/Users/jingchen/code/koreanlearning/.env')

notion = Client(auth=os.getenv('NOTION_TOKEN'))
db_id = os.getenv('NOTION_DATABASE_ID')

print(f"Testing data_sources on DB: {db_id}")
print(f"data_sources methods: {[m for m in dir(notion.data_sources) if not m.startswith('_')]}")

try:
    if hasattr(notion.data_sources, 'query'):
        response = notion.data_sources.query(
            data_source_id=db_id,
            page_size=5
        )
        
        results = response.get('results', [])
        print(f"\n✅ Success with data_sources.query()! Found {len(results)} pages")
        
        if results:
            first_page = results[0]
            korean_prop = first_page['properties'].get('Korean', {})
            korean_title = korean_prop.get('title', [])
            if korean_title:
                print(f"First entry: {korean_title[0]['text']['content']}")
    else:
        print("data_sources.query() not available")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
