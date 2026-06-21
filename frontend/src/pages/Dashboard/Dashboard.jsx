import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Activity, Clock, Target } from 'lucide-react';
import { getHistory } from '../../lib/api';
import DualZone, { ZoneA, ZoneB } from '../../components/Layout/DualZone';
import TelemetryCard from '../../components/Cards/TelemetryCard';
import { useTelemetry } from '../../hooks/useTelemetry';
import styles from './Dashboard.module.css';

export default function Dashboard() {
  const navigate = useNavigate();
  const history = useMemo(() => getHistory(), []);
  const telemetry = useTelemetry(3000);

  const atsScores = history.filter(h => h.type === 'ats_score' && h.score != null);
  const lastAts = atsScores.length > 0 ? Math.round(atsScores[0].score) : null;
  
  return (
    <DualZone>
      <ZoneA>
        <div className={styles.greetingZone}>
          <h2 className={styles.greeting}>Good evening.</h2>
          <p className={styles.greetingSub}>Your AI intelligence system is ready.</p>
        </div>

        <div className={styles.missionSurface}>
          <div 
            className={`${styles.missionTile} ${styles.tileResume}`}
            onClick={() => navigate('/app/resume')}
          >
            <div className={styles.tileContent}>
              {lastAts ? (
                <div className={styles.tileScore}>
                  <span className={styles.scoreNum}>{lastAts}</span>
                  <span className={styles.scoreMax}>/100</span>
                </div>
              ) : (
                <div className={styles.tileIcon}>◎</div>
              )}
              <div className={styles.tileAction}>Analyze Resume →</div>
            </div>
          </div>

          <div 
            className={`${styles.missionTile} ${styles.tileInterview}`}
            onClick={() => navigate('/app/interview')}
          >
            <div className={styles.tileContent}>
              <div className={styles.agentAvatars}>
                <div className={`${styles.avatarGlow} ${styles.neon}`}></div>
                <div className={`${styles.avatarGlow} ${styles.plasma}`}></div>
                <div className={`${styles.avatarGlow} ${styles.gold}`}></div>
              </div>
              <div className={styles.tileAction}>Practice Interview →</div>
            </div>
          </div>

          <div 
            className={`${styles.missionTile} ${styles.tileVoice}`}
            onClick={() => navigate('/app/voice')}
          >
            <div className={styles.tileContent}>
              <div className={styles.miniWaveform}>
                <div className={styles.waveBar} style={{ height: '40%' }}></div>
                <div className={styles.waveBar} style={{ height: '80%' }}></div>
                <div className={styles.waveBar} style={{ height: '60%' }}></div>
                <div className={styles.waveBar} style={{ height: '100%' }}></div>
                <div className={styles.waveBar} style={{ height: '50%' }}></div>
              </div>
              <div className={styles.tileAction}>Speak →</div>
            </div>
          </div>
        </div>
      </ZoneA>

      <ZoneB>
        <TelemetryCard title="System Health" icon={Activity} status={telemetry.status === 'Active' ? 'nominal' : 'warning'}>
          <div className={styles.telemetryGrid}>
            <div className={styles.tItem}>
              <span>API Latency</span>
              <strong className={styles.textNeon}>{telemetry.api_latency_ms}ms</strong>
            </div>
            <div className={styles.tItem}>
              <span>Agent Status</span>
              <strong className={styles.textNeon}>{telemetry.status}</strong>
            </div>
            <div className={styles.tItem}>
              <span>Token Usage</span>
              <strong>{telemetry.total_tokens >= 1000 ? (telemetry.total_tokens / 1000).toFixed(1) + 'k' : telemetry.total_tokens}</strong>
            </div>
            <div className={styles.tItem}>
              <span>Session Uptime</span>
              <strong>{telemetry.uptime}</strong>
            </div>
          </div>
        </TelemetryCard>

        <TelemetryCard title="Activity Timeline" icon={Clock} status="nominal">
          <div className={styles.timeline}>
            {history.slice(0, 5).map((h, i) => (
              <div key={i} className={styles.timelineItem}>
                <div className={styles.timelineDot}></div>
                <div className={styles.timelineContent}>
                  <div className={styles.tTime}>{new Date(h.timestamp).toLocaleTimeString()}</div>
                  <div className={styles.tAction}>{h.text || h.type}</div>
                </div>
              </div>
            ))}
            {history.length === 0 && (
              <div className={styles.timelineItem}>
                <div className={styles.timelineDot}></div>
                <div className={styles.timelineContent}>
                  <div className={styles.tAction}>System initialized.</div>
                </div>
              </div>
            )}
          </div>
        </TelemetryCard>

        <TelemetryCard title="Global Skill Radar" icon={Target} status="active">
          <div className={styles.radarContainer}>
            <div className={styles.radarRings}>
              <div className={styles.ring}></div>
              <div className={styles.ring}></div>
              <div className={styles.ring}></div>
              <div className={styles.radarLine} style={{ transform: 'rotate(0deg)' }}></div>
              <div className={styles.radarLine} style={{ transform: 'rotate(60deg)' }}></div>
              <div className={styles.radarLine} style={{ transform: 'rotate(120deg)' }}></div>
              <div className={styles.radarSweep}></div>
            </div>
          </div>
        </TelemetryCard>
      </ZoneB>
    </DualZone>
  );
}
