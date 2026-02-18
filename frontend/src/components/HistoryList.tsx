import { useLocation, Link } from "react-router-dom"
import { FileText } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"
import { useTranslations } from "@/hooks/queries/use-translations"
import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"

export function HistoryList() {
  const { data: translations, isLoading } = useTranslations()
  const location = useLocation()

  if (isLoading) {
    return (
      <SidebarGroup>
        <SidebarGroupLabel>History</SidebarGroupLabel>
        <SidebarGroupContent>
          <div className="space-y-2 px-2">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="flex items-center gap-2 py-1">
                <Skeleton className="size-4 rounded" />
                <Skeleton className="h-4 flex-1" />
              </div>
            ))}
          </div>
        </SidebarGroupContent>
      </SidebarGroup>
    )
  }

  if (!translations?.length) {
    return (
      <SidebarGroup>
        <SidebarGroupLabel>History</SidebarGroupLabel>
        <SidebarGroupContent>
          <p className="px-4 py-3 text-xs text-muted-foreground">
            No translations yet.
          </p>
        </SidebarGroupContent>
      </SidebarGroup>
    )
  }

  return (
    <SidebarGroup>
      <SidebarGroupLabel>History</SidebarGroupLabel>
      <SidebarGroupContent>
        <SidebarMenu>
          {translations.map((t) => (
            <SidebarMenuItem key={t.id}>
              <SidebarMenuButton
                asChild
                isActive={location.pathname === `/t/${t.id}`}
              >
                <Link to={`/t/${t.id}`}>
                  <FileText />
                  <div className="flex-1 min-w-0">
                    <span className="truncate text-sm">{t.filename}</span>
                    <span className="block truncate text-xs text-muted-foreground">
                      {t.paragraph_count} paragraphs
                    </span>
                  </div>
                </Link>
              </SidebarMenuButton>
            </SidebarMenuItem>
          ))}
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  )
}
