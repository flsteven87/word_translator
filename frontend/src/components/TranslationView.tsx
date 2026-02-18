import { Download } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Tooltip, TooltipTrigger, TooltipContent } from "@/components/ui/tooltip"
import { FontSizeControl } from "@/components/FontSizeControl"
import { getDownloadUrl } from "@/lib/api"
import type { TranslationResult, ParagraphStyle } from "@/lib/api"

interface Props {
  readonly result: TranslationResult
}

const STYLE_WEIGHTS: Record<ParagraphStyle, string> = {
  title: "font-bold",
  heading_1: "font-semibold",
  heading_2: "font-semibold",
  heading_3: "font-semibold",
  heading_4: "font-medium italic",
  normal: "",
}

const STYLE_SIZES: Record<ParagraphStyle, string> = {
  title: "calc(1.25rem * var(--font-scale, 1))",
  heading_1: "calc(1.125rem * var(--font-scale, 1))",
  heading_2: "calc(1rem * var(--font-scale, 1))",
  heading_3: "calc(0.875rem * var(--font-scale, 1))",
  heading_4: "calc(0.875rem * var(--font-scale, 1))",
  normal: "calc(0.875rem * var(--font-scale, 1))",
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
          <p className="mt-1 flex items-center gap-1.5 text-sm text-muted-foreground">
            {result.paragraphs.length} paragraphs &middot;{" "}
            {new Date(result.created_at).toLocaleDateString()}
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="ghost" size="icon-xs" asChild>
                  <a href={getDownloadUrl(result.id)} download>
                    <Download />
                  </a>
                </Button>
              </TooltipTrigger>
              <TooltipContent>Download Chinese Word file</TooltipContent>
            </Tooltip>
          </p>
        </div>
        <FontSizeControl />
      </div>

      <div className="mt-8">
        <div className="grid grid-cols-2 gap-x-8 mb-4 px-1">
          <p className="text-xs font-medium text-muted-foreground">English</p>
          <p className="text-xs font-medium text-muted-foreground">中文</p>
        </div>

        <div>
          {result.paragraphs.map((p, i) => {
            const weight = STYLE_WEIGHTS[p.style]
            const fontSize = STYLE_SIZES[p.style]
            const structural = isStructural(p.style)
            const prevIsNormal = i > 0 && !isStructural(result.paragraphs[i - 1].style)
            const topSpacing = getTopSpacing(p.style, i, prevIsNormal)

            if (structural) {
              return (
                <div
                  key={i}
                  className={`grid grid-cols-2 gap-x-8 border-b border-border/60 ${topSpacing}`}
                >
                  <div className={`px-1 pb-2 leading-relaxed ${weight}`} style={{ fontSize }}>
                    {p.original}
                  </div>
                  <div className={`px-1 pb-2 leading-relaxed ${weight}`} style={{ fontSize }}>
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
                <div className={`px-1 py-2 leading-relaxed text-muted-foreground ${weight}`} style={{ fontSize }}>
                  {p.original}
                </div>
                <div className={`px-1 py-2 leading-relaxed ${weight}`} style={{ fontSize }}>
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
