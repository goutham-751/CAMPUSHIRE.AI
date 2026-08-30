/**
 * Central API service layer for CampusHire.AI
 */
import axios from 'axios';
import { supabase } from './supabase';

const API_BASE = import.meta.env.API_URL || 'http://127.0.0.1:8000';

const api = axios.create({
    baseURL: API_BASE,
    timeout: 180000,
    headers: { 'Accept': 'application/json' },
});

// ── Request interceptor ──────────────────────────────────────
api.interceptors.request.use(
    async (config) => {
        try {
            const { data: { session } } = await supabase.auth.getSession();
            if (session?.access_token) {
                config.headers.Authorization = `Bearer ${session.access_token}`;
            }
        } catch {
            /* proceed without a token */
        }
        return config;
    },
    (error) => Promise.reject(error),
);

// ── Response interceptor ─────────────────────────────────────
api.interceptors.response.use(
    (response) => {
        if (response.config.responseType === 'blob') {
            return response.data;
        }
        return response.data;
    },
    (error) => {
        if (error.response?.status === 401) {
            const sentAuth = error.config?.headers?.Authorization;
            if (sentAuth) {
                supabase.auth.signOut().catch(() => {});
            }
            return Promise.reject(new Error('Session expired. Please log in again.'));
        }

        if (error.response?.status === 429) {
            return Promise.reject(new Error('Too many requests. Please wait a moment and try again.'));
        }

        if (error.code === 'ECONNABORTED' || error.response?.status === 502 || error.response?.status === 504 || error.message?.includes('timeout')) {
            return Promise.reject(new Error('The server is waking up or taking too long to respond. Please wait a moment and try again.'));
        }
        let message = error.response?.data?.detail || error.response?.data?.error || error.message;
        if (typeof message === 'object') {
            message = JSON.stringify(message);
        }
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
    getUserResumes: () => {
        return api.get('/api/resume/me');
    },
    feedback: (file, jobTitle, companyName, jobDescription) => {
        const form = new FormData();
        form.append('file', file);
        form.append('job_title', jobTitle);
        form.append('company_name', companyName);
        form.append('job_description', jobDescription);
        return api.post('/api/resume/feedback', form);
    },
    semanticMatch: (file, jobDescription, jobTitle = '') => {
        const form = new FormData();
        form.append('file', file);
        form.append('job_description', jobDescription);
        form.append('job_title', jobTitle);
        return api.post('/api/resume/semantic-match', form);
    },
    batchMatch: (file, jobEntries) => {
        const form = new FormData();
        form.append('file', file);
        form.append('job_entries', JSON.stringify(jobEntries));
        return api.post('/api/resume/batch-match', form);
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
    panelEvaluate: (question, answer, jobTitle) =>
        api.post('/api/interview/panel-evaluate', { question, answer, job_title: jobTitle }),
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

// ── Health & Telemetry ────────────────────────────────────────
export const healthApi = {
    check: () => api.get('/health'),
    getTelemetry: () => api.get('/api/telemetry'),
    getSystemStatus: () => api.get('/api/system/status'),
};

export default api;
