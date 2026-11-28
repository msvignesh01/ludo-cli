"use client";

import { useEffect, useRef } from "react";
import type { CommentaryMode } from "../../game/types";
import styles from "./CommentaryPanel.module.css";

export function CommentaryPanel({ messages, mode }: { messages: string[]; mode: CommentaryMode }) {
  const log = useRef<HTMLOListElement>(null);

  useEffect(() => {
    if (log.current) log.current.scrollTop = log.current.scrollHeight;
  }, [messages]);

  return (
    <section className={styles.panel} aria-labelledby="commentary-heading">
      <div className={styles.heading}>
        <h2 id="commentary-heading">Commentary transcript</h2>
        <span>{mode}</span>
      </div>
      {messages.length === 0 ? (
        <p className={styles.empty}>Commentary is off or waiting for the next action.</p>
      ) : (
        <ol
          className={styles.log}
          ref={log}
          data-testid="commentary-log"
          role="log"
          aria-live="polite"
          aria-relevant="additions"
        >
          {messages.map((message, index) => (
            <li key={`${index}-${message}`}>{message}</li>
          ))}
        </ol>
      )}
    </section>
  );
}
