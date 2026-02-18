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
