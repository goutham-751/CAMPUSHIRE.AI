import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, MessageSquare, Send, Loader2, CheckCircle, AlertCircle, HelpCircle, TrendingUp, Target, Users } from 'lucide-react';
import Card from '../../components/Card/Card';
import Button from '../../components/Button/Button';
import { interviewApi, trackActivity } from '../../lib/api';
import './Interview.css';

/* ── Score Ring (small version) ───────────────────────────── */
function ScoreRing({ score, size = 80 }) {
    const radius = (size - 8) / 2;
    const circ = 2 * Math.PI * radius;
    const progress = (score / 100) * circ;
    const color = score >= 80 ? '#10b981' : score >= 60 ? '#f59e0b' : '#ef4444';

    return (
        <div className="eval-ring" style={{ width: size, height: size }}>
            <svg viewBox={`0 0 ${size} ${size}`}>
                <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="var(--color-border)" strokeWidth="6" />
                <circle cx={size / 2} cy={size / 2} r={radius} fill="none"
                    stroke={color} strokeWidth="6" strokeLinecap="round"
                    strokeDasharray={circ} strokeDashoffset={circ - progress}
                    transform={`rotate(-90 ${size / 2} ${size / 2})`}
                    style={{ transition: 'stroke-dashoffset 1s ease' }}
                />
            </svg>
            <span className="eval-ring__value" style={{ color }}>{Math.round(score)}</span>
        </div>
    );
}

/* ── Panel Evaluation Result (Multi-Agent) ────────────────── */
function PanelEvalResult({ data }) {
    if (!data) return null;
    const verdictColor = {
        'Strong Hire': '#10b981', 'Hire': '#10b981', 'Lean Hire': '#f59e0b',
        'Lean No Hire': '#ef4444', 'No Hire': '#ef4444', 'Needs Review': '#6366f1',
    };
    return (
        <motion.div className="panel-eval" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
            {/* Aggregated Score */}
            <div className="panel-eval__aggregate">
                <ScoreRing score={data.aggregated_score || 0} />
                <div className="panel-eval__aggregate-info">
                    <span className="panel-eval__verdict-badge" style={{
                        background: `${verdictColor[data.overall_verdict] || '#6366f1'}20`,
                        color: verdictColor[data.overall_verdict] || '#6366f1',
                        border: `1px solid ${verdictColor[data.overall_verdict] || '#6366f1'}40`
                    }}>
                        {data.overall_verdict || 'Panel Verdict'}
                    </span>
                    <p className="panel-eval__recommendation">{data.final_recommendation}</p>
                </div>
            </div>

            {/* Agent Cards */}
            <div className="panel-eval__agents">
                {(data.agents || []).map((agent, i) => (
                    <motion.div
                        key={agent.agent_id}
                        className="agent-card"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.15 }}
                        style={{ '--agent-color': agent.agent_color }}
                    >
                        <div className="agent-card__header">
                            <div className="agent-card__avatar" style={{ background: `${agent.agent_color}20`, color: agent.agent_color }}>
                                {agent.agent_emoji}
                            </div>
                            <div className="agent-card__info">
                                <strong>{agent.agent_name}</strong>
                                <span className="agent-card__role">{agent.agent_role}</span>
                            </div>
                            <div className="agent-card__score" style={{ color: agent.score >= 80 ? '#10b981' : agent.score >= 60 ? '#f59e0b' : '#ef4444' }}>
                                {Math.round(agent.score)}
                            </div>
                        </div>
                        <p className="agent-card__verdict">{agent.verdict}</p>
                        {agent.key_observation && (
                            <div className="agent-card__observation">
                                <span>💡</span> {agent.key_observation}
                            </div>
                        )}
                        {agent.strengths?.length > 0 && (
                            <div className="agent-card__section">
                                <h6><TrendingUp size={12} /> Strengths</h6>
                                <ul>{agent.strengths.map((s, j) => <li key={j}><CheckCircle size={11} /> {s}</li>)}</ul>
                            </div>
                        )}
                        {agent.improvements?.length > 0 && (
                            <div className="agent-card__section">
                                <h6><Target size={12} /> Improve</h6>
                                <ul>{agent.improvements.map((s, j) => <li key={j}><AlertCircle size={11} /> {s}</li>)}</ul>
                            </div>
                        )}
                    </motion.div>
                ))}
            </div>

            {/* Debate Summary */}
            {(data.consensus || data.disagreements) && (
                <div className="panel-eval__debate">
                    {data.consensus && (
                        <div className="panel-eval__debate-item">
                            <CheckCircle size={14} color="#10b981" />
                            <div><strong>Consensus:</strong> {data.consensus}</div>
                        </div>
                    )}
                    {data.disagreements && data.disagreements !== 'None — unanimous assessment' && (
                        <div className="panel-eval__debate-item">
                            <AlertCircle size={14} color="#f59e0b" />
                            <div><strong>Disagreements:</strong> {data.disagreements}</div>
                        </div>
                    )}
                </div>
            )}
        </motion.div>
    );
}

/* ── Main Component ───────────────────────────────────────── */
export default function Interview() {
    const [file, setFile] = useState(null);
    const [jobTitle, setJobTitle] = useState('');
    const [company, setCompany] = useState('');
    const [jobDesc, setJobDesc] = useState('');
    const [questions, setQuestions] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Answer evaluation
    const [activeQ, setActiveQ] = useState(null);
    const [answer, setAnswer] = useState('');
    const [evalResult, setEvalResult] = useState(null);
    const [evalLoading, setEvalLoading] = useState(false);
    const fileRef = useRef(null);

    const handleGenerate = async () => {
        if (!file || !jobDesc) return;
        setLoading(true);
        setError(null);
        setQuestions(null);
        try {
            const data = await interviewApi.generateQuestions(file, jobTitle, company, jobDesc);
            setQuestions(data.questions || []);
            trackActivity({ type: 'interview_questions', text: `Generated ${(data.questions || []).length} interview questions`, icon: 'MessageSquare' });
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleEvaluate = async () => {
        if (!activeQ || !answer) return;
        setEvalLoading(true);
        setEvalResult(null);
        try {
            const data = await interviewApi.panelEvaluate(activeQ.question || activeQ, answer, jobTitle);
            setEvalResult(data);
            trackActivity({ type: 'panel_evaluated', text: `Panel score: ${data.aggregated_score || 0}% — ${data.overall_verdict || 'Reviewed'}`, score: data.aggregated_score, icon: 'TrendingUp' });
        } catch (err) {
            setError(err.message);
        } finally {
            setEvalLoading(false);
        }
    };

    const getDifficultyColor = (d) => {
        if (d === 'easy') return '#10b981';
        if (d === 'hard') return '#ef4444';
        return '#f59e0b';
    };

    return (
        <motion.div className="interview-page" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
            <h2><Users size={24} style={{ marginRight: 8, verticalAlign: 'middle' }} /> AI Hiring Committee</h2>
            <p className="interview-page__desc">Generate AI-tailored interview questions and get evaluated by a panel of 3 AI agents — Technical Lead, HR Manager & Domain Expert.</p>

            <div className="interview-page__layout">
                {/* Left: Setup */}
                <Card variant="glass" className="interview-page__setup">
                    <h3><HelpCircle size={18} /> Generate Questions</h3>

                    <div
                        className={`interview-page__dropzone ${file ? 'has-file' : ''}`}
                        onClick={() => fileRef.current?.click()}
                    >
                        <input ref={fileRef} type="file" accept=".pdf,.docx,.txt" hidden onChange={(e) => setFile(e.target.files?.[0] || null)} />
                        {file ? (
                            <><CheckCircle size={20} color="var(--color-success)" /> <span>{file.name}</span></>
                        ) : (
                            <><Upload size={20} /> <span>Upload Resume</span></>
                        )}
                    </div>

                    <input placeholder="Job Title" value={jobTitle} onChange={(e) => setJobTitle(e.target.value)} className="resume-page__input" />
                    <input placeholder="Company Name" value={company} onChange={(e) => setCompany(e.target.value)} className="resume-page__input" />
                    <textarea placeholder="Job Description…" value={jobDesc} onChange={(e) => setJobDesc(e.target.value)} className="resume-page__textarea" rows={3} />

                    <Button variant="primary" icon={MessageSquare} loading={loading} onClick={handleGenerate} disabled={!file || !jobDesc} fullWidth>
                        Generate Questions
                    </Button>
                </Card>

                {/* Right: Questions & Evaluation */}
                <div className="interview-page__content">
                    <AnimatePresence mode="wait">
                        {loading && (
                            <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="interview-page__loader">
                                <Loader2 size={28} className="resume-page__spinner" />
                                <p>Generating questions…</p>
                            </motion.div>
                        )}

                        {error && (
                            <motion.div key="error" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                                <Card variant="glass" className="resume-page__error-card">
                                    <AlertCircle size={20} color="var(--color-error)" /> <p>{error}</p>
                                </Card>
                            </motion.div>
                        )}

                        {questions && !loading && (
                            <motion.div key="questions" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="interview-page__questions">
                                {questions.map((q, i) => {
                                    const qText = typeof q === 'string' ? q : q.question || q.text || JSON.stringify(q);
                                    const isActive = activeQ === q;
                                    return (
                                        <Card
                                            key={i}
                                            variant={isActive ? 'gradient' : 'glass'}
                                            className={`interview-page__q-card ${isActive ? 'active' : ''}`}
                                            onClick={() => { setActiveQ(q); setAnswer(''); setEvalResult(null); }}
                                            hover
                                        >
                                            <div className="interview-page__q-top">
                                                <div className="interview-page__q-num">Q{i + 1}</div>
                                                <div className="interview-page__q-badges">
                                                    {q.category && <span className="interview-page__q-tag">{q.category}</span>}
                                                    {q.difficulty && (
                                                        <span className="interview-page__q-difficulty" style={{ color: getDifficultyColor(q.difficulty), borderColor: getDifficultyColor(q.difficulty) }}>
                                                            {q.difficulty}
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                            <p>{qText}</p>
                                        </Card>
                                    );
                                })}

                                {/* Answer box */}
                                {activeQ && (
                                    <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} className="interview-page__answer-section">
                                        <Card variant="glass" className="interview-page__answer-card">
                                            <h4>Your Answer</h4>
                                            <textarea
                                                value={answer}
                                                onChange={(e) => setAnswer(e.target.value)}
                                                placeholder="Type your answer here…"
                                                className="resume-page__textarea"
                                                rows={5}
                                            />
                                            <Button variant="primary" size="sm" icon={Users} loading={evalLoading} onClick={handleEvaluate} disabled={!answer}>
                                                Evaluate with AI Panel
                                            </Button>

                                            {evalResult && <PanelEvalResult data={evalResult} />}
                                        </Card>
                                    </motion.div>
                                )}
                            </motion.div>
                        )}

                        {!questions && !loading && !error && (
                            <motion.div key="empty" className="interview-page__empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                                <MessageSquare size={48} color="var(--color-text-tertiary)" />
                                <p>Upload a resume and job description to generate interview questions.</p>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </div>
        </motion.div>
    );
}
