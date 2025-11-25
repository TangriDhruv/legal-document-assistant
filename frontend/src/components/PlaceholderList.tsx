import React from "react";
import type { Placeholder } from "../types";

interface PlaceholderListProps {
  placeholders: Placeholder[];
}

export function PlaceholderList({ placeholders }: PlaceholderListProps) {
  const unfilled = placeholders.filter((p) => !p.filled);
  const filled = placeholders.filter((p) => p.filled);

  return (
    <div className="placeholder-list">
      <h3>📋 Document Fields</h3>

      {filled.length > 0 && (
        <div className="placeholder-section">
          <h4>✅ Completed ({filled.length})</h4>
          {filled.map((p) => (
            <div key={p.name} className="placeholder-item filled">
              <span className="placeholder-name">{p.name}</span>
              <span className="placeholder-value">{p.value}</span>
            </div>
          ))}
        </div>
      )}

      {unfilled.length > 0 && (
        <div className="placeholder-section">
          <h4>⏳ Remaining ({unfilled.length})</h4>
          {unfilled.map((p) => (
            <div key={p.name} className="placeholder-item">
              <div className="placeholder-name">{p.name}</div>
              <div className="placeholder-description">{p.description}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
