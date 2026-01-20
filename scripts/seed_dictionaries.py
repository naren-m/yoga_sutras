import os
import requests
import zipfile
import io

DATA_DIR = "data/dictionaries"

# Data from Ambuda's libraries.yaml (cached from earlier step)
DICTIONARIES = [
    {
        "name": "Monier",
        "title": "Monier-Williams Sanskrit-English Dictionary (1899)",
        "slug": "mw",
        "url": "https://www.sanskrit-lexicon.uni-koeln.de/scans/MWScan/2020/downloads/mwxml.zip",
        "type": "ZIP"
    },
    {
        "name": "Apte",
        "title": "Apte Practical Sanskrit-English Dictionary (1890)",
        "slug": "apte",
        "url": "https://www.sanskrit-lexicon.uni-koeln.de/scans/AP90Scan/2020/downloads/ap90xml.zip",
        "type": "ZIP"
    }
]

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def download_and_extract(url, target_dir):
    print(f"Downloading {url}...")
    try:
        r = requests.get(url, stream=True)
        r.raise_for_status()
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall(target_dir)
        print(f"Extracted to {target_dir}")
    except Exception as e:
        print(f"Error processing {url}: {e}")

def main():
    ensure_dir(DATA_DIR)
    
    for d in DICTIONARIES:
        print(f"Processing {d['title']}...")
        target_path = os.path.join(DATA_DIR, d['slug'])
        ensure_dir(target_path)
        
        if d['type'] == 'ZIP':
            download_and_extract(d['url'], target_path)
        else:
            print(f"Unsupported type {d['type']} for {d['name']}")

if __name__ == "__main__":
    main()
