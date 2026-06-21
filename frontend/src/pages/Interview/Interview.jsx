import { useState, useRef, useEffect, useCallback } from 'react';
import { Upload, MessageSquare, Users, CheckCircle, AlertCircle, Target, TrendingUp, Activity, Clock, Shield } from 'lucide-react';
import Button from '../../components/ui/Button/Button';
import Input from '../../components/ui/Input/Input';
import AgentCard from '../../components/Cards/AgentCard';
import IntelligenceFeed from '../../components/Feedback/IntelligenceFeed';
import DualZone, { ZoneA, ZoneB } from '../../components/Layout/DualZone';
import TelemetryCard from '../../components/Cards/TelemetryCard';
import { interviewApi, trackActivity } from '../../lib/api';
import styles from './Interview.module.css';

export default function Interview() {
  const [phase, setPhase] = useState('SETUP');
  const [file, setFile] = useState(null);
  const [jobTitle, setJobTitle] = useState('');
  const [jobDesc, setJobDesc] = useState('');
  const [questions, setQuestions] = useState(null);
  const [activeQIndex, setActiveQIndex] = useState(0);
  const [feedComplete, setFeedComplete] = useState(false);
  const [answer, setAnswer] = useState('');
  const [evalResult, setEvalResult] = useState(null);
  const [evalLoading, setEvalLoading] = useState(false);
  const [error, setError] = useState(null);
  const fileRef = useRef(null);

  const handleDrop = (e) => {
    e.preventDefault();
    const f = e.dataTransfer?.files?.[0];
    if (f) setFile(f);
  };

  useEffect(() => {
    if (phase === 'PROCESSING' && questions && feedComplete) {
      setPhase('INTERVIEW');
    }
  }, [phase, questions, feedComplete]);

  const handleFeedComplete = useCallback(() => {
    setFeedComplete(true);
  }, []);

  const handleGenerate = async () => {
    if (!file || !jobDesc) return;
    setPhase('PROCESSING');
    setFeedComplete(false);
    setError(null);
    try {
      const data = await interviewApi.generateQuestions(file, jobTitle, '', jobDesc);
      setQuestions(data.questions || []);
      trackActivity({ type: 'interview_questions', text: `Generated ${(data.questions || []).length} interview questions`, icon: 'MessageSquare' });
    } catch (err) {
      setError(err.message);
      setPhase('SETUP');
    }
  };

  const handleEvaluate = async () => {
    if (!questions || !answer) return;
    setEvalLoading(true);
    setEvalResult(null);
    const activeQ = questions[activeQIndex];
    try {
      const data = await interviewApi.panelEvaluate(activeQ.question || activeQ, answer, jobTitle);
      setEvalResult(data);
      trackActivity({ type: 'panel_evaluated', text: `Panel score: ${data.aggregated_score || 0}%`, score: data.aggregated_score, icon: 'TrendingUp' });
    } catch (err) {
      setError(err.message);
    } finally {
      setEvalLoading(false);
    }
  };

  const activeQuestion = questions?.[activeQIndex];
  const qText = activeQuestion ? (typeof activeQuestion === 'string' ? activeQuestion : activeQuestion.question || activeQuestion.text) : '';

  return (
    <DualZone>
      <ZoneA>
        <div className={styles.header}>
          <h2>Interview Committee</h2>
          <p>Defend your qualifications against a panel of autonomous AI agents.</p>
        </div>

        {phase === 'SETUP' && (
          <div className={styles.setupGrid}>
            <div className={styles.panelConfig}>
              <h3 className={styles.sectionTitle}>Committee Assembly</h3>
              <div className={styles.agentGrid}>
                <AgentCard role="Technical Lead" title="System Architecture & Code Quality" glowColor="neon" />
                <AgentCard role="HR Manager" title="Behavioral & Cultural Fit" glowColor="plasma" />
                <AgentCard role="Domain Expert" title="Industry Standards & Strategy" glowColor="gold" />
              </div>
            </div>

            <div className={styles.formPanel}>
              <div 
                className={`${styles.dropzone} ${file ? styles.hasFile : ''}`}
                onClick={() => fileRef.current?.click()}
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleDrop}
              >
                <input ref={fileRef} type="file" accept=".pdf,.docx,.txt" hidden onChange={(e) => setFile(e.target.files?.[0] || null)} />
                {file ? (
                  <div className={styles.fileStatus}>
                    <CheckCircle size={24} className={styles.successIcon} />
                    <span>{file.name}</span>
                  </div>
                ) : (
                  <div className={styles.filePrompt}>
                    <Upload size={24} />
                    <span>Upload your resume for context</span>
                  </div>
                )}
              </div>

              <div className={styles.formGroup}>
                <Input label="Target Role" placeholder="e.g. Senior Backend Engineer" value={jobTitle} onChange={(e) => setJobTitle(e.target.value)} />
                <Input label="Job Description" placeholder="Paste full job description..." value={jobDesc} onChange={(e) => setJobDesc(e.target.value)} isTextarea rows={5} />
              </div>

              <div className={styles.actions}>
                <Button variant="primary" disabled={!file || !jobDesc} onClick={handleGenerate}>
                  Initialize Committee
                </Button>
              </div>
              {error && <div className={styles.error}><AlertCircle size={16}/> {error}</div>}
            </div>
          </div>
        )}

        {phase === 'PROCESSING' && (
          <div className={styles.processingPhase}>
            <div className={styles.feedWrapper}>
              <IntelligenceFeed 
                text={`> BOOTING COMMITTEE AGENTS...
> INGESTING CANDIDATE CONTEXT...
> ANALYZING ROLE REQUIREMENTS...
> GENERATING TARGETED INQUIRY VECTORS...
> COMMITTEE READY.`}
                speed={20}
                onComplete={handleFeedComplete}
              />
            </div>
          </div>
        )}

        {phase === 'INTERVIEW' && questions && (
          <div className={styles.interviewPhase}>
            <div className={styles.questionPanel}>
              <div className={styles.qHeader}>
                <span className={styles.qNum}>Question {activeQIndex + 1}/{questions.length}</span>
              </div>
              <h3 className={styles.questionText}>{qText}</h3>

              <div className={styles.answerArea}>
                <Input 
                  isTextarea 
                  rows={6} 
                  placeholder="Compose your response here..." 
                  value={answer} 
                  onChange={(e) => setAnswer(e.target.value)} 
                />
                <div className={styles.answerActions}>
                  <Button variant="primary" onClick={handleEvaluate} disabled={!answer || evalLoading} className={styles.evalBtn}>
                    {evalLoading ? 'Evaluating...' : 'Submit to Committee'}
                  </Button>
                </div>
              </div>
            </div>

            {evalResult && (
              <div className={styles.evalResults}>
                <div className={styles.verdictBanner}>
                  <span className={styles.verdictLabel}>Panel Verdict:</span>
                  <span className={styles.verdictText}>{evalResult.overall_verdict}</span>
                </div>
                
                <div className={styles.agentFeedbackGrid}>
                  {(evalResult.agents || []).map((agent, i) => (
                    <div key={i} className={styles.feedbackCard} style={{ borderColor: agent.agent_color }}>
                      <div className={styles.feedbackHeader}>
                        <span className={styles.agentEmoji}>{agent.agent_emoji}</span>
                        <div className={styles.agentInfo}>
                          <strong>{agent.agent_name}</strong>
                          <span>{agent.agent_role}</span>
                        </div>
                        <div className={styles.agentScore}>{agent.score}/100</div>
                      </div>
                      <p className={styles.feedbackVerdict}>{agent.verdict}</p>
                      {agent.key_observation && (
                        <p className={styles.feedbackObservation}>{agent.key_observation}</p>
                      )}
                    </div>
                  ))}
                </div>

                <div className={styles.nextActions}>
                  <Button 
                    variant="ghost" 
                    onClick={() => {
                      if (activeQIndex < questions.length - 1) {
                        setActiveQIndex(activeQIndex + 1);
                        setAnswer('');
                        setEvalResult(null);
                      }
                    }}
                    disabled={activeQIndex >= questions.length - 1}
                  >
                    Next Question →
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}
      </ZoneA>

      <ZoneB>
        {phase === 'SETUP' && (
          <>
            <TelemetryCard title="Committee Readiness" icon={Users} status="nominal">
              <div style={{ color: 'var(--color-text-secondary)', display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Tech Lead (Neon)</span><span style={{ color: 'var(--color-neon)' }}>Ready</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>HR Manager (Plasma)</span><span style={{ color: 'var(--color-plasma)' }}>Ready</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Domain Expert (Gold)</span><span style={{ color: 'var(--color-gold)' }}>Ready</span>
                </div>
              </div>
            </TelemetryCard>
            <TelemetryCard title="Context Ingestion" icon={Target} status="warning">
              <div style={{ color: 'var(--color-text-secondary)', fontStyle: 'italic' }}>
                Awaiting context documents. Resume and Job Description required to calibrate question vectors.
              </div>
            </TelemetryCard>
          </>
        )}

        {phase === 'PROCESSING' && (
          <TelemetryCard title="Generation Matrix" icon={Activity} status="active">
            <div style={{ color: 'var(--color-text-primary)' }}>
              Synthesizing domain-specific interrogations...
            </div>
          </TelemetryCard>
        )}

        {phase === 'INTERVIEW' && questions && (
          <>
            <TelemetryCard title="Pacing & Confidence" icon={Activity} status={evalResult ? 'nominal' : 'active'}>
              <div className={styles.telemetryGrid}>
                <div className={styles.tItem}>
                  <span>Answer Length</span>
                  <strong className={styles.textNeon}>{answer.length > 0 ? answer.split(' ').length : 0} words</strong>
                </div>
                <div className={styles.tItem}>
                  <span>Input Status</span>
                  <strong style={{ color: answer ? 'var(--color-neon)' : 'var(--color-text-tertiary)' }}>{answer ? 'Drafting' : 'Idle'}</strong>
                </div>
                <div className={styles.tItem}>
                  <span>Time Elapsed</span>
                  <strong>--:--</strong>
                </div>
              </div>
            </TelemetryCard>

            <TelemetryCard title="Session History" icon={Clock} status="nominal">
              <div className={styles.historyList}>
                {questions.map((q, i) => (
                  <div key={i} className={styles.historyItem}>
                    <div className={styles.hStatus} style={{ 
                      backgroundColor: i < activeQIndex ? 'var(--color-gold)' : (i === activeQIndex ? 'var(--color-neon)' : 'transparent'),
                      border: i === activeQIndex ? 'none' : '1px solid var(--color-border)'
                    }}></div>
                    <span style={{ color: i === activeQIndex ? 'var(--color-text-primary)' : 'var(--color-text-tertiary)' }}>
                      Question {i + 1}
                    </span>
                  </div>
                ))}
              </div>
            </TelemetryCard>

            <TelemetryCard title="Live Agent Coaching" icon={Shield} status={evalResult ? 'nominal' : 'warning'}>
              {evalResult ? (
                <div style={{ color: 'var(--color-text-primary)', fontSize: '13px' }}>
                  Panel has reached consensus. Review feedback and prepare for the next inquiry.
                </div>
              ) : (
                <div style={{ color: 'var(--color-text-secondary)', fontStyle: 'italic', fontSize: '13px' }}>
                  {answer.length > 50 
                    ? "Good substance. Ensure you map this directly back to the job description." 
                    : "Listening... Use the STAR method (Situation, Task, Action, Result) to structure your response."}
                </div>
              )}
            </TelemetryCard>
          </>
        )}
      </ZoneB>
    </DualZone>
  );
}
