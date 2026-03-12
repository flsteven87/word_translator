import { useEffect, useState } from "react"
import { ArrowUp, Download, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { FontSizeControl } from "@/components/FontSizeControl"
import { useRetranslate } from "@/hooks/queries/use-retranslate"
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
  figure: "",
  table: "",
}

const STYLE_SIZES: Record<ParagraphStyle, string> = {
  title: "calc(1.25rem * var(--font-scale, 1))",
  heading_1: "calc(1.125rem * var(--font-scale, 1))",
  heading_2: "calc(1rem * var(--font-scale, 1))",
  heading_3: "calc(0.875rem * var(--font-scale, 1))",
  heading_4: "calc(0.875rem * var(--font-scale, 1))",
  normal: "calc(0.875rem * var(--font-scale, 1))",
  figure: "calc(0.75rem * var(--font-scale, 1))",
  table: "calc(0.75rem * var(--font-scale, 1))",
}

function isStructural(style: ParagraphStyle): boolean {
  return style !== "normal" && style !== "figure" && style !== "table"
}

function isNonTranslatable(style: ParagraphStyle): boolean {
  return style === "figure" || style === "table"
}


function getTopSpacing(style: ParagraphStyle, index: number, prevIsNormal: boolean): string {
  if (!isStructural(style) || index === 0) return ""
  if (style === "title") return "pt-8"
  if (prevIsNormal) return "pt-6"
  return "pt-4"
}

function useShowScrollTop(threshold = 300) {
  const [show, setShow] = useState(false)
  useEffect(() => {
    function handleScroll() {
      setShow(window.scrollY > threshold)
    }
    window.addEventListener("scroll", handleScroll, { passive: true })
    return () => window.removeEventListener("scroll", handleScroll)
  }, [threshold])
  return show
}

export function TranslationView({ result }: Props) {
  const retranslate = useRetranslate()
  const showScrollTop = useShowScrollTop()

  return (
    <div>
      <div>
        <h1 className="text-2xl font-semibold tracking-tight break-words">
          {result.filename}
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          {result.paragraphs.length} paragraphs &middot;{" "}
          {new Date(result.created_at).toLocaleDateString()}
        </p>

        <div className="mt-3 flex items-center gap-1.5">
          <Button
            variant="ghost"
            size="sm"
            disabled={retranslate.isPending}
            onClick={() => retranslate.mutate(result.id)}
          >
            <RefreshCw className={retranslate.isPending ? "animate-spin" : ""} />
            {retranslate.isPending ? "重翻中..." : "重翻"}
          </Button>
          <Button variant="ghost" size="sm" asChild>
            <a href={getDownloadUrl(result.id)} download>
              <Download />
              下載
            </a>
          </Button>
          <div className="flex-1" />
          <FontSizeControl />
        </div>
      </div>

      <div className="mt-8">
        <div className="grid grid-cols-2 gap-x-8 mb-4 px-1">
          <p className="text-xs font-medium text-muted-foreground">
            {result.direction === "zh_to_en" ? "中文" : "English"}
          </p>
          <p className="text-xs font-medium text-muted-foreground">
            {result.direction === "zh_to_en" ? "English" : "中文"}
          </p>
        </div>

        <div>
          {result.paragraphs.map((p, i) => {
            const weight = STYLE_WEIGHTS[p.style]
            const fontSize = STYLE_SIZES[p.style]
            const structural = isStructural(p.style)
            const prevIsNormal = i > 0 && !isStructural(result.paragraphs[i - 1].style)
            const topSpacing = getTopSpacing(p.style, i, prevIsNormal)

            if (isNonTranslatable(p.style)) {
              return (
                <div
                  key={i}
                  className={`rounded-md bg-muted/30 ${topSpacing}`}
                >
                  <div className="px-3 py-1.5 text-xs text-muted-foreground font-medium">
                    {p.style === "figure" ? "Figure" : "Table"}
                  </div>
                  {p.style === "table" ? (
                    <div
                      className="px-3 pb-3 text-sm leading-relaxed overflow-x-auto [&_table]:w-full [&_table]:border-collapse [&_td]:border [&_td]:border-border/40 [&_td]:px-2 [&_td]:py-1 [&_td]:text-xs [&_th]:border [&_th]:border-border/40 [&_th]:px-2 [&_th]:py-1 [&_th]:text-xs [&_th]:font-medium"
                      style={{ fontSize }}
                      dangerouslySetInnerHTML={{ __html: p.original }}
                    />
                  ) : p.image ? (
                    <div className="px-3 pb-3">
                      <img
                        src={`data:image/png;base64,${p.image}`}
                        alt={p.original}
                        className="max-w-full h-auto rounded"
                      />
                    </div>
                  ) : (
                    <div
                      className="px-3 pb-3 text-muted-foreground/80 font-mono leading-relaxed whitespace-pre-wrap break-all"
                      style={{ fontSize }}
                    >
                      {p.original}
                    </div>
                  )}
                </div>
              )
            }

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

      <button
        type="button"
        onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
        className={`fixed bottom-6 right-6 z-50 flex size-10 items-center justify-center rounded-full bg-foreground text-background shadow-lg transition-all duration-200 hover:opacity-80 ${showScrollTop ? "translate-y-0 opacity-100" : "translate-y-4 opacity-0 pointer-events-none"}`}
        aria-label="Scroll to top"
      >
        <ArrowUp className="size-4" />
      </button>
    </div>
  )
}
