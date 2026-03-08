import React from "react";

interface ThemeToggleProps {
  value: string;
  onChange: (value: string) => void;
}

const OPTIONS = [
  { id: "nebula", label: "Nebula" },
  { id: "aurora", label: "Aurora" },
  { id: "dawn", label: "Dawn" },
];

export function ThemeToggle({ value, onChange }: ThemeToggleProps) {
  return (
    <div className="theme-toggle" role="group" aria-label="主题切换">
      {OPTIONS.map((option) => (
        <button
          key={option.id}
          className={value === option.id ? "theme-option active" : "theme-option"}
          type="button"
          onClick={() => onChange(option.id)}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
