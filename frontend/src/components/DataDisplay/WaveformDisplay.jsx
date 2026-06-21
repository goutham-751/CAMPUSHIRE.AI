import { useEffect, useRef } from 'react';
import styles from './WaveformDisplay.module.css';

export default function WaveformDisplay({ state = 'idle', amplitude = 0 }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    let animationId;
    let phase = 0;

    const render = () => {
      const width = canvas.width;
      const height = canvas.height;
      ctx.clearRect(0, 0, width, height);

      let color = 'rgba(0, 229, 204, 0.2)'; 
      let currentAmp = Math.sin(phase) * 10 + 20;

      if (state === 'ai') {
        color = 'rgba(201, 168, 76, 0.8)';
        currentAmp = 40 + amplitude * 50;
      } else if (state === 'user') {
        color = 'rgba(0, 229, 204, 0.8)';
        currentAmp = 40 + amplitude * 50;
      }

      ctx.beginPath();
      ctx.moveTo(0, height / 2);

      for (let i = 0; i < width; i++) {
        const y = Math.sin(i * 0.05 + phase * 2) * currentAmp 
                * Math.sin(i * 0.01) 
                * Math.cos(i * 0.02 + phase);
        ctx.lineTo(i, height / 2 + y);
      }

      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.stroke();

      phase += 0.02;
      animationId = requestAnimationFrame(render);
    };

    render();

    return () => cancelAnimationFrame(animationId);
  }, [state, amplitude]);

  return (
    <div className={styles.container}>
      <canvas ref={canvasRef} width={800} height={200} className={styles.canvas} />
    </div>
  );
}
