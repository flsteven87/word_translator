import { Link } from "react-router-dom"
import { Upload, FileText } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { useTranslations } from "@/hooks/queries/use-translations"

export default function Dashboard() {
  const { data: translations, isLoading } = useTranslations()
  const recent = translations?.slice(0, 5)

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
          <p className="mt-2 text-muted-foreground">
            Translation overview and quick actions.
          </p>
        </div>
        <Button asChild>
          <Link to="/upload">
            <Upload />
            Upload Document
          </Link>
        </Button>
      </div>

      <section className="mt-10">
        <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
          Recent Translations
        </h2>

        <div className="mt-4 space-y-1">
          {isLoading &&
            Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="flex items-center gap-3 px-3 py-3">
                <Skeleton className="size-9 rounded-md" />
                <div className="flex-1 space-y-1.5">
                  <Skeleton className="h-4 w-48" />
                  <Skeleton className="h-3 w-32" />
                </div>
              </div>
            ))}

          {!isLoading && recent?.length === 0 && (
            <p className="py-8 text-center text-sm text-muted-foreground">
              No translations yet. Upload a document to get started.
            </p>
          )}

          {recent?.map((t) => (
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

          {recent && recent.length > 0 && translations && translations.length > 5 && (
            <div className="pt-2">
              <Button variant="link" size="sm" asChild className="px-3">
                <Link to="/history">View all translations</Link>
              </Button>
            </div>
          )}
        </div>
      </section>
    </div>
  )
}
