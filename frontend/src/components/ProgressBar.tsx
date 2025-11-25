import React from "react";
import type { Placeholder } from "../types";

interface ProgressBarProps {
  placeholders: Placeholder[];
}

export function ProgressBar({ placeholders }: ProgressBarProps) {
  const filled = placeholders.filter((p) => p.filled).length;
  const total = placeholders.length;
  const percentage = total > 0 ? (filled / total) * 100 : 0;

  return (
    <div className="progress-container">
      <div className="progress-info">
        <span>{filled} of {total} fields completed</span>
        <span className="percentage">{Math.round(percentage)}%</span>
      </div>
      <div className="progress-bar">
        <div className="progress-fill" style={{ width: `${percentage}%` }} />
      </div>
    </div>
  );
}