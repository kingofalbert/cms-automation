/**
 * Main navigation component
 */

import { Link, useLocation } from 'react-router-dom';
import { routes } from '../../config/routes';
import MobileMenu from './MobileMenu';

export default function Navigation() {
  const location = useLocation();

  // Filter routes that should show in navigation
  const navRoutes = routes.filter(route => route.showInNav);

  return (
    <nav className="bg-white shadow-sm border-b border-gray-200">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo/Brand */}
          <Link
            to="/"
            className="text-xl font-bold text-gray-900 hover:text-blue-600"
          >
            CMS Automation
          </Link>

          {/* Desktop Navigation Links - Hidden on mobile */}
          <div className="hidden md:flex flex-nowrap space-x-1 overflow-x-auto">
            {navRoutes.map((route) => {
              const isActive = location.pathname === route.path;
              return (
                <Link
                  key={route.path}
                  to={route.path}
                  className={`
                    px-4 py-2 rounded-md text-sm font-medium transition-colors whitespace-nowrap
                    ${
                      isActive
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
                    }
                  `}
                >
                  {route.navLabel}
                </Link>
              );
            })}
          </div>

          {/* Mobile Menu - Only visible on mobile */}
          <MobileMenu />
        </div>
      </div>
    </nav>
  );
}
