import { PLAYER_SPECS } from "../../game/presets";
import type { CanonicalSnapshot } from "../../game/types";
import styles from "./MatchHud.module.css";

export function MatchHud({ snapshot }: { snapshot: CanonicalSnapshot }) {
  const current = snapshot.players[snapshot.current_player]!;
  const rolls = snapshot.events.filter((event) => event.type === "DICE_ROLLED").length;

  return (
    <section className={styles.hud} aria-labelledby="match-heading">
      <div className={styles.turnStrip}>
        <div>
          <p className="eyebrow">Current turn</p>
          <h2 id="match-heading">{current.name}</h2>
          <p>
            {current.kind === "bot" ? "Deterministic bot" : "Human seat"} · {snapshot.config.mode} /{" "}
            {snapshot.config.profile}
          </p>
        </div>
        <dl>
          <div>
            <dt>Turn</dt>
            <dd data-testid="turn-count">{snapshot.turn_count}</dd>
          </div>
          <div>
            <dt>Rolls</dt>
            <dd data-testid="roll-count">{rolls}</dd>
          </div>
        </dl>
      </div>
      <div className={styles.players}>
        {snapshot.players.map((player) => {
          const spec = PLAYER_SPECS[player.index]!;
          const finished = player.tokens.filter(
            (token) => token.steps === snapshot.config.home_finish,
          ).length;
          return (
            <article
              className={`${styles.player} ${player.index === snapshot.current_player ? styles.active : ""}`}
              key={player.index}
              style={{ borderLeftColor: spec.hex }}
            >
              <div className={styles.playerTop}>
                <span className={styles.dot} style={{ background: spec.hex }} aria-hidden="true" />
                <h3>{player.name}</h3>
                <span className={styles.kind}>{player.kind}</span>
              </div>
              <dl>
                <div>
                  <dt>Home</dt>
                  <dd>
                    {finished}/{player.tokens.length}
                  </dd>
                </div>
                <div>
                  <dt>Captures</dt>
                  <dd>{player.captures_made}</dd>
                </div>
              </dl>
              <div className={styles.tokenRow} aria-label={`${player.name} token positions`}>
                {player.tokens.map((token) => (
                  <span
                    key={token.label}
                    className={token.steps === snapshot.config.home_finish ? styles.finished : ""}
                  >
                    {token.label}:{" "}
                    {token.steps === -1
                      ? "Yard"
                      : token.steps === snapshot.config.home_finish
                        ? "Home"
                        : token.steps}
                  </span>
                ))}
              </div>
            </article>
          );
        })}
      </div>
      {snapshot.finish_order.length > 0 ? (
        <p className={styles.podium}>
          <strong>Finish order:</strong>{" "}
          {snapshot.finish_order.map((index) => snapshot.players[index]!.name).join(" · ")}
        </p>
      ) : null}
    </section>
  );
}
