import { useState } from "react"
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import { DashboardLayout } from "@/components/layout/DashboardLayout"
import Workspace from "@/pages/Workspace"
import LoginPage from "@/pages/LoginPage"

export default function App() {
  const [authenticated, setAuthenticated] = useState(
    () => sessionStorage.getItem("authenticated") === "true",
  )

  if (!authenticated) {
    return <LoginPage onAuthenticated={() => setAuthenticated(true)} />
  }

  return (
    <BrowserRouter>
      <DashboardLayout>
        <Routes>
          <Route path="/" element={<Workspace />} />
          <Route path="/t/:id" element={<Workspace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </DashboardLayout>
    </BrowserRouter>
  )
}
