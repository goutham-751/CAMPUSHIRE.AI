import styles from './AmbientField.module.css';

export default function AmbientField({ children }) {
  return (
    <div className={styles.ambientField}>
      <div className={styles.noiseOverlay}></div>
      <div className={`${styles.orb} ${styles.orb1}`}></div>
      <div className={`${styles.orb} ${styles.orb2}`}></div>
      
      <div className={styles.content}>
        {children}
      </div>
    </div>
  );
}
