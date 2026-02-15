import { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
    LayoutDashboard, FileText, Mic, MessageSquare,
    Settings, ChevronLeft, ChevronRight, Sparkles,
} from 'lucide-react';
import './Sidebar.css';

const NAV_ITEMS = [
    { to: '/app', icon: LayoutDashboard, label: 'Dashboard', end: true },
    { to: '/app/resume', icon: FileText, label: 'Resume Analyzer' },
    { to: '/app/interview', icon: MessageSquare, label: 'Mock Interview' },
    { to: '/app/voice', icon: Mic, label: 'Voice Studio' },
    { to: '/app/settings', icon: Settings, label: 'Settings' },
];

export default function Sidebar() {
    const [collapsed, setCollapsed] = useState(false);
    const location = useLocation();

    return (
        <motion.aside
            className={`sidebar glass ${collapsed ? 'sidebar--collapsed' : ''}`}
            animate={{ width: collapsed ? 72 : 260 }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        >
            {/* Logo */}
            <div className="sidebar__logo">
                <div className="sidebar__logo-icon">
                    <Sparkles size={22} />
                </div>
                <AnimatePresence>
                    {!collapsed && (
                        <motion.span
                            className="sidebar__logo-text gradient-text"
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -10 }}
                            transition={{ duration: 0.2 }}
                        >
                            CampusHire.AI
                        </motion.span>
                    )}
                </AnimatePresence>
            </div>

            {/* Navigation */}
            <nav className="sidebar__nav">
                {NAV_ITEMS.map(({ to, icon: Icon, label, end }) => (
                    <NavLink
                        key={to}
                        to={to}
                        end={end}
                        className={({ isActive }) =>
                            `sidebar__link ${isActive ? 'sidebar__link--active' : ''}`
                        }
                    >
                        <div className="sidebar__link-icon">
                            <Icon size={20} />
                        </div>
                        <AnimatePresence>
                            {!collapsed && (
                                <motion.span
                                    className="sidebar__link-label"
                                    initial={{ opacity: 0, width: 0 }}
                                    animate={{ opacity: 1, width: 'auto' }}
                                    exit={{ opacity: 0, width: 0 }}
                                    transition={{ duration: 0.2 }}
                                >
                                    {label}
                                </motion.span>
                            )}
                        </AnimatePresence>
                    </NavLink>
                ))}
            </nav>

            {/* Collapse toggle */}
            <button
                className="sidebar__toggle"
                onClick={() => setCollapsed(!collapsed)}
                aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            >
                {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
            </button>
        </motion.aside>
    );
}
