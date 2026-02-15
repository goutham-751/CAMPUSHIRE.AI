import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * Custom hook for API calls with loading, error, and data states.
 */
export function useApi(apiFn, { immediate = false, args = [] } = {}) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const abortRef = useRef(null);

    const execute = useCallback(async (...callArgs) => {
        setLoading(true);
        setError(null);
        try {
            const result = await apiFn(...callArgs);
            setData(result);
            return result;
        } catch (err) {
            setError(err.message || 'Something went wrong');
            throw err;
        } finally {
            setLoading(false);
        }
    }, [apiFn]);

    useEffect(() => {
        if (immediate) execute(...args);
    }, []);

    return { data, loading, error, execute, setData };
}

/**
 * Hook for animated counters.
 */
export function useAnimatedCounter(end, duration = 2000) {
    const [count, setCount] = useState(0);
    const [started, setStarted] = useState(false);

    const start = useCallback(() => setStarted(true), []);

    useEffect(() => {
        if (!started || !end) return;
        let startTime = null;
        let frame;

        const animate = (timestamp) => {
            if (!startTime) startTime = timestamp;
            const progress = Math.min((timestamp - startTime) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
            setCount(Math.floor(eased * end));
            if (progress < 1) frame = requestAnimationFrame(animate);
        };

        frame = requestAnimationFrame(animate);
        return () => cancelAnimationFrame(frame);
    }, [started, end, duration]);

    return { count, start };
}
