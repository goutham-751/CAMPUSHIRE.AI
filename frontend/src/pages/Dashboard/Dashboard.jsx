import { useMemo } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
    FileText, BarChart3, MessageSquare, Mic, TrendingUp,
    Clock, Star, ArrowRight, Award, Target
} from 'lucide-react';
import Card from '../../components/Card/Card';
import Button from '../../components/Button/Button';
import { getHistory } from '../../lib/api';
import {
    AreaChart, Area, ResponsiveContainer, Tooltip, XAxis, YAxis,
    BarChart, Bar, Cell
} from 'recharts';
import './Dashboard.css';

const ICON_MAP = {
    FileText, BarChart3, MessageSquare, Mic, TrendingUp, Award, Target
};

function getIcon(name) {
    return ICON_MAP[name] || FileText;
}

const CATEGORY_COLORS = {
    skills_match: '#6366f1',
    experience_level: '#8b5cf6',
    education: '#06b6d4',
    keyword_density: '#10b981',
    formatting: '#f59e0b',
    achievements: '#ef4444',
};

const CATEGORY_NAMES = {
    skills_match: 'Skills',
    experience_level: 'Experience',
    education: 'Education',
    keyword_density: 'Keywords',
    formatting: 'Formatting',
    achievements: 'Achievements',
};

/* ── Stat Card ────────────────────────────────────────────── */
function StatCard({ icon: Icon, label, value, sub, color, to }) {
    return (
        <Link to={to} style={{ textDecoration: 'none' }}>
            <Card variant="glass" className="dash-stat">
                <div className="dash-stat__icon" style={{ background: `${color}18`, color }}>
                    <Icon size={22} />
                </div>
                <div className="dash-stat__info">
                    <span className="dash-stat__value">{value}</span>
                    <span className="dash-stat__label">{label}</span>
                    {sub && <span className="dash-stat__sub">{sub}</span>}
                </div>
            </Card>
        </Link>
    );
}

/* ── Main Dashboard ───────────────────────────────────────── */
export default function Dashboard() {
    const history = useMemo(() => getHistory(), []);

    // Compute real stats
    const resumeCount = history.filter(h => h.type === 'resume_parsed' || h.type === 'ats_score' || h.type === 'feedback').length;
    const atsScores = history.filter(h => h.type === 'ats_score' && h.score != null);
    const avgAts = atsScores.length > 0
        ? Math.round(atsScores.reduce((sum, h) => sum + h.score, 0) / atsScores.length)
        : 0;
    const lastAts = atsScores.length > 0 ? Math.round(atsScores[0].score) : null;
    const interviewCount = history.filter(h => h.type === 'interview_questions' || h.type === 'answer_evaluated').length;

    // Score history chart data (most recent 10)
    const scoreChartData = atsScores.slice(0, 10).reverse().map((h, i) => ({
        name: new Date(h.timestamp).toLocaleDateString('en', { month: 'short', day: 'numeric' }),
        score: Math.round(h.score),
    }));

    // Category breakdown from most recent ATS score
    const latestScores = atsScores.length > 0 ? atsScores[0].scores : null;
    const categoryData = latestScores
        ? Object.entries(latestScores).map(([key, val]) => ({
            name: CATEGORY_NAMES[key] || key,
            score: Math.round(val),
            fill: CATEGORY_COLORS[key] || '#6366f1',
        }))
        : null;

    // Recent activity (last 8)
    const recentActivity = history.slice(0, 8);

    const hasData = history.length > 0;

    return (
        <motion.div
            className="dashboard"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
        >
            <div className="dashboard__welcome">
                <h2>Welcome back 👋</h2>
                <p className="dashboard__subtitle">
                    {hasData
                        ? `You've completed ${resumeCount} analysis session${resumeCount !== 1 ? 's' : ''} so far.`
                        : 'Get started by analyzing your resume or practicing for an interview.'}
                </p>
            </div>

            {/* ── Stats ──────────────────────────────────────── */}
            <div className="dashboard__stats">
                <StatCard icon={FileText} label="Resumes Analyzed" value={resumeCount} color="#6366f1" to="/app/resume" />
                <StatCard icon={BarChart3} label="Avg ATS Score" value={avgAts > 0 ? `${avgAts}%` : '—'} sub={lastAts != null ? `Last: ${lastAts}%` : null} color="#10b981" to="/app/resume" />
                <StatCard icon={MessageSquare} label="Interview Sessions" value={interviewCount} color="#8b5cf6" to="/app/interview" />
                <StatCard icon={Mic} label="Voice Practice" value="—" color="#06b6d4" to="/app/voice" />
            </div>

            {/* ── Charts + Activity ──────────────────────────── */}
            <div className="dashboard__grid">
                {/* Score Trend */}
                <Card variant="glass" className="dashboard__chart-card">
                    <h3><TrendingUp size={18} /> Score Trend</h3>
                    {scoreChartData.length > 1 ? (
                        <ResponsiveContainer width="100%" height={220}>
                            <AreaChart data={scoreChartData}>
                                <defs>
                                    <linearGradient id="scoreGrad" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <XAxis dataKey="name" tick={{ fontSize: 11 }} stroke="var(--color-text-tertiary)" />
                                <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} stroke="var(--color-text-tertiary)" />
                                <Tooltip contentStyle={{ background: 'var(--color-bg-secondary)', border: '1px solid var(--color-border)', borderRadius: '8px', fontSize: '0.82rem' }} />
                                <Area type="monotone" dataKey="score" stroke="#6366f1" strokeWidth={2} fill="url(#scoreGrad)" />
                            </AreaChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="dashboard__chart-empty">
                            <TrendingUp size={36} color="var(--color-text-tertiary)" />
                            <p>Run ATS Score analysis to see your score trend here.</p>
                        </div>
                    )}
                </Card>

                {/* Category Breakdown */}
                <Card variant="glass" className="dashboard__chart-card">
                    <h3><BarChart3 size={18} /> Category Breakdown</h3>
                    {categoryData ? (
                        <ResponsiveContainer width="100%" height={220}>
                            <BarChart data={categoryData} layout="vertical" margin={{ left: 10 }}>
                                <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11 }} stroke="var(--color-text-tertiary)" />
                                <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} stroke="var(--color-text-tertiary)" width={80} />
                                <Tooltip contentStyle={{ background: 'var(--color-bg-secondary)', border: '1px solid var(--color-border)', borderRadius: '8px', fontSize: '0.82rem' }} />
                                <Bar dataKey="score" radius={[0, 4, 4, 0]} barSize={14}>
                                    {categoryData.map((entry, i) => (
                                        <Cell key={i} fill={entry.fill} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="dashboard__chart-empty">
                            <BarChart3 size={36} color="var(--color-text-tertiary)" />
                            <p>ATS Score results will show category breakdown here.</p>
                        </div>
                    )}
                </Card>

                {/* Activity Feed */}
                <Card variant="glass" className="dashboard__activity-card">
                    <h3><Clock size={18} /> Recent Activity</h3>
                    {recentActivity.length > 0 ? (
                        <div className="dashboard__activity-list">
                            {recentActivity.map((item, i) => {
                                const Icon = getIcon(item.icon);
                                const timeAgo = getTimeAgo(item.timestamp);
                                return (
                                    <motion.div
                                        key={i}
                                        className="dashboard__activity-item"
                                        initial={{ opacity: 0, x: -10 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        transition={{ delay: i * 0.05 }}
                                    >
                                        <div className="dashboard__activity-icon">
                                            <Icon size={14} />
                                        </div>
                                        <div className="dashboard__activity-info">
                                            <span className="dashboard__activity-text">{item.text}</span>
                                            <span className="dashboard__activity-time">{timeAgo}</span>
                                        </div>
                                    </motion.div>
                                );
                            })}
                        </div>
                    ) : (
                        <div className="dashboard__chart-empty">
                            <Clock size={36} color="var(--color-text-tertiary)" />
                            <p>Your activity will appear here as you use the app.</p>
                        </div>
                    )}
                </Card>

                {/* Quick Actions */}
                <Card variant="glass" className="dashboard__actions-card">
                    <h3><Star size={18} /> Quick Actions</h3>
                    <div className="dashboard__actions-list">
                        <Link to="/app/resume">
                            <Button variant="primary" size="sm" icon={FileText} fullWidth>
                                Analyze Resume
                            </Button>
                        </Link>
                        <Link to="/app/interview">
                            <Button variant="secondary" size="sm" icon={MessageSquare} fullWidth>
                                Mock Interview
                            </Button>
                        </Link>
                        <Link to="/app/voice">
                            <Button variant="secondary" size="sm" icon={Mic} fullWidth>
                                Voice Practice
                            </Button>
                        </Link>
                    </div>
                </Card>
            </div>
        </motion.div>
    );
}

/* ── Helper ───────────────────────────────────────────────── */
function getTimeAgo(timestamp) {
    const diff = Date.now() - new Date(timestamp).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'Just now';
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    const days = Math.floor(hrs / 24);
    return `${days}d ago`;
}
