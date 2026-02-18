import { useSyncExternalStore } from "react"

export type FontSizeLevel = "standard" | "large" | "xlarge" | "xxlarge"

export const FONT_SIZE_OPTIONS: readonly {
  readonly level: FontSizeLevel
  readonly label: string
  readonly scale: number
}[] = [
  { level: "standard", label: "標準", scale: 1 },
  { level: "large", label: "大", scale: 1.25 },
  { level: "xlarge", label: "特大", scale: 1.5 },
  { level: "xxlarge", label: "極大", scale: 1.75 },
] as const

const STORAGE_KEY = "font-size-level"

function getScaleForLevel(level: FontSizeLevel): number {
  return FONT_SIZE_OPTIONS.find((o) => o.level === level)?.scale ?? 1
}

function readLevel(): FontSizeLevel {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored && FONT_SIZE_OPTIONS.some((o) => o.level === stored)) {
      return stored as FontSizeLevel
    }
  } catch {
    // localStorage unavailable
  }
  return "standard"
}

function applyScale(level: FontSizeLevel) {
  const scale = getScaleForLevel(level)
  document.documentElement.style.setProperty("--font-scale", String(scale))
}

// Initialize on module load so the scale is applied before first render
applyScale(readLevel())

// Simple external store for cross-component sync
const listeners = new Set<() => void>()
let currentLevel = readLevel()

function subscribe(listener: () => void) {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

function getSnapshot(): FontSizeLevel {
  return currentLevel
}

function setFontSize(level: FontSizeLevel) {
  currentLevel = level
  applyScale(level)
  try {
    localStorage.setItem(STORAGE_KEY, level)
  } catch {
    // localStorage unavailable
  }
  listeners.forEach((l) => l())
}

export function useFontSize() {
  const level = useSyncExternalStore(subscribe, getSnapshot, () => "standard" as FontSizeLevel)
  return { level, setFontSize } as const
}
