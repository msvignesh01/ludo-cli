import type { MatchController } from "../../match/controller";
import type { CanonicalSnapshot, CommentaryMode, Speed } from "../../game/types";
import styles from "./PlaybackControls.module.css";

export function PlaybackControls({
  controller,
  snapshot,
  onDraw,
  onQuit,
  onExport,
  onResetView,
}: {
  controller: MatchController;
  snapshot: CanonicalSnapshot;
  onDraw: () => void;
  onQuit: () => void;
  onExport: () => void;
  onResetView: () => void;
}) {
  const current = snapshot.players[snapshot.current_player]!;
  const playing = snapshot.status === "PLAYING";
  const pending = controller.getPendingRoll() !== null;
  const paused = controller.isPaused();
  const canStep = current.kind === "bot" || controller.getAutoplay();

  return (
    <section className={styles.controls} aria-labelledby="controls-heading">
      <div className={styles.heading}>
        <div>
          <p className="eyebrow">Table controls</p>
          <h2 id="controls-heading">Playback</h2>
        </div>
        {pending ? <span className={styles.roll}>Roll {controller.getPendingRoll()}</span> : null}
      </div>
      <div className={styles.primary}>
        <button
          className="button buttonPrimary"
          type="button"
          disabled={!playing || pending || current.kind !== "human"}
          onClick={() => controller.rollHuman()}
        >
          Roll
        </button>
        <button
          className="button"
          type="button"
          disabled={!playing || !canStep || pending}
          onClick={() => controller.step()}
        >
          Step
        </button>
        <button
          className="button"
          type="button"
          disabled={!playing}
          onClick={() => controller.setPaused(!paused)}
        >
          {paused ? "Resume" : "Pause"}
        </button>
      </div>
      <div className={styles.settings}>
        <label className="field">
          <span>Speed</span>
          <select
            aria-label="Speed"
            className="select"
            value={controller.getSpeed()}
            onChange={(event) => controller.setSpeed(event.target.value as Speed)}
          >
            <option value="slow">Slow</option>
            <option value="normal">Normal</option>
            <option value="fast">Fast</option>
          </select>
        </label>
        <label className="field">
          <span>Commentary</span>
          <select
            aria-label="Commentary"
            className="select"
            value={controller.getCommentaryMode()}
            onChange={(event) => controller.setCommentary(event.target.value as CommentaryMode)}
          >
            <option value="gameplay">Gameplay</option>
            <option value="code">Code</option>
            <option value="both">Both</option>
            <option value="off">Off</option>
          </select>
        </label>
      </div>
      <label className="checkbox">
        <input
          type="checkbox"
          checked={controller.getAutoplay()}
          onChange={(event) => controller.setAutoplay(event.target.checked)}
        />
        <span>Autoplay human seats</span>
      </label>
      <label className="checkbox">
        <input
          type="checkbox"
          checked={controller.getReducedMotion()}
          onChange={(event) => controller.setReducedMotion(event.target.checked)}
        />
        <span>Reduce motion</span>
      </label>
      <div className={styles.secondary}>
        <button className="button buttonSmall" type="button" onClick={onResetView}>
          Reset view
        </button>
        {playing ? (
          <button className="button buttonSmall" type="button" onClick={onExport}>
            Export match
          </button>
        ) : null}
        <button
          className="button buttonDanger buttonSmall"
          type="button"
          disabled={!playing}
          onClick={onDraw}
        >
          Draw
        </button>
        <button
          className="button buttonDanger buttonSmall"
          type="button"
          disabled={!playing}
          onClick={onQuit}
        >
          Quit
        </button>
      </div>
      <p className={styles.event}>{snapshot.last_event}</p>
    </section>
  );
}
