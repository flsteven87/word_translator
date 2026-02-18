export const translationKeys = {
  all: ["translations"] as const,
  lists: () => [...translationKeys.all, "list"] as const,
  detail: (id: string) => [...translationKeys.all, "detail", id] as const,
}
