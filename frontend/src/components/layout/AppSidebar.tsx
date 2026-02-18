import { Link } from "react-router-dom"
import { Plus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { FontSizeControl } from "@/components/FontSizeControl"
import { HistoryList } from "@/components/HistoryList"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
} from "@/components/ui/sidebar"

export function AppSidebar() {
  return (
    <Sidebar>
      <SidebarHeader className="px-4 py-4 space-y-4">
        <Link to="/" className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary text-primary-foreground text-sm font-bold">
            P
          </div>
          <span className="text-sm font-semibold">PaperBridge</span>
        </Link>
        <Button asChild className="w-full" size="sm">
          <Link to="/">
            <Plus />
            New Upload
          </Link>
        </Button>
      </SidebarHeader>
      <SidebarContent>
        <HistoryList />
      </SidebarContent>
      <SidebarFooter className="px-4 py-3">
        <FontSizeControl compact />
      </SidebarFooter>
    </Sidebar>
  )
}
