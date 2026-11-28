"use client";

import { useEffect, useRef, useState } from "react";
import type { MatchController } from "../../match/controller";
import type { CanonicalSnapshot } from "../../game/types";
import { trapDialogFocus } from "./dialogFocus";
import styles from "./MatchDialog.module.css";

export function DrawDialog({
  open,
  snapshot,
  controller,
  onClose,
}: {
  open: boolean;
  snapshot: CanonicalSnapshot;
  controller: MatchController;
  onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [seatIndex, setSeatIndex] = useState(0);

  useEffect(() => {
    if (open) {
      if (!dialog.current?.open) dialog.current?.showModal();
    } else if (dialog.current?.open) {
      dialog.current.close();
    }
  }, [open]);

  const player = snapshot.players[seatIndex];

  return (
    <dialog
      ref={dialog}
      className={styles.dialog}
      aria-labelledby="draw-title"
      onKeyDown={trapDialogFocus}
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
      onClose={onClose}
    >
      <p className="eyebrow">Mutual agreement</p>
      <h2 id="draw-title">Confirm draw</h2>
      {player ? (
        <>
          <div aria-live="polite" aria-atomic="true">
            <p>
              <strong>{player.name}</strong>, do you accept ending this match as a draw?
            </p>
            <p className={styles.progress}>
              Seat {seatIndex + 1} of {snapshot.players.length}
            </p>
          </div>
          <div className={styles.actions}>
            <button className="button" type="button" onClick={onClose}>
              Decline
            </button>
            <button
              className="button buttonPrimary"
              type="button"
              onClick={() => {
                if (seatIndex + 1 >= snapshot.players.length) {
                  controller.declareDraw();
                  onClose();
                } else {
                  setSeatIndex((index) => index + 1);
                }
              }}
            >
              Accept
            </button>
          </div>
        </>
      ) : null}
    </dialog>
  );
}
