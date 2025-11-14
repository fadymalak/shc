import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Monitors from './pages/Monitors'
import Incidents from './pages/Incidents'
import StatusPages from './pages/StatusPages'
import Organizations from './pages/Organizations'
import Certificates from './pages/Certificates'
import Login from './pages/Login'
import { useAuthStore } from './store/authStore'

const queryClient = new QueryClient()

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
            <Route index element={<Dashboard />} />
            <Route path="monitors" element={<Monitors />} />
            <Route path="incidents" element={<Incidents />} />
            <Route path="status-pages" element={<StatusPages />} />
            <Route path="organizations" element={<Organizations />} />
            <Route path="certificates" element={<Certificates />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  
  return <>{children}</>
}

export default App
