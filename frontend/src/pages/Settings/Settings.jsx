import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Sun, Moon, Bell, Globe, Palette, Monitor, Shield, Save, Database, History, Link as LinkIcon } from 'lucide-react';
import Card from '../../components/Card/Card';
import Button from '../../components/Button/Button';
import DualZone, { ZoneA, ZoneB } from '../../components/Layout/DualZone';
import TelemetryCard from '../../components/Cards/TelemetryCard';
import { useTheme } from '../../store/ThemeContext';
import { healthApi, getHistory } from '../../lib/api';
import { useAuth } from '../../store/AuthContext';
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

function statusColor(status) {
    if (status === 'connected') return 'var(--color-neon)';
    if (status === 'not_configured') return 'var(--color-gold)';
    return 'var(--color-text-tertiary)';
}

export default function Settings() {
    const { theme, toggleTheme } = useTheme();
    const { user } = useAuth();
    const [notifs, setNotifs] = useState({ email: true, push: false, weekly: true });
    const [lang, setLang] = useState('en');
    const [saved, setSaved] = useState(false);
    const [privacy, setPrivacy] = useState({ analytics: true, retention: true });
    const [systemStatus, setSystemStatus] = useState(null);
    const [statusError, setStatusError] = useState(null);
    const history = getHistory().slice(0, 5);

    useEffect(() => {
        let mounted = true;
        healthApi.getSystemStatus()
            .then((data) => {
                if (!mounted) return;
                setSystemStatus(data);
            })
            .catch((err) => {
                if (!mounted) return;
                setStatusError(err.message || 'Failed to load system status');
            });
        return () => { mounted = false; };
    }, []);

    const handleSave = () => {
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
    };

    const tel = systemStatus?.telemetry || {};
    const integrations = systemStatus?.integrations || [];

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
                <TelemetryCard title="Live Telemetry" icon={Database} status="nominal">
                    <div className="tGrid">
                        <div className="tItem">
                            <span>API Latency</span>
                            <strong className="textNeon">{tel.api_latency_ms ?? '—'} ms</strong>
                        </div>
                        <div className="tItem">
                            <span>Requests</span>
                            <strong>{tel.request_count ?? 0}</strong>
                        </div>
                        <div className="tItem">
                            <span>LLM Tokens</span>
                            <strong>{tel.total_tokens ?? 0}</strong>
                        </div>
                        <div className="tItem">
                            <span>Uptime</span>
                            <strong>{tel.uptime || '—'}</strong>
                        </div>
                    </div>
                    {statusError && (
                        <div style={{ marginTop: '0.75rem', color: 'var(--color-text-tertiary)', fontSize: '0.85rem' }}>
                            {statusError}
                        </div>
                    )}
                </TelemetryCard>

                <TelemetryCard title="Activity" icon={History} status="nominal">
                    <div className="historyList">
                        {user?.email && (
                            <div className="historyItem">
                                <div className="hStatus" style={{ backgroundColor: 'var(--color-neon)' }}></div>
                                <div className="hContent">
                                    <span className="hAction">Signed in</span>
                                    <span className="hTime">{user.email}</span>
                                </div>
                            </div>
                        )}
                        {history.map((h, i) => (
                            <div key={i} className="historyItem">
                                <div className="hStatus" style={{ backgroundColor: 'var(--color-text-tertiary)' }}></div>
                                <div className="hContent">
                                    <span className="hAction">{h.text || h.type}</span>
                                    <span className="hTime">{h.timestamp ? new Date(h.timestamp).toLocaleString() : ''}</span>
                                </div>
                            </div>
                        ))}
                        {!user && history.length === 0 && (
                            <div className="historyItem">
                                <div className="hStatus" style={{ backgroundColor: 'var(--color-text-tertiary)' }}></div>
                                <div className="hContent">
                                    <span className="hAction">No activity yet</span>
                                    <span className="hTime">Run Resume Analyzer or Interview to populate</span>
                                </div>
                            </div>
                        )}
                    </div>
                </TelemetryCard>

                <TelemetryCard title="Integrations" icon={LinkIcon} status="active">
                    <div className="historyList">
                        {integrations.length === 0 && !statusError && (
                            <div className="historyItem">
                                <div className="hStatus" style={{ backgroundColor: 'var(--color-text-tertiary)' }}></div>
                                <div className="hContent">
                                    <span className="hAction">Loading status…</span>
                                    <span className="hTime">Fetching /api/system/status</span>
                                </div>
                            </div>
                        )}
                        {integrations.map((item) => (
                            <div key={item.id} className="historyItem">
                                <div className="hStatus" style={{ backgroundColor: statusColor(item.status) }}></div>
                                <div className="hContent">
                                    <span className="hAction">{item.name}</span>
                                    <span className="hTime">{item.status} — {item.detail}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </TelemetryCard>
            </ZoneB>
        </DualZone>
    );
}
