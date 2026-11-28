import type { LegalMovePreview } from "../../game/types";
import styles from "./TokenChoiceList.module.css";

export function TokenChoiceList({
  previews,
  pendingRoll,
  onSelect,
}: {
  previews: LegalMovePreview[];
  pendingRoll: number;
  onSelect: (tokenIndex: number) => void;
}) {
  if (previews.length === 0) return null;

  return (
    <section className={styles.choices} aria-labelledby="choice-heading">
      <p className="eyebrow">Rolled {pendingRoll}</p>
      <h2 id="choice-heading">Choose a token</h2>
      <div className={styles.list}>
        {previews.map((preview) => (
          <button
            className={styles.choice}
            type="button"
            key={preview.token_idx}
            onClick={() => onSelect(preview.token_idx)}
          >
            <span className={styles.label}>{preview.label}</span>
            <span className={styles.description}>
              <strong>
                Move {preview.label} to {preview.new_position}
              </strong>
              <small>
                From {preview.old_position}
                {preview.captured.length > 0 ? ` · captures ${preview.captured.join(", ")}` : ""}
              </small>
            </span>
            <span className={styles.tags}>
              {preview.reached_home ? <i>Home</i> : null}
              {preview.safe ? <i>Safe</i> : null}
              {preview.wrapped ? <i>Wrap</i> : null}
              {preview.blockade_formed ? <i>Blockade</i> : null}
            </span>
          </button>
        ))}
      </div>
    </section>
  );
}
