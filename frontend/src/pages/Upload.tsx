import { useState, useRef } from "react"
import { Upload as UploadIcon, FileText, Download, X, Plus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useUploadTranslation } from "@/hooks/queries/use-upload-translation"
import { getDownloadUrl } from "@/lib/api"
import type { TranslationResult } from "@/lib/api"

export default function Upload() {
  const [dragOver, setDragOver] = useState(false)
  const [result, setResult] = useState<TranslationResult | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const mutation = useUploadTranslation()

  function handleFile(file: File) {
    if (!file.name.endsWith(".docx")) return
    setResult(null)
    mutation.mutate(file, {
      onSuccess: (data) => setResult(data),
    })
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

  function handleReset() {
    setResult(null)
    mutation.reset()
  }

  // Loading state
  if (mutation.isPending) {
    return (
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Upload</h1>
        <div className="mt-12 flex flex-col items-center gap-4">
          <div className="size-8 animate-spin rounded-full border-2 border-muted-foreground border-t-transparent" />
          <p className="text-sm text-muted-foreground">
            Translating your document...
          </p>
        </div>
      </div>
    )
  }

  // Result state
  if (result) {
    return (
      <div>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">
              Translation Complete
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              {result.filename} &middot; {result.paragraphs.length} paragraphs
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" asChild>
              <a href={getDownloadUrl(result.id)} download>
                <Download />
                Download
              </a>
            </Button>
            <Button variant="outline" onClick={handleReset}>
              <Plus />
              New Upload
            </Button>
          </div>
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
                <div className="bg-background px-4 py-3 text-sm leading-relaxed">
                  {p.original}
                </div>
                <div className="bg-background px-4 py-3 text-sm leading-relaxed">
                  {p.translated}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  // Idle state (drag-drop zone)
  return (
    <div>
      <h1 className="text-2xl font-semibold tracking-tight">Upload</h1>
      <p className="mt-2 text-muted-foreground">
        Upload Word documents for translation.
      </p>

      {mutation.isError && (
        <div className="mt-4 flex items-center gap-2 rounded-md border border-destructive/50 bg-destructive/5 px-4 py-3 text-sm text-destructive">
          <X className="size-4 shrink-0" />
          {mutation.error.message}
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
        className={`mt-6 flex w-full flex-col items-center gap-4 rounded-lg border-2 border-dashed px-6 py-16 transition-colors ${
          dragOver
            ? "border-primary bg-primary/5"
            : "border-muted-foreground/25 hover:border-muted-foreground/50"
        }`}
      >
        <div className="flex size-12 items-center justify-center rounded-full bg-muted">
          {dragOver ? (
            <FileText className="size-6 text-primary" />
          ) : (
            <UploadIcon className="size-6 text-muted-foreground" />
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
  )
}
