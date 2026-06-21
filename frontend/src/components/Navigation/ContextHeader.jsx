import { useLocation } from 'react-router-dom';
import styles from './ContextHeader.module.css';

const PAGE_TITLES = {
    '/app': 'Command Hub',
    '/app/resume': 'Resume Intelligence',
    '/app/interview': 'Interview Committee',
    '/app/voice': 'Voice Studio',
    '/app/settings': 'System Settings',
};

export default function ContextHeader({ aiActive = false }) {
  const location = useLocation();
  const title = PAGE_TITLES[location.pathname] || 'Workspace';

  return (
    <header className={styles.header}>
      <h1 className={styles.title}>{title}</h1>
      <div className={styles.aiStatus}>
        <div className={`${styles.statusDot} ${aiActive ? styles.active : ''}`} />
        <span className={styles.statusText}>{aiActive ? 'AI Processing' : 'AI Ready'}</span>
      </div>
    </header>
  );
}
