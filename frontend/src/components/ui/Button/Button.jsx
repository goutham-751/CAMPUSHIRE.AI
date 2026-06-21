import styles from './Button.module.css';

export default function Button({ variant = 'primary', className = '', children, ...props }) {
  const baseClass = styles.button;
  const variantClass = styles[variant] || styles.primary;
  return (
    <button className={`${baseClass} ${variantClass} ${className}`} {...props}>
      {children}
    </button>
  );
}
