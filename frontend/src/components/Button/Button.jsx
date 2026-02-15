import './Button.css';
import { motion } from 'framer-motion';

export default function Button({
    children,
    variant = 'primary',
    size = 'md',
    icon: Icon,
    iconRight,
    loading,
    disabled,
    fullWidth,
    ...props
}) {
    const cls = [
        'btn',
        `btn--${variant}`,
        `btn--${size}`,
        fullWidth && 'btn--full',
        loading && 'btn--loading',
    ].filter(Boolean).join(' ');

    return (
        <motion.button
            className={cls}
            disabled={disabled || loading}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.97 }}
            transition={{ type: 'spring', stiffness: 400, damping: 20 }}
            {...props}
        >
            {loading && <span className="btn__spinner" />}
            {Icon && !loading && <Icon size={size === 'sm' ? 14 : size === 'lg' ? 20 : 16} />}
            <span>{children}</span>
            {iconRight && <iconRight size={16} />}
        </motion.button>
    );
}
