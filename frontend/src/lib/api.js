/**
 * Central API service layer for CampusHire.AI
 */
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const api = axios.create({
    baseURL: API_BASE,
    timeout: 60000,
    headers: { 'Accept': 'application/json' },
});

// ── Request interceptor ──────────────────────────────────────
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('campushire-token');
        if (token) config.headers.Authorization = `Bearer ${token}`;
        return config;
    },
    (error) => Promise.reject(error),
);

// ── Response interceptor ─────────────────────────────────────
api.interceptors.response.use(
    (response) => {
        // For blob responses (e.g. TTS audio), return the raw blob
        if (response.config.responseType === 'blob') {
            return response.data;
        }
        return response.data;
    },
    (error) => {
        const message = error.response?.data?.detail || error.response?.data?.error || error.message;
        return Promise.reject(new Error(message));
    },
);

// ── Activity Tracking ────────────────────────────────────────
const HISTORY_KEY = 'campushire-history';
const MAX_HISTORY = 100;

export function trackActivity(item) {
    try {
        const history = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
        history.unshift({ ...item, timestamp: new Date().toISOString() });
        if (history.length > MAX_HISTORY) history.length = MAX_HISTORY;
        localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
    } catch { /* ignore storage errors */ }
}

export function getHistory() {
    try {
        return JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
    } catch {
        return [];
    }
}

// ── Resume endpoints ─────────────────────────────────────────
export const resumeApi = {
    upload: (file) => {
        const form = new FormData();
        form.append('file', file);
        return api.post('/api/resume/upload', form);
    },
    score: (file, jobTitle, companyName, jobDescription) => {
        const form = new FormData();
        form.append('file', file);
        form.append('job_title', jobTitle);
        form.append('company_name', companyName);
        form.append('job_description', jobDescription);
        return api.post('/api/resume/score', form);
    },
    feedback: (file, jobTitle, companyName, jobDescription) => {
        const form = new FormData();
        form.append('file', file);
        form.append('job_title', jobTitle);
        form.append('company_name', companyName);
        form.append('job_description', jobDescription);
        return api.post('/api/resume/feedback', form);
    },
};

// ── Interview endpoints ──────────────────────────────────────
export const interviewApi = {
    generateQuestions: (file, jobTitle, companyName, jobDescription, numQuestions = 10, industry = 'technology') => {
        const form = new FormData();
        form.append('file', file);
        form.append('job_title', jobTitle);
        form.append('company_name', companyName);
        form.append('job_description', jobDescription);
        form.append('num_questions', numQuestions);
        form.append('industry', industry);
        return api.post('/api/interview/questions', form);
    },
    evaluateAnswer: (question, answer, jobTitle) =>
        api.post('/api/interview/evaluate', { question, answer, job_title: jobTitle }),
};

// ── Voice endpoints ──────────────────────────────────────────
export const voiceApi = {
    tts: (text, language = 'en', voiceId = null, outputFormat = 'mp3') =>
        api.post('/api/voice/tts', { text, language, voice_id: voiceId, output_format: outputFormat }, { responseType: 'blob' }),
    stt: (audioFile, language = 'en-US') => {
        const form = new FormData();
        form.append('file', audioFile);
        form.append('language', language);
        return api.post('/api/voice/stt', form);
    },
    getVoices: () => api.get('/api/voice/voices'),
};

// ── Health ────────────────────────────────────────────────────
export const healthApi = {
    check: () => api.get('/health'),
};

export default api;
