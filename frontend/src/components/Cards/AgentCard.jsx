import styles from './AgentCard.module.css';

export default function AgentCard({ role, title, questions = [], activeQuestionIndex = -1, glowColor = 'neon', isActive = false }) {
  const glowClass = styles[`glow_${glowColor}`] || styles.glow_neon;

  return (
    <div className={`${styles.agentCard} ${isActive ? styles.active : ''}`}>
      <div className={`${styles.avatarContainer} ${isActive ? glowClass : ''}`}>
        <div className={styles.avatarInner}>
          <span className={styles.avatarInitials}>{role.charAt(0)}</span>
        </div>
      </div>
      
      <div className={styles.agentInfo}>
        <div className={styles.role}>{role}</div>
        <div className={styles.title}>{title}</div>
      </div>
      
      {questions.length > 0 && (
        <div className={styles.questionsList}>
          {questions.map((q, idx) => (
            <div 
              key={idx} 
              className={`${styles.questionItem} ${idx === activeQuestionIndex ? styles.questionActive : ''} ${idx < activeQuestionIndex ? styles.questionCompleted : ''}`}
            >
              <div className={styles.questionDot} />
              <div className={styles.questionText}>Question {idx + 1}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
