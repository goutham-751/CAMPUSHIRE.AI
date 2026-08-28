import { useState, useRef, useEffect } from 'react';
import { Mic, Square, Target, Activity, Zap, CheckCircle, Upload, AlertCircle, Radio, Settings } from 'lucide-react';
import Button from '../../components/ui/Button/Button';
import Input from '../../components/ui/Input/Input';
import WaveformDisplay from '../../components/DataDisplay/WaveformDisplay';
import ScoreDial from '../../components/DataDisplay/ScoreDial';
import IntelligenceFeed from '../../components/Feedback/IntelligenceFeed';
import DualZone, { ZoneA, ZoneB } from '../../components/Layout/DualZone';
import TelemetryCard from '../../components/Cards/TelemetryCard';
import { useTelemetry } from '../../hooks/useTelemetry';
import { voiceApi, interviewApi, trackActivity } from '../../lib/api';
import styles from './VoiceStudio.module.css';

const PHASES = { SETUP: 'setup', RUNNING: 'running', SUMMARY: 'summary' };

export default function VoiceStudio() {
  const [phase, setPhase] = useState(PHASES.SETUP);
  const [file, setFile] = useState(null);
  const [jobTitle, setJobTitle] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [jobDesc, setJobDesc] = useState('');
  
  const [questions, setQuestions] = useState([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const [isRecording, setIsRecording] = useState(false);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [currentEval, setCurrentEval] = useState(null);
  const [transcript, setTranscript] = useState('');
  const [confidenceMetrics, setConfidenceMetrics] = useState(null);

  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const chunksRef = useRef([]);
  const fileRef = useRef(null);
  const mountedRef = useRef(true);
  const telemetry = useTelemetry(3000);
  const [micStatus, setMicStatus] = useState('Detecting...');

  useEffect(() => {
    mountedRef.current = true;
    navigator.mediaDevices.enumerateDevices()
      .then(devices => {
        const hasMic = devices.some(d => d.kind === 'audioinput');
        setMicStatus(hasMic ? 'Detected' : 'Not Found');
      })
      .catch(() => setMicStatus('Access Denied'));

    return () => {
      mountedRef.current = false;
      streamRef.current?.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
      try {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
          mediaRecorderRef.current.stop();
        }
      } catch { /* already stopped */ }
    };
  }, []);

  const handleDrop = (e) => {
    e.preventDefault();
    const f = e.dataTransfer?.files?.[0];
    if (f) setFile(f);
  };

  const handleStart = async () => {
    if (!file || !jobDesc) return;
    setLoading(true);
    setError(null);
    try {
      const data = await interviewApi.generateQuestions(file, jobTitle, companyName, jobDesc, 3);
      setQuestions(data.questions || []);
      setPhase(PHASES.RUNNING);
      trackActivity({ type: 'voice_interview_start', text: 'Voice interview started', icon: 'Mic' });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const mimeType = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4']
        .find((type) => window.MediaRecorder && MediaRecorder.isTypeSupported(type)) || '';
      const recorder = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data); };
      recorder.start();
      mediaRecorderRef.current = recorder;
      setIsRecording(true);
    } catch (err) {
      streamRef.current?.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
      setError('Microphone access denied.');
    }
  };

  const stopRecording = async () => {
    if (!mediaRecorderRef.current) return;
    return new Promise((resolve) => {
      mediaRecorderRef.current.onstop = async () => {
        streamRef.current?.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
        if (!mountedRef.current) {
          resolve();
          return;
        }
        const blobType = mediaRecorderRef.current?.mimeType || 'audio/webm';
        const blob = new Blob(chunksRef.current, { type: blobType });
        setIsRecording(false);
        setIsEvaluating(true);
        try {
          const ext = blobType.includes('mp4') ? 'mp4' : 'webm';
          const audioFile = new File([blob], `answer.${ext}`, { type: blobType });
          const sttResult = await voiceApi.stt(audioFile);
          const text = sttResult?.text || '';
          setTranscript(text);
          if (sttResult?.confidence_metrics) {
            setConfidenceMetrics(sttResult.confidence_metrics);
          }

          if (text) {
            const qText = typeof questions[currentIdx] === 'string' ? questions[currentIdx] : questions[currentIdx].question;
            const evalData = await interviewApi.panelEvaluate(qText, text, jobTitle);
            setCurrentEval(evalData);
          } else {
            setCurrentEval({ aggregated_score: 0, overall_verdict: 'No Answer' });
          }
        } catch (e) {
          setCurrentEval({ aggregated_score: 0, overall_verdict: 'Error', final_recommendation: e.message });
        } finally {
          if (mountedRef.current) setIsEvaluating(false);
          resolve();
        }
      };
      mediaRecorderRef.current.stop();
    });
  };

  const nextQuestion = () => {
    const q = questions[currentIdx];
    setResults(prev => [...prev, { question: typeof q === 'string' ? q : q.question, transcript, evaluation: currentEval, confidence: confidenceMetrics }]);
    setCurrentEval(null);
    setTranscript('');
    setConfidenceMetrics(null);

    if (currentIdx + 1 >= questions.length) {
      setPhase(PHASES.SUMMARY);
      trackActivity({ type: 'voice_interview_complete', text: 'Voice interview completed', icon: 'Award' });
    } else {
      setCurrentIdx(currentIdx + 1);
    }
  };

  const currentQ = questions[currentIdx];
  const qText = currentQ ? (typeof currentQ === 'string' ? currentQ : currentQ.question || '') : '';

  return (
    <DualZone>
      <ZoneA>
        <div className={styles.header}>
          <h2>Voice Studio</h2>
          <p>Acoustic intelligence and verbal analysis matrix.</p>
        </div>

        {phase === PHASES.SETUP && (
          <div className={styles.setupPanel}>
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
                  <span>Upload resume for context baseline</span>
                </div>
              )}
            </div>

            <div className={styles.formGroup}>
              <Input label="Target Role" placeholder="e.g. Senior Backend Engineer" value={jobTitle} onChange={(e) => setJobTitle(e.target.value)} />
              <Input label="Company Name" placeholder="e.g. Meta" value={companyName} onChange={(e) => setCompanyName(e.target.value)} />
              <Input label="Job Description" placeholder="Paste full job description..." value={jobDesc} onChange={(e) => setJobDesc(e.target.value)} isTextarea rows={5} />
            </div>

            <div className={styles.actions}>
              <Button variant="primary" disabled={!file || !jobDesc || loading} onClick={handleStart}>
                {loading ? 'Initializing...' : 'Engage Voice Protocol'}
              </Button>
            </div>
            {error && <div className={styles.error}><AlertCircle size={16}/> {error}</div>}
          </div>
        )}

        {phase === PHASES.RUNNING && (
          <div className={styles.runningPhase}>
            <div className={styles.qPanel}>
              <div className={styles.qHeader}>
                <span className={styles.qNum}>Question {currentIdx + 1}/{questions.length}</span>
              </div>
              <h3 className={styles.questionText}>{qText}</h3>
            </div>

            <div className={styles.waveformArea}>
              <WaveformDisplay state={isRecording ? 'user' : 'idle'} amplitude={isRecording ? 1 : 0.2} />
            </div>

            {!currentEval && !isEvaluating && (
              <div className={styles.controls}>
                {!isRecording ? (
                  <Button variant="primary" icon={Mic} onClick={startRecording}>
                    Begin Transmission
                  </Button>
                ) : (
                  <Button variant="danger" icon={Square} onClick={stopRecording}>
                    Terminate Transmission
                  </Button>
                )}
              </div>
            )}

            {isEvaluating && (
              <div className={styles.evaluatingState}>
                <IntelligenceFeed text={`> PROCESSING AUDIO STREAM...
> EXTRACTING TRANSCRIPT...
> ANALYZING VOCAL CONFIDENCE METRICS...
> EVALUATING RESPONSE QUALITY...`} speed={20} />
              </div>
            )}

            {currentEval && (
              <div className={styles.evalPanel}>
                <div className={styles.evalTop}>
                  <ScoreDial score={currentEval.aggregated_score || 0} label="Response Match" size={120} />
                  <div className={styles.evalFeedback}>
                    <h4>Panel Verdict:</h4>
                    <p>{currentEval.overall_verdict}</p>
                  </div>
                </div>

                <div className={styles.actionsRight}>
                  <Button variant="primary" onClick={nextQuestion}>
                    {currentIdx + 1 >= questions.length ? 'Finalize Report' : 'Next Transmission'}
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}

        {phase === PHASES.SUMMARY && (
          <div className={styles.summaryPhase}>
            <h3>Session Complete</h3>
            <Button variant="ghost" onClick={() => { setPhase(PHASES.SETUP); setQuestions([]); setResults([]); setCurrentIdx(0); }}>
              Initiate New Session
            </Button>
          </div>
        )}
      </ZoneA>

      <ZoneB>
        {phase === PHASES.SETUP && (
          <>
            <TelemetryCard title="Hardware Telemetry" icon={Settings} status={micStatus === 'Detected' ? 'nominal' : 'critical'}>
              <div className={styles.telemetryGrid}>
                <div className={styles.tItem}>
                  <span>Microphone array</span>
                  <strong className={micStatus === 'Detected' ? styles.textNeon : styles.textCrimson}>{micStatus}</strong>
                </div>
                <div className={styles.tItem}>
                  <span>Signal Latency</span>
                  <strong>{telemetry.api_latency_ms}ms</strong>
                </div>
              </div>
            </TelemetryCard>
            <TelemetryCard title="Acoustic Intelligence" icon={Radio} status="warning">
              <div style={{ color: 'var(--color-text-secondary)', fontStyle: 'italic' }}>
                Waiting for protocol initiation. Speech-to-Text models and tonal analysis agents are standing by.
              </div>
            </TelemetryCard>
          </>
        )}

        {phase === PHASES.RUNNING && (
          <>
            <TelemetryCard title="Signal Status" icon={Radio} status={isRecording ? 'active' : 'nominal'}>
              <div className={styles.telemetryGrid}>
                <div className={styles.tItem}>
                  <span>Carrier Frequency</span>
                  <strong className={isRecording ? styles.textPlasma : ''}>{isRecording ? 'Active TX' : 'RX Idle'}</strong>
                </div>
                <div className={styles.tItem}>
                  <span>Noise Floor</span>
                  <strong>-68 dBm</strong>
                </div>
              </div>
            </TelemetryCard>

            {(transcript || isEvaluating) && (
              <TelemetryCard title="Live Transcript Feed" icon={Activity} status="nominal">
                <div className={styles.transcriptLog}>
                  {transcript ? `"${transcript}"` : <span style={{ color: 'var(--color-text-tertiary)' }}>Decoding...</span>}
                </div>
              </TelemetryCard>
            )}

            {confidenceMetrics && confidenceMetrics.success && (
              <TelemetryCard title="Confidence Metrics" icon={Zap} status="nominal">
                <div className={styles.telemetryGrid}>
                  <div className={styles.tItem}>
                    <span>Pacing (WPM)</span>
                    <strong className={styles.textNeon}>{Math.round(confidenceMetrics.wpm)}</strong>
                  </div>
                  <div className={styles.tItem}>
                    <span>Filler Words</span>
                    <strong className={confidenceMetrics.filler_count > 5 ? styles.textCrimson : ''}>{confidenceMetrics.filler_count}</strong>
                  </div>
                  <div className={styles.tItem}>
                    <span>Pause Ratio</span>
                    <strong>{(confidenceMetrics.pause_ratio * 100).toFixed(0)}%</strong>
                  </div>
                </div>
              </TelemetryCard>
            )}
          </>
        )}
      </ZoneB>
    </DualZone>
  );
}
