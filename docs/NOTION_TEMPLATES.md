# Notion Database Setup

Complete guide to creating and configuring the Notion database for Korean learning materials.

## Database Schema

### Main Properties

| Property | Type | Purpose | Example |
|----------|------|---------|---------|
| **Korean** | Title | The Korean word/phrase | 미신 (superstition) |
| **English** | Rich Text | English translation | Superstition |
| **Type** | Select | Category of item | Vocabulary, Phrase, Grammar, Correction |
| **Session Date** | Date | When the class occurred | 2025-11-24 |
| **Confidence** | Select | Extraction confidence | High, Medium, Low |
| **Example Usage** | Rich Text | Sample sentence with translation | "미신을 믿지 마세요" = "Don't believe in superstition" |
| **Notes** | Rich Text | Additional context | Used when discussing Korean traditions |
| **Tags** | Multi-select | Topic keywords | Culture, Daily Conversation, Intermediate |

## Setup Instructions

### 1. Create New Database in Notion

1. Create new page in Notion
2. Click **"+"** and select **"Database"**
3. Choose **"Table"** view
4. Name it: `Korean Learning Materials`

### 2. Configure Properties

Click **"✕"** on the default `Name` property and create these:

#### Korean (Title - Required)
- **Name:** Korean
- **Type:** Title
- **Description:** Korean word/phrase

#### English
- **Name:** English
- **Type:** Rich Text
- **Description:** English translation

#### Type
- **Name:** Type
- **Type:** Select
- **Options:**
  - Vocabulary (label color: Blue)
  - Phrase (label color: Green)
  - Grammar Point (label color: Purple)
  - Teacher Correction (label color: Red)

#### Session Date
- **Name:** Session Date
- **Type:** Date
- **Description:** YYYY-MM-DD format, automatically populated

#### Confidence
- **Name:** Confidence
- **Type:** Select
- **Options:**
  - High (label color: Green)
  - Medium (label color: Yellow)
  - Low (label color: Orange)

#### Example Usage
- **Name:** Example Usage
- **Type:** Rich Text
- **Description:** Example sentence with English translation

#### Notes
- **Name:** Notes
- **Type:** Rich Text
- **Description:** Context or explanation

#### Tags
- **Name:** Tags
- **Type:** Multi-select
- **Suggested options:**
  - Culture
  - Daily Conversation
  - Business
  - Grammar
  - Intermediate
  - Advanced
  - Pronunciation
  - Idioms

### 3. Create Views

#### View 1: All Items
- Filter: None
- Sort: Session Date (newest first)
- Group by: Type

#### View 2: By Type
- Filter: None
- Sort: Confidence (high first)
- Group by: Type

#### View 3: Recent (This Week)
- Filter: Session Date is within last 7 days
- Sort: Session Date (newest first)

#### View 4: Vocabulary Only
- Filter: Type = Vocabulary
- Sort: Session Date (newest first)

#### View 5: Teacher Corrections
- Filter: Type = Teacher Correction
- Sort: Session Date (newest first)

### 4. Automation Rules (Optional)

Create automations for better organization:

**Auto-tag by Type:**
- When: Type is set to "Idioms"
- Then: Add tag "Idioms"

**Confidence Badge:**
- When: Confidence is "High"
- Then: Add emoji 🌟 to Korean property

## Data Structure Examples

### Vocabulary Entry
```
Korean:        미신
English:       Superstition
Type:          Vocabulary
Session Date:  2025-11-24
Confidence:    High
Example Usage: 미신을 믿지 마세요. = "Don't believe in superstition"
Notes:         Common word, used in cultural discussions
Tags:          Culture, Intermediate
```

### Phrase Entry
```
Korean:        장보러 가다
English:       To go shopping for groceries
Type:          Phrase
Session Date:  2025-11-24
Confidence:    Medium
Example Usage: "오늘 장보러 가야 해요." = "I need to go shopping today"
Notes:         Commonly used in daily conversation
Tags:          Daily Conversation, Common Phrases
```

### Grammar Entry
```
Korean:        했더니
English:       Past tense ending expressing surprise/realization
Type:          Grammar Point
Session Date:  2025-11-24
Confidence:    High
Example Usage: "여기 갔더니 친구가 있었어요" = "When I went there, my friend was there"
Notes:         Often used to describe unexpected situations
Tags:          Grammar, Intermediate
```

### Correction Entry
```
Korean:        이하숙집에서 지내려고 해요
English:       I'm planning to stay at this boarding house
Type:          Teacher Correction
Session Date:  2025-11-24
Confidence:    High
Example Usage: Corrected from: "이 하숙집에서 지내려고 해요"
Notes:         Spacing issue - proper compound noun usage
Tags:          Grammar, Common Mistakes
```

## API Integration

The system uses Notion API v1 with these endpoints:

### Query Database
```
POST /v1/databases/{database_id}/query
```
Used for deduplication checks to prevent duplicate entries.

### Create Page
```
POST /v1/pages
```
Used to add new learning items.

### Headers Required
```
Authorization: Bearer {NOTION_TOKEN}
Notion-Version: 2022-06-28
Content-Type: application/json
```

## Permissions & Sharing

### For Auto-Fetch to Work
1. Create **Notion Integration**
2. In Notion, open database settings
3. Click **"Connections"** → **"Manage connections"**
4. Search for your integration
5. Click **"Connect"**
6. Grant read/write permissions

### Deduplication Strategy
- Queries existing Korean entries
- Skips items with matching Korean text
- Prevents 4-5x duplication from re-uploads

## Maintenance

### Regular Tasks

**Weekly:**
- Review low-confidence items
- Add tags/notes for context
- Update examples

**Monthly:**
- Check for orphaned entries
- Update session date filters
- Archive old corrections

### Cleanup

Run cleanup script to remove duplicates:
```bash
python scripts/cleanup_duplicates.py
```

## Example Database Views

### Dashboard View
```
| Korean | English | Type | Confidence | Date |
|--------|---------|------|------------|------|
| 미신 | Superstition | Vocabulary | High | 2025-11-24 |
| 장보러 가다 | Go shopping | Phrase | Medium | 2025-11-24 |
| 했더니 | Past tense | Grammar | High | 2025-11-24 |
```

### Stats
```
Total Items:        249
├─ Vocabulary:      128
├─ Phrases:         75
├─ Grammar:         32
└─ Corrections:     14

By Confidence:
├─ High:           195
├─ Medium:          40
└─ Low:             14

This Week:          58 new items
```

## Troubleshooting

**Items not uploading?**
- Verify database ID is correct
- Check API token permissions
- Ensure integration is connected

**Duplicates still appearing?**
- Run cleanup script
- Verify dedup logic

**Missing properties?**
- Recreate missing properties
- Re-test with `python auto_fetch.py --reset`

## Next Steps

1. ✅ Create database (you are here)
2. 🔧 Configure system settings
3. 🧪 Run first test
4. 📊 Monitor uploads
5. 📚 Review learning materials

---

Need help? See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
