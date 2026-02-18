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
    if (!file.name.endsWith(".docx") && !file.name.endsWith(".pdf")) return
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
          accept=".docx,.pdf"
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
              {dragOver ? "Drop file here" : "Drag and drop your document"}
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              .docx or .pdf — or click to browse
            </p>
          </div>
        </button>
      </div>
    </div>
  )
}
