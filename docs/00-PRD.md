# Product Requirements Document (PRD)

# Yoga Sutras Sanskrit Reading Platform

**Version:** 1.0
**Date:** January 20, 2026
**Product Owner:** Naren Mudivarthy
**Status:** Active Development

---

## Executive Summary

A Sanskrit reading platform that makes Patanjali's Yoga Sutras accessible to modern learners through interactive word analysis, sandhi splitting, and integrated dictionary lookup. Built with a generic architecture to support any Sanskrit text.

---

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Vision & Goals](#2-vision--goals)
3. [Target Users](#3-target-users)
4. [Product Overview](#4-product-overview)
5. [Core Features](#5-core-features)
6. [User Experience](#6-user-experience)
7. [Technical Architecture](#7-technical-architecture)
8. [Data Strategy](#8-data-strategy)
9. [Success Metrics](#9-success-metrics)
10. [Roadmap](#10-roadmap)
11. [Risks & Mitigations](#11-risks--mitigations)
12. [Appendix](#12-appendix)

---

## 1. Problem Statement

### The Challenge

Learning Sanskrit texts like the Yoga Sutras presents unique challenges:

| Challenge | Impact |
|-----------|--------|
| **Sandhi Complexity** | Sanskrit words merge at boundaries (sandhi), making individual word lookup impossible without splitting |
| **Dictionary Access** | Traditional dictionaries require knowledge of root forms and grammar |
| **Script Barriers** | Learners may know Devanagari, IAST, or other scripts - but not all |
| **Fragmented Tools** | Text, translation, dictionary, and analysis exist in separate resources |
| **No Offline Support** | Existing tools (like Ambuda.org) require internet connectivity |

### Current Alternatives

| Solution | Limitations |
|----------|-------------|
| **Ambuda.org** | Excellent but online-only; no offline mode |
| **Physical Books** | No word lookup; require separate dictionary |
| **Google Translate** | Inaccurate for classical Sanskrit |
| **PDF/E-books** | Static; no interactive features |

### Opportunity

Create an offline-first Sanskrit reading platform that combines text display, sandhi analysis, and dictionary lookup in a unified, interactive experience.

---

## 2. Vision & Goals

### Product Vision

> *"Understand any Sanskrit word in context, with a single click."*

### Strategic Goals

| Goal | Description | Timeframe |
|------|-------------|-----------|
| **G1: Core Reading Experience** | Display all 196 Yoga Sutras with word-level interactivity | Phase 1 |
| **G2: Dictionary Integration** | Monier-Williams + Apte lookup for any word | Phase 1 |
| **G3: Sandhi Intelligence** | Split compound words automatically using Vidyut | Phase 1 |
| **G4: Offline-First** | Full functionality without internet | Phase 1 |
| **G5: Generic Architecture** | Support additional texts (Bhagavad Gita, Ramayana) | Phase 2 |
| **G6: Community Features** | Bookmarks, notes, sharing | Phase 3 |

### Non-Goals (Explicit Exclusions)

- Real-time collaborative editing
- User-generated translations
- Sanskrit grammar instruction
- Audio/video content (MVP)

---

## 3. Target Users

### Primary Personas

#### Persona 1: The Yoga Practitioner (Maya)

| Attribute | Detail |
|-----------|--------|
| **Background** | Yoga teacher, 5+ years of practice |
| **Sanskrit Level** | Beginner - can read Devanagari slowly |
| **Goal** | Understand original sutras to deepen teaching |
| **Pain Point** | Doesn't know how to look up compound words |
| **Success Criteria** | Can understand word meaning by clicking on it |

#### Persona 2: The Sanskrit Student (Arjun)

| Attribute | Detail |
|-----------|--------|
| **Background** | Graduate student studying Indology |
| **Sanskrit Level** | Intermediate - understands sandhi rules |
| **Goal** | Research-quality text with multiple dictionary sources |
| **Pain Point** | Switching between text and separate dictionary apps |
| **Success Criteria** | Multiple dictionary entries side-by-side |

#### Persona 3: The Self-Learner (Priya)

| Attribute | Detail |
|-----------|--------|
| **Background** | Software engineer interested in philosophy |
| **Sanskrit Level** | Zero - relies on transliteration |
| **Goal** | Read original text alongside English translation |
| **Pain Point** | No context when encountering a new word |
| **Success Criteria** | Click any word, see meaning + how it fits |

### User Journey (Maya - Yoga Practitioner)

```
1. Opens app → Sees Pada navigation
2. Navigates to Sutra 1.2 (योगश्चित्तवृत्तिनिरोधः)
3. Sees compound word, confused about boundaries
4. Clicks on word → System splits: योगः + चित्त + वृत्ति + निरोधः
5. Clicks on "चित्त" → Dictionary panel shows: "mind, consciousness"
6. Reads full translation with new understanding
7. Bookmarks sutra for reference in class
```

---

## 4. Product Overview

### Core Value Proposition

| For | Who | The Product Is | That | Unlike | Our Product |
|-----|-----|----------------|------|--------|-------------|
| Sanskrit learners | Want to understand classical texts | An interactive reading platform | Provides word-level analysis with one click | Ambuda.org (online-only) or physical dictionaries | Works offline with local sandhi processing |

### Product Principles

1. **Click-to-Understand**: Any word should reveal its meaning in one interaction
2. **Offline-First**: All functionality works without internet after initial setup
3. **Progressive Complexity**: Show translation first, reveal analysis on demand
4. **Generic Architecture**: Build once, apply to any Sanskrit text
5. **Respect the Text**: Accurate representation, no oversimplification

### System Context Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER                                    │
│     (Browser: Desktop / Mobile / Tablet)                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │  Text    │  │  Search  │  │Dictionary│  │Navigation│        │
│  │  Display │  │  Module  │  │  Panel   │  │  Module  │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST API
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND (Flask)                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                      │
│  │  Text    │  │Dictionary│  │  Sandhi  │                      │
│  │  Service │  │  Service │  │  Service │                      │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                      │
│       │             │             │                             │
│       ▼             ▼             ▼                             │
│  ┌──────────────────────────────────────┐                      │
│  │           SQLite Database            │                      │
│  │  (Texts, Dictionaries, Analysis)     │                      │
│  └──────────────────────────────────────┘                      │
│                      │                                          │
│                      ▼                                          │
│            ┌──────────────────┐                                │
│            │   Vidyut (Rust)  │                                │
│            │   Sandhi Engine  │                                │
│            └──────────────────┘                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Core Features

### Feature Matrix

| ID | Feature | Priority | Status | Phase |
|----|---------|----------|--------|-------|
| F1 | Sutra Display (Devanagari + IAST + Translation) | P0 | In Progress | 1 |
| F2 | Dictionary Lookup (Monier-Williams, Apte) | P0 | In Progress | 1 |
| F3 | Sandhi Splitting (Vidyut Integration) | P0 | In Progress | 1 |
| F4 | Pada Navigation (4 chapters) | P0 | In Progress | 1 |
| F5 | Fuzzy Search (Sanskrit + English) | P1 | Planned | 1 |
| F6 | Clickable Word Analysis | P0 | In Progress | 1 |
| F7 | Transliteration Toggle | P1 | Planned | 1 |
| F8 | Bookmarks/Favorites | P2 | Planned | 2 |
| F9 | Additional Texts (Bhagavad Gita) | P2 | Planned | 2 |
| F10 | Audio Pronunciation | P3 | Future | 3 |

### Feature Details

#### F1: Sutra Display

**User Story**: *As a reader, I want to see each sutra with its translation so I can understand both the original and meaning.*

| Component | Description |
|-----------|-------------|
| Sanskrit Text | Devanagari script, large readable font |
| Transliteration | IAST with proper diacritics |
| Word-by-Word | Each word separated, clickable |
| Translation | Clear English rendering |
| Commentary | Optional, collapsible section |

**Acceptance Criteria**:
- [ ] All 196 sutras display correctly
- [ ] Devanagari renders without tofu characters
- [ ] Each word is individually clickable
- [ ] Translation is always visible below text

---

#### F2: Dictionary Lookup

**User Story**: *As a learner, I want to look up any word and see its meaning from authoritative sources.*

| Dictionary | Priority | Entries | Purpose |
|------------|----------|---------|---------|
| Monier-Williams (MW) | Primary | 186,000 | Comprehensive definitions |
| Apte (AP90) | Secondary | 60,000 | Concise, practical |

**Acceptance Criteria**:
- [ ] Dictionary panel opens on word click
- [ ] Results appear within 200ms
- [ ] Multiple dictionary entries shown
- [ ] Etymology and grammar info displayed when available

---

#### F3: Sandhi Splitting

**User Story**: *As a reader, I want compound words split automatically so I can understand each component.*

**Technical Approach**: Vidyut Cheda (Rust-based sandhi splitter)

| Example | Input | Output |
|---------|-------|--------|
| Sutra 1.2 | योगश्चित्तवृत्तिनिरोधः | योगः + चित्त + वृत्ति + निरोधः |

**Acceptance Criteria**:
- [ ] Compound words identified and split
- [ ] Each component is clickable for lookup
- [ ] Visual indication of word boundaries
- [ ] Graceful fallback if split fails

---

#### F6: Clickable Word Analysis

**User Story**: *As a reader, I want to click any word and see its analysis including meaning, grammar, and related forms.*

**Interaction Flow**:
```
Click Word → Check if Compound → If Yes: Show Split Options
                               → If No: Show Dictionary Entry

Dictionary Entry Shows:
├── Word in Devanagari
├── Word in IAST
├── Base Form (if inflected)
├── Grammar (gender, case, number)
├── MW Definition
├── Apte Definition
└── Etymology (if available)
```

---

## 6. User Experience

### Information Architecture

```
Yoga Sutras Platform
├── Home
│   └── Welcome + Quick Jump to any Sutra
├── Read
│   ├── Pada I: Samadhi (51 sutras)
│   ├── Pada II: Sadhana (55 sutras)
│   ├── Pada III: Vibhuti (56 sutras)
│   └── Pada IV: Kaivalya (34 sutras)
├── Search
│   └── Full-text across Sanskrit + English
├── Dictionary (Standalone)
│   └── Direct word lookup
└── Settings
    ├── Script Preference
    ├── Font Size
    └── Theme
```

### Wireframes

#### Desktop: Main Reading View

```
┌──────────────────────────────────────────────────────────────────────────┐
│  🕉 Yoga Sutras         [____Search...____]  [🔍]      [Script ▼] [≡]   │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌──────────────────────────────────────────┐  ┌─────────────────────┐ │
│   │                                          │  │                     │ │
│   │  Sutra 1.2                               │  │   Dictionary        │ │
│   │                                          │  │                     │ │
│   │  ┌────────────────────────────────────┐  │  │   चित्त             │ │
│   │  │   योगश्चित्तवृत्तिनिरोधः              │  │  │   citta            │ │
│   │  │   ^^^^^^^^^^^^^^^^^^^^              │  │  │                     │ │
│   │  │   (click any word)                  │  │  │   ─────────────     │ │
│   │  └────────────────────────────────────┘  │  │   Monier-Williams:  │ │
│   │                                          │  │   "thought, mind,   │ │
│   │  yogaś-citta-vṛtti-nirodhaḥ              │  │   consciousness..."  │ │
│   │                                          │  │                     │ │
│   │  ─────────────────────────────────────── │  │   ─────────────     │ │
│   │                                          │  │   Apte:             │ │
│   │  Yoga is the cessation of the           │  │   "The heart, mind" │ │
│   │  modifications of the mind.              │  │                     │ │
│   │                                          │  │   ─────────────     │ │
│   │  ─────────────────────────────────────── │  │   Grammar:          │ │
│   │                                          │  │   n. (neuter)       │ │
│   │  [▸ Commentary]                          │  │                     │ │
│   │                                          │  │                     │ │
│   │  [◀ 1.1 Prev]              [Next 1.3 ▶]  │  └─────────────────────┘ │
│   └──────────────────────────────────────────┘                          │
│                                                                          │
├──────────────────────────────────────────────────────────────────────────┤
│   I. Samadhi (51)  │  II. Sadhana (55)  │  III. Vibhuti (56)  │  IV. Kaivalya │
└──────────────────────────────────────────────────────────────────────────┘
```

#### Mobile: Reading View + Dictionary Sheet

```
┌────────────────────┐     ┌────────────────────┐
│ [≡]  Sutras   [🔍] │     │ [≡]  Sutras   [🔍] │
├────────────────────┤     ├────────────────────┤
│                    │     │                    │
│ Sutra 1.2          │     │ ┌────────────────┐ │
│                    │     │ │ चित्त  citta   │ │
│ योगश्चित्त...       │     │ │                │ │
│ (tap word)         │     │ │ MW: thought,   │ │
│                    │     │ │ mind...        │ │
│ yogaś-citta...     │ ──► │ │                │ │
│                    │     │ │ Apte: heart,   │ │
│ Yoga is the        │     │ │ mind           │ │
│ cessation...       │     │ │                │ │
│                    │     │ │ [×] Close      │ │
│ [◀]         [▶]    │     │ └────────────────┘ │
├────────────────────┤     ├────────────────────┤
│ I │ II │ III │ IV  │     │ I │ II │ III │ IV  │
└────────────────────┘     └────────────────────┘
     (Tap word)              (Dictionary sheet)
```

### Design Tokens

| Token | Value | Usage |
|-------|-------|-------|
| `--color-sanskrit` | `#8B4513` (Sienna) | Devanagari text |
| `--color-transliteration` | `#4A5568` (Gray 600) | IAST text |
| `--color-translation` | `#1A202C` (Gray 900) | English text |
| `--font-sanskrit` | `'Noto Sans Devanagari', serif` | Devanagari script |
| `--font-body` | `'Inter', sans-serif` | UI and translation |
| `--spacing-word` | `0.25rem` | Between clickable words |

---

## 7. Technical Architecture

### Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Frontend** | React + TypeScript + Tailwind | Modern, type-safe, rapid UI development |
| **Backend** | Flask + SQLAlchemy | Lightweight, Python ecosystem for Sanskrit tools |
| **Database** | SQLite | Offline-capable, zero-configuration |
| **Sandhi Engine** | Vidyut (via vidyut-py) | Best-in-class Sanskrit processing |
| **Search** | rapidfuzz | Fuzzy matching for typo tolerance |
| **Deployment** | Docker → Kubernetes | Self-hosted on homelab |

### Data Model

```
┌─────────────────────────────────────────────────────────────┐
│                      TEXT HIERARCHY                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Text (e.g., "Yoga Sutras")                                │
│    │                                                        │
│    └── TextSection (e.g., "Samadhi Pada")                  │
│          │                                                  │
│          └── TextBlock (e.g., Sutra 1.2)                   │
│                ├── content (Devanagari)                    │
│                ├── content_transliteration (IAST)          │
│                ├── content_meaning (English)               │
│                ├── word_analysis (JSON)                    │
│                └── commentary                              │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                      DICTIONARY                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Dictionary (e.g., "Monier-Williams")                      │
│    │                                                        │
│    └── DictionaryEntry                                     │
│          ├── key (SLP1 encoding)                           │
│          └── value (HTML/XML definition)                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### API Design

| Endpoint | Method | Description | Response |
|----------|--------|-------------|----------|
| `/api/texts/{slug}` | GET | Full text with sections | Text + Sections |
| `/api/texts/{slug}/section/{section_slug}` | GET | Section with blocks | Section + Blocks |
| `/api/dictionary/{word}` | GET | Dictionary lookup | Definitions[] |
| `/api/split/{compound}` | GET | Sandhi splitting | Split results |
| `/api/search?q={query}` | GET | Fuzzy search | Matching blocks |

### Offline Strategy

| Data | Storage | Size | Update Frequency |
|------|---------|------|------------------|
| Sutras (196) | SQLite | ~500 KB | One-time |
| Word Analysis | SQLite | ~1 MB | With sutras |
| MW Dictionary | SQLite | ~150 MB | Yearly |
| Apte Dictionary | SQLite | ~50 MB | Yearly |
| Vidyut Data | Filesystem | ~50 MB | With releases |

**Total offline footprint**: ~250 MB

---

## 8. Data Strategy

### Data Sources

| Data | Source | Format | Acquisition Method |
|------|--------|--------|-------------------|
| Yoga Sutras text | shlokam.org | HTML | Web scraping (BeautifulSoup) |
| Monier-Williams | Cologne (CDSL) | XML | Download & parse |
| Apte | Cologne (CDSL) | XML | Download & parse |
| Vidyut linguistic data | ambuda-org/vidyut | Binary | Bundled with release |

### Data Pipeline

```
┌────────────┐     ┌────────────┐     ┌────────────┐     ┌────────────┐
│  External  │ ──► │   Scrape/  │ ──► │  Transform │ ──► │   SQLite   │
│  Sources   │     │  Download  │     │  & Clean   │     │  Database  │
└────────────┘     └────────────┘     └────────────┘     └────────────┘
                         │
                         ▼
                   data/yoga_sutras.json
                   data/dictionaries/
```

### Data Quality

| Metric | Target | Validation |
|--------|--------|------------|
| Sutra completeness | 196/196 (100%) | Automated count check |
| Dictionary coverage | MW + Apte loaded | Entry count > threshold |
| Sandhi accuracy | 80%+ correct splits | Manual sampling (20 sutras) |
| Unicode integrity | Zero tofu characters | Visual inspection + test suite |

---

## 9. Success Metrics

### Key Performance Indicators (KPIs)

| Metric | Definition | Target | Measurement |
|--------|------------|--------|-------------|
| **Word Lookup Time** | Time from click to definition shown | < 200ms | Performance monitoring |
| **Sandhi Split Accuracy** | % of compounds correctly split | > 80% | Manual evaluation |
| **Dictionary Coverage** | % of clicked words with definitions | > 95% | Log analysis |
| **Page Load Time** | Initial sutra display time | < 2s | Lighthouse |
| **Offline Success Rate** | % of requests served offline | 100% | Service worker logs |

### User Engagement Metrics (Phase 2+)

| Metric | Description | Target |
|--------|-------------|--------|
| Daily Active Users | Unique users/day | 10+ |
| Sutras Read/Session | Average blocks viewed | 5+ |
| Dictionary Lookups/Session | Word clicks per visit | 10+ |
| Return Rate | Users returning within 7 days | 40% |

---

## 10. Roadmap

### Phase 1: MVP (Current - 4 weeks)

**Goal**: Complete reading experience for Yoga Sutras

| Week | Deliverable |
|------|-------------|
| 1 | Backend APIs complete (text, dictionary, sandhi) |
| 2 | Frontend: Sutra display + navigation |
| 3 | Frontend: Dictionary panel + word interaction |
| 4 | Integration testing + deployment |

**Exit Criteria**:
- [ ] All 196 sutras viewable
- [ ] Click any word → dictionary lookup works
- [ ] Sandhi splitting functional
- [ ] Deployed to homelab K8s

### Phase 2: Enhancement (Weeks 5-8)

| Feature | Priority |
|---------|----------|
| Fuzzy search across text | P1 |
| Bookmarks & favorites | P2 |
| Transliteration toggle | P1 |
| Additional dictionaries | P2 |
| PWA offline mode | P1 |

### Phase 3: Expansion (Future)

| Feature | Description |
|---------|-------------|
| Additional texts | Bhagavad Gita, Ramayana |
| Audio pronunciation | TTS or recorded audio |
| User notes | Personal annotations |
| Community features | Shared bookmarks, discussions |

---

## 11. Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Vidyut integration fails** | Medium | High | Fallback to simple whitespace splitting; document known limitations |
| **Scraping blocked by shlokam.org** | Low | High | Backup data source (sanskritdocuments.org); request permission |
| **Dictionary data too large** | Low | Medium | Lazy loading; only load entries as needed |
| **Devanagari rendering issues** | Medium | Medium | Bundle Noto Sans Devanagari; test on multiple devices |
| **Sandhi accuracy below target** | Medium | Medium | Pre-compute and cache verified splits; allow user correction |

---

## 12. Appendix

### A. Yoga Sutras Structure

| Pada | Sanskrit | English | Sutras | Theme |
|------|----------|---------|--------|-------|
| I | समाधिपाद | Samadhi Pada | 1-51 | On Contemplation |
| II | साधनपाद | Sadhana Pada | 1-55 | On Practice |
| III | विभूतिपाद | Vibhuti Pada | 1-56 | On Powers |
| IV | कैवल्यपाद | Kaivalya Pada | 1-34 | On Liberation |
| | | **Total** | **196** | |

### B. Competitive Analysis

| Feature | This Project | Ambuda.org | Wisdom Library | Books |
|---------|--------------|------------|----------------|-------|
| Offline | ✅ | ❌ | ❌ | ✅ |
| Sandhi Split | ✅ (Vidyut) | ✅ | ❌ | ❌ |
| Dictionary | ✅ MW+Apte | ✅ Multiple | ❌ | ❌ |
| Click-to-Lookup | ✅ | ✅ | ❌ | ❌ |
| Self-Hosted | ✅ | ❌ | ❌ | N/A |
| Generic Text Support | ✅ | ✅ | Partial | N/A |

### C. Glossary

| Term | Definition |
|------|------------|
| **Sandhi** | Euphonic combination where adjacent sounds in Sanskrit modify each other |
| **Devanagari** | The primary script used to write Sanskrit (देवनागरी) |
| **IAST** | International Alphabet of Sanskrit Transliteration (with diacritics) |
| **SLP1** | Sanskrit Library Phonetic Basic encoding (ASCII-safe, used by CDSL) |
| **Vidyut** | Rust-based Sanskrit NLP library by Ambuda (includes Cheda for sandhi splitting) |
| **CDSL** | Cologne Digital Sanskrit Lexicon - source for digital Sanskrit dictionaries |

### D. Related Documents

| Document | Location | Description |
|----------|----------|-------------|
| Software Requirements Specification | `docs/01-REQUIREMENTS.md` | Technical requirements |
| Technical Design | `docs/02-DESIGN.md` | Architecture & implementation |
| CLAUDE.md | `CLAUDE.md` | Developer quick reference |

---

**Document Control**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-20 | Naren + Claude | Initial PRD |

---

*This PRD complements the existing SRS (`01-REQUIREMENTS.md`) by focusing on product vision, user needs, and success metrics rather than technical specifications.*
