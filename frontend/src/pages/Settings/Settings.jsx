import { useState } from 'react';
import { motion } from 'framer-motion';
import { Sun, Moon, Bell, Globe, Palette, Monitor, Shield, Save, Database, History, Link as LinkIcon } from 'lucide-react';
import Card from '../../components/Card/Card';
import Button from '../../components/Button/Button';
import DualZone, { ZoneA, ZoneB } from '../../components/Layout/DualZone';
import TelemetryCard from '../../components/Cards/TelemetryCard';
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
    const [privacy, setPrivacy] = useState({ analytics: true, retention: true });

    const handleSave = () => {
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
    };

    return (
        <DualZone>
            <ZoneA>
                <div className="settings__header">
                    <h2>System Configuration</h2>
                    <Button variant="primary" size="sm" icon={Save} onClick={handleSave}>
                        {saved ? 'Protocol Saved ✓' : 'Save Changes'}
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
                            <h3>Alerts & Telemetry</h3>
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
                                <option value="en">English (US)</option>
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
                            label="Analytics Collection"
                            desc="Help improve CampusHire.AI with anonymous usage data"
                            checked={privacy.analytics}
                            onChange={() => setPrivacy(p => ({ ...p, analytics: !p.analytics }))}
                        />
                        <Toggle
                            label="Session Retention"
                            desc="Keep parsed resume data for faster reanalysis"
                            checked={privacy.retention}
                            onChange={() => setPrivacy(p => ({ ...p, retention: !p.retention }))}
                        />
                        <Button variant="danger" size="sm" style={{ marginTop: 'var(--space-4)' }}>
                            Purge All Data
                        </Button>
                    </Card>
                </div>
            </ZoneA>

            <ZoneB>
                <TelemetryCard title="Storage Allocation" icon={Database} status="nominal">
                    <div className="tGrid">
                        <div className="tItem">
                            <span>Resumes</span>
                            <strong className="textNeon">2.4 MB</strong>
                        </div>
                        <div className="tItem">
                            <span>Audio Cache</span>
                            <strong>14.2 MB</strong>
                        </div>
                        <div className="tItem">
                            <span>Evaluations</span>
                            <strong>0.8 MB</strong>
                        </div>
                        <div className="tItem">
                            <span>Quota Usage</span>
                            <strong>17.4 / 100 MB</strong>
                        </div>
                    </div>
                </TelemetryCard>

                <TelemetryCard title="Access Logs" icon={History} status="nominal">
                    <div className="historyList">
                        <div className="historyItem">
                            <div className="hStatus" style={{ backgroundColor: 'var(--color-neon)' }}></div>
                            <div className="hContent">
                                <span className="hAction">Login (Current Session)</span>
                                <span className="hTime">Today, 11:01 AM (IP: 192.168.1.1)</span>
                            </div>
                        </div>
                        <div className="historyItem">
                            <div className="hStatus" style={{ backgroundColor: 'var(--color-text-tertiary)' }}></div>
                            <div className="hContent">
                                <span className="hAction">Resume Analyzed</span>
                                <span className="hTime">Yesterday, 14:32 PM</span>
                            </div>
                        </div>
                        <div className="historyItem">
                            <div className="hStatus" style={{ backgroundColor: 'var(--color-text-tertiary)' }}></div>
                            <div className="hContent">
                                <span className="hAction">System Settings Modified</span>
                                <span className="hTime">3 days ago, 09:15 AM</span>
                            </div>
                        </div>
                    </div>
                </TelemetryCard>

                <TelemetryCard title="Integrations" icon={LinkIcon} status="active">
                    <div className="historyList">
                        <div className="historyItem">
                            <div className="hStatus" style={{ backgroundColor: 'var(--color-neon)' }}></div>
                            <div className="hContent">
                                <span className="hAction">OpenAI API</span>
                                <span className="hTime">Connected (GPT-4o)</span>
                            </div>
                        </div>
                        <div className="historyItem">
                            <div className="hStatus" style={{ backgroundColor: 'var(--color-gold)' }}></div>
                            <div className="hContent">
                                <span className="hAction">AssemblyAI API</span>
                                <span className="hTime">Initializing (STT Module)</span>
                            </div>
                        </div>
                        <div className="historyItem">
                            <div className="hStatus" style={{ backgroundColor: 'var(--color-text-tertiary)' }}></div>
                            <div className="hContent">
                                <span className="hAction">Google Drive</span>
                                <span className="hTime">Not Connected</span>
                            </div>
                        </div>
                    </div>
                </TelemetryCard>
            </ZoneB>
        </DualZone>
    );
}
