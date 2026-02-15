import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, MessageSquare, Send, Loader2, CheckCircle, AlertCircle, HelpCircle, TrendingUp, Target, BookOpen } from 'lucide-react';
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

/* ── Evaluation Result Component ──────────────────────────── */
function EvalResult({ data }) {
    return (
        <motion.div className="eval-result" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
            <div className="eval-result__top">
                <ScoreRing score={data.score || 0} />
                <div className="eval-result__summary">
                    <span className="eval-result__score-label">Answer Score</span>
                    <span className="eval-result__score-text" style={{
                        color: (data.score || 0) >= 80 ? '#10b981' : (data.score || 0) >= 60 ? '#f59e0b' : '#ef4444'
                    }}>
                        {(data.score || 0) >= 80 ? 'Excellent' : (data.score || 0) >= 60 ? 'Good' : 'Needs Improvement'}
                    </span>
                </div>
            </div>

            {data.strengths?.length > 0 && (
                <div className="eval-result__section">
                    <h5><TrendingUp size={14} className="text-success" /> Strengths</h5>
                    <ul className="eval-result__list eval-result__list--success">
                        {data.strengths.map((s, i) => (
                            <motion.li key={i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.08 }}>
                                <CheckCircle size={13} /> {s}
                            </motion.li>
                        ))}
                    </ul>
                </div>
            )}

            {data.improvements?.length > 0 && (
                <div className="eval-result__section">
                    <h5><Target size={14} className="text-warning" /> Areas for Improvement</h5>
                    <ul className="eval-result__list eval-result__list--warning">
                        {data.improvements.map((item, i) => (
                            <motion.li key={i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.08 }}>
                                <AlertCircle size={13} /> {item}
                            </motion.li>
                        ))}
                    </ul>
                </div>
            )}

            {data.sample_answer && (
                <div className="eval-result__section">
                    <h5><BookOpen size={14} className="text-accent" /> Sample Ideal Answer</h5>
                    <div className="eval-result__sample">{data.sample_answer}</div>
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
            const data = await interviewApi.evaluateAnswer(activeQ.question || activeQ, answer, jobTitle);
            setEvalResult(data);
            trackActivity({ type: 'answer_evaluated', text: `Interview answer scored ${data.score || 0}%`, score: data.score, icon: 'TrendingUp' });
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
            <h2>Mock Interview</h2>
            <p className="interview-page__desc">Generate AI-tailored interview questions and practice with real-time evaluation.</p>

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
                                            <Button variant="primary" size="sm" icon={Send} loading={evalLoading} onClick={handleEvaluate} disabled={!answer}>
                                                Evaluate Answer
                                            </Button>

                                            {evalResult && <EvalResult data={evalResult} />}
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
