# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Sanskrit reading platform for the Yoga Sutras of Patanjali with sandhi splitting, dictionary lookup, and offline-first architecture. Designed to be generic enough to support any Sanskrit text (Text → Section → Block hierarchy).

## Commands

### Development
```bash
# Start full stack with Docker
docker-compose up --build

# Backend only (local)
cd backend && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python run.py  # Runs on localhost:5000

# Data population (run from project root)
pip install requests beautifulsoup4
python scripts/scrape_text.py      # Creates data/yoga_sutras.json
python scripts/seed_dictionaries.py # Downloads MW and Apte dictionaries to data/dictionaries/
```

### URLs
- Backend API: http://localhost:5000
- Frontend: http://localhost:3000

## Architecture

### Stack
- **Backend**: Flask + SQLAlchemy + SQLite
- **Frontend**: React + TypeScript + Tailwind (planned)
- **Sanskrit Processing**: Vidyut (sandhi splitting via `vidyut.cheda`)
- **Search**: rapidfuzz for fuzzy matching
- **Deployment**: Docker Compose, deployable to K8s

### Data Model (Generic Text Architecture)
```
Text (e.g., "Yoga Sutras")
  └── TextSection (e.g., "Samadhi Pada")
        └── TextBlock (e.g., Sutra 1.2)
              ├── content (Devanagari)
              ├── content_transliteration (IAST)
              ├── content_meaning (English)
              ├── word_analysis (JSON)
              └── commentary
```

This generic structure supports any Sanskrit text (Ramayana slokas, Bhagavad Gita, etc.).

### Key Services
- `SandhiService`: Wraps Vidyut Cheda for compound word splitting
- `DictionaryService`: Lookup in MW/Apte dictionaries (SLP1-keyed)
- `TextService`: CRUD for Text/Section/Block entities

### API Routes
| Route | Description |
|-------|-------------|
| `/api/texts/<slug>` | Get full text with sections |
| `/api/texts/<slug>/section/<section_slug>` | Get section with blocks |
| `/api/dictionary/<word>` | Dictionary lookup |
| `/api/split/<compound>` | Sandhi splitting |

## Data Sources
- **Sutras**: Scraped from shlokam.org (URL pattern: `shlokam.org/yogasutra/{pada}-{sutra}/`)
- **Dictionaries**: CDSL XML from Cologne (Monier-Williams, Apte)
- **Sandhi Data**: Vidyut requires `data/vidyut-data/` directory

## Sanskrit-Specific Notes
- Dictionary keys use **SLP1** encoding internally
- Display uses **Devanagari** and **IAST** transliteration
- `indic-transliteration` library handles script conversion
- Word analysis JSON stores both original forms and base forms for lookup

## File Locations
- Database: `data/yoga_sutras.db`
- Scraped text: `data/yoga_sutras.json`
- Dictionary XML: `data/dictionaries/{mw,apte}/`
- Vidyut data: `data/vidyut-data/`
