import { useTheme } from '../../store/ThemeContext';
import { Sun, Moon, Bell, Search } from 'lucide-react';
import './TopNavbar.css';

export default function TopNavbar({ title }) {
    const { theme, toggleTheme } = useTheme();

    return (
        <header className="topnav glass">
            <div className="topnav__left">
                <h1 className="topnav__title">{title}</h1>
            </div>

            <div className="topnav__right">
                {/* Search */}
                <div className="topnav__search">
                    <Search size={16} className="topnav__search-icon" />
                    <input
                        type="text"
                        placeholder="Search…"
                        className="topnav__search-input"
                    />
                </div>

                {/* Notifications */}
                <button className="topnav__icon-btn" aria-label="Notifications">
                    <Bell size={18} />
                    <span className="topnav__badge">3</span>
                </button>

                {/* Theme toggle */}
                <button
                    className="topnav__icon-btn"
                    onClick={toggleTheme}
                    aria-label="Toggle theme"
                >
                    {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
                </button>

                {/* Avatar */}
                <div className="topnav__avatar">G</div>
            </div>
        </header>
    );
}
