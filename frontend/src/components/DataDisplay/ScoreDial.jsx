import { useEffect, useState } from 'react';
import styles from './ScoreDial.module.css';

export default function ScoreDial({ score, max = 100, label, color = 'gold', size = 160 }) {
  const [currentScore, setCurrentScore] = useState(0);
  
  useEffect(() => {
    let start = 0;
    const duration = 1200;
    const startTime = performance.now();
    
    const animate = (currentTime) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      const easeProgress = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
      
      setCurrentScore(Math.floor(easeProgress * score));
      
      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };
    
    requestAnimationFrame(animate);
  }, [score]);

  const radius = (size - 10) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (currentScore / max) * circumference;
  
  const colorVar = color === 'neon' ? 'var(--color-neon)' : 'var(--color-gold)';
  
  return (
    <div className={styles.scoreDial} style={{ width: size, height: size }}>
      <svg className={styles.svg} width={size} height={size}>
        <circle
          className={styles.bgCircle}
          cx={size / 2} cy={size / 2} r={radius}
        />
        <circle
          className={styles.progressCircle}
          cx={size / 2} cy={size / 2} r={radius}
          style={{
            stroke: colorVar,
            strokeDasharray: circumference,
            strokeDashoffset: strokeDashoffset
          }}
        />
      </svg>
      <div className={styles.content}>
        <div className={styles.scoreWrapper} style={{ color: colorVar }}>
          <span className={styles.score}>{currentScore}</span>
          <span className={styles.max}>/{max}</span>
        </div>
        {label && <div className={styles.label}>{label}</div>}
      </div>
    </div>
  );
}
