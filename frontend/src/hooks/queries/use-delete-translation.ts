import { useMutation, useQueryClient } from "@tanstack/react-query"
import { deleteTranslation } from "@/lib/api"
import { translationKeys } from "./translation-keys"

export function useDeleteTranslation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: deleteTranslation,
    onSuccess: (_data, deletedId) => {
      queryClient.removeQueries({
        queryKey: translationKeys.detail(deletedId),
      })
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: translationKeys.lists() })
    },
  })
}
