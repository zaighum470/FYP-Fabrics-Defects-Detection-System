import React from 'react';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';

const Navbar = () => {
  const { user, logout } = useAuth();

  return (
    <nav className="bg-white shadow-sm border-b border-gray-100 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="flex items-center gap-2">
              <img src="/logo.svg" alt="AFD Logo" className="h-10 w-auto" />
            </Link>
            {user && (
              <div className="hidden md:flex ml-10 gap-1">
                <Link to="/upload" className="text-gray-600 hover:text-blue-600 hover:bg-blue-50 px-4 py-2 rounded-lg transition-all duration-200 font-medium text-sm">
                  Upload
                </Link>
                <Link to="/live" className="text-gray-600 hover:text-blue-600 hover:bg-blue-50 px-4 py-2 rounded-lg transition-all duration-200 font-medium text-sm">
                  Live Stream
                </Link>
              </div>
            )}
          </div>
          {user && (
            <div className="flex items-center gap-3">
              <span className="text-gray-600 text-sm hidden md:block">{user.username}</span>
              <button
                onClick={logout}
                className="text-gray-600 hover:text-red-600 hover:bg-red-50 px-4 py-2 rounded-lg transition-all duration-200 text-sm font-medium"
              >
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
