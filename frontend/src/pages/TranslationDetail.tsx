import { useParams, Link } from "react-router-dom"
import { ArrowLeft, Download } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { useTranslation } from "@/hooks/queries/use-translations"
import { getDownloadUrl } from "@/lib/api"

export default function TranslationDetail() {
  const { id } = useParams<{ id: string }>()
  const { data: result, isLoading, isError } = useTranslation(id ?? "")

  if (isLoading) {
    return (
      <div>
        <Skeleton className="h-7 w-48" />
        <Skeleton className="mt-2 h-4 w-32" />
        <div className="mt-8 space-y-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      </div>
    )
  }

  if (isError || !result) {
    return (
      <div>
        <Button variant="ghost" size="sm" asChild>
          <Link to="/history">
            <ArrowLeft />
            Back to History
          </Link>
        </Button>
        <p className="mt-8 text-center text-sm text-muted-foreground">
          Translation not found.
        </p>
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" asChild>
            <Link to="/history">
              <ArrowLeft />
            </Link>
          </Button>
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">
              {result.filename}
            </h1>
            <p className="mt-0.5 text-sm text-muted-foreground">
              {result.paragraphs.length} paragraphs &middot;{" "}
              {new Date(result.created_at).toLocaleDateString()}
            </p>
          </div>
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
