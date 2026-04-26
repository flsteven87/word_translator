import type { ReactNode, CSSProperties } from "react"
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar"
import { Separator } from "@/components/ui/separator"
import { AppSidebar } from "./AppSidebar"
import { SidebarResizer } from "./SidebarResizer"
import { useSidebarWidth } from "@/hooks/use-sidebar-width"

interface Props {
  readonly children: ReactNode
}

export function DashboardLayout({ children }: Props) {
  const width = useSidebarWidth()
  const style = { "--sidebar-width": `${width}px` } as CSSProperties

  return (
    <SidebarProvider style={style}>
      <AppSidebar />
      <SidebarResizer />
      <SidebarInset>
        <header className="sticky top-0 z-10 flex h-12 shrink-0 items-center gap-2 border-b bg-background">
          <div className="flex items-center gap-2 px-4">
            <SidebarTrigger className="-ml-1" />
            <Separator orientation="vertical" className="mr-2 data-[orientation=vertical]:h-4" />
          </div>
        </header>
        <main className="mx-auto w-full max-w-6xl p-6">
          {children}
        </main>
      </SidebarInset>
    </SidebarProvider>
  )
}
