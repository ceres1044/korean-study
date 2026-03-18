import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from notion_sender import send_to_notion

load_dotenv('/Users/jingchen/code/koreanlearning/.env')


def update_session_date(path: Path):
    session_name = path.stem.replace('_analysis', '')
    parts = session_name.split('_')
    if len(parts) >= 3 and parts[-3].isdigit() and parts[-2].isdigit() and parts[-1].isdigit():
        mm, dd, yyyy = parts[-3], parts[-2], parts[-1]
        if len(yyyy) == 4:
            session_date = f"{yyyy}-{mm.zfill(2)}-{dd.zfill(2)}"
            data = json.loads(path.read_text(encoding='utf-8'))
            data['session_date'] = session_date
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
            return session_date
    return None


analysis_files = [
    Path('output/Korean_Class_11_10_2025_analysis.json'),
    Path('output/Korean_Class_11_17_2025_analysis.json'),
]

for path in analysis_files:
    if not path.exists():
        print(f"Missing {path}")
        continue
    new_date = update_session_date(path)
    print(f"Updated {path.name} session_date -> {new_date}")

    stats = send_to_notion(
        path,
        os.getenv('NOTION_TOKEN'),
        os.getenv('NOTION_DATABASE_ID'),
        skip_duplicates=True,
        min_confidence=os.getenv('CONFIDENCE_THRESHOLD', 'medium')
    )
    print(f"Notion: {stats.get('success', 0)} sent, {stats.get('failed', 0)} failed")
