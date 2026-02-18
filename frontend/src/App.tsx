import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import { DashboardLayout } from "@/components/layout/DashboardLayout"
import Workspace from "@/pages/Workspace"

export default function App() {
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
