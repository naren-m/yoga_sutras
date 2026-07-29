#!/usr/bin/env python3
"""
Populates the database with Yoga Sutras data from the scraped JSON file.

This script:
1. Reads data/yoga_sutras.json (created by scrape_text.py)
2. Creates Text, TextSection, and TextBlock records
3. Is idempotent - can be run multiple times safely

Run this after scrape_text.py has created the JSON file.
"""
import os
import sys
import json

# Add backend to path for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, 'backend')
sys.path.insert(0, BACKEND_DIR)

DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
INPUT_FILE = os.path.join(DATA_DIR, 'yoga_sutras.json')
WORD_ANALYSIS_CACHE = os.path.join(DATA_DIR, 'word_analysis.json')


def load_word_analysis_cache() -> dict:
    """Load precomputed word_analysis (from enrich_word_analysis.py), keyed
    by block slug. Lets reseeds keep the enriched gloss without re-running
    the analyzer models."""
    if not os.path.exists(WORD_ANALYSIS_CACHE):
        return {}
    with open(WORD_ANALYSIS_CACHE, 'r', encoding='utf-8') as f:
        cache = json.load(f)
    print(f"  Loaded word_analysis cache: {len(cache)} entries")
    return cache


def load_json_data(filepath: str) -> dict:
    """Load and validate JSON data."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Input file not found: {filepath}\nRun scrape_text.py first.")

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Validate structure
    required_keys = ['slug', 'title', 'sections']
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Missing required key: {key}")

    return data


def populate_database(data: dict):
    """
    Populate database with text data.
    Uses upsert logic to be idempotent.
    """
    from app import create_app, db
    from app.models.text import Text, TextSection, TextBlock

    app = create_app()

    with app.app_context():
        # Get or create Text record
        text = db.session.query(Text).filter_by(slug=data['slug']).first()
        if text:
            print(f"Found existing text: {text.title}")
            # Update existing text
            text.title = data['title']
            text.description = data.get('description', '')

            # Remove existing sections and blocks (cascade delete)
            for section in text.sections:
                for block in section.blocks:
                    db.session.delete(block)
                db.session.delete(section)
            db.session.commit()
            print("  Cleared existing sections and blocks")
        else:
            text = Text(
                slug=data['slug'],
                title=data['title'],
                description=data.get('description', '')
            )
            db.session.add(text)
            db.session.commit()
            print(f"Created text: {text.title}")

        # Create sections and blocks
        word_analysis_cache = load_word_analysis_cache()
        total_blocks = 0
        for section_data in data['sections']:
            section = TextSection(
                text_id=text.id,
                slug=section_data['slug'],
                title=section_data['title'],
                order_in_text=section_data['order']
            )
            db.session.add(section)
            db.session.flush()  # Get section.id

            print(f"  Creating section: {section.title}")

            for block_data in section_data.get('blocks', []):
                block = TextBlock(
                    text_id=text.id,
                    section_id=section.id,
                    slug=block_data['slug'],
                    order_in_section=block_data['order'],
                    content=block_data.get('content', ''),
                    content_transliteration=block_data.get('transliteration', ''),
                    content_meaning=block_data.get('meaning', ''),
                    commentary=block_data.get('commentary'),
                    word_analysis=block_data.get('word_analysis')
                        or word_analysis_cache.get(block_data['slug'])
                )
                db.session.add(block)
                total_blocks += 1

            db.session.commit()
            print(f"    Added {len(section_data.get('blocks', []))} blocks")

        print(f"\nTotal: {len(data['sections'])} sections, {total_blocks} blocks")


def verify_data():
    """Verify the data was populated correctly."""
    from app import create_app, db
    from app.models.text import Text, TextSection, TextBlock

    app = create_app()

    with app.app_context():
        text = db.session.query(Text).filter_by(slug='yoga-sutras').first()
        if not text:
            print("ERROR: Text not found!")
            return False

        print(f"\nVerification:")
        print(f"  Text: {text.title}")
        print(f"  Sections: {len(text.sections)}")

        total_blocks = 0
        blocks_with_content = 0
        blocks_with_translation = 0

        for section in text.sections:
            section_blocks = db.session.query(TextBlock).filter_by(section_id=section.id).count()
            total_blocks += section_blocks

            # Count blocks with content
            for block in section.blocks:
                if block.content:
                    blocks_with_content += 1
                if block.content_meaning:
                    blocks_with_translation += 1

        print(f"  Total blocks: {total_blocks}")
        print(f"  Blocks with Sanskrit: {blocks_with_content}")
        print(f"  Blocks with translation: {blocks_with_translation}")

        # Verify counts match expected (196 sutras)
        expected_total = 51 + 55 + 56 + 34  # 196
        if total_blocks != expected_total:
            print(f"  WARNING: Expected {expected_total} blocks, got {total_blocks}")
            return False

        return True


def main():
    """Main function to populate database."""
    print("=" * 60)
    print("Yoga Sutras Database Populator")
    print("=" * 60)

    try:
        # Load JSON data
        print(f"\nLoading data from {INPUT_FILE}...")
        data = load_json_data(INPUT_FILE)
        print(f"  Found: {data['title']}")
        print(f"  Sections: {len(data['sections'])}")

        # Populate database
        print(f"\nPopulating database...")
        populate_database(data)

        # Verify
        print(f"\n{'=' * 60}")
        if verify_data():
            print("\nSUCCESS: Database populated correctly!")
        else:
            print("\nWARNING: Verification found issues")
            return False

        print("=" * 60)
        return True

    except FileNotFoundError as e:
        print(f"\nERROR: {e}")
        print("Run: python scripts/scrape_text.py")
        return False
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
