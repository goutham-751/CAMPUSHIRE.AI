import { useEffect, useState } from 'react';
import styles from './IntelligenceFeed.module.css';

export default function IntelligenceFeed({ text, speed = 20, onComplete }) {
  const [displayedText, setDisplayedText] = useState('');
  const [isTyping, setIsTyping] = useState(true);

  useEffect(() => {
    let i = 0;
    setIsTyping(true);
    setDisplayedText('');

    if (!text) {
      setIsTyping(false);
      return;
    }

    const timer = setInterval(() => {
      setDisplayedText(text.substring(0, i));
      i++;
      if (i > text.length) {
        clearInterval(timer);
        setIsTyping(false);
        if (onComplete) onComplete();
      }
    }, speed);

    return () => clearInterval(timer);
  }, [text, speed, onComplete]);

  return (
    <div className={styles.feed}>
      <span className={styles.text}>{displayedText}</span>
      {isTyping && <span className={styles.cursor}>_</span>}
    </div>
  );
}
