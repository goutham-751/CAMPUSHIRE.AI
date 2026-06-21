import { useState, useEffect } from 'react';
import { healthApi } from '../lib/api';

export function useTelemetry(intervalMs = 3000) {
    const [telemetry, setTelemetry] = useState({
        api_latency_ms: 0,
        total_tokens: 0,
        uptime: '00:00:00',
        status: 'Active',
        loading: true,
        error: null,
    });

    useEffect(() => {
        let isMounted = true;

        const fetchTelemetry = async () => {
            try {
                const data = await healthApi.getTelemetry();
                if (isMounted) {
                    setTelemetry({
                        ...data,
                        loading: false,
                        error: null,
                    });
                }
            } catch (err) {
                if (isMounted) {
                    setTelemetry(prev => ({
                        ...prev,
                        loading: false,
                        error: err.message,
                        status: 'Degraded'
                    }));
                }
            }
        };

        // Initial fetch
        fetchTelemetry();

        // Polling
        const intervalId = setInterval(fetchTelemetry, intervalMs);

        return () => {
            isMounted = false;
            clearInterval(intervalId);
        };
    }, [intervalMs]);

    return telemetry;
}
