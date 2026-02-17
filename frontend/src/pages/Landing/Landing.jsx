import { useRef } from 'react';
import { Link } from 'react-router-dom';
import { motion, useInView, useScroll, useTransform } from 'framer-motion';
import {
    Sparkles, FileSearch, Mic, MessageSquare, BarChart3,
    Shield, Zap, Users, ArrowRight, Star, ChevronRight,
} from 'lucide-react';
import Button from '../../components/Button/Button';
import Card from '../../components/Card/Card';
import { useTheme } from '../../store/ThemeContext';
import { Sun, Moon } from 'lucide-react';
import './Landing.css';

/* ── Animation variants ────────────────────────────────────── */
const fadeUp = {
    hidden: { opacity: 0, y: 40 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.7, ease: [0.22, 1, 0.36, 1] } },
};

const stagger = {
    visible: { transition: { staggerChildren: 0.12 } },
};

function AnimatedSection({ children, className = '' }) {
    const ref = useRef(null);
    const isInView = useInView(ref, { once: true, margin: '-80px' });
    return (
        <motion.section
            ref={ref}
            className={className}
            initial="hidden"
            animate={isInView ? 'visible' : 'hidden'}
            variants={stagger}
        >
            {children}
        </motion.section>
    );
}

/* ── Features data ─────────────────────────────────────────── */
const FEATURES = [
    {
        icon: FileSearch,
        title: 'AI Resume Analysis',
        desc: 'Upload your resume and get instant ATS scoring with detailed breakdowns across 6 key criteria.',
    },
    {
        icon: MessageSquare,
        title: 'Mock Interviews',
        desc: 'Generate tailored interview questions and get AI-powered evaluation of your answers.',
    },
    {
        icon: Mic,
        title: 'Voice Studio',
        desc: 'Practice with text-to-speech and speech-to-text for a realistic interview experience.',
    },
    {
        icon: BarChart3,
        title: 'Smart Scoring',
        desc: 'Weighted scoring engine evaluates skills, experience, education, keywords, and achievements.',
    },
    {
        icon: Shield,
        title: 'Actionable Feedback',
        desc: 'Get specific improvement areas, missing keywords, and ATS optimization tips.',
    },
    {
        icon: Zap,
        title: 'Instant Results',
        desc: 'Powered by Gemini 2.0 Flash for blazing-fast, high-quality AI analysis.',
    },
];

const TESTIMONIALS = [
    { name: 'Priya S.', role: 'CS Graduate', text: 'CampusHire.AI helped me land my dream job at a top tech company. The mock interviews were incredibly realistic!', stars: 5 },
    { name: 'Arjun M.', role: 'Data Science Intern', text: "The ATS scoring showed me exactly what I was missing. After making the suggested changes, I started getting callbacks.", stars: 5 },
    { name: 'Sneha R.', role: 'Frontend Developer', text: "Best interview prep tool I've used. The voice studio feature is a game-changer for building confidence.", stars: 5 },
];

/* ── Landing Page Component ────────────────────────────────── */
export default function Landing() {
    const { scrollYProgress } = useScroll();
    const heroY = useTransform(scrollYProgress, [0, 0.3], [0, -60]);
    const { theme, toggleTheme } = useTheme();

    return (
        <div className="landing">
            {/* ── Navbar ───────────────────────────────────────── */}
            <nav className="landing-nav">
                <Link to="/" className="landing-nav__brand">
                    <div className="landing-nav__logo-icon">
                        <Sparkles size={20} />
                    </div>
                    <span className="landing-nav__logo-text">
                        CampusHire<span className="text-gold">.AI</span>
                    </span>
                </Link>
                <div className="landing-nav__actions">
                    <button className="topnav__icon-btn" onClick={toggleTheme} aria-label="Toggle theme">
                        {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
                    </button>
                    <Link to="/app">
                        <Button variant="primary" size="sm" icon={ArrowRight}>
                            Launch App
                        </Button>
                    </Link>
                </div>
            </nav>

            {/* ── Hero ────────────────────────────────────────── */}
            <motion.section className="landing-hero" style={{ y: heroY }}>
                <div className="landing-hero__bg">
                    <div className="landing-hero__orb landing-hero__orb--1" />
                    <div className="landing-hero__orb landing-hero__orb--2" />
                    <div className="landing-hero__orb landing-hero__orb--3" />
                </div>

                <div className="landing-hero__content">
                    <motion.div
                        className="landing-hero__badge"
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: 0.2, type: 'spring' }}
                    >
                        <Sparkles size={14} />
                        <span>Powered by Gemini AI</span>
                    </motion.div>

                    <motion.h1
                        className="landing-hero__title"
                        initial={{ opacity: 0, y: 30 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.3, duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
                    >
                        Ace Your Campus<br />
                        <span>Placement Journey</span>
                    </motion.h1>

                    <motion.p
                        className="landing-hero__subtitle"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.5, duration: 0.7 }}
                    >
                        AI-powered resume analysis, mock interviews, and voice practice —
                        everything you need to land your dream job.
                    </motion.p>

                    <motion.div
                        className="landing-hero__actions"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.7, duration: 0.6 }}
                    >
                        <Link to="/app">
                            <Button variant="primary" size="lg" icon={ArrowRight}>
                                Get Started Free
                            </Button>
                        </Link>
                        <Link to="/app/resume">
                            <Button variant="secondary" size="lg">
                                Try Resume Analyzer
                            </Button>
                        </Link>
                    </motion.div>
                </div>
            </motion.section>

            {/* ── Features ────────────────────────────────────── */}
            <AnimatedSection className="landing-features">
                <motion.div className="landing-features__header" variants={fadeUp}>
                    <h2>
                        Everything you need to <span className="text-gold">succeed</span>
                    </h2>
                    <p>
                        Comprehensive AI-powered tools designed for campus placement preparation.
                    </p>
                </motion.div>

                <div className="landing-features__grid">
                    {FEATURES.map((feat) => (
                        <motion.div key={feat.title} variants={fadeUp}>
                            <div className="landing-feature-card">
                                <div className="landing-feature-card__icon">
                                    <feat.icon size={24} />
                                </div>
                                <h3>{feat.title}</h3>
                                <p>{feat.desc}</p>
                            </div>
                        </motion.div>
                    ))}
                </div>
            </AnimatedSection>

            {/* ── Testimonials ───────────────────────────────── */}
            <AnimatedSection className="landing-testimonials">
                <motion.div className="landing-testimonials__header" variants={fadeUp}>
                    <h2>
                        Loved by <span className="text-gold">students</span>
                    </h2>
                </motion.div>

                <div className="landing-testimonials__grid">
                    {TESTIMONIALS.map((t, i) => (
                        <motion.div key={i} variants={fadeUp}>
                            <div className="landing-testimonial">
                                <div style={{ display: 'flex', gap: '2px', marginBottom: '12px' }}>
                                    {Array.from({ length: t.stars }).map((_, j) => (
                                        <Star key={j} size={14} fill="#c9a962" color="#c9a962" />
                                    ))}
                                </div>
                                <p className="landing-testimonial__quote">"{t.text}"</p>
                                <div className="landing-testimonial__author">
                                    <div className="landing-testimonial__avatar">{t.name[0]}</div>
                                    <div>
                                        <div className="landing-testimonial__name">{t.name}</div>
                                        <div className="landing-testimonial__role">{t.role}</div>
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    ))}
                </div>
            </AnimatedSection>

            {/* ── CTA Banner ─────────────────────────────────── */}
            <AnimatedSection className="landing-cta">
                <motion.div className="landing-cta__content" variants={fadeUp}>
                    <h2>Ready to ace your placement?</h2>
                    <p>Join thousands of students who've already transformed their career prospects.</p>
                    <Link to="/app">
                        <Button variant="primary" size="lg" icon={ArrowRight}>
                            Start Now — It's Free
                        </Button>
                    </Link>
                </motion.div>
            </AnimatedSection>

            {/* ── Footer ─────────────────────────────────────── */}
            <footer className="landing-footer">
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div className="landing-nav__logo-icon" style={{ width: 28, height: 28 }}>
                        <Sparkles size={14} />
                    </div>
                    <span className="landing-nav__logo-text" style={{ fontSize: '0.95rem' }}>
                        CampusHire<span className="text-gold">.AI</span>
                    </span>
                </div>
                <p>© 2026 CampusHire.AI · Built with ❤️ for campus placements</p>
            </footer>
        </div>
    );
}
