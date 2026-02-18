import { useMutation, useQueryClient } from "@tanstack/react-query"
import { retranslateDocument } from "@/lib/api"
import { translationKeys } from "./translation-keys"

export function useRetranslate() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: retranslateDocument,
    onSettled: (_data, _error, id) => {
      queryClient.invalidateQueries({ queryKey: translationKeys.detail(id) })
      queryClient.invalidateQueries({ queryKey: translationKeys.lists() })
    },
  })
}
