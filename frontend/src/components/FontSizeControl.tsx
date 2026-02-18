import { useFontSize, FONT_SIZE_OPTIONS } from "@/hooks/use-font-size"
import { cn } from "@/lib/utils"

interface Props {
  readonly compact?: boolean
}

export function FontSizeControl({ compact = false }: Props) {
  const { level, setFontSize } = useFontSize()

  if (compact) {
    return (
      <div className="flex items-center gap-2">
        <span className="text-xs font-medium text-sidebar-foreground/70 select-none">
          Aa
        </span>
        <div className="flex gap-0.5">
          {FONT_SIZE_OPTIONS.map((option) => (
            <button
              key={option.level}
              onClick={() => setFontSize(option.level)}
              className={cn(
                "px-2 py-1 text-xs rounded-md transition-colors",
                level === option.level
                  ? "bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                  : "text-sidebar-foreground/60 hover:text-sidebar-foreground hover:bg-sidebar-accent/50",
              )}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-2">
      <span className="text-xs font-medium text-muted-foreground select-none">
        Aa
      </span>
      <div className="flex rounded-lg border border-border p-0.5 gap-0.5">
        {FONT_SIZE_OPTIONS.map((option) => (
          <button
            key={option.level}
            onClick={() => setFontSize(option.level)}
            className={cn(
              "px-2.5 py-1 text-xs rounded-md transition-colors",
              level === option.level
                ? "bg-primary text-primary-foreground font-medium"
                : "text-muted-foreground hover:text-foreground hover:bg-muted",
            )}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  )
}
