import { Link } from "react-router-dom"
import { FileText } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"
import { useTranslations } from "@/hooks/queries/use-translations"

export default function History() {
  const { data: translations, isLoading, isError } = useTranslations()

  return (
    <div>
      <h1 className="text-2xl font-semibold tracking-tight">History</h1>
      <p className="mt-2 text-muted-foreground">
        View past translation records.
      </p>

      <div className="mt-8 space-y-1">
        {isLoading &&
          Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex items-center gap-3 px-3 py-3">
              <Skeleton className="size-9 rounded-md" />
              <div className="flex-1 space-y-1.5">
                <Skeleton className="h-4 w-48" />
                <Skeleton className="h-3 w-32" />
              </div>
            </div>
          ))}

        {isError && (
          <p className="py-8 text-center text-sm text-muted-foreground">
            Failed to load translations.
          </p>
        )}

        {translations?.length === 0 && (
          <p className="py-8 text-center text-sm text-muted-foreground">
            No translations yet. Upload a document to get started.
          </p>
        )}

        {translations?.map((t) => (
          <Link
            key={t.id}
            to={`/history/${t.id}`}
            className="flex items-center gap-3 rounded-md px-3 py-3 transition-colors hover:bg-muted"
          >
            <div className="flex size-9 items-center justify-center rounded-md bg-muted">
              <FileText className="size-4 text-muted-foreground" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="truncate text-sm font-medium">{t.filename}</p>
              <p className="text-xs text-muted-foreground">
                {t.paragraph_count} paragraphs &middot;{" "}
                {new Date(t.created_at).toLocaleDateString()}
              </p>
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}
