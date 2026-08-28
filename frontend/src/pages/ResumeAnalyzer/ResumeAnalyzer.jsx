import { useState, useRef, useEffect, useCallback } from 'react';
import { Upload, FileText, CheckCircle, AlertCircle, TrendingUp, Search, Zap, Layers, Target, Lightbulb, Activity, BarChart2 } from 'lucide-react';
import Button from '../../components/ui/Button/Button';
import Input from '../../components/ui/Input/Input';
import ScoreDial from '../../components/DataDisplay/ScoreDial';
import IntelligenceFeed from '../../components/Feedback/IntelligenceFeed';
import DualZone, { ZoneA, ZoneB } from '../../components/Layout/DualZone';
import TelemetryCard from '../../components/Cards/TelemetryCard';
import { useTelemetry } from '../../hooks/useTelemetry';
import { resumeApi, trackActivity } from '../../lib/api';
import styles from './ResumeAnalyzer.module.css';

export default function ResumeAnalyzer() {
  const [phase, setPhase] = useState('UPLOAD');
  const [file, setFile] = useState(null);
  const [jobTitle, setJobTitle] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [jobDesc, setJobDesc] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [feedComplete, setFeedComplete] = useState(false);
  const fileRef = useRef(null);
  const telemetry = useTelemetry(3000);

  const handleDrop = (e) => {
    e.preventDefault();
    const f = e.dataTransfer?.files?.[0];
    if (f) setFile(f);
  };

  useEffect(() => {
    if (phase === 'PROCESSING' && result && feedComplete) {
      setPhase('RESULTS');
    }
  }, [phase, result, feedComplete]);

  const handleFeedComplete = useCallback(() => {
    setFeedComplete(true);
  }, []);

  const startAnalysis = async () => {
    if (!file) return;
    if (!jobDesc || jobDesc.trim().length < 10) {
      setError('A valid Job Description is required (min 10 characters).');
      return;
    }
    setPhase('PROCESSING');
    setFeedComplete(false);
    setError(null);
    try {
      const data = await resumeApi.score(file, jobTitle, companyName, jobDesc);
      trackActivity({ type: 'ats_score', text: `ATS Score: ${data.overall_score || 0}%`, score: data.overall_score, scores: data.scores, icon: 'BarChart3' });
      setResult(data);
    } catch (err) {
      setError(err.message);
      setPhase('UPLOAD');
    }
  };

  return (
    <DualZone>
      <ZoneA>
        {(phase === 'UPLOAD' || phase === 'PROCESSING') && (
          <div className={styles.uploadPhase} style={phase === 'PROCESSING' ? { opacity: 0.5, pointerEvents: 'none' } : {}}>
            <div className={styles.header}>
              <h2>Resume Intelligence</h2>
              <p>Upload your document for deep structural analysis.</p>
              <span className={styles.engineBadge}>Deterministic ATS</span>
            </div>

            <div 
              className={`${styles.dropzone} ${file ? styles.hasFile : ''}`}
              onClick={() => fileRef.current?.click()}
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
            >
              <input ref={fileRef} type="file" accept=".pdf,.docx,.txt" hidden onChange={(e) => setFile(e.target.files?.[0] || null)} />
              {file ? (
                <div className={styles.fileStatus}>
                  <CheckCircle size={32} className={styles.successIcon} />
                  <span className={styles.filename}>{file.name}</span>
                  <span className={styles.filesize}>{(file.size / 1024).toFixed(1)} KB</span>
                </div>
              ) : (
                <div className={styles.filePrompt}>
                  <Upload size={32} />
                  <span>Drop document here or click to browse</span>
                </div>
              )}
            </div>

            <div className={styles.formGroup}>
              <Input 
                label="Target Role" 
                placeholder="e.g. Senior Frontend Engineer" 
                value={jobTitle} 
                onChange={(e) => setJobTitle(e.target.value)} 
              />
              <Input 
                label="Company Name" 
                placeholder="e.g. Google" 
                value={companyName} 
                onChange={(e) => setCompanyName(e.target.value)} 
              />
              <Input 
                label="Job Description" 
                placeholder="Paste the full job description here..." 
                value={jobDesc} 
                onChange={(e) => setJobDesc(e.target.value)} 
                isTextarea 
                rows={6}
              />
            </div>

            <div className={styles.actions}>
              <Button variant="primary" disabled={!file || phase === 'PROCESSING'} onClick={startAnalysis}>
                {phase === 'PROCESSING' ? 'Analyzing...' : 'Commence Analysis'}
              </Button>
            </div>
            
            {error && <div className={styles.error}><AlertCircle size={16}/> {error}</div>}
          </div>
        )}



        {phase === 'RESULTS' && result && (
          <div className={styles.resultsPhase}>
            <div className={styles.resultsHeader}>
              <div>
                <h2>Analysis Complete</h2>
                <span className={styles.engineBadge}>
                  {result.scoring_engine === 'deterministic_v1' ? 'Deterministic ATS' : (result.scoring_engine || 'Deterministic ATS')}
                </span>
              </div>
              <Button variant="ghost" onClick={() => { setPhase('UPLOAD'); setFile(null); setResult(null); }}>
                New Analysis
              </Button>
            </div>

            <div className={styles.resultsGrid}>
              <div className={styles.detailsPanel}>
                {result.strengths?.length > 0 && (
                  <div className={styles.detailSection}>
                    <h4 className={styles.sectionTitle}><TrendingUp size={16} /> Key Strengths</h4>
                    <ul className={styles.list}>
                      {result.strengths.map((s, i) => <li key={i}>{s}</li>)}
                    </ul>
                  </div>
                )}

                {result.missing_keywords?.length > 0 && (
                  <div className={styles.detailSection}>
                    <h4 className={styles.sectionTitle}><Target size={16} /> Missing Competencies</h4>
                    <div className={styles.tags}>
                      {result.missing_keywords.map((kw, i) => <span key={i} className={styles.tag}>{kw}</span>)}
                    </div>
                  </div>
                )}

                {result.ats_optimization_tips?.length > 0 && (
                  <div className={styles.detailSection}>
                    <h4 className={styles.sectionTitle}><Zap size={16} /> Optimization Directives</h4>
                    <ul className={styles.list}>
                      {result.ats_optimization_tips.map((t, i) => <li key={i}>{t}</li>)}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </ZoneA>

      <ZoneB>
        {phase === 'UPLOAD' && (
          <>
            <TelemetryCard title="System Readiness" icon={Activity} status={telemetry.status === 'Active' ? 'nominal' : 'warning'}>
              <div style={{ color: 'var(--color-text-secondary)' }}>
                {telemetry.status === 'Active' 
                  ? "Waiting for document ingestion. Deterministic ATS evaluates skills, experience, education, TF-IDF keywords, formatting, and achievements — scores are computed in code, not by an LLM." 
                  : "System degraded. API Latency is abnormally high."}
              </div>
            </TelemetryCard>
            <TelemetryCard title="Parser Telemetry" icon={Search} status="warning">
              <div style={{ color: 'var(--color-text-secondary)', fontStyle: 'italic' }}>
                No active session...
              </div>
            </TelemetryCard>
          </>
        )}

        {phase === 'PROCESSING' && (
          <>
            <TelemetryCard title="Analysis Engine" icon={Activity} status="active">
              <div style={{ marginTop: 'var(--spacing-md)' }}>
                <IntelligenceFeed 
                  text={`> INITIALIZING RESUME ANALYSIS PROTOCOL...
> EXTRACTING STRUCTURAL TOKENS...
> MAPPING TO COMPETENCY MATRIX...
> CROSS-REFERENCING TARGET ROLE DESCRIPTION...
> IDENTIFYING CRITICAL GAPS...
> COMPILING OPTIMIZATION VECTORS...
> ANALYSIS COMPLETE.`}
                  speed={15}
                  onComplete={handleFeedComplete}
                />
              </div>
            </TelemetryCard>
          </>
        )}

        {phase === 'RESULTS' && result && (
          <>
            <TelemetryCard title="Global Match Score" icon={BarChart2} status="nominal">
              <div className={styles.scoreDialWrapper}>
                <ScoreDial score={result.overall_score || 0} max={100} label="" color="gold" size={160} />
              </div>
            </TelemetryCard>

            <TelemetryCard title="Telemetry Breakdown" icon={Layers} status="nominal">
              <div className={styles.telemetryBreakdown}>
                <div className={styles.tRow}>
                  <span>Skills Match</span>
                  <span className={styles.tVal}>{result.scores?.skills_match || 0}/100</span>
                </div>
                <div className={styles.tRow}>
                  <span>Experience</span>
                  <span className={styles.tVal}>{result.scores?.experience_level || 0}/100</span>
                </div>
                <div className={styles.tRow}>
                  <span>Keyword Density</span>
                  <span className={styles.tVal}>{result.scores?.keyword_density || 0}/100</span>
                </div>
                <div className={styles.tRow}>
                  <span>Formatting</span>
                  <span className={styles.tVal}>{result.scores?.formatting || 0}/100</span>
                </div>
              </div>
            </TelemetryCard>

            {result.missing_keywords && result.missing_keywords.length > 0 && (
              <TelemetryCard title="Critical Gaps" icon={AlertCircle} status="critical">
                <div className={styles.gapList}>
                  {result.missing_keywords.slice(0, 3).map((kw, i) => (
                    <div key={i} className={styles.gapItem}>{kw}</div>
                  ))}
                </div>
              </TelemetryCard>
            )}
          </>
        )}
      </ZoneB>
    </DualZone>
  );
}
