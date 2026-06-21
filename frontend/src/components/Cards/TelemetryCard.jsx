import styles from './TelemetryCard.module.css';

export default function TelemetryCard({ title, icon: Icon, children, status = 'nominal' }) {
  return (
    <div className={`${styles.card} ${styles[status]}`}>
      <div className={styles.header}>
        <div className={styles.titleArea}>
          {Icon && <Icon size={14} className={styles.icon} />}
          <span className={styles.title}>{title}</span>
        </div>
        <div className={styles.statusIndicator} />
      </div>
      <div className={styles.content}>
        {children}
      </div>
    </div>
  );
}
