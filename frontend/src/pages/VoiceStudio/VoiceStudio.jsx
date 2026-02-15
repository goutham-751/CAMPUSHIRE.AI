import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Mic, Volume2, Loader2, Play, Square, List, Upload, MessageSquare,
    CheckCircle, AlertCircle, ChevronRight, TrendingUp, Target, BookOpen,
    StopCircle, SkipForward, BarChart3
} from 'lucide-react';
import Card from '../../components/Card/Card';
import Button from '../../components/Button/Button';
import { voiceApi, interviewApi, trackActivity } from '../../lib/api';
import './VoiceStudio.css';

/* ── Tab Navigation ───────────────────────────────────────── */
function Tabs({ active, onChange }) {
    const tabs = [
        { id: 'tools', label: 'Voice Tools', icon: Volume2 },
        { id: 'interview', label: 'AI Interview', icon: MessageSquare },
    ];
    return (
        <div className="voice-tabs">
            {tabs.map(t => (
                <button
                    key={t.id}
                    className={`voice-tabs__btn ${active === t.id ? 'active' : ''}`}
                    onClick={() => onChange(t.id)}
                >
                    <t.icon size={16} />
                    <span>{t.label}</span>
                </button>
            ))}
        </div>
    );
}

/* ── Score Ring ────────────────────────────────────────────── */
function ScoreRing({ score, size = 64 }) {
    const r = (size - 6) / 2;
    const c = 2 * Math.PI * r;
    const p = (score / 100) * c;
    const color = score >= 80 ? '#10b981' : score >= 60 ? '#f59e0b' : '#ef4444';
    return (
        <div className="vi-score-ring" style={{ width: size, height: size }}>
            <svg viewBox={`0 0 ${size} ${size}`}>
                <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--color-border)" strokeWidth="5" />
                <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={color} strokeWidth="5"
                    strokeLinecap="round" strokeDasharray={c} strokeDashoffset={c - p}
                    transform={`rotate(-90 ${size / 2} ${size / 2})`}
                    style={{ transition: 'stroke-dashoffset 0.8s ease' }}
                />
            </svg>
            <span className="vi-score-ring__val" style={{ color, fontSize: size * 0.26 }}>{Math.round(score)}</span>
        </div>
    );
}

/* ════════════════════════════════════════════════════════════ */
/*  VOICE TOOLS TAB (original TTS / STT)                      */
/* ════════════════════════════════════════════════════════════ */
function VoiceTools() {
    const [text, setText] = useState('');
    const [voices, setVoices] = useState(null);
    const [selectedVoice, setSelectedVoice] = useState('');
    const [ttsLoading, setTtsLoading] = useState(false);
    const [audioUrl, setAudioUrl] = useState(null);
    const [sttFile, setSttFile] = useState(null);
    const [sttResult, setSttResult] = useState(null);
    const [sttLoading, setSttLoading] = useState(false);

    useEffect(() => {
        voiceApi.getVoices().then(data => setVoices(data.voices || data)).catch(() => { });
    }, []);

    const handleTTS = async () => {
        if (!text) return;
        setTtsLoading(true);
        try {
            const blob = await voiceApi.tts(text, 'en', selectedVoice || null, 'mp3');
            setAudioUrl(URL.createObjectURL(blob));
        } catch (err) { console.error(err); }
        finally { setTtsLoading(false); }
    };

    const handleSTT = async () => {
        if (!sttFile) return;
        setSttLoading(true);
        setSttResult(null);
        try {
            const data = await voiceApi.stt(sttFile);
            setSttResult(data);
        } catch (err) {
            setSttResult({ success: false, error: err.message });
        } finally { setSttLoading(false); }
    };

    return (
        <div className="voice-page__grid">
            {/* TTS */}
            <Card variant="glass" className="voice-page__card">
                <div className="voice-page__card-header"><Volume2 size={20} /><h3>Text-to-Speech</h3></div>
                <textarea value={text} onChange={(e) => setText(e.target.value)} placeholder="Enter text to convert to speech…"
                    className="resume-page__textarea" rows={4} />
                {voices && (
                    <select value={selectedVoice} onChange={(e) => setSelectedVoice(e.target.value)} className="settings__select">
                        <option value="">Default Voice</option>
                        {Object.entries(voices).map(([group, voiceList]) => (
                            <optgroup label={group} key={group}>
                                {voiceList.map(v => <option key={v} value={v}>{v}</option>)}
                            </optgroup>
                        ))}
                    </select>
                )}
                <Button variant="primary" icon={Play} loading={ttsLoading} onClick={handleTTS} disabled={!text}>
                    Generate Speech
                </Button>
                {audioUrl && (
                    <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} className="voice-page__audio">
                        <audio controls src={audioUrl} style={{ width: '100%' }} />
                    </motion.div>
                )}
            </Card>

            {/* STT */}
            <Card variant="glass" className="voice-page__card">
                <div className="voice-page__card-header"><Mic size={20} /><h3>Speech-to-Text</h3></div>
                <div className={`interview-page__dropzone ${sttFile ? 'has-file' : ''}`}
                    onClick={() => document.getElementById('stt-input').click()}>
                    <input id="stt-input" type="file" accept="audio/*" hidden onChange={(e) => setSttFile(e.target.files?.[0] || null)} />
                    {sttFile ? (<><Mic size={18} color="var(--color-success)" /> <span>{sttFile.name}</span></>) :
                        (<><Mic size={18} /> <span>Upload audio file</span></>)}
                </div>
                <Button variant="primary" icon={Mic} loading={sttLoading} onClick={handleSTT} disabled={!sttFile}>Transcribe</Button>
                {sttResult && (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                        {sttResult.success ? (
                            <Card variant="gradient" padding><p style={{ fontStyle: 'italic' }}>"{sttResult.text}"</p>
                                <span style={{ fontSize: '0.75rem', color: 'var(--color-text-tertiary)' }}>
                                    Confidence: {((sttResult.confidence || 0) * 100).toFixed(0)}%
                                </span>
                            </Card>
                        ) : (
                            <Card variant="glass" padding><p style={{ color: 'var(--color-error)' }}>Error: {sttResult.error}</p></Card>
                        )}
                    </motion.div>
                )}
            </Card>
        </div>
    );
}

/* ════════════════════════════════════════════════════════════ */
/*  AI INTERVIEW CONDUCTOR                                    */
/* ════════════════════════════════════════════════════════════ */

const PHASES = { SETUP: 'setup', RUNNING: 'running', SUMMARY: 'summary' };

function AIInterview() {
    // Setup state
    const [file, setFile] = useState(null);
    const [jobTitle, setJobTitle] = useState('');
    const [company, setCompany] = useState('');
    const [jobDesc, setJobDesc] = useState('');
    const [numQ, setNumQ] = useState(5);

    // Interview state
    const [phase, setPhase] = useState(PHASES.SETUP);
    const [questions, setQuestions] = useState([]);
    const [currentIdx, setCurrentIdx] = useState(0);
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Recording state
    const [isRecording, setIsRecording] = useState(false);
    const [recordingTime, setRecordingTime] = useState(0);
    const [isSpeaking, setIsSpeaking] = useState(false);
    const [isEvaluating, setIsEvaluating] = useState(false);
    const [currentEval, setCurrentEval] = useState(null);
    const [transcript, setTranscript] = useState('');

    const mediaRecorderRef = useRef(null);
    const chunksRef = useRef([]);
    const timerRef = useRef(null);
    const audioRef = useRef(null);
    const fileRef = useRef(null);

    // Cleanup
    useEffect(() => {
        return () => {
            if (timerRef.current) clearInterval(timerRef.current);
            if (audioRef.current) { audioRef.current.pause(); audioRef.current = null; }
        };
    }, []);

    // ── Generate Questions ──
    const handleStart = async () => {
        if (!file || !jobDesc) return;
        setLoading(true);
        setError(null);
        try {
            const data = await interviewApi.generateQuestions(file, jobTitle, company, jobDesc, numQ);
            const qs = data.questions || [];
            if (qs.length === 0) throw new Error('No questions generated');
            setQuestions(qs);
            setResults([]);
            setCurrentIdx(0);
            setPhase(PHASES.RUNNING);
            trackActivity({ type: 'voice_interview_start', text: `Voice interview started (${qs.length} questions)`, icon: 'Mic' });
            // Read first question
            setTimeout(() => speakQuestion(qs[0]), 500);
        } catch (e) {
            setError(e.message);
        } finally { setLoading(false); }
    };

    // ── Speak Question via TTS ──
    const speakQuestion = async (q) => {
        const qText = typeof q === 'string' ? q : q.question || '';
        if (!qText) return;
        setIsSpeaking(true);
        try {
            const blob = await voiceApi.tts(qText, 'en', null, 'mp3');
            const url = URL.createObjectURL(blob);
            const audio = new Audio(url);
            audioRef.current = audio;
            audio.onended = () => { setIsSpeaking(false); URL.revokeObjectURL(url); };
            audio.onerror = () => { setIsSpeaking(false); URL.revokeObjectURL(url); };
            await audio.play();
        } catch {
            setIsSpeaking(false);
        }
    };

    // ── Start recording ──
    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
            chunksRef.current = [];
            recorder.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data); };
            recorder.onstop = () => { stream.getTracks().forEach(t => t.stop()); };
            recorder.start();
            mediaRecorderRef.current = recorder;
            setIsRecording(true);
            setRecordingTime(0);
            timerRef.current = setInterval(() => setRecordingTime(t => t + 1), 1000);
        } catch (err) {
            setError('Microphone access denied. Please allow microphone access.');
        }
    };

    // ── Stop recording & process ──
    const stopRecording = async () => {
        if (!mediaRecorderRef.current) return;
        clearInterval(timerRef.current);

        return new Promise((resolve) => {
            mediaRecorderRef.current.onstop = async () => {
                mediaRecorderRef.current.stream?.getTracks().forEach(t => t.stop());
                const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
                setIsRecording(false);
                setIsEvaluating(true);
                setTranscript('');
                setCurrentEval(null);

                try {
                    // STT
                    const audioFile = new File([blob], 'answer.webm', { type: 'audio/webm' });
                    const sttResult = await voiceApi.stt(audioFile);
                    const text = sttResult?.text || '';
                    setTranscript(text);

                    if (!text) {
                        setCurrentEval({ score: 0, strengths: [], improvements: ['Could not transcribe your answer. Please speak clearly and try again.'] });
                        setIsEvaluating(false);
                        resolve();
                        return;
                    }

                    // Evaluate
                    const q = questions[currentIdx];
                    const qText = typeof q === 'string' ? q : q.question || '';
                    const evalData = await interviewApi.evaluateAnswer(qText, text, jobTitle);
                    setCurrentEval(evalData);
                    trackActivity({ type: 'answer_evaluated', text: `Voice answer scored ${evalData.score || 0}%`, score: evalData.score, icon: 'TrendingUp' });
                } catch (e) {
                    setCurrentEval({ score: 0, strengths: [], improvements: [`Error: ${e.message}`] });
                } finally {
                    setIsEvaluating(false);
                    resolve();
                }
            };
            mediaRecorderRef.current.stop();
        });
    };

    // ── Next question ──
    const nextQuestion = () => {
        // Save result
        const q = questions[currentIdx];
        setResults(prev => [...prev, { question: typeof q === 'string' ? q : q.question, transcript, evaluation: currentEval }]);
        setCurrentEval(null);
        setTranscript('');

        if (currentIdx + 1 >= questions.length) {
            setPhase(PHASES.SUMMARY);
            trackActivity({ type: 'voice_interview_complete', text: 'Voice interview completed', icon: 'Award' });
        } else {
            const nextIdx = currentIdx + 1;
            setCurrentIdx(nextIdx);
            setTimeout(() => speakQuestion(questions[nextIdx]), 500);
        }
    };

    // ── Skip question ──
    const skipQuestion = () => {
        setResults(prev => [...prev, { question: typeof questions[currentIdx] === 'string' ? questions[currentIdx] : questions[currentIdx].question, transcript: '(skipped)', evaluation: { score: 0 } }]);
        setCurrentEval(null);
        setTranscript('');
        if (currentIdx + 1 >= questions.length) {
            setPhase(PHASES.SUMMARY);
        } else {
            const nextIdx = currentIdx + 1;
            setCurrentIdx(nextIdx);
            setTimeout(() => speakQuestion(questions[nextIdx]), 500);
        }
    };

    // ── Computed ──
    const currentQ = questions[currentIdx];
    const qText = currentQ ? (typeof currentQ === 'string' ? currentQ : currentQ.question || '') : '';
    const avgScore = results.length > 0 ? Math.round(results.reduce((s, r) => s + (r.evaluation?.score || 0), 0) / results.length) : 0;

    // ════════════════════ RENDER ════════════════════

    // SETUP
    if (phase === PHASES.SETUP) {
        return (
            <div className="vi-setup">
                <Card variant="glass" className="vi-setup__card">
                    <div className="voice-page__card-header"><MessageSquare size={20} /><h3>AI Interview Setup</h3></div>
                    <p className="vi-setup__desc">Upload your resume and provide job details. The AI will conduct a voice interview — reading questions aloud and evaluating your spoken answers.</p>

                    <div className={`interview-page__dropzone ${file ? 'has-file' : ''}`}
                        onClick={() => fileRef.current?.click()}>
                        <input ref={fileRef} type="file" accept=".pdf,.docx,.txt" hidden onChange={(e) => setFile(e.target.files?.[0] || null)} />
                        {file ? (<><CheckCircle size={20} color="var(--color-success)" /> <span>{file.name}</span></>) :
                            (<><Upload size={20} /> <span>Upload Resume</span></>)}
                    </div>

                    <input placeholder="Job Title" value={jobTitle} onChange={(e) => setJobTitle(e.target.value)} className="resume-page__input" />
                    <input placeholder="Company Name" value={company} onChange={(e) => setCompany(e.target.value)} className="resume-page__input" />
                    <textarea placeholder="Job Description…" value={jobDesc} onChange={(e) => setJobDesc(e.target.value)} className="resume-page__textarea" rows={3} />

                    <div className="vi-setup__q-count">
                        <label>Number of Questions</label>
                        <div className="vi-setup__q-btns">
                            {[3, 5, 8, 10].map(n => (
                                <button key={n} className={`vi-setup__q-btn ${numQ === n ? 'active' : ''}`} onClick={() => setNumQ(n)}>{n}</button>
                            ))}
                        </div>
                    </div>

                    <Button variant="primary" icon={Mic} loading={loading} onClick={handleStart} disabled={!file || !jobDesc} fullWidth>
                        Start Voice Interview
                    </Button>

                    {error && <p className="vi-error"><AlertCircle size={14} /> {error}</p>}
                </Card>
            </div>
        );
    }

    // RUNNING
    if (phase === PHASES.RUNNING) {
        return (
            <div className="vi-running">
                {/* Progress bar */}
                <div className="vi-progress">
                    <div className="vi-progress__bar">
                        <motion.div className="vi-progress__fill" animate={{ width: `${((currentIdx + 1) / questions.length) * 100}%` }} />
                    </div>
                    <span className="vi-progress__text">Question {currentIdx + 1} of {questions.length}</span>
                </div>

                {/* Question card */}
                <Card variant="glass" className="vi-question-card">
                    <div className="vi-question-card__header">
                        <div className="vi-question-card__num">Q{currentIdx + 1}</div>
                        <div className="vi-question-card__badges">
                            {currentQ?.category && <span className="interview-page__q-tag">{currentQ.category}</span>}
                            {currentQ?.difficulty && (
                                <span className="interview-page__q-difficulty" style={{
                                    color: currentQ.difficulty === 'easy' ? '#10b981' : currentQ.difficulty === 'hard' ? '#ef4444' : '#f59e0b',
                                    borderColor: currentQ.difficulty === 'easy' ? '#10b981' : currentQ.difficulty === 'hard' ? '#ef4444' : '#f59e0b',
                                }}>{currentQ.difficulty}</span>
                            )}
                        </div>
                    </div>
                    <p className="vi-question-card__text">{qText}</p>

                    {/* Speaking indicator */}
                    {isSpeaking && (
                        <motion.div className="vi-speaking" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                            <div className="vi-speaking__waves">
                                {[1, 2, 3, 4, 5].map(i => (
                                    <motion.div key={i} className="vi-speaking__bar"
                                        animate={{ height: [8, 20 + Math.random() * 12, 8] }}
                                        transition={{ repeat: Infinity, duration: 0.5 + Math.random() * 0.4, delay: i * 0.08 }}
                                    />
                                ))}
                            </div>
                            <span>AI is reading the question…</span>
                        </motion.div>
                    )}

                    {/* Recording controls */}
                    {!isSpeaking && !isEvaluating && !currentEval && (
                        <div className="vi-record">
                            {!isRecording ? (
                                <Button variant="primary" icon={Mic} onClick={startRecording}>
                                    Record Your Answer
                                </Button>
                            ) : (
                                <div className="vi-record__active">
                                    <motion.div className="vi-record__pulse"
                                        animate={{ scale: [1, 1.3, 1], opacity: [1, 0.5, 1] }}
                                        transition={{ repeat: Infinity, duration: 1.5 }}
                                    />
                                    <span className="vi-record__time">{Math.floor(recordingTime / 60)}:{String(recordingTime % 60).padStart(2, '0')}</span>
                                    <Button variant="danger" size="sm" icon={StopCircle} onClick={stopRecording}>
                                        Stop Recording
                                    </Button>
                                </div>
                            )}
                            <Button variant="ghost" size="sm" icon={SkipForward} onClick={skipQuestion}>Skip</Button>
                        </div>
                    )}

                    {/* Evaluating */}
                    {isEvaluating && (
                        <motion.div className="vi-evaluating" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                            <Loader2 size={24} className="resume-page__spinner" />
                            <span>{transcript ? 'Evaluating your answer…' : 'Transcribing your answer…'}</span>
                        </motion.div>
                    )}

                    {/* Transcript */}
                    {transcript && !isEvaluating && (
                        <motion.div className="vi-transcript" initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }}>
                            <h5>Your Answer (transcribed):</h5>
                            <p>"{transcript}"</p>
                        </motion.div>
                    )}

                    {/* Evaluation result */}
                    {currentEval && (
                        <motion.div className="vi-eval" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                            <div className="vi-eval__top">
                                <ScoreRing score={currentEval.score || 0} />
                                <div>
                                    <span className="vi-eval__label">Answer Score</span>
                                    <span className="vi-eval__verdict" style={{
                                        color: (currentEval.score || 0) >= 80 ? '#10b981' : (currentEval.score || 0) >= 60 ? '#f59e0b' : '#ef4444'
                                    }}>
                                        {(currentEval.score || 0) >= 80 ? 'Excellent' : (currentEval.score || 0) >= 60 ? 'Good' : 'Needs Work'}
                                    </span>
                                </div>
                            </div>

                            {currentEval.strengths?.length > 0 && (
                                <div className="vi-eval__section">
                                    <h5><TrendingUp size={14} style={{ color: '#10b981' }} /> Strengths</h5>
                                    <ul>{currentEval.strengths.map((s, i) => <li key={i}><CheckCircle size={12} /> {s}</li>)}</ul>
                                </div>
                            )}
                            {currentEval.improvements?.length > 0 && (
                                <div className="vi-eval__section">
                                    <h5><Target size={14} style={{ color: '#f59e0b' }} /> Improvements</h5>
                                    <ul>{currentEval.improvements.map((s, i) => <li key={i}><AlertCircle size={12} /> {s}</li>)}</ul>
                                </div>
                            )}
                            {currentEval.sample_answer && (
                                <div className="vi-eval__section">
                                    <h5><BookOpen size={14} style={{ color: '#6366f1' }} /> Sample Answer</h5>
                                    <p className="vi-eval__sample">{currentEval.sample_answer}</p>
                                </div>
                            )}

                            <Button variant="primary" icon={ChevronRight} onClick={nextQuestion}>
                                {currentIdx + 1 >= questions.length ? 'View Summary' : 'Next Question'}
                            </Button>
                        </motion.div>
                    )}
                </Card>
            </div>
        );
    }

    // SUMMARY
    if (phase === PHASES.SUMMARY) {
        const allResults = [...results];
        // Include last result if we transitioned from nextQuestion
        const finalAvg = allResults.length > 0
            ? Math.round(allResults.reduce((s, r) => s + (r.evaluation?.score || 0), 0) / allResults.length)
            : 0;

        return (
            <div className="vi-summary">
                <Card variant="glass" className="vi-summary__main">
                    <h3><BarChart3 size={20} /> Interview Summary</h3>

                    <div className="vi-summary__score-area">
                        <ScoreRing score={finalAvg} size={100} />
                        <div>
                            <span className="vi-summary__avg-label">Average Score</span>
                            <span className="vi-summary__avg-text" style={{
                                color: finalAvg >= 80 ? '#10b981' : finalAvg >= 60 ? '#f59e0b' : '#ef4444'
                            }}>
                                {finalAvg >= 80 ? 'Excellent Performance!' : finalAvg >= 60 ? 'Good Performance' : 'Needs Improvement'}
                            </span>
                            <span className="vi-summary__count">{allResults.length} questions answered</span>
                        </div>
                    </div>

                    <div className="vi-summary__questions">
                        {allResults.map((r, i) => (
                            <div key={i} className="vi-summary__q-item">
                                <div className="vi-summary__q-header">
                                    <span className="vi-summary__q-num">Q{i + 1}</span>
                                    <span className="vi-summary__q-text">{r.question}</span>
                                    <span className="vi-summary__q-score" style={{
                                        color: (r.evaluation?.score || 0) >= 80 ? '#10b981' : (r.evaluation?.score || 0) >= 60 ? '#f59e0b' : '#ef4444'
                                    }}>{r.evaluation?.score || 0}%</span>
                                </div>
                                {r.transcript && r.transcript !== '(skipped)' && (
                                    <p className="vi-summary__q-answer">"{r.transcript}"</p>
                                )}
                                {r.transcript === '(skipped)' && (
                                    <p className="vi-summary__q-skipped">Skipped</p>
                                )}
                            </div>
                        ))}
                    </div>

                    <Button variant="primary" icon={Mic} onClick={() => { setPhase(PHASES.SETUP); setQuestions([]); setResults([]); setCurrentIdx(0); setCurrentEval(null); setTranscript(''); }} fullWidth>
                        Start New Interview
                    </Button>
                </Card>
            </div>
        );
    }

    return null;
}

/* ════════════════════════════════════════════════════════════ */
/*  MAIN VOICE STUDIO COMPONENT                               */
/* ════════════════════════════════════════════════════════════ */
export default function VoiceStudio() {
    const [tab, setTab] = useState('interview');

    return (
        <motion.div className="voice-page" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
            <h2>Voice Studio</h2>
            <p className="voice-page__desc">AI-powered voice interview practice, text-to-speech, and speech-to-text tools.</p>

            <Tabs active={tab} onChange={setTab} />

            <AnimatePresence mode="wait">
                {tab === 'tools' && (
                    <motion.div key="tools" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
                        <VoiceTools />
                    </motion.div>
                )}
                {tab === 'interview' && (
                    <motion.div key="interview" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
                        <AIInterview />
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
}
