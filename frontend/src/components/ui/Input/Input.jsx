import { forwardRef } from 'react';
import styles from './Input.module.css';

const Input = forwardRef(({ className = '', hasError, label, isTextarea, ...props }, ref) => {
  const Component = isTextarea ? 'textarea' : 'input';
  
  return (
    <div className={styles.wrapper}>
      {label && <label className={styles.label}>{label}</label>}
      <Component
        ref={ref}
        className={`${styles.input} ${isTextarea ? styles.textarea : ''} ${hasError ? styles.error : ''} ${className}`}
        {...props}
      />
    </div>
  );
});

Input.displayName = 'Input';
export default Input;
