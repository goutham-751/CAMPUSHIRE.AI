import styles from './Badge.module.css';

export function BadgeAI() {
  return (
    <span className={styles.badgeAi}>
      AI-Powered
    </span>
  );
}

export function BadgeStatus({ status = 'info', children }) {
  const statusClass = styles[`status_${status}`] || styles.status_info;
  return (
    <span className={`${styles.badgeStatus} ${statusClass}`}>
      {children}
    </span>
  );
}
