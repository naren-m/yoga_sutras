# Yoga Sutras Platform

A generic Sanskrit reading platform, starting with the Yoga Sutras of Patanjali. exact implementation of the design document.

## Overview

This application provides a rich reading experience for Sanskrit texts, featuring:
- **Sandhi Splitting**: Compound words are split into components using [Vidyut](https://github.com/ambuda-org/vidyut).
- **Dictionary Lookup**: Integrated dictionaries (Monier-Williams, Apte).
- **Generic Architecture**: Support for any Sanskrit text (Text -> Section -> Block).
- **Offline First**: All data and processing (including Sandhi) happen locally.

## Architecture

- **Backend**: Python/Flask (REST API, SQLAlchemy, Vidyut integration).
- **Frontend**: React (TypeScript, Tailwind).
- **Database**: SQLite.
- **Infrastructure**: Docker & Docker Compose.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop)
- [Python 3.10+](https://www.python.org/) (for running data scripts locally)

## Quick Start

### 1. Start the Application

Run the entire stack with Docker Compose:

```bash
docker-compose up --build
```

- **Backend API**: http://localhost:5000
- **Frontend**: http://localhost:3000

### 2. Populate Data

The database starts empty. You need to scrape the text and download dictionaries.

**Option A: Running scripts locally (Recommended)**

```bash
# 1. Install script dependencies
pip install requests beautifulsoup4

# 2. Scrape Yoga Sutras (Creates data/yoga_sutras.json)
python scripts/scrape_text.py

# 3. Download Dictionaries (Creates data/dictionaries/...)
python scripts/seed_dictionaries.py
```

*Note: Currently, these scripts download the raw data. A future update will import this data into the SQLite database.*

## Project Structure

```
├── backend/            # Flask API
│   ├── app/
│   │   ├── models/     # Database Models (Text, Dictionary)
│   │   ├── routes/     # API Endpoints
│   │   └── services/   # Business Logic
│   └── requirements.txt
├── docker/             # Dockerfiles
├── docs/               # Architecture & Design Docs
├── frontend/           # React Frontend (to be implemented)
├── scripts/            # Data Scraping & Seeding Scripts
└── docker-compose.yml
```

## Development

**Backend Local Setup:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
```


## Resource

- Dictionanries
  https://github.com/ambuda-org/dictionaries/blob/main/src/dictionaries.yaml
