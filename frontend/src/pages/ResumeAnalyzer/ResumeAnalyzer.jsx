import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Upload, FileText, BarChart3, MessageSquare, CheckCircle, AlertCircle, Loader2,
    Mail, Phone, Linkedin, Github, Award, BookOpen, Briefcase, Code, Globe, Star,
    TrendingUp, Target, Lightbulb, ChevronDown, ChevronUp, Zap, Search, Layers
} from 'lucide-react';
import Card from '../../components/Card/Card';
import Button from '../../components/Button/Button';
import { resumeApi, trackActivity } from '../../lib/api';
import './ResumeAnalyzer.css';

/* ── Score Gauge Component ────────────────────────────────── */
function ScoreGauge({ score, size = 160, label = 'ATS Score' }) {
    const radius = (size - 16) / 2;
    const circumference = 2 * Math.PI * radius;
    const progress = (score / 100) * circumference;
    const color = score >= 80 ? '#10b981' : score >= 60 ? '#f59e0b' : '#ef4444';

    return (
        <div className="score-gauge" style={{ width: size, height: size }}>
            <svg viewBox={`0 0 ${size} ${size}`} className="score-gauge__svg">
                <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="var(--color-border)" strokeWidth="10" />
                <circle
                    cx={size / 2} cy={size / 2} r={radius} fill="none"
                    stroke={color} strokeWidth="10" strokeLinecap="round"
                    strokeDasharray={circumference}
                    strokeDashoffset={circumference - progress}
                    transform={`rotate(-90 ${size / 2} ${size / 2})`}
                    style={{ transition: 'stroke-dashoffset 1.5s ease' }}
                />
            </svg>
            <div className="score-gauge__content">
                <span className="score-gauge__value" style={{ color }}>{Math.round(score)}</span>
                <span className="score-gauge__label">{label}</span>
            </div>
        </div>
    );
}

/* ── Category Bar Component ───────────────────────────────── */
function CategoryBar({ name, score, delay = 0 }) {
    const color = score >= 80 ? '#10b981' : score >= 60 ? '#f59e0b' : '#ef4444';
    return (
        <motion.div className="cat-bar" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay }}>
            <div className="cat-bar__header">
                <span className="cat-bar__name">{name}</span>
                <span className="cat-bar__score" style={{ color }}>{Math.round(score)}%</span>
            </div>
            <div className="cat-bar__track">
                <motion.div
                    className="cat-bar__fill"
                    style={{ background: color }}
                    initial={{ width: 0 }}
                    animate={{ width: `${score}%` }}
                    transition={{ duration: 1, delay: delay + 0.2, ease: 'easeOut' }}
                />
            </div>
        </motion.div>
    );
}

/* ── Tag List Component ───────────────────────────────────── */
function TagList({ items, color = 'var(--color-accent)', icon: Icon }) {
    if (!items?.length) return null;
    return (
        <div className="tag-list">
            {items.map((item, i) => (
                <motion.span key={i} className="tag-list__item" style={{ borderColor: color }}
                    initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: i * 0.05 }}>
                    {Icon && <Icon size={12} style={{ color, flexShrink: 0 }} />}
                    {item}
                </motion.span>
            ))}
        </div>
    );
}

/* ── Feedback Section Component ───────────────────────────── */
function FeedbackSection({ title, items, icon: Icon, color, defaultOpen = false }) {
    const [open, setOpen] = useState(defaultOpen);
    if (!items?.length) return null;
    return (
        <div className="feedback-section">
            <button className="feedback-section__header" onClick={() => setOpen(!open)}>
                <div className="feedback-section__title" style={{ color }}>
                    <Icon size={18} />
                    <span>{title}</span>
                    <span className="feedback-section__count">{items.length}</span>
                </div>
                {open ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </button>
            <AnimatePresence>
                {open && (
                    <motion.ul className="feedback-section__list"
                        initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.3 }}>
                        {items.map((item, i) => (
                            <motion.li key={i} initial={{ x: -10, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ delay: i * 0.06 }}>
                                <span className="feedback-section__bullet" style={{ background: color }} />
                                {item}
                            </motion.li>
                        ))}
                    </motion.ul>
                )}
            </AnimatePresence>
        </div>
    );
}

/* ── Parsed Resume Renderer ───────────────────────────────── */
function ParsedResult({ data }) {
    const d = data?.data || data || {};
    return (
        <div className="parsed-result">
            {/* Header */}
            {d.name && (
                <div className="parsed-result__header">
                    <div className="parsed-result__avatar">{d.name?.[0]?.toUpperCase() || '?'}</div>
                    <div>
                        <h3 className="parsed-result__name">{d.name}</h3>
                        <div className="parsed-result__contact">
                            {d.email && <span><Mail size={13} /> {d.email}</span>}
                            {d.phone && <span><Phone size={13} /> {d.phone}</span>}
                            {d.linkedin && <span><Linkedin size={13} /> LinkedIn</span>}
                            {d.github && <span><Github size={13} /> GitHub</span>}
                        </div>
                    </div>
                </div>
            )}

            {/* Summary */}
            {d.summary && (
                <div className="parsed-result__section">
                    <h4><BookOpen size={16} /> Professional Summary</h4>
                    <p className="parsed-result__summary">{d.summary}</p>
                </div>
            )}

            {/* Skills */}
            {d.skills?.length > 0 && (
                <div className="parsed-result__section">
                    <h4><Code size={16} /> Skills</h4>
                    <div className="parsed-result__skills">
                        {d.skills.map((skill, i) => (
                            <span key={i} className="parsed-result__skill-tag">{skill}</span>
                        ))}
                    </div>
                </div>
            )}

            {/* Experience */}
            {d.experience?.length > 0 && (
                <div className="parsed-result__section">
                    <h4><Briefcase size={16} /> Experience</h4>
                    <div className="parsed-result__timeline">
                        {d.experience.map((exp, i) => (
                            <div key={i} className="parsed-result__exp-card">
                                <div className="parsed-result__exp-dot" />
                                <div className="parsed-result__exp-content">
                                    <strong>{exp.title || 'Role'}</strong>
                                    {exp.company && <span className="parsed-result__exp-company">{exp.company}</span>}
                                    {exp.duration && <span className="parsed-result__exp-duration">{exp.duration}</span>}
                                    {exp.description?.length > 0 && (
                                        <ul>{exp.description.map((d, j) => <li key={j}>{d}</li>)}</ul>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Education */}
            {d.education?.length > 0 && (
                <div className="parsed-result__section">
                    <h4><Award size={16} /> Education</h4>
                    {d.education.map((edu, i) => (
                        <div key={i} className="parsed-result__edu-item">
                            <strong>{edu.degree || 'Degree'}</strong>
                            {edu.institution && <span>{edu.institution}</span>}
                            {edu.year && <span className="parsed-result__edu-year">{edu.year}</span>}
                        </div>
                    ))}
                </div>
            )}

            {/* Projects */}
            {d.projects?.length > 0 && (
                <div className="parsed-result__section">
                    <h4><Star size={16} /> Projects</h4>
                    <div className="parsed-result__projects">
                        {d.projects.map((proj, i) => (
                            <Card key={i} variant="glass" className="parsed-result__proj-card" hover={false}>
                                <strong>{proj.title}</strong>
                                {proj.description && (
                                    <p>{Array.isArray(proj.description) ? proj.description.join(' ') : proj.description}</p>
                                )}
                            </Card>
                        ))}
                    </div>
                </div>
            )}

            {/* Languages & Certifications */}
            {d.languages?.length > 0 && (
                <div className="parsed-result__section">
                    <h4><Globe size={16} /> Languages</h4>
                    <TagList items={d.languages} color="#06b6d4" />
                </div>
            )}
            {d.certifications?.length > 0 && (
                <div className="parsed-result__section">
                    <h4><Award size={16} /> Certifications</h4>
                    <TagList items={d.certifications} color="#8b5cf6" />
                </div>
            )}
        </div>
    );
}

/* ── ATS Score Renderer ───────────────────────────────────── */
function ScoreResult({ data }) {
    const scoreMap = {
        skills_match: 'Skills Match',
        experience_level: 'Experience',
        education: 'Education',
        keyword_density: 'Keywords',
        formatting: 'Formatting',
        achievements: 'Achievements',
    };

    return (
        <div className="score-result">
            <div className="score-result__top">
                <ScoreGauge score={data.overall_score || 0} />
                <div className="score-result__categories">
                    <h4>Category Breakdown</h4>
                    {data.scores && Object.entries(scoreMap).map(([key, label], i) => (
                        <CategoryBar key={key} name={label} score={data.scores[key] || 0} delay={i * 0.08} />
                    ))}
                </div>
            </div>

            <div className="score-result__details">
                {data.strengths?.length > 0 && (
                    <div className="score-result__detail-section">
                        <h4><TrendingUp size={16} className="text-success" /> Strengths</h4>
                        <ul className="score-result__list score-result__list--success">
                            {data.strengths.map((s, i) => <li key={i}>{s}</li>)}
                        </ul>
                    </div>
                )}
                {data.weaknesses?.length > 0 && (
                    <div className="score-result__detail-section">
                        <h4><AlertCircle size={16} className="text-warning" /> Weaknesses</h4>
                        <ul className="score-result__list score-result__list--warning">
                            {data.weaknesses.map((w, i) => <li key={i}>{w}</li>)}
                        </ul>
                    </div>
                )}
                {data.suggestions?.length > 0 && (
                    <div className="score-result__detail-section">
                        <h4><Lightbulb size={16} className="text-accent" /> Suggestions</h4>
                        <ul className="score-result__list score-result__list--accent">
                            {data.suggestions.map((s, i) => <li key={i}>{s}</li>)}
                        </ul>
                    </div>
                )}
                {data.missing_keywords?.length > 0 && (
                    <div className="score-result__detail-section">
                        <h4><Search size={16} className="text-error" /> Missing Keywords</h4>
                        <TagList items={data.missing_keywords} color="#ef4444" icon={Target} />
                    </div>
                )}
                {data.ats_optimization_tips?.length > 0 && (
                    <div className="score-result__detail-section">
                        <h4><Zap size={16} className="text-info" /> ATS Optimization Tips</h4>
                        <ul className="score-result__list score-result__list--info">
                            {data.ats_optimization_tips.map((t, i) => <li key={i}>{t}</li>)}
                        </ul>
                    </div>
                )}
            </div>
        </div>
    );
}

/* ── Feedback Renderer ────────────────────────────────────── */
function FeedbackResult({ data }) {
    const fb = data?.feedback || {};
    return (
        <div className="feedback-result">
            <FeedbackSection title="Strengths" items={fb.strengths} icon={TrendingUp} color="#10b981" defaultOpen />
            <FeedbackSection title="Areas for Improvement" items={fb.areas_for_improvement} icon={Target} color="#f59e0b" defaultOpen />
            <FeedbackSection title="ATS Optimization" items={fb.ats_optimization} icon={Zap} color="#6366f1" />
            <FeedbackSection title="Skill Gap Analysis" items={fb.skill_gap_analysis} icon={Search} color="#ef4444" />
            <FeedbackSection title="Actionable Recommendations" items={fb.actionable_recommendations} icon={Lightbulb} color="#06b6d4" />
        </div>
    );
}

/* ── Semantic Match Result ────────────────────────────────── */
function SemanticMatchResultView({ data }) {
    const res = data?.result || data || {};
    const gradeColor = {
        'Excellent Match': '#10b981', 'Strong Match': '#22c55e', 'Moderate Match': '#f59e0b',
        'Weak Match': '#ef4444', 'Poor Match': '#dc2626',
    };
    const sections = res.section_scores || {};

    return (
        <div className="semantic-result">
            {/* Top Score */}
            <div className="semantic-result__top">
                <ScoreGauge score={res.overall_similarity || 0} label="Semantic Match" />
                <div className="semantic-result__grade-area">
                    <span className="semantic-result__grade" style={{
                        background: `${gradeColor[res.match_grade] || '#6366f1'}15`,
                        color: gradeColor[res.match_grade] || '#6366f1',
                        border: `1px solid ${gradeColor[res.match_grade] || '#6366f1'}40`
                    }}>{res.match_grade}</span>
                    {res.job_title && <span className="semantic-result__job-title">vs. {res.job_title}</span>}
                </div>
            </div>

            {/* Section Breakdown */}
            {Object.keys(sections).length > 0 && (
                <div className="semantic-result__sections">
                    <h4><Layers size={16} /> Section Breakdown</h4>
                    {Object.entries(sections).map(([key, score], i) => (
                        <CategoryBar key={key} name={key.charAt(0).toUpperCase() + key.slice(1)} score={score} delay={i * 0.1} />
                    ))}
                </div>
            )}

            {/* Keywords */}
            <div className="semantic-result__keywords">
                {res.matched_keywords?.length > 0 && (
                    <div className="semantic-result__kw-group">
                        <h5><CheckCircle size={14} color="#10b981" /> Matched Keywords ({res.matched_keywords.length})</h5>
                        <div className="tag-list">
                            {res.matched_keywords.map((kw, i) => (
                                <span key={i} className="tag-list__item" style={{ borderColor: '#10b981' }}>{kw}</span>
                            ))}
                        </div>
                    </div>
                )}
                {res.missing_keywords?.length > 0 && (
                    <div className="semantic-result__kw-group">
                        <h5><AlertCircle size={14} color="#ef4444" /> Missing Keywords ({res.missing_keywords.length})</h5>
                        <div className="tag-list">
                            {res.missing_keywords.map((kw, i) => (
                                <span key={i} className="tag-list__item" style={{ borderColor: '#ef4444' }}>{kw}</span>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* Recommendations */}
            {res.recommendations?.length > 0 && (
                <div className="semantic-result__recs">
                    <h4><Lightbulb size={16} /> Recommendations</h4>
                    <ul>{res.recommendations.map((r, i) => <li key={i}>{r}</li>)}</ul>
                </div>
            )}
        </div>
    );
}

/* ── Main Component ───────────────────────────────────────── */
export default function ResumeAnalyzer() {
    const [file, setFile] = useState(null);
    const [mode, setMode] = useState(null);
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [jobTitle, setJobTitle] = useState('');
    const [company, setCompany] = useState('');
    const [jobDesc, setJobDesc] = useState('');
    const fileRef = useRef(null);

    const handleDrop = (e) => {
        e.preventDefault();
        const f = e.dataTransfer?.files?.[0];
        if (f) setFile(f);
    };

    const handleAnalyze = async (action) => {
        if (!file) return;
        setMode(action);
        setLoading(true);
        setError(null);
        setResult(null);

        try {
            let data;
            if (action === 'parse') {
                data = await resumeApi.upload(file);
                trackActivity({ type: 'resume_parsed', text: 'Resume analyzed', icon: 'FileText' });
            } else if (action === 'score') {
                data = await resumeApi.score(file, jobTitle, company, jobDesc);
                trackActivity({ type: 'ats_score', text: `ATS Score: ${data.overall_score || 0}%`, score: data.overall_score, scores: data.scores, icon: 'BarChart3' });
            } else if (action === 'semantic') {
                data = await resumeApi.semanticMatch(file, jobDesc, jobTitle);
                trackActivity({ type: 'semantic_match', text: `Semantic Match: ${data?.result?.overall_similarity || 0}%`, score: data?.result?.overall_similarity, icon: 'Layers' });
            } else {
                data = await resumeApi.feedback(file, jobTitle, company, jobDesc);
                trackActivity({ type: 'feedback', text: 'Feedback report generated', icon: 'MessageSquare' });
            }
            setResult(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <motion.div
            className="resume-page"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
        >
            <h2>Resume Analyzer</h2>
            <p className="resume-page__desc">Upload your resume to get AI-powered analysis, ATS scoring, and improvement feedback.</p>

            <div className="resume-page__grid">
                {/* Upload area */}
                <Card variant="glass" className="resume-page__upload-card">
                    <div
                        className={`resume-page__dropzone ${file ? 'has-file' : ''}`}
                        onClick={() => fileRef.current?.click()}
                        onDragOver={(e) => e.preventDefault()}
                        onDrop={handleDrop}
                    >
                        <input
                            ref={fileRef}
                            type="file"
                            accept=".pdf,.docx,.txt"
                            hidden
                            onChange={(e) => setFile(e.target.files?.[0] || null)}
                        />
                        {file ? (
                            <>
                                <CheckCircle size={32} color="var(--color-success)" />
                                <strong>{file.name}</strong>
                                <span className="resume-page__file-size">{(file.size / 1024).toFixed(1)} KB</span>
                                <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); setFile(null); setResult(null); }}>
                                    Remove
                                </Button>
                            </>
                        ) : (
                            <>
                                <Upload size={36} color="var(--color-accent)" />
                                <strong>Drop your resume here</strong>
                                <span>or click to browse — PDF, DOCX, TXT</span>
                            </>
                        )}
                    </div>

                    {/* Job details */}
                    <div className="resume-page__fields">
                        <input placeholder="Job Title" value={jobTitle} onChange={(e) => setJobTitle(e.target.value)} className="resume-page__input" />
                        <input placeholder="Company Name" value={company} onChange={(e) => setCompany(e.target.value)} className="resume-page__input" />
                        <textarea placeholder="Paste the job description here…" value={jobDesc} onChange={(e) => setJobDesc(e.target.value)} className="resume-page__textarea" rows={4} />
                    </div>

                    {/* Actions */}
                    <div className="resume-page__actions">
                        <Button variant="primary" size="sm" icon={FileText} loading={loading && mode === 'parse'} onClick={() => handleAnalyze('parse')} disabled={!file}>
                            Parse Resume
                        </Button>
                        <Button variant="secondary" size="sm" icon={BarChart3} loading={loading && mode === 'score'} onClick={() => handleAnalyze('score')} disabled={!file || !jobDesc}>
                            ATS Score
                        </Button>
                        <Button variant="secondary" size="sm" icon={Layers} loading={loading && mode === 'semantic'} onClick={() => handleAnalyze('semantic')} disabled={!file || !jobDesc}>
                            Semantic Match
                        </Button>
                        <Button variant="secondary" size="sm" icon={MessageSquare} loading={loading && mode === 'feedback'} onClick={() => handleAnalyze('feedback')} disabled={!file || !jobDesc}>
                            Get Feedback
                        </Button>
                    </div>
                </Card>

                {/* Results */}
                <AnimatePresence mode="wait">
                    {loading && (
                        <motion.div key="loader" className="resume-page__loader" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                            <Card variant="glass" className="resume-page__loader-card">
                                <Loader2 size={32} className="resume-page__spinner" />
                                <p>Analyzing your resume…</p>
                            </Card>
                        </motion.div>
                    )}

                    {error && (
                        <motion.div key="error" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }}>
                            <Card variant="glass" className="resume-page__error-card">
                                <AlertCircle size={24} color="var(--color-error)" />
                                <p>{error}</p>
                            </Card>
                        </motion.div>
                    )}

                    {result && !loading && (
                        <motion.div key="result" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
                            <Card variant="glass" className="resume-page__result-card">
                                <h3 className="resume-page__result-title">
                                    {mode === 'parse' && <><FileText size={20} /> Parsed Resume</>}
                                    {mode === 'score' && <><BarChart3 size={20} /> ATS Score Report</>}
                                    {mode === 'semantic' && <><Layers size={20} /> Semantic Match Report</>}
                                    {mode === 'feedback' && <><MessageSquare size={20} /> Improvement Feedback</>}
                                </h3>
                                {mode === 'parse' && <ParsedResult data={result} />}
                                {mode === 'score' && <ScoreResult data={result} />}
                                {mode === 'semantic' && <SemanticMatchResultView data={result} />}
                                {mode === 'feedback' && <FeedbackResult data={result} />}
                            </Card>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </motion.div>
    );
}
