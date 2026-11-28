"use client";

import { useEffect, useRef } from "react";
import type { MatchController } from "../../match/controller";
import { trapDialogFocus } from "./dialogFocus";
import styles from "./MatchDialog.module.css";

export function QuitDialog({
  open,
  controller,
  onClose,
}: {
  open: boolean;
  controller: MatchController;
  onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    if (open && !dialog.current?.open) dialog.current?.showModal();
    if (!open && dialog.current?.open) dialog.current.close();
  }, [open]);

  return (
    <dialog
      ref={dialog}
      className={styles.dialog}
      aria-labelledby="quit-title"
      onKeyDown={trapDialogFocus}
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
      onClose={onClose}
    >
      <p className="eyebrow">End this table</p>
      <h2 id="quit-title">Quit match?</h2>
      <p>
        The result will be recorded as quit. You can still export the match before starting a new
        one.
      </p>
      <div className={styles.actions}>
        <button className="button" type="button" onClick={onClose}>
          Keep playing
        </button>
        <button
          className="button buttonDanger"
          type="button"
          onClick={() => {
            controller.quit();
            onClose();
          }}
        >
          Quit match
        </button>
      </div>
    </dialog>
  );
}
