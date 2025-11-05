import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import './App.css';

// Import store
import { useAppStore } from './store';

// Import contexts
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { I18nProvider } from './contexts/I18nContext';

// Import components
import Sidebar from './components/Layout/Sidebar';
import Header from './components/Layout/Header';
import ThemeProvider from './components/Theme/ThemeProvider';

// Import pages
import Predictions from './pages/Predictions';
import NewsInjuries from './pages/NewsInjuries';
import History from './pages/History';
import Settings from './pages/Settings';
import GreenRedDashboard from './pages/GreenRedDashboard';
import LiveMatches from './pages/LiveMatches';
import Login from './pages/Login';
import Register from './pages/Register';
import UserDashboard from './pages/UserDashboard';
import UserBankroll from './pages/UserBankroll';
import UserTickets from './pages/UserTickets';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 0, // SEMPRE BUSCAR DADOS FRESCOS - SEM CACHE
      gcTime: 0, // NÃO MANTER CACHE EM MEMÓRIA (garbage collection time)
      refetchOnWindowFocus: true, // Atualizar ao focar na janela
      refetchOnMount: true, // Atualizar ao montar componente
    },
  },
});

// Protected Route component
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen bg-bg-primary flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto"></div>
          <p className="mt-4 text-text-secondary">Carregando...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}

// Layout component
function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();
  const { setCurrentPage } = useAppStore();

  // Update current page in store when route changes
  useEffect(() => {
    setCurrentPage(location.pathname);
  }, [location.pathname, setCurrentPage]);

  return (
    <div className="min-h-screen bg-bg-primary">
      {/* Header */}
      <Header onMenuToggle={() => setSidebarOpen(true)} />

      {/* Sidebar */}
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Main content */}
      <div className="lg:pl-64 pt-16">
        <main className="p-4 lg:p-6">
          <Routes>
            {/* Default redirect to user dashboard */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />

            {/* User pages */}
            <Route path="/dashboard" element={<UserDashboard />} />
            <Route path="/bankroll" element={<UserBankroll />} />
            <Route path="/tickets" element={<UserTickets />} />
            <Route path="/green-red" element={<GreenRedDashboard />} />

            {/* App pages */}
            <Route path="/live-matches" element={<LiveMatches />} />
            <Route path="/predictions" element={<Predictions />} />
            <Route path="/news-injuries" element={<NewsInjuries />} />
            <Route path="/history" element={<History />} />
            <Route path="/settings" element={<Settings />} />

            {/* Catch all route */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

function App() {
  // 🔥 LIMPAR TODO O CACHE AO INICIAR O APP
  useEffect(() => {
    queryClient.clear();
    console.log('🔄 Cache do React Query limpo - dados sempre frescos');
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <I18nProvider>
          <Router>
            <AuthProvider>
              <Routes>
                {/* Public routes */}
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />

                {/* Protected app routes */}
                <Route path="/*" element={
                  <ProtectedRoute>
                    <AppLayout />
                  </ProtectedRoute>
                } />
              </Routes>
            </AuthProvider>
          </Router>
        </I18nProvider>
      </ThemeProvider>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

export default App;