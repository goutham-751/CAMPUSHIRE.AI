import { useNavigate } from 'react-router-dom';
import AmbientField from '../../components/Ambient/AmbientField';
import Button from '../../components/ui/Button/Button';
import { BadgeAI } from '../../components/ui/Badge/Badge';
import { ArrowRight } from 'lucide-react';
import styles from './Landing.module.css';

export default function Landing() {
  const navigate = useNavigate();

  return (
    <AmbientField>
      <nav className={styles.topNav}>
        <div className={styles.logo}>
          <span className={styles.logoIcon}>◈</span>
        </div>
        <Button variant="ghost" onClick={() => navigate('/app')}>
          Enter <ArrowRight size={16} />
        </Button>
      </nav>

      <div className={styles.heroContainer}>
        <div className={styles.badgeWrapper}>
          <BadgeAI />
        </div>
        
        <h1 className={styles.headline}>
          <span className={styles.headlineLight}>Ace Your</span><br/>
          Campus Placement<br/>
          Journey.
        </h1>
        
        <p className={styles.subtitle}>
          The defining AI-native career intelligence platform.
        </p>

        <div className={styles.ctaGroup}>
          <Button variant="primary" onClick={() => navigate('/app')} className={styles.mainCta}>
            <span className={styles.ctaIcon}>◉</span> Enter the Platform
          </Button>
          <Button variant="ghost" onClick={() => navigate('/app/resume')}>
            Try Resume Analyzer <ArrowRight size={16} />
          </Button>
        </div>
      </div>
    </AmbientField>
  );
}
