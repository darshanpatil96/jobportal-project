# ARTISAN. — React Migration Roadmap

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PRODUCTION ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─ candidate.artisan.io ─────┐  ┌─ ats.artisan.io ──────────────┐ │
│  │                             │  │                                │ │
│  │  React (Vite + TanStack)    │  │  React (Vite + TanStack)      │ │
│  │  Candidate Portal           │  │  Employer ATS Workspace       │ │
│  │  SSR-ready (Next.js later)  │  │  SPA (client-side only)       │ │
│  │                             │  │                                │ │
│  └──────────────┬──────────────┘  └──────────────┬─────────────────┘ │
│                 │                                 │                   │
│                 └──────────┬──────────────────────┘                   │
│                            │                                          │
│                            ▼                                          │
│              ┌─ api.artisan.io ──────────────────────┐               │
│              │                                        │               │
│              │  Django + DRF                          │               │
│              │  ├── /api/v1/auth/*                    │               │
│              │  ├── /api/v1/candidate/*               │               │
│              │  ├── /api/v1/employer/*                │               │
│              │  ├── AI Engine                         │               │
│              │  ├── ATS Pipeline                      │               │
│              │  └── PostgreSQL                        │               │
│              │                                        │               │
│              └────────────────────────────────────────┘               │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Recommended React Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Build tool | **Vite 5** | Fast HMR, native ESM, smaller bundles than CRA |
| Framework | **React 18** | Stable, huge ecosystem |
| Routing | **React Router 6** | Standard, supports lazy loading |
| State (server) | **TanStack Query v5** | Caching, background refetch, optimistic updates |
| State (client) | **Zustand** | Minimal, no boilerplate, scales well |
| Forms | **React Hook Form + Zod** | Performant, type-safe validation |
| Styling | **Tailwind CSS 3** | Already used in Django templates — zero learning curve |
| HTTP client | **Axios** | Interceptors for JWT refresh |
| Charts | **Recharts** | Lightweight, React-native, good for ATS analytics |
| Tables | **TanStack Table** | Headless, sortable, filterable — perfect for ATS |
| Notifications | **React Hot Toast** | Lightweight toast notifications |
| TypeScript | **Yes** | Type safety for API contracts |

---

## Phased Migration Strategy

### Phase 0: Current State (DONE)
- Django templates serve both portals
- DRF API layer exists at `/api/v1/*`
- JWT auth configured
- CORS configured for localhost:3000 and :5173

### Phase 1: Parallel Development (No Breaking Changes)
```
Duration: 2-3 weeks
Risk: Zero (Django templates still serve production)

Tasks:
1. Scaffold React projects (candidate + employer)
2. Build shared API client library
3. Implement auth flow (login → JWT → refresh)
4. Build candidate job list page (mirrors /jobs/)
5. Build employer dashboard page (mirrors /employer/)
6. Run React on localhost:5173, Django on localhost:8000
```

### Phase 2: Feature Parity — Candidate Portal
```
Duration: 3-4 weeks
Risk: Low (Django still serves production)

Pages to build:
- Home / Landing page
- Job list (with filters)
- Job detail
- Apply flow
- My Applications
- Application Timeline
- Saved Jobs
- Profile / Edit Profile
- Dashboard
- Notifications
```

### Phase 3: Feature Parity — Employer ATS
```
Duration: 4-5 weeks
Risk: Low (Django still serves production)

Pages to build:
- ATS Dashboard (with charts)
- Job Management (CRUD)
- Candidate Pipeline (drag-and-drop Kanban)
- Candidate Detail (match score, resume, timeline)
- Interview Scheduler
- Analytics Dashboard
- Company Profile
- Team Management (workspace members)
```

### Phase 4: Gradual Cutover
```
Duration: 1-2 weeks
Risk: Medium (traffic routing changes)

Strategy:
1. Deploy React apps to separate subdomains
2. Route /employer/* to React ATS app (employer users)
3. Route /* to React candidate app (everyone else)
4. Keep Django templates as fallback (feature flag)
5. Monitor error rates for 1 week
6. Remove Django template routes after stable
```

### Phase 5: Django Becomes API-Only
```
Duration: 1 week
Risk: Low (cleanup only)

Tasks:
1. Remove template dependencies from Django
2. Remove Tailwind CDN from Django
3. Remove template folders
4. Django serves only /api/* and /admin/*
5. Static files served by CDN (Cloudflare/Vercel)
```

---

## Frontend Folder Structures

### Candidate Portal (`frontend-candidate/`)

```
frontend-candidate/
├── public/
│   └── favicon.ico
├── src/
│   ├── api/
│   │   ├── client.ts              ← Axios instance + JWT interceptor
│   │   ├── auth.ts                ← login, register, refresh
│   │   ├── jobs.ts                ← getJobs, getJobDetail
│   │   ├── applications.ts       ← apply, getMyApps, withdraw
│   │   └── profile.ts            ← getProfile, updateProfile
│   ├── components/
│   │   ├── ui/                    ← Button, Card, Badge, Input, Modal
│   │   ├── layout/
│   │   │   ├── Navbar.tsx
│   │   │   ├── Footer.tsx
│   │   │   └── Layout.tsx
│   │   ├── jobs/
│   │   │   ├── JobCard.tsx
│   │   │   ├── JobFilters.tsx
│   │   │   └── JobDetail.tsx
│   │   └── applications/
│   │       ├── ApplicationRow.tsx
│   │       ├── StatusBadge.tsx
│   │       └── Timeline.tsx
│   ├── pages/
│   │   ├── Home.tsx
│   │   ├── Jobs.tsx
│   │   ├── JobDetail.tsx
│   │   ├── Apply.tsx
│   │   ├── Dashboard.tsx
│   │   ├── Applications.tsx
│   │   ├── SavedJobs.tsx
│   │   ├── Profile.tsx
│   │   ├── Login.tsx
│   │   └── Register.tsx
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useJobs.ts
│   │   └── useApplications.ts
│   ├── stores/
│   │   └── authStore.ts           ← Zustand: user, tokens, role
│   ├── lib/
│   │   ├── utils.ts
│   │   └── constants.ts
│   ├── types/
│   │   ├── job.ts
│   │   ├── application.ts
│   │   └── user.ts
│   ├── App.tsx
│   ├── main.tsx
│   └── router.tsx
├── tailwind.config.ts
├── tsconfig.json
├── vite.config.ts
└── package.json
```

### Employer ATS (`frontend-employer/`)

```
frontend-employer/
├── public/
│   └── favicon.ico
├── src/
│   ├── api/
│   │   ├── client.ts              ← Shared Axios + JWT (same as candidate)
│   │   ├── auth.ts
│   │   ├── dashboard.ts          ← getDashboard, getStats
│   │   ├── jobs.ts                ← CRUD jobs
│   │   ├── candidates.ts         ← getCandidates, updateStatus
│   │   ├── interviews.ts         ← schedule, update, list
│   │   └── analytics.ts          ← getAnalytics
│   ├── components/
│   │   ├── ui/                    ← Button, Card, Badge, Table, Modal
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx
│   │   │   ├── TopBar.tsx
│   │   │   └── ATSLayout.tsx
│   │   ├── dashboard/
│   │   │   ├── KPICard.tsx
│   │   │   ├── PipelineChart.tsx
│   │   │   └── RecentCandidates.tsx
│   │   ├── candidates/
│   │   │   ├── CandidateRow.tsx
│   │   │   ├── CandidateDetail.tsx
│   │   │   ├── MatchScoreRing.tsx
│   │   │   ├── PipelineKanban.tsx
│   │   │   └── StatusDropdown.tsx
│   │   ├── interviews/
│   │   │   ├── InterviewCard.tsx
│   │   │   ├── ScheduleModal.tsx
│   │   │   └── Calendar.tsx
│   │   └── analytics/
│   │       ├── FunnelChart.tsx
│   │       ├── TimeToHire.tsx
│   │       └── SourceBreakdown.tsx
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   ├── Jobs.tsx
│   │   ├── JobCreate.tsx
│   │   ├── JobDetail.tsx
│   │   ├── Candidates.tsx
│   │   ├── CandidateDetail.tsx
│   │   ├── Interviews.tsx
│   │   ├── Analytics.tsx
│   │   ├── Company.tsx
│   │   ├── Team.tsx
│   │   └── Login.tsx
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useCandidates.ts
│   │   ├── useInterviews.ts
│   │   └── usePipeline.ts
│   ├── stores/
│   │   ├── authStore.ts
│   │   └── workspaceStore.ts      ← Current workspace context
│   ├── lib/
│   │   ├── utils.ts
│   │   └── constants.ts
│   ├── types/
│   │   ├── candidate.ts
│   │   ├── job.ts
│   │   ├── interview.ts
│   │   └── workspace.ts
│   ├── App.tsx
│   ├── main.tsx
│   └── router.tsx
├── tailwind.config.ts
├── tsconfig.json
├── vite.config.ts
└── package.json
```

---

## Authentication Integration

### JWT Flow (React ↔ Django)

```
┌─ React App ──────────────────────────────────────────────────────┐
│                                                                    │
│  1. User submits login form                                        │
│     POST /api/v1/auth/token/                                       │
│     Body: { username, password }                                   │
│                                                                    │
│  2. Django returns tokens                                          │
│     Response: { access: "...", refresh: "..." }                    │
│                                                                    │
│  3. Store tokens                                                   │
│     access  → memory (Zustand store)                               │
│     refresh → httpOnly cookie OR localStorage                      │
│                                                                    │
│  4. All API calls include:                                         │
│     Header: Authorization: Bearer <access_token>                   │
│                                                                    │
│  5. On 401 response (token expired):                               │
│     Axios interceptor → POST /api/v1/auth/token/refresh/           │
│     Body: { refresh: "..." }                                       │
│     → Get new access token → retry original request                │
│                                                                    │
│  6. On refresh failure (refresh expired):                          │
│     → Clear store → redirect to /login                             │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Axios Interceptor Pattern

```typescript
// src/api/client.ts
import axios from 'axios';
import { useAuthStore } from '../stores/authStore';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
});

// Attach access token to every request
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto-refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const refresh = useAuthStore.getState().refreshToken;
        const { data } = await axios.post(`${api.defaults.baseURL}/auth/token/refresh/`, {
          refresh,
        });
        useAuthStore.getState().setAccessToken(data.access);
        originalRequest.headers.Authorization = `Bearer ${data.access}`;
        return api(originalRequest);
      } catch {
        useAuthStore.getState().logout();
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
```

---

## State Management Strategy

### Server State (TanStack Query)
```
Used for: Jobs, applications, candidates, interviews, analytics
Why: Auto-caching, background refetch, optimistic updates, pagination

Example:
  const { data: jobs, isLoading } = useQuery({
    queryKey: ['jobs', filters],
    queryFn: () => api.get('/candidate/jobs/', { params: filters }),
  });
```

### Client State (Zustand)
```
Used for: Auth tokens, current user, UI state, workspace context
Why: Minimal boilerplate, persists to localStorage, no providers needed

Example:
  const { user, accessToken, logout } = useAuthStore();
```

### When to Use What

| Data | Tool | Reason |
|------|------|--------|
| Job listings | TanStack Query | Server data, paginated, cacheable |
| Current user profile | TanStack Query | Server data, rarely changes |
| Auth tokens | Zustand | Client-only, needs persistence |
| Sidebar open/closed | Zustand | UI state |
| Form inputs | React Hook Form | Local form state |
| Candidate pipeline (drag) | Zustand + mutation | Optimistic UI |

---

## Deployment Strategy

### Development
```
Django:  localhost:8000  (API + admin)
React Candidate: localhost:5173
React Employer:  localhost:5174
```

### Staging / Production

| Service | Platform | URL |
|---------|----------|-----|
| Django API | Render / Railway | api.artisan.io |
| Candidate React | Vercel | artisan.io |
| Employer React | Vercel | ats.artisan.io |
| Database | Render PostgreSQL | (internal) |
| Media/Uploads | Cloudflare R2 / S3 | cdn.artisan.io |

### Nginx / Reverse Proxy (Alternative: Single Domain)
```nginx
server {
    server_name artisan.io;

    # API
    location /api/ {
        proxy_pass http://django:8000;
    }
    location /admin/ {
        proxy_pass http://django:8000;
    }

    # Employer SPA
    location /employer/ {
        alias /var/www/employer/;
        try_files $uri /employer/index.html;
    }

    # Candidate SPA (everything else)
    location / {
        root /var/www/candidate/;
        try_files $uri /index.html;
    }
}
```

---

## Migration Execution Order

```
Week 1-2:   Scaffold projects, shared API client, auth flow
Week 3-4:   Candidate portal — job list, detail, apply
Week 5-6:   Candidate portal — dashboard, applications, profile
Week 7-8:   Employer ATS — dashboard, job management
Week 9-10:  Employer ATS — candidate pipeline (Kanban), interviews
Week 11-12: Employer ATS — analytics, team management
Week 13:    Integration testing, performance optimization
Week 14:    Gradual cutover (feature flags)
Week 15:    Full React in production, Django → API-only
```

---

## What NOT to Do

| Anti-pattern | Why |
|-------------|-----|
| Build one monolithic React app for both portals | Different UX needs, different deployment cycles |
| Use Redux for everything | Overkill — TanStack Query handles 80% of state |
| Duplicate API logic between apps | Extract shared `@artisan/api-client` package |
| Build React before API is stable | API must be tested and documented first |
| Remove Django templates before React is production-ready | Always keep fallback |
| Use SSR for employer ATS | It's a private dashboard — SPA is fine |
| Skip TypeScript | API contracts will drift without types |

---

## Shared Package Strategy

For code shared between both React apps:

```
packages/
├── @artisan/api-client/     ← Axios instance, interceptors, types
├── @artisan/ui/             ← Shared Tailwind components (Button, Badge, etc.)
└── @artisan/types/          ← TypeScript interfaces matching DRF serializers
```

Use a monorepo tool (Turborepo or pnpm workspaces) to manage shared packages.

---

## API Contract Documentation

Before building React, document the API with:
- **DRF Spectacular** (OpenAPI/Swagger auto-generation)
- Export TypeScript types from OpenAPI spec
- Use `openapi-typescript` to auto-generate types

```bash
pip install drf-spectacular
# Generates /api/schema/ endpoint
# React apps consume types from this schema
```

This ensures React types always match Django serializers.
