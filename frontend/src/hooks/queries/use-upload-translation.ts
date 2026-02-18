import { useMutation, useQueryClient } from "@tanstack/react-query"
import { uploadDocument } from "@/lib/api"
import { translationKeys } from "./translation-keys"

export function useUploadTranslation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: uploadDocument,
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: translationKeys.lists() })
    },
  })
}
