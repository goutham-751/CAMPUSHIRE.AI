import styles from './DualZone.module.css';

export default function DualZone({ children }) {
  return (
    <div className={styles.dualZone}>
      {children}
    </div>
  );
}

export function ZoneA({ children }) {
  return <div className={styles.zoneA}>{children}</div>;
}

export function ZoneB({ children }) {
  return <div className={styles.zoneB}>{children}</div>;
}
