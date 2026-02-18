# Software Requirements Specification (SRS)

# Yoga Sutras of Patanjali - Searchable Digital Library

**Version:** 1.0  
**Date:** January 11, 2026  
**Project Code:** YOGA-SUTRAS-LIB  
**Status:** Draft for Review

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Overall Description](#2-overall-description)
3. [Functional Requirements](#3-functional-requirements)
4. [Non-Functional Requirements](#4-non-functional-requirements)
5. [Data Requirements](#5-data-requirements)
6. [External Interface Requirements](#6-external-interface-requirements)
7. [Appendices](#7-appendices)

---

## 1. Introduction

### 1.1 Purpose

This document specifies the requirements for a web-based digital library application for studying Patanjali's Yoga Sutras. The application will provide searchable access to all 196 sutras with Sanskrit text, transliteration, English translations, and word-by-word analysis with dictionary lookup capabilities.

### 1.2 Scope

The Yoga Sutras Digital Library will:

- Download all 196 sutras from shlokam.org along with their  original sanskrit, transliteration, commentary and english translations
- Display all 196 sutras organized by their four padas (chapters)
- Provide fuzzy search across Sanskrit and English content
- Enable click-on-word dictionary lookup (similar to Ambuda.org)
- Support sandhi/compound word splitting for complex Sanskrit terms
- Integrate multiple Sanskrit dictionaries (Monier-Williams, Apte, Amarakosha, etc.)

### 1.3 Definitions and Acronyms

| Term             | Definition                                              |
| ---------------- | ------------------------------------------------------- |
| **Sutra**        | An aphorism or concise statement (Sanskrit: सूत्र)        |
| **Pada**         | Chapter or section (the Yoga Sutras has 4 padas)        |
| **Sandhi**       | Euphonic combination where words merge at boundaries    |
| **Devanagari**   | The script used to write Sanskrit (देवनागरी)               |
| **IAST**         | International Alphabet of Sanskrit Transliteration      |
| **SLP1**         | Sanskrit Library Phonetic encoding (used by CDSL)       |
| **CDSL**         | Cologne Digital Sanskrit Lexicon                        |
| **Fuzzy Search** | Search that finds approximate matches, tolerating typos |

### 1.4 References

| Reference   | Description                        | URL                                          |
| ----------- | ---------------------------------- | -------------------------------------------- |
| Ambuda.org  | Reference implementation for UI/UX | <https://ambuda.org>                         |
| Shlokam.org | Primary data source for sutras     | <https://shlokam.org/yogasutra/>             |
| CDSL        | Dictionary data source             | <https://www.sanskrit-lexicon.uni-koeln.de/> |
| PyCDSL      | Python library for CDSL access     | <https://github.com/hrishikeshrt/PyCDSL>     |
| indic-dict  | Additional dictionary sources      | <https://github.com/indic-dict>              |

### 1.5 Project Background

This project is inspired by a similar Ramayana slokas project previously built using Python, BeautifulSoup, SQLite, and fuzzy search. The Yoga Sutras application will follow a similar architecture but with enhanced features for word-level analysis and dictionary integration.

---

## 2. Overall Description

### 2.1 Product Perspective

The application is a standalone web application that will:

- Run as a Flask backend with React frontend
- Store data in SQLite database
- Be deployable on a home Kubernetes cluster or cloud platform
- Be accessible via subdomain (e.g., yogasutras.naren.me)

### 2.2 Product Features (High-Level)

| Feature ID | Feature Name                      | Priority    |
| ---------- | --------------------------------- | ----------- |
| F001       | Sutra Display                     | Must Have   |
| F002       | Fuzzy Search (Sanskrit + English) | Must Have   |
| F003       | Click-on-Word Dictionary Lookup   | Must Have   |
| F004       | Sandhi/Compound Splitting         | Should Have |
| F005       | Multiple Dictionary Support       | Must Have   |
| F006       | Navigation by Pada/Sutra Number   | Must Have   |
| F007       | Transliteration Toggle            | Should Have |
| F008       | Bookmarking/Favorites             | Could Have  |
| F009       | Audio Pronunciation               | Could Have  |
| F010       | Commentary Display                | Should Have |

### 2.3 User Classes and Characteristics

| User Class        | Description                                | Technical Level |
| ----------------- | ------------------------------------------ | --------------- |
| Sanskrit Student  | Learning Sanskrit, needs word meanings     | Low-Medium      |
| Yoga Practitioner | Studying philosophy, needs translations    | Low             |
| Scholar           | Research purposes, needs detailed analysis | High            |
| Developer         | Extending/maintaining the system           | High            |

### 2.4 Operating Environment

- **Server:** Linux (Ubuntu 22.04+), Python 3.10+, Node.js 18+
- **Client:** Modern web browsers (Chrome, Firefox, Safari, Edge)
- **Database:** SQLite 3.x (upgradeable to PostgreSQL)
- **Deployment:** Docker/Kubernetes compatible

### 2.5 Constraints

1. Must work offline after initial data load (dictionary data cached locally)
2. Must handle Devanagari Unicode correctly
3. Must support multiple transliteration schemes
4. Dictionary data subject to CDSL licensing (CC BY-NC-SA 3.0)

---

## 3. Functional Requirements

### 3.1 Sutra Display (F001)

#### FR-001: Display Individual Sutra

- **Description:** Display a single sutra with all its components
- **Input:** Sutra identifier (pada.sutra_number, e.g., "1.2")
- **Output:**
  - Sanskrit text in Devanagari
  - Transliteration (IAST)
  - Word-by-word breakdown
  - English translation
  - Commentary (if available)
- **Priority:** Must Have

#### FR-002: Display Sutra List by Pada

- **Description:** Show all sutras in a pada as a navigable list
- **Input:** Pada number (1-4)
- **Output:** List of sutras with number, first line in Sanskrit, first line in English
- **Priority:** Must Have

#### FR-003: Navigate Between Sutras

- **Description:** Previous/Next navigation between sutras
- **Input:** Current sutra ID + direction
- **Output:** Adjacent sutra display
- **Priority:** Must Have

### 3.2 Search Functionality (F002)

#### FR-004: Fuzzy Search - Sanskrit

- **Description:** Search sutras by Sanskrit text (Devanagari or transliteration)
- **Input:** Search query string
- **Algorithm:** Fuzzy matching with Levenshtein distance ≤ 2
- **Output:** Ranked list of matching sutras with relevance score
- **Priority:** Must Have

#### FR-005: Fuzzy Search - English

- **Description:** Search sutras by English translation text
- **Input:** Search query string (English)
- **Algorithm:** Full-text search with fuzzy matching
- **Output:** Ranked list of matching sutras
- **Priority:** Must Have

#### FR-006: Combined Search

- **Description:** Search across both Sanskrit and English simultaneously
- **Input:** Search query
- **Output:** Combined results from both, deduplicated
- **Priority:** Must Have

#### FR-007: Search Suggestions

- **Description:** Auto-complete suggestions as user types
- **Input:** Partial search query (≥2 characters)
- **Output:** Top 5-10 suggestions
- **Priority:** Should Have

### 3.3 Word Analysis and Dictionary (F003, F005)

#### FR-008: Clickable Words

- **Description:** Each word in the sutra is clickable
- **Input:** Click/tap on a Sanskrit word
- **Output:** Dictionary panel opens with word definition
- **Priority:** Must Have

#### FR-009: Dictionary Lookup

- **Description:** Look up word in multiple dictionaries
- **Input:** Sanskrit word (Devanagari or transliterated)
- **Output:** Definitions from:
  - Monier-Williams (MW) - Primary
  - Apte Sanskrit-English (AP90)
  - Amarakosha (thesaurus)
  - Shabda-Sagara (SHS)
  - Vacaspatyam (Sanskrit-Sanskrit, optional)
- **Priority:** Must Have

#### FR-010: Dictionary Panel Display

- **Description:** Side panel showing dictionary results
- **Components:**
  - Word in Devanagari
  - Word in transliteration
  - Grammatical info (gender, case, etc. if available)
  - Multiple dictionary entries (collapsible)
- **Priority:** Must Have

### 3.4 Sandhi Splitting (F004)

#### FR-011: Automatic Sandhi Detection

- **Description:** Identify compound words that can be split
- **Input:** Sanskrit word/phrase
- **Output:** List of possible splits with confidence scores
- **Priority:** Should Have

#### FR-012: Display Split Words

- **Description:** Show component words after sandhi splitting
- **Input:** Compound word
- **Output:** Visual display of components (e.g., "योगश्चित्तवृत्तिनिरोधः" → "योगः + चित्त + वृत्ति + निरोधः")
- **Priority:** Should Have

#### FR-013: Lookup Split Components

- **Description:** Each split component is clickable for dictionary lookup
- **Input:** Click on component word
- **Output:** Dictionary definition of that component
- **Priority:** Should Have

### 3.5 Navigation and Structure (F006)

#### FR-014: Pada Navigation

- **Description:** Navigate between the four padas
- **Padas:**
  1. Samādhi Pāda (51 sutras) - On Contemplation
  2. Sādhana Pāda (55 sutras) - On Practice
  3. Vibhūti Pāda (56 sutras) - On Powers
  4. Kaivalya Pāda (34 sutras) - On Liberation
- **Priority:** Must Have

#### FR-015: Direct Sutra Jump

- **Description:** Jump to specific sutra by number
- **Input:** Sutra reference (e.g., "2.46" or "II.46")
- **Output:** Display that sutra
- **Priority:** Must Have

#### FR-016: Table of Contents

- **Description:** Expandable TOC showing all padas and sutras
- **Output:** Hierarchical list with pada > sutra structure
- **Priority:** Should Have

### 3.6 Transliteration (F007)

#### FR-017: Script Toggle

- **Description:** Toggle between display scripts
- **Options:**
  - Devanagari (default)
  - IAST (with diacritics)
  - Harvard-Kyoto (ASCII-safe)
- **Priority:** Should Have

#### FR-018: Input Transliteration

- **Description:** Accept search input in multiple schemes
- **Supported Input:**
  - Devanagari
  - IAST
  - Harvard-Kyoto
  - ITRANS
- **Priority:** Should Have

---

## 4. Non-Functional Requirements

### 4.1 Performance

| Requirement | Specification                   |
| ----------- | ------------------------------- |
| NFR-001     | Page load time < 2 seconds      |
| NFR-002     | Search results returned < 500ms |
| NFR-003     | Dictionary lookup < 200ms       |
| NFR-004     | Support 100 concurrent users    |

### 4.2 Usability

| Requirement | Specification                        |
| ----------- | ------------------------------------ |
| NFR-005     | Mobile-responsive design             |
| NFR-006     | Keyboard navigation support          |
| NFR-007     | Font size adjustable                 |
| NFR-008     | High contrast mode for accessibility |

### 4.3 Reliability

| Requirement | Specification                                |
| ----------- | -------------------------------------------- |
| NFR-009     | 99% uptime availability                      |
| NFR-010     | Graceful degradation if dictionary API fails |
| NFR-011     | Data backup capability                       |

### 4.4 Security

| Requirement | Specification                              |
| ----------- | ------------------------------------------ |
| NFR-012     | HTTPS encryption                           |
| NFR-013     | Input sanitization (prevent XSS/injection) |
| NFR-014     | Rate limiting on API endpoints             |

### 4.5 Maintainability

| Requirement | Specification                          |
| ----------- | -------------------------------------- |
| NFR-015     | Modular codebase with clear separation |
| NFR-016     | API documentation (OpenAPI/Swagger)    |
| NFR-017     | Logging for debugging                  |
| NFR-018     | Easy dictionary updates                |

---

## 5. Data Requirements

### 5.1 Sutra Data Structure

Each sutra record must contain:

```
Sutra {
  id: string              // Unique ID (e.g., "1.2")
  pada: integer           // 1-4
  sutra_number: integer   // Number within pada
  sanskrit: string        // Devanagari text
  transliteration: string // IAST transliteration
  words: array            // Word-by-word breakdown
  translation_en: string  // English translation
  commentary: string      // Optional commentary
  word_analysis: JSON     // Pre-analyzed word data
}
```

### 5.2 Dictionary Data Structure

```
DictionaryEntry {
  id: string              // Unique entry ID
  headword: string        // Lookup word (Devanagari)
  headword_slp1: string   // SLP1 encoding for search
  dictionary: string      // Source dictionary code
  definition: string      // Definition text (may contain HTML)
  grammar: string         // Grammatical information
  etymology: string       // Word origin (if available)
}
```

### 5.3 Data Sources

| Data Type       | Source                | Format        | Update Frequency |
| --------------- | --------------------- | ------------- | ---------------- |
| Sutras          | shlokam.org           | HTML (scrape) | One-time         |
| Sutras (backup) | sanskritdocuments.org | ITX           | One-time         |
| MW Dictionary   | CDSL/PyCDSL           | XML/SQLite    | Yearly           |
| Apte Dictionary | CDSL/PyCDSL           | XML/SQLite    | Yearly           |
| Amarakosha      | CDSL/PyCDSL           | XML/SQLite    | Yearly           |
| Word Analysis   | Pre-computed          | JSON          | With sutras      |

### 5.4 Data Volume Estimates

| Data Type       | Estimated Records | Storage     |
| --------------- | ----------------- | ----------- |
| Sutras          | 196               | ~500 KB     |
| Word Analysis   | ~2,000 words      | ~1 MB       |
| MW Dictionary   | 186,000 entries   | ~150 MB     |
| Apte Dictionary | 60,000 entries    | ~50 MB      |
| Amarakosha      | 10,000 entries    | ~10 MB      |
| **Total**       |                   | **~220 MB** |

---

## 6. External Interface Requirements

### 6.1 User Interfaces

#### 6.1.1 Main Layout (Desktop)

```
┌─────────────────────────────────────────────────────────────────┐
│  [Logo] Yoga Sutras    [Search Bar............] [🔍]   [≡ Menu] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────┐  ┌──────────────┐ │
│  │                                         │  │              │ │
│  │         SUTRA DISPLAY AREA              │  │  DICTIONARY  │ │
│  │                                         │  │    PANEL     │ │
│  │  Sanskrit: योगश्चित्तवृत्तिनिरोधः         │  │              │ │
│  │  (clickable words)                      │  │  Word: योग   │ │
│  │                                         │  │              │ │
│  │  Transliteration: yogaś-citta-vṛtti...  │  │  MW: yoga... │ │
│  │                                         │  │  Apte: ...   │ │
│  │  Translation: Yoga is the cessation...  │  │              │ │
│  │                                         │  │              │ │
│  │  [◀ Prev]              [Next ▶]         │  │              │ │
│  └─────────────────────────────────────────┘  └──────────────┘ │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  Pada I: Samādhi (51) | Pada II: Sādhana (55) | III | IV       │
└─────────────────────────────────────────────────────────────────┘
```

![alt text](<ambuda_example.png>)

#### 6.1.2 Mobile Layout

```
┌────────────────────────┐
│ [≡] Yoga Sutras   [🔍] │
├────────────────────────┤
│  [Search Bar........]  │
├────────────────────────┤
│                        │
│  Sutra 1.2             │
│                        │
│  योगश्चित्तवृत्तिनिरोधः          │
│  (tap words for def)   │
│                        │
│  yogaś-citta-vṛtti-    │
│  nirodhaḥ              │
│                        │
│  Yoga is the cessation │
│  of the modifications  │
│  of the mind.          │
│                        │
│  [◀ Prev]   [Next ▶]   │
│                        │
├────────────────────────┤
│  I | II | III | IV     │
└────────────────────────┘

(Dictionary as bottom sheet on word tap)
```

### 6.2 API Endpoints

| Endpoint                 | Method | Description                    |
| ------------------------ | ------ | ------------------------------ |
| `/api/sutras`            | GET    | List all sutras (paginated)    |
| `/api/sutras/{id}`       | GET    | Get single sutra by ID         |
| `/api/sutras/pada/{n}`   | GET    | Get all sutras in pada n       |
| `/api/search`            | GET    | Search sutras (query param: q) |
| `/api/dictionary/{word}` | GET    | Lookup word in dictionaries    |
| `/api/split/{compound}`  | GET    | Split compound word            |
| `/api/transliterate`     | POST   | Convert between scripts        |

### 6.3 External Systems

| System                | Integration Type | Purpose           |
| --------------------- | ---------------- | ----------------- |
| PyCDSL                | Python Library   | Dictionary access |
| sanskrit_parser       | Python Library   | Sandhi splitting  |
| indic-transliteration | Python Library   | Script conversion |

---

## 7. Appendices

### 7.1 Yoga Sutras Structure

| Pada | Name          | Sanskrit | Sutras  | Topic         |
| ---- | ------------- | -------- | ------- | ------------- |
| I    | Samādhi Pāda  | समाधिपाद    | 1-51    | Contemplation |
| II   | Sādhana Pāda  | साधनपाद    | 1-55    | Practice      |
| III  | Vibhūti Pāda  | विभूतिपाद    | 1-56    | Powers        |
| IV   | Kaivalya Pāda | कैवल्यपाद   | 1-34    | Liberation    |
|      | **Total**     |          | **196** |               |

### 7.2 Sample Sutra Data

```json
{
  "id": "1.2",
  "pada": 1,
  "sutra_number": 2,
  "sanskrit": "योगश्चित्तवृत्तिनिरोधः",
  "transliteration": "yogaś-citta-vṛtti-nirodhaḥ",
  "words": [
    {"word": "योगः", "transliteration": "yogaḥ", "meaning": "yoga"},
    {"word": "चित्त", "transliteration": "citta", "meaning": "mind"},
    {"word": "वृत्ति", "transliteration": "vṛtti", "meaning": "modifications"},
    {"word": "निरोधः", "transliteration": "nirodhaḥ", "meaning": "cessation"}
  ],
  "translation_en": "Yoga is the cessation of the modifications of the mind.",
  "commentary": "This is the definition of yoga according to Patanjali..."
}
```

### 7.3 Dictionary Entry Sample

```json
{
  "headword": "योग",
  "headword_slp1": "yoga",
  "entries": [
    {
      "dictionary": "MW",
      "definition": "the act of yoking, joining, attaching, harnessing...",
      "grammar": "m."
    },
    {
      "dictionary": "AP90", 
      "definition": "Joining, uniting. Union, junction, combination...",
      "grammar": "m. (युज्-घञ्)"
    }
  ]
}
```

### 7.4 Acceptance Criteria Summary

| Feature    | Acceptance Criteria                                 |
| ---------- | --------------------------------------------------- |
| Search     | Returns relevant results in <500ms for any query    |
| Dictionary | Shows results from at least 2 dictionaries per word |
| Navigation | User can reach any sutra in ≤3 clicks               |
| Mobile     | All features accessible on 375px width screen       |
| Sandhi     | Correctly splits 80%+ of compound words             |

---

**Document Control**

| Version | Date       | Author | Changes       |
| ------- | ---------- | ------ | ------------- |
| 1.0     | 2026-01-11 | Claude | Initial draft |

---

*End of Requirements Document*
