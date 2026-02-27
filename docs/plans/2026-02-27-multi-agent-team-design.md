# Multi-Agent Team Design for Yoga Sutras Phase 1 MVP

**Date:** 2026-02-27
**Status:** Approved
**Goal:** Complete Phase 1 MVP with reusable agent team

---

## Executive Summary

Design a domain-based multi-agent team to complete Phase 1 MVP:
1. All 196 sutras viewable
2. Deployed to homelab K8s with two domains

The team uses Claude Code's agent teams feature with reusable agent definitions.

---

## Agent Team Structure

### Team Composition

| Agent | Type | Location | Primary Responsibility |
|-------|------|----------|------------------------|
| **architect-agent** | New | `.claude/agents/` | System design, API contracts, coordination |
| **backend-agent** | New | `.claude/agents/` | Flask/Python APIs, data seeding, Sanskrit services |
| **frontend-agent** | Reuse | `~/.claude/agents/frontend-ui-specialist.md` | React/TypeScript, pages, styling |
| **devops-agent** | Reuse | `~/.claude/agents/homelab-devops-mentor.md` | Docker, K8s, Jenkins, deployment |
| **reviewer-agent** | Reuse | `~/.claude/agents/senior-code-reviewer.md` | Code review, quality gates |

### Hierarchy

```
                    ┌─────────────────┐
                    │ architect-agent │  ← Design decisions, coordination
                    │  (orchestrator) │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────▼────┐        ┌─────▼─────┐       ┌─────▼─────┐
    │ backend │        │ frontend  │       │  devops   │
    │  agent  │        │   agent   │       │   agent   │
    └────┬────┘        └─────┬─────┘       └─────┬─────┘
         │                   │                   │
         └───────────────────┴───────────────────┘
                             │
                    ┌────────▼────────┐
                    │ reviewer-agent  │  ← Quality gates
                    └─────────────────┘
```

---

## Phase 1 Tasks

### Backend Tasks (backend-agent)

| ID | Task | Description |
|----|------|-------------|
| B1 | Verify sutra data | Check if all 196 sutras exist in database |
| B2 | Fix scraping gaps | Re-scrape any missing sutras from shlokam.org |
| B3 | Seed database | Run seed scripts to populate data |
| B4 | API validation | Ensure all text endpoints return complete data |

### Frontend Tasks (frontend-agent)

| ID | Task | Description |
|----|------|-------------|
| F1 | Sutra list view | Display all sutras in a pada with navigation |
| F2 | Sutra detail view | Show complete sutra with word analysis |
| F3 | Loading states | Handle async data fetching gracefully |
| F4 | Error boundaries | Handle API failures elegantly |

### DevOps Tasks (devops-agent)

| ID | Task | Description |
|----|------|-------------|
| D1 | Docker images | Build and tag frontend/backend images for local registry |
| D2 | K8s manifests | Create deployment, service, ingress YAML in `~/Projects/deployment/homelab/base/applications/yoga-sutras/` |
| D3 | Multi-domain ingress | Configure ingress for `yogasutras.naren.me` AND `yogasutras.hanuma.com` |
| D4 | Jenkins pipeline | CI/CD in `backend/jenkins/Jenkinsfile` and `frontend/jenkins/Jenkinsfile` |
| D5 | Homer dashboard | Add entries for both domains in `~/Projects/deployment/homelab/homer/config.yml` |
| D6 | DNS/TLS | Ensure both domains resolve with valid certificates |

### Architect Tasks (architect-agent)

| ID | Task | Description |
|----|------|-------------|
| A1 | Task coordination | Break down work, assign to agents |
| A2 | API review | Validate API contracts are consistent |
| A3 | Integration testing | Verify end-to-end flows work |

---

## Deployment Configuration

### Domains

Both domains serve the same application:
- `yogasutras.naren.me`
- `yogasutras.hanuma.com`

### Ingress Configuration

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: yoga-sutras-ingress
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  rules:
    - host: yogasutras.naren.me
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: yoga-sutras-frontend
                port:
                  number: 80
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: yoga-sutras-backend
                port:
                  number: 5001
    - host: yogasutras.hanuma.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: yoga-sutras-frontend
                port:
                  number: 80
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: yoga-sutras-backend
                port:
                  number: 5001
  tls:
    - hosts:
        - yogasutras.naren.me
        - yogasutras.hanuma.com
      secretName: yoga-sutras-tls
```

---

## Design Workflow

### Figma-First Approach

Before implementation, create UI designs in Figma:

1. **Claude creates designs** in Figma
2. **User reviews** and provides feedback
3. **Iterate** until approved
4. **Implement** using designs as reference

### Screens to Design

| Screen | Purpose | Key Elements |
|--------|---------|--------------|
| Home | Landing + pada navigation | 4 padas, search bar, Sanskrit typography |
| Pada view | List all sutras in chapter | Sutra cards with number, Devanagari, transliteration |
| Sutra detail | Single sutra with analysis | Clickable words, dictionary panel, sandhi splits |
| Dictionary panel | Word lookup results | MW/Apte entries, morphology, dhatu info |

### Design Tokens

- **Font:** Noto Sans Devanagari for Sanskrit, Inter for UI
- **Colors:** Warm, scholarly palette (earth tones, gold accents)
- **Spacing:** Generous for Devanagari readability
- **Components:** Sutra cards, word chips, collapsible panels

---

## Agent Definitions

### New Agent: architect-agent

```markdown
---
name: architect-agent
description: Technical lead for Yoga Sutras project. Use for system design, API contracts, cross-cutting decisions, and coordinating other agents.
model: sonnet
---

You are the technical architect for the Yoga Sutras Sanskrit Reading Platform.

## Responsibilities
- Design API contracts between frontend and backend
- Make cross-cutting technical decisions
- Coordinate work across backend, frontend, and devops agents
- Review integration points and data flows
- Ensure consistency with project architecture (Text → Section → Block)

## Project Context
- Backend: Flask + SQLAlchemy + SQLite
- Frontend: React + TypeScript + Tailwind
- Sanskrit: Vidyut (sandhi), Dharmamitra (morphology), CDSL dictionaries
- Deployment: Docker + K8s on homelab

## Decision Framework
1. Favor simplicity over complexity
2. Maintain offline-first architecture
3. Keep API contracts RESTful and predictable
4. Ensure Sanskrit processing accuracy over speed
```

### New Agent: backend-agent

```markdown
---
name: backend-agent
description: Flask/Python specialist for Yoga Sutras. Use for API development, data models, Sanskrit services, and backend testing.
model: sonnet
---

You are a backend engineer specializing in the Yoga Sutras Flask application.

## Responsibilities
- Implement Flask routes and API endpoints
- Manage SQLAlchemy models (Text, TextSection, TextBlock, Dictionary)
- Build Sanskrit processing services (Sandhi, Dictionary, Morphology)
- Write data scraping and seeding scripts
- Create pytest tests for all endpoints

## Technical Context
- Framework: Flask with SQLAlchemy ORM
- Database: SQLite at data/yoga_sutras.db
- Sanskrit Tools:
  - Vidyut Cheda for sandhi splitting
  - Dharmamitra for morphological analysis
  - CDSL dictionaries (MW, Apte) with SLP1 keys
- Transliteration: indic-transliteration library

## API Patterns
- GET /api/texts - List all texts
- GET /api/texts/<slug> - Get text with sections
- GET /api/texts/<slug>/section/<section_slug> - Get section with blocks
- GET /api/dictionary/<word> - Dictionary lookup
- GET /api/split/<compound> - Sandhi splitting
- GET /api/morphology/<word> - Morphological analysis
```

---

## Implementation Order

1. **Create agent definitions** (architect-agent, backend-agent)
2. **Figma design** all screens
3. **Backend verification** (B1-B4)
4. **Frontend implementation** (F1-F4)
5. **DevOps setup** (D1-D6)
6. **Integration testing** (A2-A3)
7. **Code review** (reviewer-agent)
8. **Deploy to production**

---

## Success Criteria

Phase 1 MVP is complete when:
- [ ] All 196 sutras viewable in the UI
- [ ] Click any word → dictionary lookup works
- [ ] Sandhi splitting functional
- [ ] Deployed to homelab K8s
- [ ] Both domains accessible: `yogasutras.naren.me`, `yogasutras.hanuma.com`
- [ ] Code reviewed and approved

---

**Document Control**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-27 | Claude + Naren | Initial design |
