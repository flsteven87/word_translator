import { Download } from "lucide-react"
import { Button } from "@/components/ui/button"
import { getDownloadUrl } from "@/lib/api"
import type { TranslationResult } from "@/lib/api"

interface Props {
  readonly result: TranslationResult
}

export function TranslationView({ result }: Props) {
  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            {result.filename}
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {result.paragraphs.length} paragraphs &middot;{" "}
            {new Date(result.created_at).toLocaleDateString()}
          </p>
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
              <div className="bg-background px-4 py-3 text-sm leading-relaxed border-b border-border last:border-b-0">
                {p.original}
              </div>
              <div className="bg-background px-4 py-3 text-sm leading-relaxed border-b border-border last:border-b-0">
                {p.translated}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
