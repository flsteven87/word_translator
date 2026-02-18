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

function isStructural(style: ParagraphStyle): boolean {
  return style !== "normal"
}

function getTopSpacing(style: ParagraphStyle, index: number, prevIsNormal: boolean): string {
  if (!isStructural(style) || index === 0) return ""
  if (style === "title") return "pt-8"
  if (prevIsNormal) return "pt-6"
  return "pt-4"
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
        <div className="grid grid-cols-2 gap-x-8 mb-4 px-1">
          <p className="text-xs font-medium text-muted-foreground">English</p>
          <p className="text-xs font-medium text-muted-foreground">中文</p>
        </div>

        <div>
          {result.paragraphs.map((p, i) => {
            const styleClass = STYLE_CLASSES[p.style]
            const structural = isStructural(p.style)
            const prevIsNormal = i > 0 && !isStructural(result.paragraphs[i - 1].style)
            const topSpacing = getTopSpacing(p.style, i, prevIsNormal)

            if (structural) {
              return (
                <div
                  key={i}
                  className={`grid grid-cols-2 gap-x-8 border-b border-border/60 ${topSpacing}`}
                >
                  <div className={`px-1 pb-2 leading-relaxed ${styleClass}`}>
                    {p.original}
                  </div>
                  <div className={`px-1 pb-2 leading-relaxed ${styleClass}`}>
                    {p.translated}
                  </div>
                </div>
              )
            }

            return (
              <div
                key={i}
                className="grid grid-cols-2 gap-x-8 rounded-md transition-colors hover:bg-muted/40"
              >
                <div className={`px-1 py-2 leading-relaxed text-muted-foreground ${styleClass}`}>
                  {p.original}
                </div>
                <div className={`px-1 py-2 leading-relaxed ${styleClass}`}>
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
