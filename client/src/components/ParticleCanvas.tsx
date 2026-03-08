import React, { useEffect, useRef } from "react";

interface ParticleCanvasProps {
  intensity: number;
}

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  hue: number;
  life: number;
  alpha: number;
}

export function ParticleCanvas({ intensity }: ParticleCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>();
  const particlesRef = useRef<Particle[]>([]);
  const intensityRef = useRef(intensity);

  useEffect(() => {
    intensityRef.current = intensity;
  }, [intensity]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    resize();
    window.addEventListener("resize", resize);

    const spawnParticle = (width: number, height: number) => {
      const speed = 0.3 + intensityRef.current * 2;
      particlesRef.current.push({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * speed,
        vy: (Math.random() - 0.5) * (speed * 0.6),
        size: 0.65 + Math.random() * 2 + intensityRef.current,
        hue: 180 + Math.random() * 140,
        life: 60 + Math.random() * 80,
        alpha: 0.25 + Math.random() * 0.5,
      });
    };

    const render = () => {
      const width = canvas.width / dpr;
      const height = canvas.height / dpr;
      const fillAlpha = Math.max(0.3, 0.55 - intensityRef.current * 0.35);
      ctx.fillStyle = `rgba(2, 5, 14, ${fillAlpha})`;
      ctx.fillRect(0, 0, width, height);

      const spawnCount = Math.max(1, Math.floor(6 + intensityRef.current * 18));
      for (let i = 0; i < spawnCount; i += 1) {
        spawnParticle(width, height);
      }

      particlesRef.current = particlesRef.current.filter((particle) => {
        particle.x += particle.vx;
        particle.y += particle.vy;
        particle.life -= 1;
        const alive =
          particle.life > 0 && particle.x >= -10 && particle.x <= width + 10 && particle.y >= -10 && particle.y <= height + 10;
        if (alive) {
          const brightness = Math.min(1, particle.life / 90);
          ctx.beginPath();
          ctx.fillStyle = `hsla(${particle.hue}, 70%, 64%, ${particle.alpha * brightness})`;
          ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
          ctx.fill();
        }
        return alive;
      });

      animationRef.current = requestAnimationFrame(render);
    };

    animationRef.current = requestAnimationFrame(render);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      window.removeEventListener("resize", resize);
    };
  }, []);

  return <canvas ref={canvasRef} className="canvas-layer" aria-hidden="true" />;
}
