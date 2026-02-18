# Word Translator - Core Feature Design

## Overview

Upload English Word (.docx) documents, translate to Chinese via OpenAI, display side-by-side bilingual results, and download as a bilingual Word file.

## Requirements

| Item | Decision |
|------|----------|
| Translation direction | English → Chinese |
| Display | Left-right side-by-side, paragraph-aligned |
| Download | Web view + downloadable bilingual Word file |
| Storage | Backend JSON file system |
| Translation granularity | Batch grouping with swappable Strategy Pattern |

## Architecture

### API Endpoints

```
POST /api/v1/translations/upload       Upload .docx + translate
GET  /api/v1/translations              List translation history
GET  /api/v1/translations/{id}         Get single translation result
GET  /api/v1/translations/{id}/download  Download bilingual Word file
```

### Backend Modules

```
DocumentParser     Parse .docx → extract paragraphs
TranslationStrategy (ABC)  Swappable translation engine
  └─ BatchTranslationStrategy  Default: batch 5-10 paragraphs per API call
TranslationStore   Save/load JSON results to file system
WordExporter       Generate bilingual Word file (two-column table)
```

### Data Flow

```
.docx upload
  → DocumentParser (extract paragraphs)
  → TranslationStrategy (batch translate via OpenAI)
  → TranslationStore (persist as JSON)
  → Response (return translation result)

Download request
  → TranslationStore (load JSON)
  → WordExporter (generate bilingual .docx)
  → FileResponse
```

### JSON Storage Format

```json
{
  "id": "uuid",
  "filename": "document.docx",
  "created_at": "2026-02-18T10:00:00Z",
  "paragraphs": [
    {"original": "English text...", "translated": "Chinese translation..."}
  ]
}
```

### Frontend Pages

| Page | Function |
|------|----------|
| Dashboard | Quick entry + recent translations |
| Upload | Drag-drop upload → loading → side-by-side result + download button |
| History | Translation history list, click to view result |

## Key Design Decisions

- **Strategy Pattern** for translation: easy to swap engines (OpenAI, Claude, DeepL) or change granularity (per-paragraph, batch, whole-doc).
- **Synchronous API** for MVP: simpler error handling, reliable. SSE can be layered on later.
- **File system storage**: JSON files in a `data/translations/` directory. No database dependency.
- **4-layer architecture**: API → Service → modules (parser, translator, store, exporter).
