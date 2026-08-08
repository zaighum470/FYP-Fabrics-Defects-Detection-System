import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, Link } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Navbar from './components/Navbar';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';
import Register from './pages/Register';
import ImageUpload from './pages/ImageUpload';
import LiveStream from './pages/LiveStream';

const Home = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center px-4 py-8">
      <div className="text-center max-w-2xl">
        <img src="/logo.svg" alt="AFD Logo" className="h-32 sm:h-40 mx-auto mb-6" />
        <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-gray-800 mb-4">AI Based Fabric Defects Detection System</h1>
        <p className="text-gray-600 mb-8 max-w-md mx-auto text-sm sm:text-base">
          Real-time fabric defect detection using YOLO deep learning models with ESP32-CAM integration
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link to="/login" className="btn-primary px-8 py-3 text-center">
            Get Started
          </Link>
          <Link to="/register" className="btn-secondary px-8 py-3 text-center">
            Register
          </Link>
        </div>
      </div>
    </div>
  );
};

const AppRoutes = () => {
  const { user } = useAuth();

  return (
    <Routes>
      <Route path="/" element={user ? <Navigate to="/upload" /> : <Home />} />
      <Route path="/login" element={user ? <Navigate to="/upload" /> : <Login />} />
      <Route path="/register" element={user ? <Navigate to="/upload" /> : <Register />} />
      <Route
        path="/upload"
        element={
          <ProtectedRoute>
            <ImageUpload />
          </ProtectedRoute>
        }
      />
      <Route
        path="/live"
        element={
          <ProtectedRoute>
            <LiveStream />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  );
};

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <div className="min-h-screen bg-gray-50">
          <Navbar />
          <AppRoutes />
        </div>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
