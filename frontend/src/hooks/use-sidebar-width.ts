import { useSyncExternalStore } from "react"

export const SIDEBAR_WIDTH_DEFAULT = 256
export const SIDEBAR_WIDTH_MIN = 224
export const SIDEBAR_WIDTH_MAX = 480

const STORAGE_KEY = "sidebar-width-px"

export function clampSidebarWidth(value: number): number {
  return Math.max(SIDEBAR_WIDTH_MIN, Math.min(SIDEBAR_WIDTH_MAX, value))
}

function readWidth(): number {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw === null) return SIDEBAR_WIDTH_DEFAULT
    const n = Number(raw)
    if (Number.isFinite(n)) return clampSidebarWidth(n)
  } catch {
    // localStorage unavailable
  }
  return SIDEBAR_WIDTH_DEFAULT
}

const listeners = new Set<() => void>()
let currentWidth = readWidth()

function subscribe(listener: () => void) {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

function getSnapshot(): number {
  return currentWidth
}

export function setSidebarWidth(width: number) {
  const next = clampSidebarWidth(width)
  if (next === currentWidth) return
  currentWidth = next
  try {
    localStorage.setItem(STORAGE_KEY, String(next))
  } catch {
    // localStorage unavailable
  }
  listeners.forEach((l) => l())
}

export function useSidebarWidth(): number {
  return useSyncExternalStore(subscribe, getSnapshot, () => SIDEBAR_WIDTH_DEFAULT)
}
