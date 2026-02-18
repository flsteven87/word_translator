# PDF Support Design

## Goal

Add PDF file support to DocDual, enabling users to upload `.pdf` files (primarily academic papers) and get the same bilingual side-by-side reading experience as `.docx`.

## Parsing Library

**PyMuPDF4LLM** — converts PDF to structured Markdown with heading detection via font-size analysis, automatic multi-column handling, and header/footer removal. ~0.12s/page, minimal dependencies.

## Architecture

The existing `DocumentParser.parse()` is the sole integration point. It currently only handles `.docx`. The change:

```
DocumentParser.parse(file_content, filename)
    ├── .docx → DocxParser (existing logic, extracted)
    └── .pdf  → PdfParser (new, PyMuPDF4LLM)
    Both return → list[ParsedParagraph]
```

No changes needed to `TranslationService`, `TranslationStrategy`, `TranslationStore`, or the data model. They all operate on `list[ParsedParagraph]` which remains unchanged.

## Backend Changes

### 1. `DocumentParser` — route by file extension

`parse(file_content, filename)` dispatches to the correct parser based on filename extension. The existing docx logic moves into a private `_parse_docx()` method.

### 2. `PdfParser` — new private method `_parse_pdf()`

Uses `pymupdf4llm.to_markdown()` to get structured Markdown, then parses it:

- `#` → `ParagraphStyle.TITLE`
- `##` → `ParagraphStyle.HEADING_1`
- `###` → `ParagraphStyle.HEADING_2`
- `####` → `ParagraphStyle.HEADING_3`
- `#####` → `ParagraphStyle.HEADING_4`
- Plain text → `ParagraphStyle.NORMAL`
- Empty lines / page breaks → paragraph boundaries
- Bold-only lines (likely sub-headings) → `HEADING_3`

### 3. API endpoint — accept PDF content type

Add `application/pdf` to `ALLOWED_CONTENT_TYPES`. Update error message.

### 4. `translate_document` — pass filename for dispatch

`DocumentParser.parse()` gains a `filename` parameter to determine file type.

## Frontend Changes

### 1. `UploadZone.tsx`

- `accept` attribute: `.docx,.pdf`
- File validation: accept both extensions
- Drag-and-drop text: "Drag and drop your document" (remove `.docx` specificity)

### 2. `api.ts`

No changes needed — already sends `FormData` with the file as-is.

## Markdown Parsing Strategy

PyMuPDF4LLM outputs Markdown like:

```markdown
# Paper Title

## Abstract

This paper presents...

## 1. Introduction

The field of...
```

The parser will:
1. Split by lines
2. Detect heading level via `#` prefix count
3. Accumulate consecutive non-heading lines into a single paragraph
4. Skip image references (`![...](...)`), page markers, and empty lines
5. Strip bold markers (`**`) from heading text

## Edge Cases

- **Scanned PDFs** (image-only): PyMuPDF4LLM returns empty/minimal text. Detect and return a clear error: "This PDF appears to be scanned. Please use a text-based PDF."
- **Very large PDFs**: The existing 10MB limit applies. Academic papers are typically 1-5MB.
- **Tables**: PyMuPDF4LLM outputs Markdown tables. For now, treat table rows as normal paragraphs. Future enhancement could preserve table structure.
- **Figures/captions**: Skip image markdown, keep caption text if present.
- **References section**: Parse normally as paragraphs. No special handling needed for translation.

## Dependencies

```bash
uv add pymupdf4llm
```

This pulls in `pymupdf` (PyMuPDF) as a transitive dependency. AGPL-licensed — acceptable since the project is open-source.

## Files to Modify

| File | Change |
|------|--------|
| `backend/pyproject.toml` | Add `pymupdf4llm` dependency |
| `backend/src/services/document_parser.py` | Add `filename` param, extract docx logic, add PDF parsing |
| `backend/src/services/translation_service.py` | Pass `filename` to parser |
| `backend/src/api/v1/endpoints/translations.py` | Add PDF content type, update error message |
| `frontend/src/components/UploadZone.tsx` | Accept `.pdf`, update text |

## Files Unchanged

- `models/translation.py` — `ParagraphStyle` enum already covers all needed styles
- `translation_strategy.py` — operates on `list[str]`, format-agnostic
- `translation_store.py` — stores `TranslationResult`, format-agnostic
- `word_exporter.py` — exports to `.docx` regardless of source format (acceptable)
- `api.ts`, query hooks — already generic
