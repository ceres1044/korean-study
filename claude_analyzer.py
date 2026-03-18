#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Claude Analyzer for Korean Learning
============================================
- Aggressive extraction of ALL vocabulary/phrases
- English translation (not Chinese)
- 2 daily usage examples per item
- No session summary
- Teacher corrections categorized properly
"""

import json
import anthropic
from typing import Dict, Any


def analyze_transcript(transcript: str, session_date: str, api_key: str,
                      teacher_name: str = "Cathy", student_name: str = "Jing") -> Dict[str, Any]:
    """
    Analyze Korean learning transcript with Claude
    
    Returns dict with extracted learning materials in English
    """
    
    client = anthropic.Anthropic(api_key=api_key)
    
    prompt = f"""You are analyzing a Korean language learning conversation between:
- **{teacher_name}** (teacher): Speaks fluently, teaches, corrects mistakes
- **{student_name}** (student): Learning Korean, makes mistakes, asks questions

SESSION DATE: {session_date}

TRANSCRIPT:
{transcript}

---

YOUR TASK: Extract EVERY piece of Korean language content that {student_name} should learn.

## EXTRACTION RULES (AGGRESSIVE):

### 1. VOCABULARY (Individual words)
Extract EVERY Korean word that:
- Teacher explicitly teaches
- Student doesn't know or uses incorrectly
- Appears in corrections
- Is interesting or useful for daily conversation

For each word provide:
- Korean word (in Hangul)
- English meaning
- Part of speech (noun/verb/adjective/adverb)
- 2 NEW daily usage example sentences (CREATE these - they should NOT be from the transcript)
  * Examples must be realistic daily conversation scenarios
  * Keep examples simple and practical
  * Show natural usage in context

### 2. PHRASES & EXPRESSIONS (Multi-word)
Extract EVERY phrase/expression that:
- Teacher teaches as a complete unit
- Is a common daily expression
- Is an idiomatic phrase
- Would be useful in conversation

For each phrase provide:
- Korean phrase (in Hangul)
- English meaning
- Usage context (when/how to use it)
- 2 NEW daily usage example sentences (CREATE these)
  * Show different situations where this phrase works
  * Make them practical for daily life

### 3. GRAMMAR PATTERNS
Extract EVERY grammar pattern that:
- Teacher explains
- Appears in corrections
- Is a sentence ending or connector
- Uses grammatical markers like -(으)ㄴ, -는, -던, -아/어서, etc.

For each pattern provide:
- Pattern structure (e.g., "Verb stem + -(으)ㄴ 적이 있다")
- English explanation
- When to use it
- 2 NEW daily usage example sentences (CREATE these)
  * Show the pattern in action
  * Use different verbs/contexts

### 4. TEACHER CORRECTIONS (CRITICAL!)
Extract EVERY time teacher corrects student:
- What {student_name} said (incorrect Korean)
- What {teacher_name} corrected it to (correct Korean)
- What type it is: vocabulary/phrase/grammar/pronunciation
- English explanation of the correction
- 2 NEW example sentences showing CORRECT usage (CREATE these)

## EXAMPLE SENTENCE REQUIREMENTS:
- Must be NEW (not from transcript)
- Must be daily conversation scenarios
- Keep it simple and natural
- Show practical usage
- Both Korean and English

Example format:
```
"examples": [
  {{"korean": "오늘 날씨가 정말 좋네요.", "english": "The weather is really nice today."}},
  {{"korean": "내일 시간 있으면 영화 볼래요?", "english": "If you have time tomorrow, do you want to watch a movie?"}}
]
```

## OUTPUT FORMAT (JSON ONLY):

{{
  "session_date": "{session_date}",
  "total_items_extracted": 0,
  "learning_materials": [
    {{
      "korean": "Korean content here",
      "english": "English translation",
      "type": "vocabulary|phrase|grammar|correction",
      "category": "noun|verb|adjective|daily_expression|sentence_pattern|etc",
      "context_from_class": "Brief note about how this appeared in class",
      "examples": [
        {{"korean": "example sentence 1", "english": "translation 1"}},
        {{"korean": "example sentence 2", "english": "translation 2"}}
      ],
      "correction_details": {{
        "incorrect": "What student said (if this is a correction)",
        "correct": "What teacher corrected to",
        "explanation": "Why the correction was needed"
      }},
      "confidence": "high|medium|low",
      "notes": "Additional helpful information"
    }}
  ],
  "statistics": {{
    "vocabulary_count": 0,
    "phrase_count": 0,
    "grammar_count": 0,
    "correction_count": 0
  }}
}}

## CRITICAL RULES:
- ✅ Extract EVERYTHING - be comprehensive, not selective
- ✅ Create 2 NEW example sentences for EVERY item
- ✅ All translations in ENGLISH (not Chinese)
- ✅ Categorize corrections by type (vocabulary/phrase/grammar)
- ✅ Mark confidence: high (explicitly taught), medium (used clearly), low (ambiguous)
- ❌ NO session summary
- ❌ NO made-up Korean from transcript (examples must be NEW)
- ❌ NO Chinese translations

Analyze the transcript now and return ONLY valid JSON (no markdown, no other text).
"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=16000,  # Increased for comprehensive analysis with many items
            temperature=0.3,  # Slightly creative for example generation
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Extract JSON from response
        content = response.content[0].text.strip()
        
        # Remove markdown code blocks if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        
        analysis = json.loads(content)
        
        # Validate structure
        if "learning_materials" not in analysis:
            raise ValueError("Missing learning_materials in analysis")
        
        # Update total count
        analysis["total_items_extracted"] = len(analysis.get("learning_materials", []))
        
        return analysis
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        print(f"Response content: {content[:500]}...")
        return None
    except Exception as e:
        print(f"❌ Analysis error: {e}")
        return None


def save_analysis(analysis: Dict[str, Any], output_path: str) -> bool:
    """Save analysis to JSON file"""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ Save error: {e}")
        return False
