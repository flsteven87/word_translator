# Bidirectional Translation Design

## Problem

PaperBridge currently only supports English → Traditional Chinese translation. Users need the ability to translate Chinese documents into English as well.

## Decision

Automatic language detection via OpenAI structured output, supporting bidirectional Chinese ↔ English translation with zero additional user interaction.

## Design

### Language Detection

Use `client.beta.chat.completions.parse()` with a Pydantic model to detect the document language from a text sample.

```python
class DocumentLanguage(str, Enum):
    EN = "en"
    ZH = "zh"

class LanguageDetectionResult(BaseModel):
    language: DocumentLanguage
```

**Sampling strategy**: Extract the first 3-5 parsed paragraphs (up to ~1000 chars). This is sufficient for language identification in academic papers.

**Model**: `gpt-4o-mini` with `temperature=0` for deterministic, cost-efficient detection (< $0.001 per call).

**Key constraint**: OpenAI structured output does not support Pydantic field constraints (`ge`, `le`, `minLength`). Keep the schema minimal — a single enum field is all that's needed.

### Translation Direction

New enum representing translation direction:

```python
class TranslationDirection(str, Enum):
    EN_TO_ZH = "en_to_zh"
    ZH_TO_EN = "zh_to_en"
```

Direction-specific system prompts:

| Direction | Prompt focus |
|-----------|-------------|
| `en_to_zh` | "English to Traditional Chinese (繁體中文)" — current behavior |
| `zh_to_en` | "Traditional Chinese to natural, academic English" |

`BatchTranslationStrategy.__init__` receives a `direction` parameter to select the appropriate prompt. All batch/parse logic remains unchanged.

### Data Model Changes

`TranslationResult` gains a `direction` field:

```python
class TranslationResult(BaseModel):
    id: UUID
    filename: str
    direction: TranslationDirection = TranslationDirection.EN_TO_ZH  # backward compatible
    created_at: datetime
    paragraphs: list[TranslatedParagraph]
```

Existing saved translations without `direction` default to `EN_TO_ZH`, ensuring backward compatibility with stored JSON files.

### Translation Service Flow

```
upload file
  → parse document
  → sample first N paragraphs
  → detect language (structured output)
  → determine direction (zh → en_to_zh becomes zh_to_en, en → stays en_to_zh)
  → create BatchTranslationStrategy with direction
  → translate (existing pipeline, unchanged)
  → save result with direction field
```

### Word Exporter Changes

Export filename suffix changes based on direction:

| Direction | Filename suffix |
|-----------|----------------|
| `en_to_zh` | `_中文.docx` (current) |
| `zh_to_en` | `_English.docx` |

### Frontend Changes

**`api.ts`**: Add `direction` field to `TranslationResult` type.

**`TranslationView.tsx`**: Dynamic column headers based on `result.direction`:

| Direction | Left column | Right column |
|-----------|------------|-------------|
| `en_to_zh` | English | 中文 |
| `zh_to_en` | 中文 | English |

Download tooltip text adapts accordingly.

**No changes needed**: UploadZone, Workspace, HistoryList, query hooks, sidebar.

## Files to Modify

| File | Change |
|------|--------|
| `backend/src/models/translation.py` | Add `TranslationDirection` enum, `direction` field |
| `backend/src/services/translation_strategy.py` | Direction-aware prompts, `LanguageDetectionResult` model, detect method |
| `backend/src/services/translation_service.py` | Call detection before translation, pass direction to strategy |
| `backend/src/services/word_exporter.py` | Direction-aware export filename |
| `frontend/src/lib/api.ts` | Add `direction` type |
| `frontend/src/components/TranslationView.tsx` | Dynamic column headers and tooltip |

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Mixed-language documents (e.g., Chinese paper with English abstract) | LLM detection on sampled text handles this well; majority language wins |
| Detection failure / API error | Default to `en_to_zh` (current behavior) as fallback |
| Existing stored translations lack `direction` | Pydantic default value ensures backward compatibility |
