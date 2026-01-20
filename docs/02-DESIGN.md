# Technical Design Document (TDD)

# Yoga Sutras of Patanjali - Searchable Digital Library

**Version:** 1.0  
**Date:** January 11, 2026  
**Project Code:** YOGA-SUTRAS-LIB  
**Status:** Draft for Review

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture Design](#2-architecture-design)
3. [Data Design](#3-data-design)
4. [API Design](#4-api-design)
5. [Frontend Design](#5-frontend-design)
6. [Component Specifications](#6-component-specifications)
7. [Implementation Guide](#7-implementation-guide)
8. [Deployment](#8-deployment)
9. [Testing Strategy](#9-testing-strategy)

---

## 1. System Overview

### 1.1 Purpose

This document provides the technical design and implementation details for building the Yoga Sutras Digital Library application. It serves as a guide for developers (human or AI agents) to implement the system.

### 1.2 Technology Stack

| Layer        | Technology            | Version | Purpose           |
| ------------ | --------------------- | ------- | ----------------- |
| **Backend**  | Python                | 3.10+   | Server-side logic |
|              | Flask                 | 3.0+    | Web framework     |
|              | SQLAlchemy            | 2.0+    | ORM               |
|              | Vidyut                | latest  | Sandhi & Dicts    |
|              | indic-transliteration | latest  | Script conversion |
|              | rapidfuzz             | latest  | Fuzzy search      |
| **Frontend** | React                 | 18+     | UI framework      |
|              | TypeScript            | 5.0+    | Type safety       |
|              | Tailwind CSS          | 3.0+    | Styling           |
|              | React Query           | 5.0+    | Data fetching     |
| **Database** | SQLite                | 3.x     | Data storage      |
| **DevOps**   | Docker                | latest  | Containerization  |
| **DevOps**   | Docker                | latest  | Containerization  |


### 1.3 System Context Diagram

```
└─────────┼─────────────────┼─────────────────────────────────────────┘
          │                 │
          ▼                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      YOGA SUTRAS APPLICATION                        │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                     FLASK BACKEND                          │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │    │
│  │  │  Sutra   │ │  Search  │ │Dictionary│ │   Sandhi     │  │    │
│  │  │  Service │ │  Service │ │ Service  │ │   Service    │  │    │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────┬───────┘  │    │
│  │       │            │            │              │          │    │
│  │       └────────────┴─────┬──────┴──────────────┘          │    │
│  │                          │                                │    │
│  │                    ┌─────▼─────┐                          │    │
│  │                    │  SQLite   │                          │    │
│  │                    │  Database │                          │    │
│  │                    └───────────┘                          │    │
│  └────────────────────────────────────────────────────────────┘    │
│                              │                                      │
│                         REST API                                    │
│                              │                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                    REACT FRONTEND                          │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │    │
│  │  │  Sutra   │ │  Search  │ │Dictionary│ │  Navigation  │  │    │
│  │  │  Display │ │   Bar    │ │  Panel   │ │   Components │  │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │    │
│  └────────────────────────────────────────────────────────────┘    │
│                              │                                      │
└──────────────────────────────┼──────────────────────────────────────┘
                               │
                          ┌────▼────┐
                          │  User   │
                          │ Browser │
                          └─────────┘
```

---

## 2. Architecture Design

### 2.1 High-Level Architecture

The application follows a **3-tier architecture**:

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION TIER                        │
│                    (React Frontend)                         │
│  - Single Page Application (SPA)                           │
│  - Responsive UI with Tailwind CSS                         │
│  - Client-side routing with React Router                   │
└─────────────────────────────────────────────────────────────┘
                              │
                         HTTP/JSON
                              │
┌─────────────────────────────────────────────────────────────┐
│                    APPLICATION TIER                         │
│                    (Flask Backend)                          │
│  - RESTful API endpoints                                   │
│  - Business logic services                                 │
│  - Data validation and transformation                      │
└─────────────────────────────────────────────────────────────┘
                              │
                        SQLAlchemy
                              │
┌─────────────────────────────────────────────────────────────┐
│                       DATA TIER                             │
│                      (SQLite DB)                            │
│  - Sutras table                                            │
│  - Dictionary entries table                                │
│  - Search index (FTS5)                                     │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Directory Structure

```
yoga-sutras/
├── backend/
│   ├── app/
│   │   ├── __init__.py           # Flask app factory
│   │   ├── config.py             # Configuration
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── sutra.py          # Sutra model
│   │   │   └── dictionary.py     # Dictionary model
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── text_service.py       # Generic text service
│   │   │   ├── search_service.py
│   │   │   ├── dictionary_service.py
│   │   │   └── sandhi_service.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── text_routes.py        # Generic text routes
│   │   │   ├── search_routes.py
│   │   │   └── dictionary_routes.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── transliteration.py
│   │       └── text_processing.py
│   ├── scripts/
│   │   ├── scrape_sutras.py      # Scraper for shlokam.org
│   │   ├── setup_dictionary.py   # Dictionary import
│   │   └── init_db.py            # Database initialization
│   ├── tests/
│   │   ├── test_sutra_service.py
│   │   ├── test_search_service.py
│   │   └── test_dictionary_service.py
│   ├── requirements.txt
│   └── run.py                    # Entry point
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── SutraDisplay.tsx
│   │   │   ├── SearchBar.tsx
│   │   │   ├── DictionaryPanel.tsx
│   │   │   ├── ClickableWord.tsx
│   │   │   ├── PadaNavigation.tsx
│   │   │   └── Layout.tsx
│   │   ├── pages/
│   │   │   ├── HomePage.tsx
│   │   │   ├── SutraPage.tsx
│   │   │   ├── SearchResultsPage.tsx
│   │   │   └── AboutPage.tsx
│   │   ├── hooks/
│   │   │   ├── useSutra.ts
│   │   │   ├── useSearch.ts
│   │   │   └── useDictionary.ts
│   │   ├── services/
│   │   │   └── api.ts
│   │   ├── types/
│   │   │   └── index.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── data/
│   ├── sutras.json               # Scraped sutra data
│   ├── yoga_sutras.db            # SQLite database
│   └── dictionaries/             # CDSL dictionary files
│
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
│
├── docs/
│   ├── 01-REQUIREMENTS.md
│   ├── 02-DESIGN.md
│   └── API.md
│
└── README.md
```

```

### 2.4 Data Acquisition Strategy

1.  **Texts (Sutras/Slokas)**:
    -   **Source**: [shlokam.org](https://shlokam.org/) (for Yoga Sutras)
    -   **Method**: Custom scraper (`scripts/scrape_text.py`)
    -   **Storage**: Normalize to `Text`/`Section`/`Block` format in SQLite.

2.  **Dictionaries**:
    -   **Source**: [ambuda-org/dictionaries](https://github.com/ambuda-org/dictionaries/blob/main/src/dictionaries.yaml)
    -   **Method**: Download dictionary files defined in `dictionaries.yaml`.
    -   **Storage**: Parse into `Dictionary` / `DictionaryEntry` tables.
    -   **Role of Vidyut**: Used for *Sandhi Splitting* (linguistic processing), not as the dictionary data source itself.

### 2.5 Component Interaction Flow

#### 2.3.1 Sutra Display Flow

```
User clicks Sutra 1.2
        │
        ▼
┌─────────────────┐
│ React Router    │
│ /sutra/1.2      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌─────────────────┐
│ SutraPage.tsx   │─────▶│ useSutra hook   │
└─────────────────┘      └────────┬────────┘
                                  │
                         GET /api/sutras/1.2
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ Flask Backend   │
                         │ sutra_routes.py │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ sutra_service   │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ SQLite DB       │
                         │ SELECT * FROM   │
                         │ sutras WHERE    │
                         │ id = '1.2'      │
                         └────────┬────────┘
                                  │
                         JSON Response
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ SutraDisplay    │
                         │ component       │
                         └─────────────────┘
```

#### 2.3.2 Word Click → Dictionary Lookup Flow

```
User clicks word "योगश्चित्तवृत्तिनिरोधः"
        │
        ▼
┌─────────────────┐
│ ClickableWord   │
│ onClick handler │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌─────────────────┐
│ DictionaryPanel │─────▶│ useExamples     │
│ (Sandhi mode)   │      │ (Sandhi Split)  │
└─────────────────┘      └────────┬────────┘
                                  │
                         GET /api/split/योगश्चित्तवृत्तिनिरोधः
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ sandhi_service  │
                         │ (Vidyut Cheda)  │
                         └────────┬────────┘
                                  │
                         JSON Response
                         {
                           "original": "योगश्चित्तवृत्तिनिरोधः",
                           "splits": ["योगः", "चित्त", "वृत्ति", "निरोधः"]
                         }
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ DictionaryPanel │
                         │ displays splits │
                         └────────┬────────┘
                                  │
                         User clicks "योगः"
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ Dictionary Lookup│
                         │ (Vidyut Kosha)   │
                         └─────────────────┘
```

---

## 3. Data Design

### 3.1 Database Schema

```sql
-- Sutras table
CREATE TABLE sutras (
    id TEXT PRIMARY KEY,              -- e.g., "1.2"
    pada INTEGER NOT NULL,            -- 1-4
    sutra_number INTEGER NOT NULL,    -- number within pada
    sanskrit TEXT NOT NULL,           -- Devanagari text
    transliteration TEXT NOT NULL,    -- IAST
    translation_en TEXT NOT NULL,     -- English translation
    commentary TEXT,                  -- Optional commentary
    word_analysis JSON,               -- Pre-analyzed words
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(pada, sutra_number)
);

-- Full-text search index for sutras
CREATE VIRTUAL TABLE sutras_fts USING fts5(
    id,
    sanskrit,
    transliteration,
    translation_en,
    content='sutras',
    content_rowid='rowid'
);

-- Triggers to keep FTS index in sync
CREATE TRIGGER sutras_ai AFTER INSERT ON sutras BEGIN
    INSERT INTO sutras_fts(rowid, id, sanskrit, transliteration, translation_en)
    VALUES (new.rowid, new.id, new.sanskrit, new.transliteration, new.translation_en);
END;

CREATE TRIGGER sutras_ad AFTER DELETE ON sutras BEGIN
    INSERT INTO sutras_fts(sutras_fts, rowid, id, sanskrit, transliteration, translation_en)
    VALUES ('delete', old.rowid, old.id, old.sanskrit, old.transliteration, old.translation_en);
END;

CREATE TRIGGER sutras_au AFTER UPDATE ON sutras BEGIN
    INSERT INTO sutras_fts(sutras_fts, rowid, id, sanskrit, transliteration, translation_en)
    VALUES ('delete', old.rowid, old.id, old.sanskrit, old.transliteration, old.translation_en);
    INSERT INTO sutras_fts(rowid, id, sanskrit, transliteration, translation_en)
    VALUES (new.rowid, new.id, new.sanskrit, new.transliteration, new.translation_en);
END;

-- Dictionary entries table
CREATE TABLE dictionary_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    headword TEXT NOT NULL,           -- Devanagari
    headword_slp1 TEXT NOT NULL,      -- SLP1 for indexing
    headword_iast TEXT NOT NULL,      -- IAST for display
    dictionary_code TEXT NOT NULL,    -- MW, AP90, AK, etc.
    definition TEXT NOT NULL,         -- Definition text
    grammar TEXT,                     -- Grammatical info
    etymology TEXT,                   -- Etymology if available
    
    UNIQUE(headword_slp1, dictionary_code)
);

-- Index for fast lookups
CREATE INDEX idx_dict_headword ON dictionary_entries(headword);
CREATE INDEX idx_dict_slp1 ON dictionary_entries(headword_slp1);
CREATE INDEX idx_dict_code ON dictionary_entries(dictionary_code);

-- Padas reference table
CREATE TABLE padas (
    id INTEGER PRIMARY KEY,
    name_en TEXT NOT NULL,
    name_sanskrit TEXT NOT NULL,
    name_iast TEXT NOT NULL,
    description TEXT,
    sutra_count INTEGER NOT NULL
);

-- Initial pada data
INSERT INTO padas VALUES
    (1, 'Samadhi Pada', 'समाधिपाद', 'Samādhi Pāda', 'On Contemplation', 51),
    (2, 'Sadhana Pada', 'साधनपाद', 'Sādhana Pāda', 'On Practice', 55),
    (3, 'Vibhuti Pada', 'विभूतिपाद', 'Vibhūti Pāda', 'On Powers', 56),
    (4, 'Kaivalya Pada', 'कैवल्यपाद', 'Kaivalya Pāda', 'On Liberation', 34);
```

### 3.2 SQLAlchemy Models
(Generic Architecture for any Text)

```python
# backend/app/models/base.py

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

def pk():
    """Define a simple integer primary key."""
    return Column(Integer, primary_key=True, autoincrement=True)

def foreign_key(field: str, nullable=False):
    """Define a simple foreign key."""
    return Column(Integer, ForeignKey(field), nullable=nullable, index=True)
```

```python
# backend/app/models/text.py

from sqlalchemy import Column, String, Integer, Text, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base, pk, foreign_key

class Text(Base):
    """Represents a complete work (e.g., 'Yoga Sutras', 'Ramayana')."""
    __tablename__ = 'texts'
    
    id = pk()
    slug = Column(String, unique=True, index=True, nullable=False) # e.g. "yoga-sutras"
    title = Column(String, nullable=False)
    description = Column(Text)
    
    sections = relationship("TextSection", backref="text", cascade="delete")

class TextSection(Base):
    """A division within a text (e.g., 'Pada', 'Kanda', 'Chapter')."""
    __tablename__ = 'text_sections'
    
    id = pk()
    text_id = foreign_key("texts.id")
    slug = Column(String, nullable=False) # e.g. "1", "samadhi-pada"
    title = Column(String, nullable=False)
    order_in_text = Column(Integer, nullable=False)
    
    blocks = relationship("TextBlock", backref="section", cascade="delete")

class TextBlock(Base):
    """The atomic unit of content (e.g., a single Sutra, Sloka, or Verse)."""
    __tablename__ = 'text_blocks'
    
    id = pk()
    text_id = foreign_key("texts.id")
    section_id = foreign_key("text_sections.id")
    
    slug = Column(String, nullable=False) # e.g. "1.2"
    order_in_section = Column(Integer, nullable=False)
    
    # Core Content
    content = Column(Text, nullable=False)         # Devanagari
    content_transliteration = Column(Text)         # IAST
    content_meaning = Column(Text)                 # English Translation
    
    # Analysis & Metadata
    commentary = Column(Text)                      # Optional commentary
    word_analysis = Column(JSON)                   # {"words": [...], "sandhi": ...}
    validations = Column(JSON)                     # {"meter": "anushtubh", ...}
```

```python
# backend/app/models/dictionary.py
# (Remains the same - generic dictionary model)

from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.models.base import Base, pk, foreign_key

class Dictionary(Base):
    """A dictionary that maps Sanskrit expressions to definitions."""
    __tablename__ = "dictionaries"

    id = pk()
    slug = Column(String, unique=True, nullable=False) # e.g. "mw"
    title = Column(String, nullable=False)             # e.g. "Monier-Williams"

    entries = relationship("DictionaryEntry", backref="dictionary", cascade="delete")

class DictionaryEntry(Base):
    """Dictionary definitions for a specific entry key."""
    __tablename__ = "dictionary_entries"

    id = pk()
    dictionary_id = foreign_key("dictionaries.id")
    key = Column(String, index=True, nullable=False) # Standardized lookup key (SLP1)
    value = Column(String, nullable=False)           # XML/HTML payload
```

### 3.3 Generic Data Interaction

By abstracting `Sutra` into `TextBlock`, the system can support any Sanskrit text. 

- **Yoga Sutras**: 
    - `Text`: "Yoga Sutras"
    - `Section`: "Samadhi Pada"
    - `Block`: Sutra 1.1 "atha yoganushasanam"
- **Ramayana**:
    - `Text`: "Ramayana"
    - `Section`: "Bala Kanda"
    - `Block`: Sloka 1.1

### 3.4 Word Analysis JSON Structure

The `word_analysis` field in the sutras table stores pre-analyzed word data:

```json
{
  "words": [
    {
      "word": "योगः",
      "word_slp1": "yogaH",
      "position": 0,
      "base_form": "योग",
      "base_form_slp1": "yoga",
      "transliteration": "yogaḥ",
      "meaning": "yoga, union",
      "grammar": {
        "stem": "yoga",
        "gender": "masculine",
        "case": "nominative",
        "number": "singular"
      },
      "is_compound": false
    },
    {
      "word": "चित्तवृत्तिनिरोधः",
      "word_slp1": "cittavfttinirodhaH",
      "position": 1,
      "transliteration": "citta-vṛtti-nirodhaḥ",
      "meaning": "cessation of mental modifications",
      "is_compound": true,
      "compound_parts": [
        {
          "word": "चित्त",
          "base_form_slp1": "citta",
          "meaning": "mind, consciousness"
        },
        {
          "word": "वृत्ति",
          "base_form_slp1": "vftti",
          "meaning": "modification, activity"
        },
        {
          "word": "निरोधः",
          "base_form_slp1": "nirodha",
          "meaning": "cessation, restraint"
        }
      ]
    }
  ],
  "sandhi_analysis": "योगः + चित्तवृत्तिनिरोधः = योगश्चित्तवृत्तिनिरोधः"
}
```

---

## 4. API Design

### 4.1 RESTful Endpoints

#### 4.1.1 Sutra Endpoints

| Method | Endpoint                     | Description        | Response       |
| ------ | ---------------------------- | ------------------ | -------------- |
| GET    | `/api/sutras`                | List all sutras    | Paginated list |
| GET    | `/api/sutras/{id}`           | Get single sutra   | Sutra object   |
| GET    | `/api/sutras/pada/{pada_id}` | Get sutras by pada | List of sutras |
| GET    | `/api/padas`                 | List all padas     | List of padas  |

#### 4.1.2 Search Endpoints

| Method | Endpoint              | Description   | Parameters     |
| ------ | --------------------- | ------------- | -------------- |
| GET    | `/api/search`         | Search sutras | q, lang, limit |
| GET    | `/api/search/suggest` | Auto-complete | q, limit       |

#### 4.1.3 Dictionary Endpoints

| Method | Endpoint                 | Description    | Parameters       |
| ------ | ------------------------ | -------------- | ---------------- |
| GET    | `/api/dictionary/{word}` | Lookup word    | dicts (optional) |
| GET    | `/api/split/{compound}`  | Split compound | -                |

#### 4.1.4 Utility Endpoints

| Method | Endpoint             | Description    | Parameters     |
| ------ | -------------------- | -------------- | -------------- |
| POST   | `/api/transliterate` | Convert script | text, from, to |

### 4.2 API Response Formats

#### 4.2.1 Sutra Response

```json
// GET /api/sutras/1.2
{
  "success": true,
  "data": {
    "id": "1.2",
    "pada": 1,
    "sutra_number": 2,
    "sanskrit": "योगश्चित्तवृत्तिनिरोधः",
    "transliteration": "yogaś-citta-vṛtti-nirodhaḥ",
    "translation_en": "Yoga is the cessation of the modifications of the mind.",
    "commentary": "This sutra defines yoga...",
    "word_analysis": {
      "words": [...]
    },
    "navigation": {
      "prev": "1.1",
      "next": "1.3"
    }
  }
}
```

#### 4.2.2 Search Response

```json
// GET /api/search?q=yoga&limit=10
{
  "success": true,
  "data": {
    "query": "yoga",
    "total": 15,
    "results": [
      {
        "id": "1.2",
        "sanskrit": "योगश्चित्तवृत्तिनिरोधः",
        "transliteration": "yogaś-citta-vṛtti-nirodhaḥ",
        "translation_en": "Yoga is the cessation...",
        "score": 0.95,
        "highlight": {
          "translation_en": "<mark>Yoga</mark> is the cessation..."
        }
      }
    ]
  }
}
```

#### 4.2.3 Dictionary Response

```json
// GET /api/dictionary/योग
{
  "success": true,
  "data": {
    "word": "योग",
    "transliteration": "yoga",
    "entries": [
      {
        "dictionary": "MW",
        "dictionary_name": "Monier-Williams",
        "definition": "the act of yoking, joining, attaching, harnessing, putting to (of horses); a yoke, team, vehicle, conveyance; employment, use, application, performance; a means, expedient, device, way, manner, method...",
        "grammar": "m."
      },
      {
        "dictionary": "AP90",
        "dictionary_name": "Apte Sanskrit-English",
        "definition": "1. Joining, uniting. 2. Union, junction, combination. 3. Contact, touch. 4. Application, employment, use...",
        "grammar": "m. (युज्-घञ्)"
      }
    ]
  }
}
```

#### 4.2.4 Compound Split Response

```json
// GET /api/split/चित्तवृत्तिनिरोधः
{
  "success": true,
  "data": {
    "compound": "चित्तवृत्तिनिरोधः",
    "transliteration": "citta-vṛtti-nirodhaḥ",
    "splits": [
      {
        "confidence": 0.95,
        "parts": [
          {
            "word": "चित्त",
            "transliteration": "citta",
            "meaning": "mind, consciousness",
            "grammar": "n. stem"
          },
          {
            "word": "वृत्ति",
            "transliteration": "vṛtti",
            "meaning": "modification, activity",
            "grammar": "f. stem"
          },
          {
            "word": "निरोधः",
            "transliteration": "nirodhaḥ",
            "meaning": "cessation, restraint",
            "grammar": "m. nom. sg."
          }
        ],
        "compound_type": "tatpuruṣa"
      }
    ]
  }
}
```

### 4.3 Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Sutra with id '5.1' not found",
    "details": null
  }
}
```

### 4.4 Flask Route Implementation

```python
# backend/app/routes/sutra_routes.py

from flask import Blueprint, jsonify, request
from app.services.sutra_service import SutraService

sutra_bp = Blueprint('sutras', __name__, url_prefix='/api')
sutra_service = SutraService()

@sutra_bp.route('/sutras', methods=['GET'])
def get_all_sutras():
    """Get all sutras with optional pagination."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    result = sutra_service.get_all(page=page, per_page=per_page)
    return jsonify({
        'success': True,
        'data': result
    })

@sutra_bp.route('/sutras/<sutra_id>', methods=['GET'])
def get_sutra(sutra_id):
    """Get a single sutra by ID."""
    sutra = sutra_service.get_by_id(sutra_id)
    
    if not sutra:
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': f"Sutra with id '{sutra_id}' not found"
            }
        }), 404
    
    return jsonify({
        'success': True,
        'data': sutra
    })

@sutra_bp.route('/sutras/pada/<int:pada_id>', methods=['GET'])
def get_sutras_by_pada(pada_id):
    """Get all sutras in a specific pada."""
    if pada_id < 1 or pada_id > 4:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_PADA',
                'message': 'Pada must be between 1 and 4'
            }
        }), 400
    
    sutras = sutra_service.get_by_pada(pada_id)
    return jsonify({
        'success': True,
        'data': sutras
    })

@sutra_bp.route('/padas', methods=['GET'])
def get_padas():
    """Get all padas with metadata."""
    padas = sutra_service.get_all_padas()
    return jsonify({
        'success': True,
        'data': padas
    })
```

```python
# backend/app/routes/search_routes.py

from flask import Blueprint, jsonify, request
from app.services.search_service import SearchService

search_bp = Blueprint('search', __name__, url_prefix='/api')
search_service = SearchService()

@search_bp.route('/search', methods=['GET'])
def search():
    """Search sutras by query."""
    query = request.args.get('q', '').strip()
    lang = request.args.get('lang', 'all')  # 'sanskrit', 'english', 'all'
    limit = request.args.get('limit', 20, type=int)
    
    if not query:
        return jsonify({
            'success': False,
            'error': {
                'code': 'EMPTY_QUERY',
                'message': 'Search query cannot be empty'
            }
        }), 400
    
    results = search_service.search(query, lang=lang, limit=limit)
    return jsonify({
        'success': True,
        'data': {
            'query': query,
            'total': len(results),
            'results': results
        }
    })

@search_bp.route('/search/suggest', methods=['GET'])
def suggest():
    """Get search suggestions."""
    query = request.args.get('q', '').strip()
    limit = request.args.get('limit', 5, type=int)
    
    if len(query) < 2:
        return jsonify({
            'success': True,
            'data': {'suggestions': []}
        })
    
    suggestions = search_service.get_suggestions(query, limit=limit)
    return jsonify({
        'success': True,
        'data': {'suggestions': suggestions}
    })
```

```python
# backend/app/routes/dictionary_routes.py

from flask import Blueprint, jsonify, request
from app.services.dictionary_service import DictionaryService

dict_bp = Blueprint('dictionary', __name__, url_prefix='/api')
dict_service = DictionaryService()

@dict_bp.route('/dictionary/<word>', methods=['GET'])
def lookup_word(word):
    """Look up a word in dictionaries."""
    dicts = request.args.get('dicts', 'MW,AP90').split(',')
    
    entries = dict_service.lookup(word, dictionaries=dicts)
    
    if not entries:
        return jsonify({
            'success': False,
            'error': {
                'code': 'WORD_NOT_FOUND',
                'message': f"No dictionary entries found for '{word}'"
            }
        }), 404
    
    return jsonify({
        'success': True,
        'data': entries
    })

@dict_bp.route('/split/<compound>', methods=['GET'])
def split_compound(compound):
    """Split a Sanskrit compound word."""
    from app.services.sandhi_service import SandhiService
    sandhi_service = SandhiService()
    
    result = sandhi_service.split(compound)
    return jsonify({
        'success': True,
        'data': result
    })
```

---

## 5. Frontend Design

### 5.1 Component Hierarchy

```
App
├── Layout
│   ├── Header
│   │   ├── Logo
│   │   ├── SearchBar
│   │   └── MenuButton
│   ├── Main Content (React Router Outlet)
│   │   ├── HomePage
│   │   │   ├── WelcomeSection
│   │   │   └── PadaGrid
│   │   ├── SutraPage
│   │   │   ├── SutraDisplay
│   │   │   │   ├── SutraHeader
│   │   │   │   ├── SanskritText (with ClickableWords)
│   │   │   │   ├── Transliteration
│   │   │   │   ├── Translation
│   │   │   │   └── Commentary
│   │   │   ├── SutraNavigation
│   │   │   └── DictionaryPanel
│   │   │       ├── WordHeader
│   │   │       ├── DictionaryEntry (multiple)
│   │   │       └── CompoundSplit
│   │   └── SearchResultsPage
│   │       └── SearchResult (multiple)
│   └── Footer
│       └── PadaNavigation
└── Modals/Sheets
    └── MobileDictionarySheet
```

### 5.2 TypeScript Types

```typescript
// frontend/src/types/index.ts

export interface Sutra {
  id: string;
  pada: number;
  sutra_number: number;
  sanskrit: string;
  transliteration: string;
  translation_en: string;
  commentary?: string;
  word_analysis?: WordAnalysis;
  navigation?: {
    prev?: string;
    next?: string;
  };
}

export interface WordAnalysis {
  words: AnalyzedWord[];
  sandhi_analysis?: string;
}

export interface AnalyzedWord {
  word: string;
  word_slp1: string;
  position: number;
  base_form?: string;
  base_form_slp1?: string;
  transliteration: string;
  meaning?: string;
  grammar?: GrammarInfo;
  is_compound: boolean;
  compound_parts?: CompoundPart[];
}

export interface GrammarInfo {
  stem?: string;
  gender?: 'masculine' | 'feminine' | 'neuter';
  case?: string;
  number?: 'singular' | 'dual' | 'plural';
}

export interface CompoundPart {
  word: string;
  base_form_slp1: string;
  meaning: string;
}

export interface Pada {
  id: number;
  name_en: string;
  name_sanskrit: string;
  name_iast: string;
  description: string;
  sutra_count: number;
}

export interface DictionaryResult {
  word: string;
  transliteration: string;
  entries: DictionaryEntry[];
}

export interface DictionaryEntry {
  dictionary: string;
  dictionary_name: string;
  definition: string;
  grammar?: string;
  etymology?: string;
}

export interface SearchResult {
  id: string;
  sanskrit: string;
  transliteration: string;
  translation_en: string;
  score: number;
  highlight?: {
    sanskrit?: string;
    translation_en?: string;
  };
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
  };
}
```

### 5.3 Key Component Implementations

#### 5.3.1 ClickableWord Component

```tsx
// frontend/src/components/ClickableWord.tsx

import React from 'react';
import { AnalyzedWord } from '../types';

interface ClickableWordProps {
  word: AnalyzedWord;
  onWordClick: (word: AnalyzedWord) => void;
  isSelected?: boolean;
}

export const ClickableWord: React.FC<ClickableWordProps> = ({
  word,
  onWordClick,
  isSelected = false
}) => {
  return (
    <span
      className={`
        cursor-pointer 
        hover:bg-amber-100 
        hover:rounded 
        px-1 
        transition-colors
        ${isSelected ? 'bg-amber-200 rounded' : ''}
        ${word.is_compound ? 'border-b-2 border-dotted border-amber-400' : ''}
      `}
      onClick={() => onWordClick(word)}
      title={word.meaning || 'Click for definition'}
    >
      {word.word}
    </span>
  );
};
```

#### 5.3.2 SutraDisplay Component

```tsx
// frontend/src/components/SutraDisplay.tsx

import React from 'react';
import { Sutra, AnalyzedWord } from '../types';
import { ClickableWord } from './ClickableWord';

interface SutraDisplayProps {
  sutra: Sutra;
  onWordClick: (word: AnalyzedWord) => void;
  selectedWord?: AnalyzedWord | null;
}

export const SutraDisplay: React.FC<SutraDisplayProps> = ({
  sutra,
  onWordClick,
  selectedWord
}) => {
  const renderSanskritText = () => {
    if (sutra.word_analysis?.words) {
      return (
        <div className="text-3xl font-sanskrit leading-relaxed">
          {sutra.word_analysis.words.map((word, index) => (
            <React.Fragment key={index}>
              <ClickableWord
                word={word}
                onWordClick={onWordClick}
                isSelected={selectedWord?.position === word.position}
              />
              {index < sutra.word_analysis!.words.length - 1 && ' '}
            </React.Fragment>
          ))}
        </div>
      );
    }
    
    // Fallback if no word analysis
    return (
      <div className="text-3xl font-sanskrit leading-relaxed">
        {sutra.sanskrit}
      </div>
    );
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      {/* Sutra Header */}
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold text-gray-600">
          Sutra {sutra.id}
        </h2>
        <span className="text-sm text-gray-500">
          Pada {sutra.pada} · Sūtra {sutra.sutra_number}
        </span>
      </div>
      
      {/* Sanskrit Text */}
      <div className="mb-4 pb-4 border-b border-gray-200">
        {renderSanskritText()}
      </div>
      
      {/* Transliteration */}
      <div className="mb-4 text-xl text-gray-700 italic">
        {sutra.transliteration}
      </div>
      
      {/* Translation */}
      <div className="mb-4 text-lg text-gray-800">
        {sutra.translation_en}
      </div>
      
      {/* Commentary (if available) */}
      {sutra.commentary && (
        <div className="mt-6 pt-4 border-t border-gray-200">
          <h3 className="text-sm font-semibold text-gray-600 mb-2">
            Commentary
          </h3>
          <div className="text-gray-700 leading-relaxed">
            {sutra.commentary}
          </div>
        </div>
      )}
    </div>
  );
};
```

#### 5.3.3 DictionaryPanel Component

```tsx
// frontend/src/components/DictionaryPanel.tsx

import React from 'react';
import { DictionaryResult, AnalyzedWord } from '../types';
import { useDictionary } from '../hooks/useDictionary';

interface DictionaryPanelProps {
  word: AnalyzedWord | null;
  onClose: () => void;
}

export const DictionaryPanel: React.FC<DictionaryPanelProps> = ({
  word,
  onClose
}) => {
  const { data, isLoading, error } = useDictionary(word?.base_form || word?.word);

  if (!word) {
    return (
      <div className="bg-gray-50 rounded-lg p-6 text-center text-gray-500">
        Click on a Sanskrit word to see its definition
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md h-full overflow-y-auto">
      {/* Header */}
      <div className="sticky top-0 bg-white border-b border-gray-200 p-4">
        <div className="flex justify-between items-start">
          <div>
            <h3 className="text-2xl font-sanskrit">{word.word}</h3>
            <p className="text-gray-600 italic">{word.transliteration}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>
        
        {/* Quick meaning */}
        {word.meaning && (
          <p className="mt-2 text-gray-700">{word.meaning}</p>
        )}
        
        {/* Grammar info */}
        {word.grammar && (
          <p className="mt-1 text-sm text-gray-500">
            {word.grammar.gender} · {word.grammar.case} · {word.grammar.number}
          </p>
        )}
      </div>
      
      {/* Compound Split */}
      {word.is_compound && word.compound_parts && (
        <div className="p-4 bg-amber-50 border-b border-amber-100">
          <h4 className="text-sm font-semibold text-amber-800 mb-2">
            Compound Analysis
          </h4>
          <div className="flex flex-wrap gap-2">
            {word.compound_parts.map((part, index) => (
              <span
                key={index}
                className="px-2 py-1 bg-white rounded border border-amber-200 text-sm"
              >
                <span className="font-sanskrit">{part.word}</span>
                <span className="text-gray-500 ml-1">({part.meaning})</span>
              </span>
            ))}
          </div>
        </div>
      )}
      
      {/* Dictionary Entries */}
      <div className="p-4">
        {isLoading && (
          <div className="text-center text-gray-500">Loading...</div>
        )}
        
        {error && (
          <div className="text-center text-red-500">
            Failed to load dictionary entries
          </div>
        )}
        
        {data?.entries.map((entry, index) => (
          <div
            key={index}
            className="mb-4 pb-4 border-b border-gray-100 last:border-0"
          >
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-semibold text-blue-600">
                {entry.dictionary_name}
              </span>
              {entry.grammar && (
                <span className="text-xs text-gray-500">{entry.grammar}</span>
              )}
            </div>
            <p className="text-gray-700 text-sm leading-relaxed">
              {entry.definition}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};
```

#### 5.3.4 SearchBar Component

```tsx
// frontend/src/components/SearchBar.tsx

import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSearchSuggestions } from '../hooks/useSearch';
import debounce from 'lodash/debounce';

export const SearchBar: React.FC = () => {
  const [query, setQuery] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const navigate = useNavigate();
  
  const { data: suggestions } = useSearchSuggestions(query);
  
  const debouncedSetQuery = useCallback(
    debounce((value: string) => setQuery(value), 300),
    []
  );
  
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    debouncedSetQuery(value);
    setShowSuggestions(value.length >= 2);
  };
  
  const handleSearch = (searchQuery: string) => {
    setShowSuggestions(false);
    navigate(`/search?q=${encodeURIComponent(searchQuery)}`);
  };
  
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && query) {
      handleSearch(query);
    }
  };

  return (
    <div className="relative w-full max-w-md">
      <div className="relative">
        <input
          type="text"
          placeholder="Search sutras (Sanskrit or English)..."
          className="w-full px-4 py-2 pr-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500"
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={() => query.length >= 2 && setShowSuggestions(true)}
          onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
        />
        <button
          onClick={() => query && handleSearch(query)}
          className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-amber-600"
        >
          🔍
        </button>
      </div>
      
      {/* Suggestions Dropdown */}
      {showSuggestions && suggestions && suggestions.length > 0 && (
        <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg">
          {suggestions.map((suggestion, index) => (
            <button
              key={index}
              className="w-full px-4 py-2 text-left hover:bg-gray-50 first:rounded-t-lg last:rounded-b-lg"
              onClick={() => handleSearch(suggestion.text)}
            >
              <span className="font-sanskrit">{suggestion.sanskrit}</span>
              <span className="text-gray-500 ml-2">{suggestion.text}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
```

### 5.4 Custom Hooks

```typescript
// frontend/src/hooks/useSutra.ts

import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import { Sutra, ApiResponse } from '../types';

export const useSutra = (id: string) => {
  return useQuery<Sutra>({
    queryKey: ['sutra', id],
    queryFn: async () => {
      const response = await api.get<ApiResponse<Sutra>>(`/sutras/${id}`);
      if (!response.data.success) {
        throw new Error(response.data.error?.message);
      }
      return response.data.data!;
    },
    enabled: !!id,
  });
};

export const useSutrasByPada = (padaId: number) => {
  return useQuery<Sutra[]>({
    queryKey: ['sutras', 'pada', padaId],
    queryFn: async () => {
      const response = await api.get<ApiResponse<Sutra[]>>(`/sutras/pada/${padaId}`);
      if (!response.data.success) {
        throw new Error(response.data.error?.message);
      }
      return response.data.data!;
    },
    enabled: padaId >= 1 && padaId <= 4,
  });
};
```

```typescript
// frontend/src/hooks/useDictionary.ts

import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import { DictionaryResult, ApiResponse } from '../types';

export const useDictionary = (word: string | undefined) => {
  return useQuery<DictionaryResult>({
    queryKey: ['dictionary', word],
    queryFn: async () => {
      const response = await api.get<ApiResponse<DictionaryResult>>(
        `/dictionary/${encodeURIComponent(word!)}`
      );
      if (!response.data.success) {
        throw new Error(response.data.error?.message);
      }
      return response.data.data!;
    },
    enabled: !!word,
    staleTime: 1000 * 60 * 60, // Cache for 1 hour
  });
};
```

```typescript
// frontend/src/hooks/useSearch.ts

import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import { SearchResult, ApiResponse } from '../types';

interface SearchResponse {
  query: string;
  total: number;
  results: SearchResult[];
}

export const useSearch = (query: string) => {
  return useQuery<SearchResponse>({
    queryKey: ['search', query],
    queryFn: async () => {
      const response = await api.get<ApiResponse<SearchResponse>>(
        `/search?q=${encodeURIComponent(query)}`
      );
      if (!response.data.success) {
        throw new Error(response.data.error?.message);
      }
      return response.data.data!;
    },
    enabled: query.length >= 2,
  });
};

interface Suggestion {
  text: string;
  sanskrit: string;
}

export const useSearchSuggestions = (query: string) => {
  return useQuery<Suggestion[]>({
    queryKey: ['search', 'suggestions', query],
    queryFn: async () => {
      const response = await api.get<ApiResponse<{ suggestions: Suggestion[] }>>(
        `/search/suggest?q=${encodeURIComponent(query)}`
      );
      if (!response.data.success) {
        throw new Error(response.data.error?.message);
      }
      return response.data.data!.suggestions;
    },
    enabled: query.length >= 2,
  });
};
```

---

## 6. Component Specifications

### 6.1 Backend Services

#### 6.1.1 SutraService

```python
# backend/app/services/sutra_service.py

from typing import List, Optional, Dict
from app.models.sutra import Sutra, Pada
from app import db

class SutraService:
    """Service for sutra-related operations."""
    
    def get_all(self, page: int = 1, per_page: int = 20) -> Dict:
        """Get all sutras with pagination."""
        pagination = Sutra.query.order_by(
            Sutra.pada, Sutra.sutra_number
        ).paginate(page=page, per_page=per_page)
        
        return {
            'sutras': [s.to_dict() for s in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }
    
    def get_by_id(self, sutra_id: str) -> Optional[Dict]:
        """Get a single sutra by ID with navigation."""
        sutra = Sutra.query.get(sutra_id)
        if not sutra:
            return None
        
        result = sutra.to_dict()
        result['navigation'] = self._get_navigation(sutra)
        return result
    
    def get_by_pada(self, pada_id: int) -> List[Dict]:
        """Get all sutras in a specific pada."""
        sutras = Sutra.query.filter_by(pada=pada_id).order_by(
            Sutra.sutra_number
        ).all()
        return [s.to_dict() for s in sutras]
    
    def get_all_padas(self) -> List[Dict]:
        """Get all padas with metadata."""
        padas = Pada.query.order_by(Pada.id).all()
        return [p.to_dict() for p in padas]
    
    def _get_navigation(self, sutra: Sutra) -> Dict:
        """Get previous and next sutra IDs."""
        nav = {}
        
        # Previous sutra
        if sutra.sutra_number > 1:
            nav['prev'] = f"{sutra.pada}.{sutra.sutra_number - 1}"
        elif sutra.pada > 1:
            # Get last sutra of previous pada
            prev_pada = Pada.query.get(sutra.pada - 1)
            if prev_pada:
                nav['prev'] = f"{sutra.pada - 1}.{prev_pada.sutra_count}"
        
        # Next sutra
        current_pada = Pada.query.get(sutra.pada)
        if sutra.sutra_number < current_pada.sutra_count:
            nav['next'] = f"{sutra.pada}.{sutra.sutra_number + 1}"
        elif sutra.pada < 4:
            nav['next'] = f"{sutra.pada + 1}.1"
        
        return nav
```

#### 6.1.2 SearchService

```python
# backend/app/services/search_service.py

from typing import List, Dict
from rapidfuzz import fuzz, process
from indic_transliteration import sanscript
from app.models.sutra import Sutra
from app import db

class SearchService:
    """Service for search operations with fuzzy matching."""
    
    def __init__(self):
        self.min_score = 60  # Minimum fuzzy match score
    
    def search(self, query: str, lang: str = 'all', limit: int = 20) -> List[Dict]:
        """
        Search sutras with fuzzy matching.
        
        Args:
            query: Search query string
            lang: 'sanskrit', 'english', or 'all'
            limit: Maximum results to return
        """
        # Normalize query
        query_normalized = self._normalize_query(query)
        
        # Get all sutras for matching
        sutras = Sutra.query.all()
        results = []
        
        for sutra in sutras:
            score = 0
            highlights = {}
            
            if lang in ('sanskrit', 'all'):
                # Match against Sanskrit and transliteration
                sanskrit_score = fuzz.partial_ratio(
                    query_normalized, 
                    sutra.sanskrit.lower()
                )
                trans_score = fuzz.partial_ratio(
                    query_normalized,
                    sutra.transliteration.lower()
                )
                score = max(score, sanskrit_score, trans_score)
                
                if sanskrit_score >= self.min_score:
                    highlights['sanskrit'] = self._highlight(
                        sutra.sanskrit, query
                    )
            
            if lang in ('english', 'all'):
                # Match against English translation
                english_score = fuzz.partial_ratio(
                    query_normalized,
                    sutra.translation_en.lower()
                )
                score = max(score, english_score)
                
                if english_score >= self.min_score:
                    highlights['translation_en'] = self._highlight(
                        sutra.translation_en, query
                    )
            
            if score >= self.min_score:
                results.append({
                    'id': sutra.id,
                    'sanskrit': sutra.sanskrit,
                    'transliteration': sutra.transliteration,
                    'translation_en': sutra.translation_en,
                    'score': score / 100,
                    'highlight': highlights
                })
        
        # Sort by score and limit
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]
    
    def get_suggestions(self, query: str, limit: int = 5) -> List[Dict]:
        """Get search suggestions based on partial query."""
        query_normalized = self._normalize_query(query)
        
        sutras = Sutra.query.all()
        suggestions = []
        
        for sutra in sutras:
            # Check if query matches beginning of any word
            words = sutra.translation_en.split()
            for word in words:
                if word.lower().startswith(query_normalized):
                    suggestions.append({
                        'text': sutra.translation_en[:50] + '...',
                        'sanskrit': sutra.sanskrit,
                        'id': sutra.id
                    })
                    break
        
        return suggestions[:limit]
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query for comparison."""
        query = query.lower().strip()
        
        # Try to detect and convert transliteration schemes
        try:
            # If it looks like IAST, convert to Devanagari for matching
            if any(c in query for c in 'āīūṛṝḷḹṃḥśṣṇṭḍ'):
                query_deva = sanscript.transliterate(
                    query, sanscript.IAST, sanscript.DEVANAGARI
                )
                return query_deva
        except:
            pass
        
        return query
    
    def _highlight(self, text: str, query: str) -> str:
        """Add highlight markers to matching text."""
        import re
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        return pattern.sub(f'<mark>{query}</mark>', text)
```

#### 6.1.3 DictionaryService

```python
# backend/app/services/dictionary_service.py

from typing import List, Dict, Optional
from indic_transliteration import sanscript
from app.models.dictionary import DictionaryEntry
from app import db

# Dictionary display names
DICT_NAMES = {
    'MW': 'Monier-Williams Sanskrit-English Dictionary',
    'AP90': 'Apte Practical Sanskrit-English Dictionary',
    'AK': 'Amarakosha',
    'SHS': 'Shabda-Sagara Sanskrit-English Dictionary',
    'VCP': 'Vacaspatyam (Sanskrit-Sanskrit)',
}

class DictionaryService:
    """Service for dictionary lookups."""
    
    def lookup(
        self, 
        word: str, 
        dictionaries: List[str] = ['MW', 'AP90']
    ) -> Optional[Dict]:
        """
        Look up a word in specified dictionaries.
        
        Args:
            word: Word to look up (Devanagari or transliterated)
            dictionaries: List of dictionary codes to search
        """
        # Normalize word to SLP1 for database lookup
        word_slp1 = self._to_slp1(word)
        word_deva = self._to_devanagari(word)
        word_iast = self._to_iast(word)
        
        # Query database
        entries = DictionaryEntry.query.filter(
            DictionaryEntry.headword_slp1 == word_slp1,
            DictionaryEntry.dictionary_code.in_(dictionaries)
        ).all()
        
        if not entries:
            # Try fuzzy match
            entries = self._fuzzy_lookup(word_slp1, dictionaries)
        
        if not entries:
            return None
        
        return {
            'word': word_deva,
            'transliteration': word_iast,
            'entries': [
                {
                    'dictionary': e.dictionary_code,
                    'dictionary_name': DICT_NAMES.get(
                        e.dictionary_code, e.dictionary_code
                    ),
                    'definition': e.definition,
                    'grammar': e.grammar,
                    'etymology': e.etymology
                }
                for e in entries
            ]
        }
    
    def _to_slp1(self, word: str) -> str:
        """Convert word to SLP1 encoding."""
        # Detect input script and convert
        if self._is_devanagari(word):
            return sanscript.transliterate(
                word, sanscript.DEVANAGARI, sanscript.SLP1
            )
        elif self._is_iast(word):
            return sanscript.transliterate(
                word, sanscript.IAST, sanscript.SLP1
            )
        return word  # Assume already SLP1
    
    def _to_devanagari(self, word: str) -> str:
        """Convert word to Devanagari."""
        if self._is_devanagari(word):
            return word
        slp1 = self._to_slp1(word)
        return sanscript.transliterate(
            slp1, sanscript.SLP1, sanscript.DEVANAGARI
        )
    
    def _to_iast(self, word: str) -> str:
        """Convert word to IAST."""
        slp1 = self._to_slp1(word)
        return sanscript.transliterate(
            slp1, sanscript.SLP1, sanscript.IAST
        )
    
    def _is_devanagari(self, text: str) -> bool:
        """Check if text is in Devanagari script."""
        return any('\u0900' <= c <= '\u097F' for c in text)
    
    def _is_iast(self, text: str) -> bool:
        """Check if text contains IAST diacritics."""
        return any(c in text for c in 'āīūṛṝḷḹṃḥśṣṇṭḍ')
    
    def _fuzzy_lookup(
        self, 
        word_slp1: str, 
        dictionaries: List[str]
    ) -> List[DictionaryEntry]:
        """Attempt fuzzy matching for word lookup."""
        from rapidfuzz import fuzz
        
        # Get candidate entries
        candidates = DictionaryEntry.query.filter(
            DictionaryEntry.dictionary_code.in_(dictionaries)
        ).all()
        
        matches = []
        for entry in candidates:
            score = fuzz.ratio(word_slp1, entry.headword_slp1)
            if score >= 85:  # High threshold for dictionary
                matches.append((score, entry))
        
        matches.sort(key=lambda x: x[0], reverse=True)
        return [m[1] for m in matches[:5]]
```

#### 6.1.4 SandhiService

```python
# backend/app/services/sandhi_service.py

from typing import Dict, List, Optional
import subprocess
import json

class SandhiService:
    """Service for Sanskrit sandhi and compound splitting."""
    
    def __init__(self):
        # Configure external splitter (UoH SCL or local)
        self.use_external_api = False
        self.scl_api_url = "https://sanskrit.uohyd.ac.in/cgi-bin/scl/sandhi/sandhi_splitter.cgi"
    
    def split(self, compound: str) -> Dict:
        """
        Split a Sanskrit compound word.
        
        Returns possible splits with confidence scores.
        """
        from indic_transliteration import sanscript
        
        # Convert to appropriate format
        compound_slp1 = self._to_slp1(compound)
        compound_iast = sanscript.transliterate(
            compound_slp1, sanscript.SLP1, sanscript.IAST
        )
        
        if self.use_external_api:
            splits = self._split_via_api(compound_slp1)
        else:
            splits = self._split_local(compound_slp1)
        
        return {
            'compound': compound,
            'transliteration': compound_iast,
            'splits': splits
        }
    
    def _split_local(self, compound_slp1: str) -> List[Dict]:
        """
        Local compound splitting using rules or sanskrit_parser.
        """
        try:
            from sanskrit_parser import Parser
            parser = Parser()
            
            splits = parser.split(compound_slp1)
            results = []
            
            for split in splits[:3]:  # Top 3 splits
                parts = []
                for part in split.parts:
                    parts.append({
                        'word': self._to_devanagari(part.word),
                        'transliteration': self._to_iast(part.word),
                        'meaning': self._get_quick_meaning(part.word),
                        'grammar': part.grammar if hasattr(part, 'grammar') else None
                    })
                
                results.append({
                    'confidence': split.score if hasattr(split, 'score') else 0.8,
                    'parts': parts,
                    'compound_type': split.compound_type if hasattr(split, 'compound_type') else None
                })
            
            return results
            
        except ImportError:
            # Fallback: simple hyphen-based splitting
            return self._simple_split(compound_slp1)
    
    def _simple_split(self, compound_slp1: str) -> List[Dict]:
        """Simple fallback splitting on common patterns."""
        from indic_transliteration import sanscript
        
        # Common sandhi patterns (simplified)
        # This is a very basic implementation
        parts = compound_slp1.split('-') if '-' in compound_slp1 else [compound_slp1]
        
        result_parts = []
        for part in parts:
            result_parts.append({
                'word': self._to_devanagari(part),
                'transliteration': self._to_iast(part),
                'meaning': self._get_quick_meaning(part),
                'grammar': None
            })
        
        return [{
            'confidence': 0.5,
            'parts': result_parts,
            'compound_type': 'unknown'
        }]
    
    def _split_via_api(self, compound_slp1: str) -> List[Dict]:
        """Split using external API (UoH SCL)."""
        import requests
        
        try:
            response = requests.post(
                self.scl_api_url,
                data={'word': compound_slp1},
                timeout=5
            )
            # Parse response and format
            # (actual format depends on SCL API)
            return self._parse_scl_response(response.json())
        except:
            return self._simple_split(compound_slp1)
    
    def _get_quick_meaning(self, word_slp1: str) -> Optional[str]:
        """Get quick meaning from dictionary."""
        from app.services.dictionary_service import DictionaryService
        dict_service = DictionaryService()
        
        result = dict_service.lookup(word_slp1, ['MW'])
        if result and result['entries']:
            # Return first 50 chars of first definition
            defn = result['entries'][0]['definition']
            return defn[:50] + '...' if len(defn) > 50 else defn
        return None
    
    def _to_slp1(self, text: str) -> str:
        from indic_transliteration import sanscript
        if any('\u0900' <= c <= '\u097F' for c in text):
            return sanscript.transliterate(text, sanscript.DEVANAGARI, sanscript.SLP1)
        return text
    
    def _to_devanagari(self, text: str) -> str:
        from indic_transliteration import sanscript
        return sanscript.transliterate(text, sanscript.SLP1, sanscript.DEVANAGARI)
    
    def _to_iast(self, text: str) -> str:
        from indic_transliteration import sanscript
        return sanscript.transliterate(text, sanscript.SLP1, sanscript.IAST)
```

---

## 7. Implementation Guide

### 7.1 Phase 1: Data Collection (Week 1)

#### Task 1.1: Scrape Sutras from shlokam.org

```python
# backend/scripts/scrape_sutras.py

"""
Scraper for Yoga Sutras from shlokam.org
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from typing import Dict, List

BASE_URL = "https://shlokam.org/yogasutra/"

# Pada URLs
PADA_URLS = {
    1: "samadhipada/",
    2: "sadhanapada/",
    3: "vibhutipada/",
    4: "kaivalyapada/"
}

def scrape_sutra_page(url: str) -> Dict:
    """Scrape a single sutra page."""
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extract components (adjust selectors based on actual HTML)
    sanskrit = soup.select_one('.sanskrit-text').text.strip()
    transliteration = soup.select_one('.transliteration').text.strip()
    translation = soup.select_one('.translation').text.strip()
    commentary = soup.select_one('.commentary')
    commentary_text = commentary.text.strip() if commentary else None
    
    return {
        'sanskrit': sanskrit,
        'transliteration': transliteration,
        'translation_en': translation,
        'commentary': commentary_text
    }

def scrape_all_sutras() -> List[Dict]:
    """Scrape all 196 sutras."""
    all_sutras = []
    
    sutra_counts = {1: 51, 2: 55, 3: 56, 4: 34}
    
    for pada, count in sutra_counts.items():
        print(f"Scraping Pada {pada}...")
        
        for sutra_num in range(1, count + 1):
            sutra_id = f"{pada}.{sutra_num}"
            url = f"{BASE_URL}{PADA_URLS[pada]}{sutra_num}/"
            
            try:
                data = scrape_sutra_page(url)
                data['id'] = sutra_id
                data['pada'] = pada
                data['sutra_number'] = sutra_num
                all_sutras.append(data)
                print(f"  Scraped {sutra_id}")
                
                time.sleep(1)  # Be polite
                
            except Exception as e:
                print(f"  Error scraping {sutra_id}: {e}")
    
    return all_sutras

def main():
    sutras = scrape_all_sutras()
    
    with open('data/sutras.json', 'w', encoding='utf-8') as f:
        json.dump(sutras, f, ensure_ascii=False, indent=2)
    
    print(f"Scraped {len(sutras)} sutras")

if __name__ == '__main__':
    main()
```

#### Task 1.2: Setup PyCDSL Dictionaries

```python
# backend/scripts/setup_dictionary.py

"""
Setup script for importing CDSL dictionaries into SQLite.
"""

import pycdsl
from app import create_app, db
from app.models.dictionary import DictionaryEntry
from indic_transliteration import sanscript

# Dictionaries to import
DICTIONARIES = ['MW', 'AP90', 'AK', 'SHS']

def setup_cdsl():
    """Download and setup CDSL dictionaries."""
    cdsl = pycdsl.CDSLCorpus()
    cdsl.setup()
    
    for dict_code in DICTIONARIES:
        print(f"Downloading {dict_code}...")
        cdsl.download(dict_code)
    
    return cdsl

def import_dictionary(cdsl, dict_code: str):
    """Import a dictionary into SQLite."""
    print(f"Importing {dict_code}...")
    
    dictionary = getattr(cdsl, dict_code)
    count = 0
    
    for entry in dictionary.entries():
        try:
            headword_slp1 = entry.key
            headword_deva = sanscript.transliterate(
                headword_slp1, sanscript.SLP1, sanscript.DEVANAGARI
            )
            headword_iast = sanscript.transliterate(
                headword_slp1, sanscript.SLP1, sanscript.IAST
            )
            
            db_entry = DictionaryEntry(
                headword=headword_deva,
                headword_slp1=headword_slp1,
                headword_iast=headword_iast,
                dictionary_code=dict_code,
                definition=entry.data,
                grammar=entry.grammar if hasattr(entry, 'grammar') else None
            )
            
            db.session.add(db_entry)
            count += 1
            
            if count % 10000 == 0:
                db.session.commit()
                print(f"  Imported {count} entries...")
                
        except Exception as e:
            print(f"  Error importing entry: {e}")
    
    db.session.commit()
    print(f"  Completed {dict_code}: {count} entries")

def main():
    app = create_app()
    
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Setup CDSL
        cdsl = setup_cdsl()
        
        # Import each dictionary
        for dict_code in DICTIONARIES:
            import_dictionary(cdsl, dict_code)
        
        print("Dictionary setup complete!")

if __name__ == '__main__':
    main()
```

### 7.2 Phase 2: Backend Development (Weeks 2-3)

#### Task 2.1: Flask Application Setup

```python
# backend/app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

db = SQLAlchemy()

def create_app(config_name='development'):
    app = Flask(__name__)
    
    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data/yoga_sutras.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    
    # Register blueprints
    from app.routes.sutra_routes import sutra_bp
    from app.routes.search_routes import search_bp
    from app.routes.dictionary_routes import dict_bp
    
    app.register_blueprint(sutra_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(dict_bp)
    
    return app
```

```python
# backend/run.py

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

```
# backend/requirements.txt

flask>=3.0.0
flask-sqlalchemy>=3.1.0
flask-cors>=4.0.0
sqlalchemy>=2.0.0
pycdsl>=0.3.0
indic-transliteration>=2.3.0
rapidfuzz>=3.0.0
requests>=2.31.0
beautifulsoup4>=4.12.0
gunicorn>=21.0.0
```

### 7.3 Phase 3: Frontend Development (Weeks 3-4)

#### Task 3.1: React Project Setup

```bash
# Create Vite React project
npm create vite@latest frontend -- --template react-ts
cd frontend

# Install dependencies
npm install @tanstack/react-query axios react-router-dom lodash
npm install -D tailwindcss postcss autoprefixer @types/lodash

# Initialize Tailwind
npx tailwindcss init -p
```

```typescript
// frontend/src/services/api.ts

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});
```

```typescript
// frontend/src/App.tsx

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from './components/Layout';
import { HomePage } from './pages/HomePage';
import { SutraPage } from './pages/SutraPage';
import { SearchResultsPage } from './pages/SearchResultsPage';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<HomePage />} />
            <Route path="sutra/:id" element={<SutraPage />} />
            <Route path="search" element={<SearchResultsPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
```

---

## 8. Deployment

### 8.1 Docker Configuration

```dockerfile
# docker/Dockerfile.backend

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY backend/ .

# Copy data
COPY data/ /app/data/

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app"]
```

```dockerfile
# docker/Dockerfile.frontend

FROM node:20-alpine as builder

WORKDIR /app

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

```yaml
# docker/docker-compose.yml

version: '3.8'

services:
  backend:
    build:
      context: ..
      dockerfile: docker/Dockerfile.backend
    ports:
      - "5000:5000"
    volumes:
      - ../data:/app/data
    environment:
      - FLASK_ENV=production

  frontend:
    build:
      context: ..
      dockerfile: docker/Dockerfile.frontend
    ports:
      - "80:80"
    depends_on:
      - backend

  # Optional: Nginx reverse proxy
  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx-proxy.conf:/etc/nginx/conf.d/default.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend
```

### 8.2 Kubernetes Deployment

```yaml
# k8s/deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: yoga-sutras
  namespace: apps
spec:
  replicas: 2
  selector:
    matchLabels:
      app: yoga-sutras
  template:
    metadata:
      labels:
        app: yoga-sutras
    spec:
      containers:
      - name: backend
        image: yoga-sutras-backend:latest
        ports:
        - containerPort: 5000
        volumeMounts:
        - name: data
          mountPath: /app/data
      - name: frontend
        image: yoga-sutras-frontend:latest
        ports:
        - containerPort: 80
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: yoga-sutras-data

---
apiVersion: v1
kind: Service
metadata:
  name: yoga-sutras
  namespace: apps
spec:
  selector:
    app: yoga-sutras
  ports:
  - name: http
    port: 80
    targetPort: 80
  - name: api
    port: 5000
    targetPort: 5000

---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: yoga-sutras
  namespace: apps
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - yogasutras.naren.me
    secretName: yoga-sutras-tls
  rules:
  - host: yogasutras.naren.me
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: yoga-sutras
            port:
              number: 5000
      - path: /
        pathType: Prefix
        backend:
          service:
            name: yoga-sutras
            port:
              number: 80
```

---

## 9. Testing Strategy

### 9.1 Backend Tests

```python
# backend/tests/test_sutra_service.py

import pytest
from app import create_app, db
from app.models.sutra import Sutra, Pada
from app.services.sutra_service import SutraService

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        # Add test data
        pada = Pada(id=1, name_en='Test Pada', name_sanskrit='टेस्ट', 
                    name_iast='Test', description='Test', sutra_count=2)
        db.session.add(pada)
        
        sutra1 = Sutra(id='1.1', pada=1, sutra_number=1,
                      sanskrit='अथ योगानुशासनम्',
                      transliteration='atha yogānuśāsanam',
                      translation_en='Now begins the instruction on yoga')
        sutra2 = Sutra(id='1.2', pada=1, sutra_number=2,
                      sanskrit='योगश्चित्तवृत्तिनिरोधः',
                      transliteration='yogaś-citta-vṛtti-nirodhaḥ',
                      translation_en='Yoga is the cessation of the modifications of the mind')
        db.session.add_all([sutra1, sutra2])
        db.session.commit()
        
        yield app
        
        db.drop_all()

def test_get_by_id(app):
    with app.app_context():
        service = SutraService()
        sutra = service.get_by_id('1.1')
        
        assert sutra is not None
        assert sutra['id'] == '1.1'
        assert sutra['sanskrit'] == 'अथ योगानुशासनम्'

def test_get_by_id_not_found(app):
    with app.app_context():
        service = SutraService()
        sutra = service.get_by_id('99.99')
        
        assert sutra is None

def test_navigation(app):
    with app.app_context():
        service = SutraService()
        sutra = service.get_by_id('1.1')
        
        assert sutra['navigation']['next'] == '1.2'
        assert 'prev' not in sutra['navigation']
```

```python
# backend/tests/test_search_service.py

import pytest
from app.services.search_service import SearchService

def test_search_english(app):
    with app.app_context():
        service = SearchService()
        results = service.search('yoga', lang='english')
        
        assert len(results) > 0
        assert all('yoga' in r['translation_en'].lower() for r in results)

def test_search_sanskrit(app):
    with app.app_context():
        service = SearchService()
        results = service.search('योग', lang='sanskrit')
        
        assert len(results) > 0

def test_search_fuzzy(app):
    with app.app_context():
        service = SearchService()
        results = service.search('yog', lang='all')  # Partial match
        
        assert len(results) > 0
```

### 9.2 Frontend Tests

```typescript
// frontend/src/components/__tests__/ClickableWord.test.tsx

import { render, screen, fireEvent } from '@testing-library/react';
import { ClickableWord } from '../ClickableWord';

const mockWord = {
  word: 'योग',
  word_slp1: 'yoga',
  position: 0,
  transliteration: 'yoga',
  meaning: 'union',
  is_compound: false
};

test('renders word correctly', () => {
  render(<ClickableWord word={mockWord} onWordClick={() => {}} />);
  expect(screen.getByText('योग')).toBeInTheDocument();
});

test('calls onWordClick when clicked', () => {
  const handleClick = jest.fn();
  render(<ClickableWord word={mockWord} onWordClick={handleClick} />);
  
  fireEvent.click(screen.getByText('योग'));
  expect(handleClick).toHaveBeenCalledWith(mockWord);
});

test('shows selected state', () => {
  render(<ClickableWord word={mockWord} onWordClick={() => {}} isSelected={true} />);
  expect(screen.getByText('योग')).toHaveClass('bg-amber-200');
});
```

### 9.3 End-to-End Tests

```typescript
// frontend/e2e/sutra.spec.ts (Playwright)

import { test, expect } from '@playwright/test';

test('can navigate to sutra and click word for dictionary', async ({ page }) => {
  await page.goto('/');
  
  // Click on first sutra
  await page.click('text=1.1');
  
  // Verify sutra is displayed
  await expect(page.locator('.sanskrit-text')).toContainText('अथ योगानुशासनम्');
  
  // Click on a word
  await page.click('text=योग');
  
  // Verify dictionary panel opens
  await expect(page.locator('.dictionary-panel')).toBeVisible();
  await expect(page.locator('.dictionary-panel')).toContainText('Monier-Williams');
});

test('search works with fuzzy matching', async ({ page }) => {
  await page.goto('/');
  
  // Enter search query
  await page.fill('input[placeholder*="Search"]', 'samadhi');
  await page.press('input[placeholder*="Search"]', 'Enter');
  
  // Verify results
  await expect(page.locator('.search-results')).toBeVisible();
  await expect(page.locator('.search-result')).toHaveCount.greaterThan(0);
});
```

---

## Document Control

| Version | Date       | Author | Changes       |
| ------- | ---------- | ------ | ------------- |
| 1.0     | 2026-01-11 | Claude | Initial draft |

---

*End of Design Document*
