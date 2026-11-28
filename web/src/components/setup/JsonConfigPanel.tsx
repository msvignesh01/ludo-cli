"use client";

import { useId, useRef } from "react";
import styles from "./JsonConfigPanel.module.css";

export function JsonConfigPanel({
  value,
  error,
  onChange,
  onLoad,
}: {
  value: string;
  error: string;
  onChange: (value: string) => void;
  onLoad: (value: string) => void;
}) {
  const fileInput = useRef<HTMLInputElement>(null);
  const errorId = useId();

  async function loadFile(file: File | undefined): Promise<void> {
    if (!file) return;
    onLoad(await file.text());
  }

  return (
    <section className={styles.panel} aria-labelledby="json-heading">
      <div>
        <p className="eyebrow">Portable setup</p>
        <h2 id="json-heading">Configuration JSON import</h2>
      </div>
      <p className={styles.help}>
        Paste a preset or export a configuration file. URL settings keep the highest precedence.
      </p>
      <label className="field" htmlFor="configuration-json">
        <span>Configuration JSON</span>
        <textarea
          id="configuration-json"
          className="textarea"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder={'{"mode":"quick","profile":"showcase","player_count":2}'}
          spellCheck={false}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? errorId : undefined}
        />
      </label>
      {error ? (
        <p className="alert" id={errorId} role="alert">
          {error}
        </p>
      ) : null}
      <div className={styles.actions}>
        <button
          className="button buttonPrimary buttonSmall"
          type="button"
          onClick={() => onLoad(value)}
        >
          Load configuration
        </button>
        <button
          className="button buttonSmall"
          type="button"
          onClick={() => fileInput.current?.click()}
        >
          Choose JSON file
        </button>
        <input
          ref={fileInput}
          className={styles.fileInput}
          type="file"
          accept=".json,application/json"
          aria-label="Choose configuration file"
          onChange={(event) => {
            void loadFile(event.target.files?.[0]);
            event.target.value = "";
          }}
        />
      </div>
      <div
        className={styles.dropZone}
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => {
          event.preventDefault();
          void loadFile(event.dataTransfer.files[0]);
        }}
      >
        Or drop a JSON configuration here.
      </div>
    </section>
  );
}
