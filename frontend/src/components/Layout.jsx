
import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Bell, Map, Radio, ShieldAlert, LogOut,
  Settings, MapPinned, Menu, X
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

export default function Layout({ children, admin = false }) {
  const { user, logout } = useAuth();
  const loc = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);

  const links = admin
    ? [
        ["/admin", "Overview", Radio],
        ["/admin/sensors", "Sensors", MapPinned],
        ["/admin/safe-locations", "Safe locations", Map],
        ["/admin/warnings", "Direct warning", ShieldAlert]
      ]
    : [
        ["/member", "My safety map", Map],
        ["/member", "Alerts", Bell]
      ];

  return (
    <div className="app-shell">

      {menuOpen && (
        <button
          className="sidebar-backdrop"
          aria-label="Close navigation"
          onClick={() => setMenuOpen(false)}
        />
      )}

      <aside className={menuOpen ? "sidebar sidebar-open" : "sidebar"}>

        <div className="brand">
          <span className="brand-mark">⌁</span>
          <div>
            <b>FloodGuard</b>
            <small>LIVE RESPONSE GRID</small>
          </div>

          <button
            className="sidebar-close"
            onClick={() => setMenuOpen(false)}
            aria-label="Close menu"
          >
            <X size={21} />
          </button>
        </div>

        <nav>
          {links.map(([to, label, I], i) => (
            <Link
              key={i}
              className={loc.pathname === to ? 'active' : ''}
              to={to}
              onClick={() => setMenuOpen(false)}
            >
              <I size={18} />
              {label}
            </Link>
          ))}
        </nav>

        <div className="side-bottom">
          <div className="role-chip">
            {admin ? 'ADMIN CONTROL' : 'COMMUNITY MEMBER'}
          </div>

          <button onClick={logout}>
            <LogOut size={17} />
            Sign out
          </button>
        </div>
      </aside>

      <main>
        <header>

          <button
            className="mobile-menu-toggle"
            onClick={() => setMenuOpen(true)}
            aria-label="Open navigation"
          >
            <Menu size={23} />
          </button>

          <div>
            <span className="eyebrow">REAL-TIME HYDROLOGY</span>
            <h1>
              {admin ? 'Command Center' : 'Community Safety Center'}
            </h1>
          </div>

          <div className="identity">
            <span className="live-dot" />
            {user?.name}
            <small>{user?.mobile}</small>
          </div>

        </header>

        {children}
      </main>
    </div>
  );
}
