#!/usr/bin/env python3
"""
Downloads and processes Sanskrit dictionaries from CDSL (Cologne Digital Sanskrit Lexicon).

This script:
1. Downloads MW (Monier-Williams) and Apte dictionary XML files
2. Parses the XML and extracts entries
3. Populates the database with DictionaryEntry records

Dictionary keys are stored in SLP1 encoding for standardized lookup.
"""
import os
import sys
import requests
import zipfile
import io
import xml.etree.ElementTree as ET
from pathlib import Path

# Add backend to path for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, 'backend')
sys.path.insert(0, BACKEND_DIR)

DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
DICT_DIR = os.path.join(DATA_DIR, 'dictionaries')

# Dictionary configurations
DICTIONARIES = [
    {
        "name": "Monier-Williams",
        "slug": "mw",
        "title": "Monier-Williams Sanskrit-English Dictionary (1899)",
        "url": "https://www.sanskrit-lexicon.uni-koeln.de/scans/MWScan/2020/downloads/mwxml.zip",
        "xml_pattern": "mw.xml",
    },
    {
        "name": "Apte",
        "slug": "apte",
        "title": "Apte Practical Sanskrit-English Dictionary (1890)",
        "url": "https://www.sanskrit-lexicon.uni-koeln.de/scans/AP90Scan/2020/downloads/ap90xml.zip",
        "xml_pattern": "ap90.xml",
    }
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 YogaSutras-Sanskrit-Platform/1.0"
}


def ensure_dir(path: str):
    """Create directory if it doesn't exist."""
    Path(path).mkdir(parents=True, exist_ok=True)


def download_and_extract(url: str, target_dir: str) -> bool:
    """Download a ZIP file and extract it to target directory."""
    print(f"Downloading {url}...")
    try:
        response = requests.get(url, headers=HEADERS, stream=True, timeout=120)
        response.raise_for_status()

        z = zipfile.ZipFile(io.BytesIO(response.content))
        z.extractall(target_dir)
        print(f"  Extracted to {target_dir}")
        return True
    except Exception as e:
        print(f"  Error: {e}")
        return False


def find_xml_file(directory: str, pattern: str) -> str:
    """Find XML file matching pattern in directory (recursive)."""
    for root, dirs, files in os.walk(directory):
        for f in files:
            if pattern in f.lower() or f.lower().endswith('.xml'):
                return os.path.join(root, f)
    return None


def parse_mw_xml(xml_path: str) -> list:
    """
    Parse Monier-Williams XML format.
    Returns list of (key, value) tuples.
    """
    print(f"  Parsing {xml_path}...")
    entries = []

    try:
        # Parse iteratively to handle large files
        context = ET.iterparse(xml_path, events=('end',))
        count = 0

        for event, elem in context:
            if elem.tag == 'H1' or elem.tag == 'H2' or elem.tag == 'H3' or elem.tag == 'H4':
                # Find the key element
                key_elem = elem.find('.//key1')
                if key_elem is not None and key_elem.text:
                    key = key_elem.text.strip()

                    # Get the full text content as definition
                    # Convert element to string to preserve inner markup
                    value = ET.tostring(elem, encoding='unicode', method='text')
                    value = ' '.join(value.split())  # Normalize whitespace

                    if key and value:
                        entries.append((key, value))
                        count += 1

                        if count % 10000 == 0:
                            print(f"    Processed {count} entries...")

                # Clear element to save memory
                elem.clear()

        print(f"  Found {len(entries)} entries")
        return entries

    except ET.ParseError as e:
        print(f"  XML Parse Error: {e}")
        # Try alternative approach with string parsing
        return parse_xml_fallback(xml_path)


def parse_apte_xml(xml_path: str) -> list:
    """
    Parse Apte dictionary XML format.
    Returns list of (key, value) tuples.
    """
    print(f"  Parsing {xml_path}...")
    entries = []

    try:
        context = ET.iterparse(xml_path, events=('end',))
        count = 0

        for event, elem in context:
            # Apte uses similar H1/H2/H3/H4 structure
            if elem.tag in ('H1', 'H2', 'H3', 'H4', 'H1A', 'H1B', 'H2A', 'H2B'):
                key_elem = elem.find('.//key1')
                if key_elem is not None and key_elem.text:
                    key = key_elem.text.strip()
                    value = ET.tostring(elem, encoding='unicode', method='text')
                    value = ' '.join(value.split())

                    if key and value:
                        entries.append((key, value))
                        count += 1

                        if count % 10000 == 0:
                            print(f"    Processed {count} entries...")

                elem.clear()

        print(f"  Found {len(entries)} entries")
        return entries

    except ET.ParseError as e:
        print(f"  XML Parse Error: {e}")
        return parse_xml_fallback(xml_path)


def parse_xml_fallback(xml_path: str) -> list:
    """
    Fallback XML parser using regex for malformed XML.
    """
    import re
    print(f"  Using fallback parser...")
    entries = []

    try:
        with open(xml_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Pattern to find <key1>...</key1> and surrounding content
        pattern = r'<(H[1-4][AB]?)(?:[^>]*)>.*?<key1>([^<]+)</key1>.*?</\1>'
        matches = re.findall(pattern, content, re.DOTALL)

        for tag, key in matches:
            # Find the full entry for this key
            entry_pattern = rf'<{tag}[^>]*>.*?<key1>{re.escape(key)}</key1>(.*?)</{tag}>'
            entry_match = re.search(entry_pattern, content, re.DOTALL)
            if entry_match:
                value = re.sub(r'<[^>]+>', ' ', entry_match.group(1))
                value = ' '.join(value.split())
                entries.append((key.strip(), value))

        print(f"  Found {len(entries)} entries (fallback)")
        return entries

    except Exception as e:
        print(f"  Fallback parser error: {e}")
        return []


def populate_database(dictionary_config: dict, entries: list):
    """
    Populate database with dictionary entries.
    Uses upsert logic to be idempotent.
    """
    from app import create_app, db
    from app.models.dictionary import Dictionary, DictionaryEntry

    app = create_app()

    with app.app_context():
        # Get or create dictionary record
        dictionary = db.session.query(Dictionary).filter_by(slug=dictionary_config["slug"]).first()
        if not dictionary:
            dictionary = Dictionary(
                slug=dictionary_config["slug"],
                title=dictionary_config["title"]
            )
            db.session.add(dictionary)
            db.session.commit()
            print(f"  Created dictionary: {dictionary_config['title']}")
        else:
            print(f"  Using existing dictionary: {dictionary_config['title']}")
            # Clear existing entries for fresh load
            db.session.query(DictionaryEntry).filter_by(dictionary_id=dictionary.id).delete()
            db.session.commit()
            print(f"  Cleared existing entries")

        # Batch insert entries
        batch_size = 1000
        total = len(entries)

        for i in range(0, total, batch_size):
            batch = entries[i:i + batch_size]
            for key, value in batch:
                entry = DictionaryEntry(
                    dictionary_id=dictionary.id,
                    key=key,
                    value=value
                )
                db.session.add(entry)

            db.session.commit()
            print(f"    Inserted {min(i + batch_size, total)}/{total} entries")

        print(f"  Completed: {total} entries for {dictionary_config['slug']}")


def process_dictionary(config: dict) -> bool:
    """Process a single dictionary: download, parse, and populate."""
    print(f"\n{'=' * 60}")
    print(f"Processing: {config['name']}")
    print(f"{'=' * 60}")

    # Ensure directories exist
    dict_path = os.path.join(DICT_DIR, config['slug'])
    ensure_dir(dict_path)

    # Download if needed
    xml_file = find_xml_file(dict_path, config['xml_pattern'])
    if not xml_file:
        if not download_and_extract(config['url'], dict_path):
            print(f"  Failed to download {config['name']}")
            return False
        xml_file = find_xml_file(dict_path, config['xml_pattern'])

    if not xml_file:
        print(f"  Could not find XML file for {config['name']}")
        return False

    print(f"  Using XML file: {xml_file}")

    # Parse XML
    if config['slug'] == 'mw':
        entries = parse_mw_xml(xml_file)
    else:
        entries = parse_apte_xml(xml_file)

    if not entries:
        print(f"  No entries found for {config['name']}")
        return False

    # Populate database
    populate_database(config, entries)
    return True


def main():
    """Main function to process all dictionaries."""
    print("=" * 60)
    print("Sanskrit Dictionary Seeder")
    print("=" * 60)

    # Ensure data directories exist
    ensure_dir(DATA_DIR)
    ensure_dir(DICT_DIR)

    success_count = 0
    for config in DICTIONARIES:
        try:
            if process_dictionary(config):
                success_count += 1
        except Exception as e:
            print(f"Error processing {config['name']}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'=' * 60}")
    print(f"Completed: {success_count}/{len(DICTIONARIES)} dictionaries processed")
    print(f"{'=' * 60}")

    return success_count == len(DICTIONARIES)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
