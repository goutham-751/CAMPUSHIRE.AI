import { useState } from 'react';
import { motion } from 'framer-motion';
import { Sun, Moon, Bell, BellOff, Globe, Palette, Monitor, Shield, Save } from 'lucide-react';
import Card from '../../components/Card/Card';
import Button from '../../components/Button/Button';
import { useTheme } from '../../store/ThemeContext';
import './Settings.css';

function Toggle({ checked, onChange, label, desc }) {
    return (
        <div className="settings-toggle" onClick={onChange} role="switch" aria-checked={checked} tabIndex={0}>
            <div className="settings-toggle__info">
                <span className="settings-toggle__label">{label}</span>
                {desc && <span className="settings-toggle__desc">{desc}</span>}
            </div>
            <div className={`settings-toggle__switch ${checked ? 'on' : ''}`}>
                <motion.div
                    className="settings-toggle__knob"
                    animate={{ x: checked ? 20 : 0 }}
                    transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                />
            </div>
        </div>
    );
}

export default function Settings() {
    const { theme, toggleTheme } = useTheme();
    const [notifs, setNotifs] = useState({ email: true, push: false, weekly: true });
    const [lang, setLang] = useState('en');
    const [saved, setSaved] = useState(false);

    const handleSave = () => {
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
    };

    return (
        <motion.div
            className="settings"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
        >
            <div className="settings__header">
                <h2>Settings</h2>
                <Button variant="primary" size="sm" icon={Save} onClick={handleSave}>
                    {saved ? 'Saved ✓' : 'Save Changes'}
                </Button>
            </div>

            <div className="settings__grid">
                {/* Appearance */}
                <Card variant="glass" className="settings__section">
                    <div className="settings__section-header">
                        <Palette size={20} />
                        <h3>Appearance</h3>
                    </div>
                    <div className="settings__theme-options">
                        <button
                            className={`settings__theme-btn ${theme === 'light' ? 'active' : ''}`}
                            onClick={() => theme !== 'light' && toggleTheme()}
                        >
                            <Sun size={20} />
                            <span>Light</span>
                        </button>
                        <button
                            className={`settings__theme-btn ${theme === 'dark' ? 'active' : ''}`}
                            onClick={() => theme !== 'dark' && toggleTheme()}
                        >
                            <Moon size={20} />
                            <span>Dark</span>
                        </button>
                        <button className="settings__theme-btn" disabled>
                            <Monitor size={20} />
                            <span>System</span>
                        </button>
                    </div>
                </Card>

                {/* Notifications */}
                <Card variant="glass" className="settings__section">
                    <div className="settings__section-header">
                        <Bell size={20} />
                        <h3>Notifications</h3>
                    </div>
                    <Toggle
                        label="Email Notifications"
                        desc="Receive resume analysis results via email"
                        checked={notifs.email}
                        onChange={() => setNotifs(p => ({ ...p, email: !p.email }))}
                    />
                    <Toggle
                        label="Push Notifications"
                        desc="Browser push notifications for new features"
                        checked={notifs.push}
                        onChange={() => setNotifs(p => ({ ...p, push: !p.push }))}
                    />
                    <Toggle
                        label="Weekly Reports"
                        desc="Weekly summary of your preparation progress"
                        checked={notifs.weekly}
                        onChange={() => setNotifs(p => ({ ...p, weekly: !p.weekly }))}
                    />
                </Card>

                {/* Language */}
                <Card variant="glass" className="settings__section">
                    <div className="settings__section-header">
                        <Globe size={20} />
                        <h3>Language &amp; Region</h3>
                    </div>
                    <div className="settings__select-group">
                        <label htmlFor="lang-select">Interface Language</label>
                        <select id="lang-select" value={lang} onChange={(e) => setLang(e.target.value)} className="settings__select">
                            <option value="en">English</option>
                            <option value="hi">Hindi</option>
                            <option value="es">Spanish</option>
                            <option value="fr">French</option>
                        </select>
                    </div>
                </Card>

                {/* Privacy */}
                <Card variant="glass" className="settings__section">
                    <div className="settings__section-header">
                        <Shield size={20} />
                        <h3>Privacy &amp; Data</h3>
                    </div>
                    <Toggle
                        label="Analytics"
                        desc="Help improve CampusHire.AI with anonymous usage data"
                        checked={true}
                        onChange={() => { }}
                    />
                    <Toggle
                        label="Save Resume Data"
                        desc="Keep parsed resume data for faster reanalysis"
                        checked={true}
                        onChange={() => { }}
                    />
                    <Button variant="danger" size="sm" style={{ marginTop: 'var(--space-4)' }}>
                        Delete All Data
                    </Button>
                </Card>
            </div>
        </motion.div>
    );
}
