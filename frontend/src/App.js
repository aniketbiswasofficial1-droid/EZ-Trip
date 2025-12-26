import { useEffect, useState, useRef, createContext, useContext } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, useNavigate, useLocation, Link } from "react-router-dom";
import axios from "axios";
import { Toaster } from "@/components/ui/sonner";
import { toast } from "sonner";
import { GoogleOAuthProvider } from '@react-oauth/google';

// Pages
import LandingPage from "@/pages/LandingPage";
import Dashboard from "@/pages/Dashboard";
import TripDetail from "@/pages/TripDetail";
import TripPlanner from "@/pages/TripPlanner";
import AdminPanel from "@/pages/AdminPanel";
import Profile from "@/pages/Profile";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
export const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
};

// Auth Provider

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const checkAuth = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`, {
        withCredentials: true
      });
      setUser(response.data);
    } catch (error) {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  // Google Login Removed as requested
  const login = () => {
    toast.info("Google login is currently disabled.");
  };

  // NEW: Email/Password Login
  const loginWithPassword = async (email, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`,
        { email, password },
        { withCredentials: true }
      );
      setUser(response.data);
      toast.success("Welcome back!");
      return response.data;
    } catch (error) {
      console.error("Login error:", error);
      throw error; // Re-throw to handle in UI
    }
  };

  // Google OAuth Login with ID token
  const loginWithGoogle = async (idToken) => {
    try {
      const response = await axios.post(`${API}/auth/google`,
        {
          id_token: idToken
        },
        { withCredentials: true }
      );
      setUser(response.data);
      toast.success("Welcome!");
      return response.data;
    } catch (error) {
      console.error("Google login error:", error);
      throw error;
    }
  };

  // NEW: Registration
  const register = async (name, email, username, password) => {
    try {
      const response = await axios.post(`${API}/auth/register`,
        { name, email, username, password },  // NEW: Include username
        { withCredentials: true }
      );
      setUser(response.data);
      toast.success("Account created successfully!");
      return response.data;
    } catch (error) {
      console.error("Registration error:", error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      await axios.post(`${API}/auth/logout`, {}, { withCredentials: true });
      setUser(null);
      toast.success("Logged out successfully");
    } catch (error) {
      console.error("Logout error:", error);
    }
  };

  const refreshUser = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`, {
        withCredentials: true
      });
      setUser(response.data);
      return response.data;
    } catch (error) {
      console.error("Refresh user error:", error);
      setUser(null);
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  return (
    <AuthContext.Provider value={{
      user,
      setUser,
      loading,
      login,
      loginWithPassword,
      loginWithGoogle,
      register,
      logout,
      checkAuth,
      refreshUser
    }}>
      {children}
    </AuthContext.Provider>
  );
};

// Auth Callback Component
const AuthCallback = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { setUser } = useAuth();
  const hasProcessed = useRef(false);

  useEffect(() => {
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const processSession = async () => {
      const hash = location.hash;
      const sessionIdMatch = hash.match(/session_id=([^&]+)/);

      if (sessionIdMatch) {
        const sessionId = sessionIdMatch[1];

        try {
          const response = await axios.post(
            `${API}/auth/session`,
            { session_id: sessionId },
            { withCredentials: true }
          );

          setUser(response.data);
          toast.success("Welcome back!");
          navigate('/dashboard', { replace: true, state: { user: response.data } });
        } catch (error) {
          console.error("Session error:", error);
          toast.error("Authentication failed");
          navigate('/', { replace: true });
        }
      } else {
        navigate('/dashboard', { replace: true });
      }
    };

    processSession();
  }, [location, navigate, setUser]);

  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="text-center">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <p className="text-muted-foreground">Authenticating...</p>
      </div>
    </div>
  );
};

// Protected Route
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (!loading && !user && !location.state?.user) {
      navigate('/', { replace: true });
    }
  }, [user, loading, navigate, location]);

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  if (!user && !location.state?.user) {
    return null;
  }

  return children;
};

// App Router
function AppRouter() {
  const location = useLocation();

  // Check for session_id in hash SYNCHRONOUSLY during render
  if (location.hash?.includes('session_id=')) {
    return <AuthCallback />;
  }

  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/trip/:tripId"
        element={
          <ProtectedRoute>
            <TripDetail />
          </ProtectedRoute>
        }
      />
      <Route
        path="/planner"
        element={
          <ProtectedRoute>
            <TripPlanner />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin"
        element={
          <ProtectedRoute>
            <AdminPanel />
          </ProtectedRoute>
        }
      />
      <Route
        path="/profile"
        element={
          <ProtectedRoute>
            <Profile />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

function App() {
  const googleClientId = process.env.REACT_APP_GOOGLE_CLIENT_ID || '';

  return (
    <GoogleOAuthProvider clientId={googleClientId}>
      <div className="App noise-bg min-h-screen">
        <BrowserRouter>
          <AuthProvider>
            <AppRouter />
            <Toaster
              position="bottom-right"
              toastOptions={{
                style: {
                  background: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  color: 'hsl(var(--foreground))'
                }
              }}
            />
          </AuthProvider>
        </BrowserRouter>
      </div>
    </GoogleOAuthProvider>
  );
}

export default App;
export { API };