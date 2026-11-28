"use client";

import { useEffect, useState } from "react";
import type { LegalMovePreview } from "../../game/types";
import type { MatchController } from "../../match/controller";
import { useMatch } from "../../match/MatchProvider";
import { exportMatch } from "../../match/persistence";
import { BoardCanvas } from "../board/BoardCanvas";
import { DomBoard } from "../board/DomBoard";
import { CommentaryPanel } from "./CommentaryPanel";
import { DrawDialog } from "./DrawDialog";
import { MatchHud } from "./MatchHud";
import { PlaybackControls } from "./PlaybackControls";
import { QuitDialog } from "./QuitDialog";
import { ResultPanel } from "./ResultPanel";
import { TokenChoiceList } from "./TokenChoiceList";
import styles from "./MatchScreen.module.css";

export function MatchScreen({
  controller,
  onNewMatch,
}: {
  controller: MatchController;
  onNewMatch: () => void;
}) {
  const { revision } = useMatch();
  const snapshot = controller.getSnapshot();
  const [messages, setMessages] = useState<string[]>([]);
  const [drawOpen, setDrawOpen] = useState(false);
  const [drawSession, setDrawSession] = useState(0);
  const [quitOpen, setQuitOpen] = useState(false);
  const [resetSignal, setResetSignal] = useState(0);
  const [webglAvailable, setWebglAvailable] = useState(false);
  const [exportError, setExportError] = useState("");
  const pendingRoll = controller.getPendingRoll();
  const previews = controller
    .getPreviews()
    .filter((preview): preview is LegalMovePreview => preview.legal);

  useEffect(() => {
    let active = true;
    queueMicrotask(() => {
      if (!active) return;
      const next = controller.drainCommentary();
      if (next.length > 0) setMessages((current) => [...current, ...next].slice(-200));
    });
    return () => {
      active = false;
    };
  }, [controller, revision]);

  function downloadMatch(): void {
    try {
      const text = exportMatch(controller);
      const url = URL.createObjectURL(new Blob([text], { type: "application/json" }));
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "ludo-match.json";
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      setTimeout(() => URL.revokeObjectURL(url), 0);
      setExportError("");
    } catch (error) {
      setExportError(error instanceof Error ? error.message : "Match export failed.");
    }
  }

  return (
    <main className={styles.page}>
      <header className={styles.masthead}>
        <div className={styles.brand}>
          <span className={styles.brandMark} aria-hidden="true" />
          <span>Ludo Showcase</span>
        </div>
        <div className={styles.tableLabel}>
          <span>{snapshot.config.mode} table</span>
          <span>{snapshot.config.player_count} players</span>
        </div>
      </header>

      <div className={styles.layout}>
        <section className={styles.boardPanel} aria-labelledby="board-title">
          <div className={styles.boardHeading}>
            <div>
              <p className="eyebrow">Live board</p>
              <h1 id="board-title">The local table</h1>
            </div>
            <span className={styles.viewStatus}>
              {webglAvailable ? "3D presentation" : "Accessible board"}
            </span>
          </div>
          <div className={styles.boardStage}>
            <DomBoard snapshot={snapshot} previews={previews} />
            <div className={`${styles.canvasLayer} ${webglAvailable ? styles.canvasVisible : ""}`}>
              <BoardCanvas
                snapshot={snapshot}
                previews={previews}
                resetSignal={resetSignal}
                onAvailability={setWebglAvailable}
              />
            </div>
          </div>
          <div className={styles.boardFooter}>
            <p>
              Gold rings mark legal destinations. Each player has a distinct token shape in the 3D
              view.
            </p>
            <span>
              Turn {snapshot.turn_count} / {snapshot.max_turns}
            </span>
          </div>
        </section>

        <aside className={styles.rail} aria-label="Match controls and score">
          <ResultPanel snapshot={snapshot} onExport={downloadMatch} onNewMatch={onNewMatch} />
          <MatchHud snapshot={snapshot} />
          <PlaybackControls
            controller={controller}
            snapshot={snapshot}
            onDraw={() => {
              setDrawSession((value) => value + 1);
              setDrawOpen(true);
            }}
            onQuit={() => setQuitOpen(true)}
            onExport={downloadMatch}
            onResetView={() => setResetSignal((value) => value + 1)}
          />
          {pendingRoll !== null ? (
            <TokenChoiceList
              previews={previews}
              pendingRoll={pendingRoll}
              onSelect={(tokenIndex) => controller.selectMove(tokenIndex)}
            />
          ) : null}
          {exportError ? (
            <p className="alert" role="alert">
              {exportError}
            </p>
          ) : null}
          <CommentaryPanel messages={messages} mode={controller.getCommentaryMode()} />
        </aside>
      </div>

      <DrawDialog
        key={drawSession}
        open={drawOpen}
        snapshot={snapshot}
        controller={controller}
        onClose={() => setDrawOpen(false)}
      />
      <QuitDialog open={quitOpen} controller={controller} onClose={() => setQuitOpen(false)} />
    </main>
  );
}
