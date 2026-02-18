const BASE_URL = "/api/v1"

export interface TranslatedParagraph {
  original: string
  translated: string
}

export interface TranslationResult {
  id: string
  filename: string
  created_at: string
  paragraphs: TranslatedParagraph[]
}

export interface TranslationSummary {
  id: string
  filename: string
  created_at: string
  paragraph_count: number
}

export async function uploadDocument(file: File): Promise<TranslationResult> {
  const formData = new FormData()
  formData.append("file", file)
  const res = await fetch(`${BASE_URL}/translations/upload`, {
    method: "POST",
    body: formData,
  })
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Upload failed" }))
    throw new Error(error.detail)
  }
  return res.json()
}

export async function fetchTranslations(): Promise<TranslationSummary[]> {
  const res = await fetch(`${BASE_URL}/translations`)
  if (!res.ok) throw new Error("Failed to fetch translations")
  return res.json()
}

export async function fetchTranslation(
  id: string,
): Promise<TranslationResult> {
  const res = await fetch(`${BASE_URL}/translations/${id}`)
  if (!res.ok) throw new Error("Translation not found")
  return res.json()
}

export function getDownloadUrl(id: string): string {
  return `${BASE_URL}/translations/${id}/download`
}
