import { useQuery } from "@tanstack/react-query"
import { fetchTranslations, fetchTranslation } from "@/lib/api"
import { translationKeys } from "./translation-keys"

export function useTranslations() {
  return useQuery({
    queryKey: translationKeys.lists(),
    queryFn: fetchTranslations,
  })
}

export function useTranslation(id: string) {
  return useQuery({
    queryKey: translationKeys.detail(id),
    queryFn: () => fetchTranslation(id),
    enabled: !!id,
  })
}
