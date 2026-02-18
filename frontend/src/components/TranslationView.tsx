import { Download } from "lucide-react"
import { Button } from "@/components/ui/button"
import { getDownloadUrl } from "@/lib/api"
import type { TranslationResult, ParagraphStyle } from "@/lib/api"

interface Props {
  readonly result: TranslationResult
}

const STYLE_CLASSES: Record<ParagraphStyle, string> = {
  title: "text-xl font-bold",
  heading_1: "text-lg font-semibold",
  heading_2: "text-base font-semibold",
  heading_3: "text-sm font-semibold",
  heading_4: "text-sm font-medium italic",
  normal: "text-sm",
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
          {result.paragraphs.map((p, i) => {
            const styleClass = STYLE_CLASSES[p.style]
            return (
              <div key={i} className="contents">
                <div
                  className={`bg-background px-4 py-3 leading-relaxed border-b border-border last:border-b-0 ${styleClass}`}
                >
                  {p.original}
                </div>
                <div
                  className={`bg-background px-4 py-3 leading-relaxed border-b border-border last:border-b-0 ${styleClass}`}
                >
                  {p.translated}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
