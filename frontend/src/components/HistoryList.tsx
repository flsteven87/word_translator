import { useState } from "react"
import { useLocation, useNavigate, useParams, Link } from "react-router-dom"
import { FileText, Trash2 } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { useTranslations } from "@/hooks/queries/use-translations"
import { useDeleteTranslation } from "@/hooks/queries/use-delete-translation"
import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuAction,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"

export function HistoryList() {
  const { data: translations, isLoading } = useTranslations()
  const deleteMutation = useDeleteTranslation()
  const location = useLocation()
  const navigate = useNavigate()
  const { id: activeId } = useParams<{ id: string }>()
  const [deleteTarget, setDeleteTarget] = useState<{ id: string; filename: string } | null>(null)

  function handleConfirmDelete() {
    if (!deleteTarget) return
    const { id } = deleteTarget
    deleteMutation.mutate(id, {
      onSuccess: () => {
        if (activeId === id) navigate("/")
      },
      onSettled: () => setDeleteTarget(null),
    })
  }

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
    <>
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
                <SidebarMenuAction
                  onClick={() => setDeleteTarget({ id: t.id, filename: t.filename })}
                  showOnHover
                >
                  <Trash2 />
                </SidebarMenuAction>
              </SidebarMenuItem>
            ))}
          </SidebarMenu>
        </SidebarGroupContent>
      </SidebarGroup>

      <AlertDialog open={!!deleteTarget} onOpenChange={(open) => { if (!open) setDeleteTarget(null) }}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete translation?</AlertDialogTitle>
            <AlertDialogDescription>
              &ldquo;{deleteTarget?.filename}&rdquo; will be permanently deleted. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              onClick={handleConfirmDelete}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? "Deleting..." : "Delete"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
