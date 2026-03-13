# Phase 1 MVP Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete Phase 1 MVP - all 196 sutras viewable and deployed to homelab K8s with dual domains.

**Architecture:** Figma-first design workflow, then verify backend data, enhance frontend components, deploy to K8s with ingress for both `yogasutras.naren.me` and `yogasutras.hanuma.com`.

**Tech Stack:** Flask/SQLAlchemy (backend), React/TypeScript/Tailwind (frontend), Docker/K8s (deployment), Figma (design)

---

## Current State Assessment

| Component           | Status           | Notes                                       |
| ------------------- | ---------------- | ------------------------------------------- |
| Database            | ✅ Complete       | 196 sutras across 4 padas                   |
| Backend APIs        | ✅ Exists         | Text, dictionary, sandhi, morphology routes |
| Frontend Pages      | ✅ Exists         | Home, Pada, Sutra, Bookmarks pages          |
| Frontend Components | ✅ Exists         | Dictionary panel, sandhi view, etc.         |
| Docker              | ⚠️ Partial        | docker-compose exists, needs K8s manifests  |
| K8s Deployment      | ❌ Missing        | No manifests, no ingress                    |
| Domains             | ❌ Not configured | Need ingress for both domains               |

---

## Phase 1: Figma Design (User Review Loop)

### Task 1: Home Page Design

**Goal:** Design the landing page with pada navigation

**Step 1: Create Figma design for Home page**

Design elements:
- Header with app title "Yoga Sutras" in elegant typography
- Search bar (prominent placement)
- 4 pada cards in a grid:
  - Samadhi Pada (51 sutras)
  - Sadhana Pada (55 sutras)
  - Vibhuti Pada (56 sutras)
  - Kaivalya Pada (34 sutras)
- Each card shows: Sanskrit name, English name, sutra count
- Warm scholarly color palette (earth tones, gold accents)
- Fonts: Noto Sans Devanagari (Sanskrit), Inter (UI)

**Step 2: Share design with user for review**

**Step 3: Iterate based on feedback**

---

### Task 2: Pada Page Design

**Goal:** Design the sutra list view for a pada

**Step 1: Create Figma design for Pada page**

Design elements:
- Breadcrumb navigation (Home > Samadhi Pada)
- Pada title with Sanskrit and English
- List of sutra cards:
  - Sutra number (I.1, I.2, etc.)
  - First line in Devanagari
  - First line in IAST transliteration
  - Brief meaning preview
- Scroll-friendly layout
- Click card → navigate to sutra detail

**Step 2: Share design with user for review**

**Step 3: Iterate based on feedback**

---

### Task 3: Sutra Detail Page Design

**Goal:** Design the single sutra view with word analysis

**Step 1: Create Figma design for Sutra page**

Design elements:
- Sutra header: number, navigation arrows (prev/next)
- Main content area:
  - Full Devanagari text (large, readable)
  - IAST transliteration below
  - English meaning
  - Clickable words (highlighted on hover)
- Side panel (collapsible on mobile):
  - Dictionary lookup results
  - Sandhi split view
  - Morphology analysis
- Bookmark button
- Script toggle (Devanagari/IAST)

**Step 2: Share design with user for review**

**Step 3: Iterate based on feedback**

---

### Task 4: Dictionary Panel Design

**Goal:** Design the word lookup panel

**Step 1: Create Figma design for Dictionary panel**

Design elements:
- Selected word display (Devanagari + IAST)
- Sandhi split section:
  - Original compound
  - Split words with → arrows
  - Sandhi type indicator
- Dictionary entries:
  - Source tabs (MW, Apte)
  - Entry with meaning, grammar info
  - Collapsible for long entries
- Morphology section:
  - Lemma (base form)
  - Case, gender, number
  - Verb root (if applicable)
- Loading states
- Empty states

**Step 2: Share design with user for review**

**Step 3: Iterate based on feedback**

---

## Phase 2: Backend Verification

### Task 5: Verify API Endpoints

**Files:**
- Test: `backend/app/routes/text_routes.py`
- Test: `backend/app/routes/dictionary_routes.py`

**Step 1: Test texts list endpoint**

Run:
```bash
cd /Users/narenmudivarthy/Projects/yoga_sutras
source backend/venv/bin/activate
python backend/run.py &
sleep 3
curl http://localhost:5001/api/texts | python -m json.tool
```

Expected: JSON with Yoga Sutras text and 4 sections

**Step 2: Test section endpoint**

Run:
```bash
curl "http://localhost:5001/api/texts/yoga-sutras/section/samadhi-pada" | python -m json.tool | head -50
```

Expected: JSON with 51 sutra blocks

**Step 3: Test dictionary endpoint**

Run:
```bash
curl "http://localhost:5001/api/dictionary/yoga" | python -m json.tool
```

Expected: Dictionary entries for "yoga"

**Step 4: Test sandhi split endpoint**

Run:
```bash
curl "http://localhost:5001/api/split/yogaścittavṛttinirodhaḥ" | python -m json.tool
```

Expected: Split components

**Step 5: Document any issues found**

Create issues list in `docs/plans/backend-issues.md` if any endpoints fail

---

## Phase 3: Frontend Polish (Post-Figma)

### Task 6: Update HomePage based on Figma

**Files:**
- Modify: `frontend/src/pages/HomePage.tsx`
- Modify: `frontend/src/index.css` (if new styles needed)

**Step 1: Compare current HomePage to Figma design**

Read current implementation:
```bash
cat frontend/src/pages/HomePage.tsx
```

**Step 2: Implement design changes**

Update component to match approved Figma design:
- Typography updates
- Color palette changes
- Layout adjustments
- Card component styling

**Step 3: Test locally**

Run:
```bash
cd frontend && npm run dev
```

Open http://localhost:3000 and verify against Figma

**Step 4: Commit**

```bash
git add frontend/src/pages/HomePage.tsx frontend/src/index.css
git commit -m "feat: Update HomePage to match Figma design"
```

---

### Task 7: Update PadaPage based on Figma

**Files:**
- Modify: `frontend/src/pages/PadaPage.tsx`

**Step 1: Compare current PadaPage to Figma design**

**Step 2: Implement design changes**

**Step 3: Test locally**

**Step 4: Commit**

```bash
git add frontend/src/pages/PadaPage.tsx
git commit -m "feat: Update PadaPage to match Figma design"
```

---

### Task 8: Update SutraPage based on Figma

**Files:**
- Modify: `frontend/src/pages/SutraPage.tsx`
- Modify: `frontend/src/components/DictionaryPanel.tsx`

**Step 1: Compare current SutraPage to Figma design**

**Step 2: Implement design changes**

**Step 3: Test locally**

**Step 4: Commit**

```bash
git add frontend/src/pages/SutraPage.tsx frontend/src/components/DictionaryPanel.tsx
git commit -m "feat: Update SutraPage and DictionaryPanel to match Figma design"
```

---

### Task 9: Add Loading and Error States

**Files:**
- Modify: `frontend/src/pages/HomePage.tsx`
- Modify: `frontend/src/pages/PadaPage.tsx`
- Modify: `frontend/src/pages/SutraPage.tsx`

**Step 1: Add loading skeletons**

```tsx
// Loading skeleton component
const LoadingSkeleton = () => (
  <div className="animate-pulse">
    <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
    <div className="h-4 bg-gray-200 rounded w-1/2"></div>
  </div>
);
```

**Step 2: Add error boundaries**

```tsx
// Error display component
const ErrorDisplay = ({ message, retry }: { message: string; retry: () => void }) => (
  <div className="text-center py-8">
    <p className="text-red-600 mb-4">{message}</p>
    <button onClick={retry} className="px-4 py-2 bg-amber-600 text-white rounded">
      Try Again
    </button>
  </div>
);
```

**Step 3: Test error states**

Stop backend, verify frontend shows error gracefully

**Step 4: Commit**

```bash
git add frontend/src/pages/*.tsx
git commit -m "feat: Add loading skeletons and error states"
```

---

## Phase 4: DevOps Setup

### Task 10: Create Dockerfiles

**Files:**
- Create: `docker/backend/Dockerfile`
- Create: `docker/frontend/Dockerfile`

**Step 1: Verify existing Dockerfiles**

```bash
ls -la docker/
cat docker/backend/Dockerfile 2>/dev/null || echo "Need to create"
cat docker/frontend/Dockerfile 2>/dev/null || echo "Need to create"
```

**Step 2: Create/update backend Dockerfile**

```dockerfile
# docker/backend/Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
COPY data/ /app/data/

EXPOSE 5001

CMD ["python", "run.py"]
```

**Step 3: Create/update frontend Dockerfile**

```dockerfile
# docker/frontend/Dockerfile
FROM node:18-alpine as build

WORKDIR /app

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY docker/frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

**Step 4: Build and test locally**

```bash
docker-compose build
docker-compose up -d
curl http://localhost:3002
docker-compose down
```

**Step 5: Commit**

```bash
git add docker/
git commit -m "feat: Add production Dockerfiles for backend and frontend"
```

---

### Task 11: Create K8s Manifests

**Files:**
- Create: `~/Projects/deployment/homelab/base/applications/yoga-sutras/namespace.yaml`
- Create: `~/Projects/deployment/homelab/base/applications/yoga-sutras/backend-deployment.yaml`
- Create: `~/Projects/deployment/homelab/base/applications/yoga-sutras/frontend-deployment.yaml`
- Create: `~/Projects/deployment/homelab/base/applications/yoga-sutras/services.yaml`
- Create: `~/Projects/deployment/homelab/base/applications/yoga-sutras/ingress.yaml`
- Create: `~/Projects/deployment/homelab/base/applications/yoga-sutras/kustomization.yaml`

**Step 1: Create namespace**

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: yoga-sutras
```

**Step 2: Create backend deployment**

```yaml
# backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: yoga-sutras-backend
  namespace: yoga-sutras
spec:
  replicas: 1
  selector:
    matchLabels:
      app: yoga-sutras-backend
  template:
    metadata:
      labels:
        app: yoga-sutras-backend
    spec:
      containers:
      - name: backend
        image: registry.hanuma.local/yoga-sutras-backend:latest
        ports:
        - containerPort: 5001
        resources:
          limits:
            memory: "256Mi"
            cpu: "500m"
```

**Step 3: Create frontend deployment**

```yaml
# frontend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: yoga-sutras-frontend
  namespace: yoga-sutras
spec:
  replicas: 1
  selector:
    matchLabels:
      app: yoga-sutras-frontend
  template:
    metadata:
      labels:
        app: yoga-sutras-frontend
    spec:
      containers:
      - name: frontend
        image: registry.hanuma.local/yoga-sutras-frontend:latest
        ports:
        - containerPort: 80
        resources:
          limits:
            memory: "128Mi"
            cpu: "250m"
```

**Step 4: Create services**

```yaml
# services.yaml
apiVersion: v1
kind: Service
metadata:
  name: yoga-sutras-backend
  namespace: yoga-sutras
spec:
  selector:
    app: yoga-sutras-backend
  ports:
  - port: 5001
    targetPort: 5001
---
apiVersion: v1
kind: Service
metadata:
  name: yoga-sutras-frontend
  namespace: yoga-sutras
spec:
  selector:
    app: yoga-sutras-frontend
  ports:
  - port: 80
    targetPort: 80
```

**Step 5: Create ingress with dual domains**

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: yoga-sutras-ingress
  namespace: yoga-sutras
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
spec:
  ingressClassName: nginx
  rules:
  - host: yogasutras.naren.me
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: yoga-sutras-backend
            port:
              number: 5001
      - path: /
        pathType: Prefix
        backend:
          service:
            name: yoga-sutras-frontend
            port:
              number: 80
  - host: yogasutras.hanuma.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: yoga-sutras-backend
            port:
              number: 5001
      - path: /
        pathType: Prefix
        backend:
          service:
            name: yoga-sutras-frontend
            port:
              number: 80
  tls:
  - hosts:
    - yogasutras.naren.me
    - yogasutras.hanuma.com
    secretName: yoga-sutras-tls
```

**Step 6: Create kustomization**

```yaml
# kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: yoga-sutras

resources:
- namespace.yaml
- backend-deployment.yaml
- frontend-deployment.yaml
- services.yaml
- ingress.yaml
```

**Step 7: Commit to deployment repo**

```bash
cd ~/Projects/deployment/homelab
git add base/applications/yoga-sutras/
git commit -m "feat: Add yoga-sutras K8s manifests with dual-domain ingress"
```

---

### Task 12: Create Jenkins Pipeline

**Files:**
- Create: `jenkins/Jenkinsfile`

**Step 1: Create Jenkinsfile**

```groovy
// jenkins/Jenkinsfile
pipeline {
    agent any

    environment {
        REGISTRY = 'registry.hanuma.local'
        IMAGE_TAG = "${sh(script: 'date +%H%M%S-%d%m%y', returnStdout: true).trim()}-${GIT_COMMIT.take(7)}"
    }

    stages {
        stage('Build Backend') {
            steps {
                sh '''
                    docker build -f docker/backend/Dockerfile -t ${REGISTRY}/yoga-sutras-backend:${IMAGE_TAG} .
                    docker tag ${REGISTRY}/yoga-sutras-backend:${IMAGE_TAG} ${REGISTRY}/yoga-sutras-backend:latest
                    docker push ${REGISTRY}/yoga-sutras-backend:${IMAGE_TAG}
                    docker push ${REGISTRY}/yoga-sutras-backend:latest
                '''
            }
        }

        stage('Build Frontend') {
            steps {
                sh '''
                    docker build -f docker/frontend/Dockerfile -t ${REGISTRY}/yoga-sutras-frontend:${IMAGE_TAG} .
                    docker tag ${REGISTRY}/yoga-sutras-frontend:${IMAGE_TAG} ${REGISTRY}/yoga-sutras-frontend:latest
                    docker push ${REGISTRY}/yoga-sutras-frontend:${IMAGE_TAG}
                    docker push ${REGISTRY}/yoga-sutras-frontend:latest
                '''
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                    kubectl apply -k ~/Projects/deployment/homelab/base/applications/yoga-sutras/
                    kubectl rollout restart deployment/yoga-sutras-backend -n yoga-sutras
                    kubectl rollout restart deployment/yoga-sutras-frontend -n yoga-sutras
                '''
            }
        }
    }

    post {
        success {
            echo 'Deployment successful! Access at:'
            echo '  - https://yogasutras.naren.me'
            echo '  - https://yogasutras.hanuma.com'
        }
    }
}
```

**Step 2: Commit**

```bash
git add jenkins/
git commit -m "feat: Add Jenkins CI/CD pipeline"
```

---

### Task 13: Update Homer Dashboard

**Files:**
- Modify: `~/Projects/deployment/homelab/homer/config.yml`

**Step 1: Add yoga-sutras entries**

Add to the Applications section:

```yaml
- name: "Yoga Sutras"
  logo: "assets/icons/om.png"
  subtitle: "Sanskrit Reading Platform"
  tag: "app"
  url: "https://yogasutras.naren.me"
  target: "_blank"

- name: "Yoga Sutras (hanuma)"
  logo: "assets/icons/om.png"
  subtitle: "Sanskrit Reading Platform"
  tag: "app"
  url: "https://yogasutras.hanuma.com"
  target: "_blank"
```

**Step 2: Commit**

```bash
cd ~/Projects/deployment/homelab
git add homer/config.yml
git commit -m "feat: Add Yoga Sutras to Homer dashboard"
```

---

## Phase 5: Deployment

### Task 14: Deploy to K8s

**Step 1: Build and push images**

```bash
cd /Users/narenmudivarthy/Projects/yoga_sutras
docker build -f docker/backend/Dockerfile -t registry.hanuma.local/yoga-sutras-backend:latest .
docker build -f docker/frontend/Dockerfile -t registry.hanuma.local/yoga-sutras-frontend:latest .
docker push registry.hanuma.local/yoga-sutras-backend:latest
docker push registry.hanuma.local/yoga-sutras-frontend:latest
```

**Step 2: Apply K8s manifests**

```bash
kubectl apply -k ~/Projects/deployment/homelab/base/applications/yoga-sutras/
```

**Step 3: Verify deployment**

```bash
kubectl get pods -n yoga-sutras
kubectl get ingress -n yoga-sutras
```

**Step 4: Test both domains**

```bash
curl -I https://yogasutras.naren.me
curl -I https://yogasutras.hanuma.com
```

---

### Task 15: End-to-End Testing

**Step 1: Test Home page loads**

Open https://yogasutras.naren.me in browser

**Step 2: Test pada navigation**

Click Samadhi Pada → verify 51 sutras listed

**Step 3: Test sutra detail**

Click first sutra → verify content, translation displayed

**Step 4: Test word click**

Click a Sanskrit word → verify dictionary panel opens

**Step 5: Test second domain**

Repeat tests on https://yogasutras.hanuma.com

**Step 6: Document results**

Update success criteria checklist in design doc

---

## Success Criteria Checklist

- [ ] All 196 sutras viewable in the UI
- [ ] Click any word → dictionary lookup works
- [ ] Sandhi splitting functional
- [ ] Deployed to homelab K8s
- [ ] https://yogasutras.naren.me accessible
- [ ] https://yogasutras.hanuma.com accessible
- [ ] Code reviewed and approved

---

**Document Control**

| Version | Date       | Author         | Changes      |
| ------- | ---------- | -------------- | ------------ |
| 1.0     | 2026-02-27 | Claude + Naren | Initial plan |
