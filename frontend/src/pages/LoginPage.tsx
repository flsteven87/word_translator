import { useState } from "react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"

const ACCESS_CODE = import.meta.env.VITE_ACCESS_CODE ?? ""

interface Props {
  readonly onAuthenticated: () => void
}

export default function LoginPage({ onAuthenticated }: Props) {
  const [code, setCode] = useState("")
  const [error, setError] = useState(false)

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (code === ACCESS_CODE) {
      sessionStorage.setItem("authenticated", "true")
      onAuthenticated()
    } else {
      setError(true)
    }
  }

  return (
    <div className="flex min-h-svh items-center justify-center bg-background px-4">
      <div className="w-full max-w-xs space-y-8">
        <div className="flex flex-col items-center gap-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground text-lg font-bold">
            D
          </div>
          <h1 className="text-lg font-semibold tracking-tight">
            DocDual
          </h1>
          <p className="text-sm text-muted-foreground">
            Enter access code to continue
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <Input
            type="password"
            placeholder="Access code"
            value={code}
            onChange={(e) => {
              setCode(e.target.value)
              setError(false)
            }}
            aria-invalid={error}
            autoFocus
          />
          {error && (
            <p className="text-xs text-destructive">
              Invalid access code
            </p>
          )}
          <Button type="submit" className="w-full" disabled={!code}>
            Enter
          </Button>
        </form>
      </div>
    </div>
  )
}
