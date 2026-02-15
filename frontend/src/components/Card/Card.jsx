import './Card.css';
import { motion } from 'framer-motion';

export default function Card({
    children,
    variant = 'default',
    hover = true,
    padding = true,
    className = '',
    ...props
}) {
    return (
        <motion.div
            className={`card card--${variant} ${padding ? 'card--padded' : ''} ${className}`}
            whileHover={hover ? { y: -4, boxShadow: '0 12px 40px rgba(0,0,0,0.12)' } : {}}
            transition={{ type: 'spring', stiffness: 300, damping: 25 }}
            {...props}
        >
            {children}
        </motion.div>
    );
}
