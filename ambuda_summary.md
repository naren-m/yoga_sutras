# Ambuda Project Summary

Ambuda is an open Sanskrit library - a Flask web application for reading, analyzing, and proofing Sanskrit texts with morphological analysis capabilities.

---

## Project Structure

```
ambuda/
├── ambuda/                 # Main application
│   ├── models/            # SQLAlchemy ORM (texts, parse, auth)
│   ├── views/             # Flask routes (reader, proofing, admin)
│   ├── utils/             # Core utilities (dharmamitra, sandhi)
│   ├── tasks/             # Celery background jobs (tagging, OCR)
│   ├── seed/              # Data import scripts (dictionaries, texts)
│   └── templates/         # Jinja2 HTML templates
├── migrations/            # Alembic database migrations
├── scripts/               # CLI tools
└── config.py              # Environment configuration
```

**Tech Stack:** Flask + SQLAlchemy + Celery + Redis | TypeScript + Alpine.js + TailwindCSS

---

## Sandhi Splitting

**Location:** `ambuda/seed/utils/sandhi_utils.py`

Sandhi is the phonetic fusion that occurs when Sanskrit words combine. This implementation follows classical Pāṇinian rules (Shiva Sutras) to reverse-engineer compound words.

The sandhi module handles three types of sound changes:

| Type | Rule | Example |
|------|------|---------|
| **Vowel (ac)** | Similar vowels merge | `aMSa + aMSa → aMSAMSa` |
| **Visarga** | `s/r` transforms before consonants | `manas + hara → manohara` |
| **Consonant (hal)** | Voicing/nasal changes | `tvac + indriya → tvagindriya` |

**Usage:** Primarily used when importing the Apte dictionary to generate compound word entries in `ambuda/seed/dictionaries/apte.py`.

---

## Dharmamitra Integration

**Location:** `ambuda/utils/dharmamitra.py`

Dharmamitra is an external Sanskrit grammar processor (package: `dharmamitra-sanskrit-grammar`) that provides automatic morphological analysis. Ambuda acts as a bridge, converting Dharmamitra's output format into its own internal representation.

### How It Works

```
Text Upload → Celery Task (tag_text) → Dharmamitra API
                                            ↓
                            DharmamitraToken (external format)
                                            ↓
                            remap_token() + Kosha lookup
                                            ↓
                            AmbudaToken (internal format)
                                            ↓
                            Store in TokenBlock/TokenRevision
```

### Key Data Flow

1. **Input:** Sanskrit text (Devanagari)
2. **API Call:** `processor.process_batch(mode="unsandhied-lemma-morphosyntax")`
3. **Response:** Tokens with `unsandhied`, `lemma`, `tag`, `meanings`
4. **Remapping:** Converts tags like `Case=Nom|Gender=Masc` → `vi=1|li=pum`
5. **Storage:** TSV format in database: `form\tbase\tparse`

### Tag Mapping Examples

| Dharmamitra | Ambuda | Meaning |
|-------------|--------|---------|
| `Case=Nom` | `vi=1` | Nominative case |
| `Gender=Masc` | `li=pum` | Masculine gender |
| `Tense=Pres` | `la=lat` | Present tense (laṭ) |

The tagging task in `ambuda/tasks/tagging.py` respects rate limits (100 sentences/minute) and uses optimistic locking for concurrent edits.

---

## Key Files Reference

| Purpose | File |
|---------|------|
| Sandhi rules | `ambuda/seed/utils/sandhi_utils.py` |
| Dharmamitra bridge | `ambuda/utils/dharmamitra.py` |
| Tagging task | `ambuda/tasks/tagging.py` |
| Parse alignment | `ambuda/utils/parse_alignment.py` |
| Token models | `ambuda/models/parse.py` |

---

## Database Models for Parse Data

**Token & Parsing Models** (`ambuda/models/parse.py`):

```python
class Token(Base):
    form: str              # Surface form (e.g., "bhArata")
    base: str              # Lemma (e.g., "bhArata")
    parse: str             # Morphological analysis
    block_id: FK           # Reference to TextBlock
    order: int             # Position in block

class TokenBlock(Base):
    text_id: FK            # Which Text
    block_id: FK           # Which TextBlock
    version: int           # For optimistic locking
    status: TokenBlockStatus (R0, R1, R2)

class TokenRevision(Base):
    data: Text             # TSV blob: form\tbase\tparse
    status: TokenBlockStatus
    token_block_id: FK
    author_id: FK          # Who made this revision
    created_at: DateTime
```

---

## Development Workflow

**Setup:**
```bash
make ambuda-dev              # Start Docker services
make ambuda-dev-shell        # Access container
uv run cli.py create-user    # Create admin user
uv run cli.py add-role       # Assign admin role
```

**Data Population:**
```bash
make db-seed-ci              # GitHub-hosted data only
make db-seed-basic           # Basic texts + dictionaries
make db-seed-all             # Complete production dataset
```

**Testing:**
```bash
make test                    # Run pytest
make js-test                 # Run Jest
make lint-check              # Check code style
```
