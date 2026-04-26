import { useEffect, useRef } from "react"
import { useSidebar } from "@/components/ui/sidebar"
import {
  clampSidebarWidth,
  setSidebarWidth,
} from "@/hooks/use-sidebar-width"

const RESIZING_ATTR = "data-sidebar-resizing"

export function SidebarResizer() {
  const { isMobile, state } = useSidebar()
  const wrapperRef = useRef<HTMLElement | null>(null)
  const draggingRef = useRef(false)

  // Recover from mid-drag unmount (e.g. user hits Cmd+B keyboard shortcut while dragging).
  useEffect(() => {
    return () => {
      if (draggingRef.current) {
        document.body.removeAttribute(RESIZING_ATTR)
        document.body.style.cursor = ""
      }
    }
  }, [])

  if (isMobile || state === "collapsed") return null

  function handlePointerDown(e: React.PointerEvent<HTMLDivElement>) {
    e.preventDefault()
    const wrapper = e.currentTarget.closest<HTMLElement>(
      '[data-slot="sidebar-wrapper"]',
    )
    if (!wrapper) return
    wrapperRef.current = wrapper
    draggingRef.current = true
    e.currentTarget.setPointerCapture(e.pointerId)
    document.body.setAttribute(RESIZING_ATTR, "")
    document.body.style.cursor = "ew-resize"
  }

  function handlePointerMove(e: React.PointerEvent<HTMLDivElement>) {
    const wrapper = wrapperRef.current
    if (!wrapper || !e.currentTarget.hasPointerCapture(e.pointerId)) return
    const next = clampSidebarWidth(e.clientX)
    wrapper.style.setProperty("--sidebar-width", `${next}px`)
  }

  function handlePointerUp(e: React.PointerEvent<HTMLDivElement>) {
    if (!e.currentTarget.hasPointerCapture(e.pointerId)) return
    e.currentTarget.releasePointerCapture(e.pointerId)
    setSidebarWidth(clampSidebarWidth(e.clientX))
    wrapperRef.current = null
    draggingRef.current = false
    document.body.removeAttribute(RESIZING_ATTR)
    document.body.style.cursor = ""
  }

  return (
    <div
      role="separator"
      aria-orientation="vertical"
      aria-label="Resize sidebar"
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerCancel={handlePointerUp}
      className="fixed inset-y-0 z-30 hidden w-2 -translate-x-1/2 cursor-ew-resize touch-none after:absolute after:inset-y-0 after:left-1/2 after:w-px after:-translate-x-1/2 after:bg-sidebar-border/0 after:transition-colors hover:after:bg-sidebar-border md:block"
      style={{ left: "var(--sidebar-width)" }}
    />
  )
}
