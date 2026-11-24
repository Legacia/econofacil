// Identidade visual EconoFácil: logo, marca e ondas decorativas.
import { useId } from "react";

export function LogoMark({ size = 44, flat = false }) {
  const gid = useId();
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" role="img" aria-label="EconoFácil">
      {!flat && (
        <>
          <defs>
            <linearGradient id={gid} x1="0" y1="0" x2="1" y2="1">
              <stop offset="0" stopColor="#1B8B4B" />
              <stop offset="1" stopColor="#1B4B8B" />
            </linearGradient>
          </defs>
          <rect width="64" height="64" rx="16" fill={`url(#${gid})`} />
        </>
      )}
      <g
        transform="translate(10 10) scale(1.83)"
        fill="none"
        stroke={flat ? "currentColor" : "#fff"}
        strokeWidth="1.9"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M3 4.5h2.2l2 9.6a1.5 1.5 0 0 0 1.5 1.2h7.8a1.5 1.5 0 0 0 1.45-1.1L19.6 8H6.3" />
        <circle cx="9.5" cy="19" r="1.3" />
        <circle cx="16.5" cy="19" r="1.3" />
        <path d="M10 11.4l1.9 1.9 3.6-3.6" />
      </g>
    </svg>
  );
}

export function Wordmark({ light = false, size = 22 }) {
  return (
    <span className="wordmark" style={{ fontSize: size }}>
      <span style={{ color: light ? "#fff" : "var(--azul)" }}>Econo</span>
      <span style={{ color: light ? "#bff0cf" : "var(--verde)" }}>Fácil</span>
    </span>
  );
}

export function Logo({ size = 40, light = false, textSize = 22 }) {
  return (
    <span className="logo-lockup">
      <LogoMark size={size} />
      <Wordmark light={light} size={textSize} />
    </span>
  );
}

// Ondas decorativas de rodapé (verde → azul)
export function Waves({ className = "" }) {
  const gid = useId();
  return (
    <svg className={`waves ${className}`} viewBox="0 0 1200 140" preserveAspectRatio="none" aria-hidden="true">
      <defs>
        <linearGradient id={gid} x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stopColor="#1B8B4B" />
          <stop offset="1" stopColor="#1B4B8B" />
        </linearGradient>
      </defs>
      <path fill="#4CAF50" fillOpacity=".22" d="M0 70 C200 20 360 120 600 70 C840 20 1000 110 1200 60 L1200 140 L0 140Z" />
      <path fill="#2196F3" fillOpacity=".22" d="M0 90 C220 50 400 130 640 92 C880 54 1020 124 1200 84 L1200 140 L0 140Z" />
      <path fill={`url(#${gid})`} fillOpacity=".92" d="M0 112 C240 82 420 140 660 112 C900 84 1040 134 1200 108 L1200 140 L0 140Z" />
    </svg>
  );
}
