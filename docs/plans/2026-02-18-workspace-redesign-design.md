# Workspace Redesign — Single-Page Workspace

## Problem

The current UI has 4 separate pages (Dashboard, Upload, History, TranslationDetail) connected by sidebar navigation. This creates unnecessary page transitions for a tool whose core loop is simply "upload → view result." The Dashboard and History pages duplicate the same translation list, and Upload results are disconnected from history.

## Solution

Consolidate into a single Workspace page with a sidebar that doubles as history navigation, inspired by chat-app patterns (e.g., ChatGPT's conversation list).

## Routes

| Route | Purpose |
|-------|---------|
| `/` | Workspace — idle state shows upload zone |
| `/t/:id` | Workspace — loads specific translation result |
| `*` | Redirect to `/` |

**Removed routes:** `/upload`, `/history`, `/history/:id`

## Layout

```
┌──────────────────────────────────────────────────┐
│ ┌────────────────┐ ┌──────────────────────────┐  │
│ │ W  Translator  │ │                          │  │
│ ├────────────────┤ │   [UploadZone]           │  │
│ │ [+ New Upload] │ │   or                     │  │
│ ├────────────────┤ │   [TranslationPending]   │  │
│ │ History        │ │   or                     │  │
│ │                │ │   [TranslationView]      │  │
│ │ ▸ report.docx  │ │                          │  │
│ │   article.docx │ │   Original │ Translation │  │
│ │   memo.docx    │ │   ...      │ ...         │  │
│ │                │ │                          │  │
│ └────────────────┘ └──────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

## Sidebar Behavior

- **Logo**: top, links to `/` (resets to upload zone)
- **"+ New Upload" button**: full-width, clears selection, navigates to `/`
- **History list**: all past translations, sorted by newest first
  - Selected item: `bg-muted rounded-md`
  - Hover: `hover:bg-muted/50 transition-colors duration-150`
  - Each item shows: filename (truncated), paragraph count, date
  - Empty state: "No translations yet" muted text

### Sidebar Interactions

| Action | Result |
|--------|--------|
| Click "+ New Upload" | Navigate to `/`, right side shows upload zone, clear sidebar selection |
| Click history item | Navigate to `/t/:id`, right side loads translation, item highlights |
| Upload completes | Invalidate list cache, navigate to `/t/:id`, new item appears at top |

## Component Tree

```
App
└── BrowserRouter
    └── Workspace                    (routes / and /t/:id)
        ├── AppSidebar (modified)
        │   ├── Logo + "New Upload" button
        │   └── HistoryList          (new component)
        └── MainArea
            ├── UploadZone           (extracted from Upload.tsx)
            ├── TranslationPending   (inline spinner)
            └── TranslationView      (extracted shared component)
```

## State Management

| State | Source | Notes |
|-------|--------|-------|
| Selected translation ID | URL params (`useParams`) | `/t/:id` drives everything |
| Translation list | TanStack Query (`useTranslations`) | Powers sidebar history |
| Single translation | TanStack Query (`useTranslation(id)`) | Powers right-side detail, enabled only when id exists |
| Upload mutation | `useUploadTranslation` | Tracks pending/error state |

### Right-Side State Logic

```
if (mutation.isPending)  → TranslationPending
else if (id from URL)    → TranslationView
else                     → UploadZone
```

### Upload Success Flow

```
mutation.onSuccess(data)
  → invalidateQueries(translationKeys.lists())
  → navigate(`/t/${data.id}`)
```

URL change triggers `useTranslation(id)` → right side renders result. Sidebar list refreshes via cache invalidation. Zero redundant state.

## File Changes

### Delete

- `frontend/src/pages/Dashboard.tsx`
- `frontend/src/pages/Upload.tsx`
- `frontend/src/pages/History.tsx`
- `frontend/src/pages/TranslationDetail.tsx`

### Create

- `frontend/src/pages/Workspace.tsx` — main page, orchestrates state logic
- `frontend/src/components/UploadZone.tsx` — drag-drop upload (extracted from Upload.tsx)
- `frontend/src/components/TranslationView.tsx` — side-by-side comparison table (shared)
- `frontend/src/components/HistoryList.tsx` — sidebar translation list

### Modify

- `frontend/src/App.tsx` — simplify routes to `/` and `/t/:id`
- `frontend/src/components/layout/AppSidebar.tsx` — replace nav items with "New Upload" button + HistoryList

## Visual Design

**Style:** Minimalism — reuse existing shadcn/ui theme, no new colors or dependencies.

**Translation table:** Keep existing `grid grid-cols-2 gap-px` design. Add `border-b border-border` between rows for readability.

**Upload zone:** Reuse existing dashed-border drag-drop design, slightly more compact since it shares space with sidebar.

**No new dependencies.** Everything built with existing shadcn/ui + Tailwind + Lucide.
