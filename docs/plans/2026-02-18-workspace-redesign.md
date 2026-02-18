# Workspace Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Consolidate 4 pages into a single Workspace page with sidebar history navigation.

**Architecture:** Single `Workspace.tsx` page handles three states (idle/pending/result) driven by URL params + TanStack Query. Sidebar shows "New Upload" button + history list. No new dependencies.

**Tech Stack:** React 19, TypeScript, React Router v7, TanStack Query v5, shadcn/ui, Tailwind CSS v4, Lucide icons

---

### Task 1: Extract TranslationView component

Extract the shared side-by-side comparison table used in both `Upload.tsx` and `TranslationDetail.tsx`.

**Files:**
- Create: `frontend/src/components/TranslationView.tsx`

**Step 1: Create TranslationView component**

```tsx
import { Download } from "lucide-react"
import { Button } from "@/components/ui/button"
import { getDownloadUrl } from "@/lib/api"
import type { TranslationResult } from "@/lib/api"

interface Props {
  readonly result: TranslationResult
}

export function TranslationView({ result }: Props) {
  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            {result.filename}
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {result.paragraphs.length} paragraphs &middot;{" "}
            {new Date(result.created_at).toLocaleDateString()}
          </p>
        </div>
        <Button variant="outline" asChild>
          <a href={getDownloadUrl(result.id)} download>
            <Download />
            Download
          </a>
        </Button>
      </div>

      <div className="mt-8">
        <div className="grid grid-cols-2 gap-px rounded-lg border bg-border overflow-hidden">
          <div className="bg-muted px-4 py-2 text-xs font-medium text-muted-foreground uppercase tracking-wider">
            Original
          </div>
          <div className="bg-muted px-4 py-2 text-xs font-medium text-muted-foreground uppercase tracking-wider">
            Translation
          </div>
          {result.paragraphs.map((p, i) => (
            <div key={i} className="contents">
              <div className="bg-background px-4 py-3 text-sm leading-relaxed border-b border-border last:border-b-0">
                {p.original}
              </div>
              <div className="bg-background px-4 py-3 text-sm leading-relaxed border-b border-border last:border-b-0">
                {p.translated}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
```

**Step 2: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds (component not yet imported anywhere)

**Step 3: Commit**

```bash
git add frontend/src/components/TranslationView.tsx
git commit -m "feat: extract TranslationView shared component"
```

---

### Task 2: Extract UploadZone component

Extract drag-drop upload area from `Upload.tsx` into a reusable component.

**Files:**
- Create: `frontend/src/components/UploadZone.tsx`

**Step 1: Create UploadZone component**

This component handles drag-drop and file selection, delegates mutation to parent via `onFileSelect` callback.

```tsx
import { useState, useRef } from "react"
import { Upload, FileText, X } from "lucide-react"

interface Props {
  readonly onFileSelect: (file: File) => void
  readonly error?: string | null
}

export function UploadZone({ onFileSelect, error }: Props) {
  const [dragOver, setDragOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  function handleFile(file: File) {
    if (!file.name.endsWith(".docx")) return
    onFileSelect(file)
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  function handleDragOver(e: React.DragEvent) {
    e.preventDefault()
    setDragOver(true)
  }

  function handleDragLeave(e: React.DragEvent) {
    e.preventDefault()
    setDragOver(false)
  }

  function handleFileInput(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
    e.target.value = ""
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh]">
      <div className="w-full max-w-lg">
        {error && (
          <div className="mb-4 flex items-center gap-2 rounded-md border border-destructive/50 bg-destructive/5 px-4 py-3 text-sm text-destructive">
            <X className="size-4 shrink-0" />
            {error}
          </div>
        )}

        <input
          ref={fileInputRef}
          type="file"
          accept=".docx"
          className="hidden"
          onChange={handleFileInput}
        />

        <button
          type="button"
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => fileInputRef.current?.click()}
          className={`flex w-full flex-col items-center gap-4 rounded-lg border-2 border-dashed px-6 py-16 transition-colors cursor-pointer ${
            dragOver
              ? "border-primary bg-primary/5"
              : "border-muted-foreground/25 hover:border-muted-foreground/50"
          }`}
        >
          <div className="flex size-12 items-center justify-center rounded-full bg-muted">
            {dragOver ? (
              <FileText className="size-6 text-primary" />
            ) : (
              <Upload className="size-6 text-muted-foreground" />
            )}
          </div>
          <div className="text-center">
            <p className="text-sm font-medium">
              {dragOver ? "Drop file here" : "Drag and drop your .docx file"}
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              or click to browse
            </p>
          </div>
        </button>
      </div>
    </div>
  )
}
```

**Step 2: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds

**Step 3: Commit**

```bash
git add frontend/src/components/UploadZone.tsx
git commit -m "feat: extract UploadZone component"
```

---

### Task 3: Create HistoryList sidebar component

**Files:**
- Create: `frontend/src/components/HistoryList.tsx`

**Step 1: Create HistoryList component**

```tsx
import { useLocation, Link } from "react-router-dom"
import { FileText } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"
import { useTranslations } from "@/hooks/queries/use-translations"
import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"

export function HistoryList() {
  const { data: translations, isLoading } = useTranslations()
  const location = useLocation()

  if (isLoading) {
    return (
      <SidebarGroup>
        <SidebarGroupLabel>History</SidebarGroupLabel>
        <SidebarGroupContent>
          <div className="space-y-2 px-2">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="flex items-center gap-2 py-1">
                <Skeleton className="size-4 rounded" />
                <Skeleton className="h-4 flex-1" />
              </div>
            ))}
          </div>
        </SidebarGroupContent>
      </SidebarGroup>
    )
  }

  if (!translations?.length) {
    return (
      <SidebarGroup>
        <SidebarGroupLabel>History</SidebarGroupLabel>
        <SidebarGroupContent>
          <p className="px-4 py-3 text-xs text-muted-foreground">
            No translations yet.
          </p>
        </SidebarGroupContent>
      </SidebarGroup>
    )
  }

  return (
    <SidebarGroup>
      <SidebarGroupLabel>History</SidebarGroupLabel>
      <SidebarGroupContent>
        <SidebarMenu>
          {translations.map((t) => (
            <SidebarMenuItem key={t.id}>
              <SidebarMenuButton
                asChild
                isActive={location.pathname === `/t/${t.id}`}
              >
                <Link to={`/t/${t.id}`}>
                  <FileText />
                  <div className="flex-1 min-w-0">
                    <span className="truncate text-sm">{t.filename}</span>
                    <span className="block truncate text-xs text-muted-foreground">
                      {t.paragraph_count} paragraphs
                    </span>
                  </div>
                </Link>
              </SidebarMenuButton>
            </SidebarMenuItem>
          ))}
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  )
}
```

**Step 2: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds

**Step 3: Commit**

```bash
git add frontend/src/components/HistoryList.tsx
git commit -m "feat: add HistoryList sidebar component"
```

---

### Task 4: Rewrite AppSidebar

Replace nav items with "New Upload" button + HistoryList.

**Files:**
- Modify: `frontend/src/components/layout/AppSidebar.tsx`

**Step 1: Rewrite AppSidebar**

Replace entire file contents:

```tsx
import { Link } from "react-router-dom"
import { Plus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { HistoryList } from "@/components/HistoryList"
import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
} from "@/components/ui/sidebar"

export function AppSidebar() {
  return (
    <Sidebar>
      <SidebarHeader className="px-4 py-4 space-y-4">
        <Link to="/" className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary text-primary-foreground text-sm font-bold">
            W
          </div>
          <span className="text-sm font-semibold">Word Translator</span>
        </Link>
        <Button asChild className="w-full" size="sm">
          <Link to="/">
            <Plus />
            New Upload
          </Link>
        </Button>
      </SidebarHeader>
      <SidebarContent>
        <HistoryList />
      </SidebarContent>
    </Sidebar>
  )
}
```

**Step 2: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds (pages still reference old routes but sidebar is updated)

**Step 3: Commit**

```bash
git add frontend/src/components/layout/AppSidebar.tsx
git commit -m "feat: rewrite AppSidebar with new upload button and history list"
```

---

### Task 5: Create Workspace page

The single page that orchestrates all three states.

**Files:**
- Create: `frontend/src/pages/Workspace.tsx`

**Step 1: Create Workspace page**

```tsx
import { useParams, useNavigate } from "react-router-dom"
import { useTranslation } from "@/hooks/queries/use-translations"
import { useUploadTranslation } from "@/hooks/queries/use-upload-translation"
import { UploadZone } from "@/components/UploadZone"
import { TranslationView } from "@/components/TranslationView"

export default function Workspace() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const mutation = useUploadTranslation()
  const { data: result, isLoading, isError } = useTranslation(id ?? "")

  function handleFileSelect(file: File) {
    mutation.mutate(file, {
      onSuccess: (data) => navigate(`/t/${data.id}`),
    })
  }

  // Upload in progress
  if (mutation.isPending) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <div className="size-8 animate-spin rounded-full border-2 border-muted-foreground border-t-transparent" />
        <p className="text-sm text-muted-foreground">
          Translating your document...
        </p>
      </div>
    )
  }

  // Viewing a specific translation
  if (id) {
    if (isLoading) {
      return (
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="size-8 animate-spin rounded-full border-2 border-muted-foreground border-t-transparent" />
        </div>
      )
    }

    if (isError || !result) {
      return (
        <div className="flex flex-col items-center justify-center min-h-[60vh] gap-2">
          <p className="text-sm text-muted-foreground">
            Translation not found.
          </p>
        </div>
      )
    }

    return <TranslationView result={result} />
  }

  // Idle — show upload zone
  return (
    <UploadZone
      onFileSelect={handleFileSelect}
      error={mutation.isError ? mutation.error.message : null}
    />
  )
}
```

**Step 2: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds

**Step 3: Commit**

```bash
git add frontend/src/pages/Workspace.tsx
git commit -m "feat: add Workspace page with three-state orchestration"
```

---

### Task 6: Update routes and delete old pages

Wire up Workspace as the only page and remove the old pages.

**Files:**
- Modify: `frontend/src/App.tsx`
- Delete: `frontend/src/pages/Dashboard.tsx`
- Delete: `frontend/src/pages/Upload.tsx`
- Delete: `frontend/src/pages/History.tsx`
- Delete: `frontend/src/pages/TranslationDetail.tsx`

**Step 1: Rewrite App.tsx**

Replace entire file contents:

```tsx
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import { DashboardLayout } from "@/components/layout/DashboardLayout"
import Workspace from "@/pages/Workspace"

export default function App() {
  return (
    <BrowserRouter>
      <DashboardLayout>
        <Routes>
          <Route path="/" element={<Workspace />} />
          <Route path="/t/:id" element={<Workspace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </DashboardLayout>
    </BrowserRouter>
  )
}
```

**Step 2: Delete old pages**

```bash
rm frontend/src/pages/Dashboard.tsx
rm frontend/src/pages/Upload.tsx
rm frontend/src/pages/History.tsx
rm frontend/src/pages/TranslationDetail.tsx
```

**Step 3: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds with no errors

**Step 4: Verify lint**

Run: `cd frontend && npm run lint`
Expected: No errors

**Step 5: Commit**

```bash
git add -A frontend/src/App.tsx frontend/src/pages/
git commit -m "feat: wire Workspace routes and remove old pages"
```

---

### Task 7: Manual smoke test

Verify the full user flow works end-to-end.

**Step 1: Start backend (if not running)**

Run: `cd backend && uv run uvicorn src.main:app --reload --port 8888`

**Step 2: Start frontend (if not running)**

Run: `cd frontend && npm run dev`

**Step 3: Test checklist**

- [ ] `/` shows upload zone with drag-drop area
- [ ] Upload a `.docx` file → spinner appears → result shows in main area
- [ ] After upload, sidebar shows new item highlighted
- [ ] URL changes to `/t/<id>`
- [ ] Click "New Upload" → returns to upload zone, URL changes to `/`
- [ ] Click a history item → loads that translation
- [ ] Direct navigation to `/t/<id>` loads the translation
- [ ] `/anything-else` redirects to `/`
- [ ] Sidebar toggle (mobile) still works

**Step 4: Final commit if any fixes needed**

```bash
git add -A && git commit -m "fix: workspace smoke test fixes"
```
