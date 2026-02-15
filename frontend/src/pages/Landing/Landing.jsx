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
        color: '#6366f1',
    },
    {
        icon: MessageSquare,
        title: 'Mock Interviews',
        desc: 'Generate tailored interview questions and get AI-powered evaluation of your answers.',
        color: '#8b5cf6',
    },
    {
        icon: Mic,
        title: 'Voice Studio',
        desc: 'Practice with text-to-speech and speech-to-text for a realistic interview experience.',
        color: '#06b6d4',
    },
    {
        icon: BarChart3,
        title: 'Smart Scoring',
        desc: 'Weighted scoring engine evaluates skills, experience, education, keywords, and achievements.',
        color: '#10b981',
    },
    {
        icon: Shield,
        title: 'Actionable Feedback',
        desc: 'Get specific improvement areas, missing keywords, and ATS optimization tips.',
        color: '#f59e0b',
    },
    {
        icon: Zap,
        title: 'Instant Results',
        desc: 'Powered by Gemini 2.0 Flash for blazing-fast, high-quality AI analysis.',
        color: '#ef4444',
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
            <nav className="landing__nav glass">
                <div className="landing__nav-inner">
                    <div className="landing__nav-brand">
                        <div className="landing__nav-logo">
                            <Sparkles size={20} />
                        </div>
                        <span className="gradient-text" style={{ fontFamily: 'var(--font-primary)', fontWeight: 800, fontSize: '1.2rem' }}>
                            CampusHire.AI
                        </span>
                    </div>
                    <div className="landing__nav-actions">
                        <button className="topnav__icon-btn" onClick={toggleTheme} aria-label="Toggle theme">
                            {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
                        </button>
                        <Link to="/app">
                            <Button variant="primary" size="sm" icon={ArrowRight}>
                                Launch App
                            </Button>
                        </Link>
                    </div>
                </div>
            </nav>

            {/* ── Hero ────────────────────────────────────────── */}
            <motion.section className="hero" style={{ y: heroY }}>
                {/* Gradient orbs */}
                <div className="hero__orb hero__orb--1 animate-float" />
                <div className="hero__orb hero__orb--2 animate-float" style={{ animationDelay: '-2s' }} />
                <div className="hero__orb hero__orb--3 animate-float" style={{ animationDelay: '-4s' }} />

                <div className="hero__content">
                    <motion.div
                        className="hero__badge glass"
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: 0.2, type: 'spring' }}
                    >
                        <Sparkles size={14} />
                        <span>Powered by Gemini AI</span>
                    </motion.div>

                    <motion.h1
                        className="hero__title"
                        initial={{ opacity: 0, y: 30 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.3, duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
                    >
                        Ace Your Campus<br />
                        <span className="gradient-text">Placement Journey</span>
                    </motion.h1>

                    <motion.p
                        className="hero__subtitle"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.5, duration: 0.7 }}
                    >
                        AI-powered resume analysis, mock interviews, and voice practice —
                        everything you need to land your dream job.
                    </motion.p>

                    <motion.div
                        className="hero__cta"
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

                    {/* Stats */}
                    <motion.div
                        className="hero__stats"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 1, duration: 0.6 }}
                    >
                        {[
                            { num: '10K+', label: 'Resumes Analyzed' },
                            { num: '95%', label: 'Success Rate' },
                            { num: '50+', label: 'Companies' },
                        ].map(({ num, label }) => (
                            <div key={label} className="hero__stat">
                                <span className="hero__stat-num gradient-text">{num}</span>
                                <span className="hero__stat-label">{label}</span>
                            </div>
                        ))}
                    </motion.div>
                </div>
            </motion.section>

            {/* ── Features ────────────────────────────────────── */}
            <AnimatedSection className="features">
                <motion.div className="section-header" variants={fadeUp}>
                    <span className="section-badge">Features</span>
                    <h2 className="section-title">
                        Everything you need to <span className="gradient-text">succeed</span>
                    </h2>
                    <p className="section-subtitle">
                        Comprehensive AI-powered tools designed for campus placement preparation.
                    </p>
                </motion.div>

                <div className="features__grid">
                    {FEATURES.map((feat, i) => (
                        <motion.div key={feat.title} variants={fadeUp}>
                            <Card variant="glass" className="feature-card">
                                <div className="feature-card__icon" style={{ background: `${feat.color}18`, color: feat.color }}>
                                    <feat.icon size={24} />
                                </div>
                                <h3 className="feature-card__title">{feat.title}</h3>
                                <p className="feature-card__desc">{feat.desc}</p>
                            </Card>
                        </motion.div>
                    ))}
                </div>
            </AnimatedSection>

            {/* ── Showcase ────────────────────────────────────── */}
            <AnimatedSection className="showcase">
                <motion.div className="section-header" variants={fadeUp}>
                    <span className="section-badge">How It Works</span>
                    <h2 className="section-title">
                        Three steps to your <span className="gradient-text">dream job</span>
                    </h2>
                </motion.div>

                <div className="showcase__steps">
                    {[
                        { step: '01', title: 'Upload Resume', desc: 'Upload your resume in PDF, DOCX, or TXT format. Our AI parser extracts all key information.' },
                        { step: '02', title: 'AI Analysis', desc: 'Get instant ATS scoring, tailored feedback, and improvement suggestions powered by Gemini AI.' },
                        { step: '03', title: 'Practice & Improve', desc: 'Practice mock interviews with AI-generated questions and voice-based practice sessions.' },
                    ].map((item, i) => (
                        <motion.div key={item.step} className="showcase__step" variants={fadeUp}>
                            <div className="showcase__step-num gradient-text">{item.step}</div>
                            <h3>{item.title}</h3>
                            <p>{item.desc}</p>
                            {i < 2 && <ChevronRight className="showcase__step-arrow" size={24} />}
                        </motion.div>
                    ))}
                </div>
            </AnimatedSection>

            {/* ── Testimonials ───────────────────────────────── */}
            <AnimatedSection className="testimonials">
                <motion.div className="section-header" variants={fadeUp}>
                    <span className="section-badge">Testimonials</span>
                    <h2 className="section-title">
                        Loved by <span className="gradient-text">students</span>
                    </h2>
                </motion.div>

                <div className="testimonials__grid">
                    {TESTIMONIALS.map((t, i) => (
                        <motion.div key={i} variants={fadeUp}>
                            <Card variant="glass" className="testimonial-card">
                                <div className="testimonial-card__stars">
                                    {Array.from({ length: t.stars }).map((_, j) => (
                                        <Star key={j} size={14} fill="#f59e0b" color="#f59e0b" />
                                    ))}
                                </div>
                                <p className="testimonial-card__text">"{t.text}"</p>
                                <div className="testimonial-card__author">
                                    <div className="testimonial-card__avatar">{t.name[0]}</div>
                                    <div>
                                        <strong>{t.name}</strong>
                                        <span>{t.role}</span>
                                    </div>
                                </div>
                            </Card>
                        </motion.div>
                    ))}
                </div>
            </AnimatedSection>

            {/* ── CTA Banner ─────────────────────────────────── */}
            <AnimatedSection className="cta-banner">
                <motion.div className="cta-banner__inner" variants={fadeUp}>
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
            <footer className="landing__footer">
                <div className="landing__footer-inner">
                    <div className="landing__footer-brand">
                        <div className="landing__nav-logo"><Sparkles size={18} /></div>
                        <span className="gradient-text" style={{ fontWeight: 800, fontFamily: 'var(--font-primary)' }}>CampusHire.AI</span>
                    </div>
                    <p className="landing__footer-copy">
                        © 2026 CampusHire.AI · Built with ❤️ for campus placements
                    </p>
                </div>
            </footer>
        </div>
    );
}
