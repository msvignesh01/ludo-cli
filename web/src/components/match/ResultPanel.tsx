import type { CanonicalSnapshot } from "../../game/types";
import styles from "./ResultPanel.module.css";

function statusLabel(status: CanonicalSnapshot["status"]): string {
  return status.charAt(0) + status.slice(1).toLowerCase();
}

export function ResultPanel({
  snapshot,
  onExport,
  onNewMatch,
}: {
  snapshot: CanonicalSnapshot;
  onExport: () => void;
  onNewMatch: () => void;
}) {
  if (snapshot.status === "PLAYING") return null;
  const winner = snapshot.winner_index === null ? null : snapshot.players[snapshot.winner_index];
  const reason =
    snapshot.status === "WON"
      ? `${winner?.name ?? "Winner"} brought every token home.`
      : snapshot.status === "DRAW"
        ? (snapshot.draw_reason ?? "Draw")
        : "Game quit.";

  return (
    <section className={styles.result} aria-labelledby="result-heading">
      <p className="eyebrow">Table closed</p>
      <h2 id="result-heading">Match result</h2>
      <div className={styles.outcome}>
        <strong data-testid="result-status">{statusLabel(snapshot.status)}</strong>
        <span data-testid="result-reason">{reason}</span>
      </div>
      <dl>
        <div>
          <dt>Turns</dt>
          <dd>{snapshot.turn_count}</dd>
        </div>
        <div>
          <dt>Rolls</dt>
          <dd>{snapshot.events.filter((event) => event.type === "DICE_ROLLED").length}</dd>
        </div>
        <div>
          <dt>Mode</dt>
          <dd>{snapshot.config.mode}</dd>
        </div>
      </dl>
      <div className={styles.actions}>
        <button className="button buttonPrimary" type="button" onClick={onExport}>
          Export match
        </button>
        <button className="button" type="button" onClick={onNewMatch}>
          New match
        </button>
      </div>
    </section>
  );
}
