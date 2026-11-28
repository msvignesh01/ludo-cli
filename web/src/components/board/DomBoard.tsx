import type { CSSProperties } from "react";
import { buildGuiViewModel } from "../../game/view-model";
import type { BoardMarker } from "../../game/view-model";
import type { CanonicalSnapshot, LegalMovePreview } from "../../game/types";
import type { Cell } from "../../game/geometry";
import styles from "./DomBoard.module.css";

function cellStyle(cell: Cell): CSSProperties {
  return { gridColumn: cell[0] + 1, gridRow: cell[1] + 1 };
}

function targetCell(preview: LegalMovePreview, view: ReturnType<typeof buildGuiViewModel>): Cell {
  if (preview.global_pos !== null) return view.geometry.track_cells[preview.global_pos]!;
  if (preview.reached_home) return view.geometry.home_center;
  const laneIndex = preview.new_steps - (view.config.track_len - 1);
  return view.geometry.home_cells[view.current_player]![laneIndex] ?? view.geometry.home_center;
}

function markerPosition(
  marker: BoardMarker,
  size: number,
  stackIndex: number,
  stackSize: number,
): CSSProperties {
  const offset = (stackIndex - (stackSize - 1) / 2) * 0.2;
  return {
    left: `${((marker.cell[0] + 0.5 + offset) / size) * 100}%`,
    top: `${((marker.cell[1] + 0.5 + offset) / size) * 100}%`,
    width: `${62 / size}%`,
    backgroundColor: marker.color_hex,
    borderColor: marker.location === "finished" ? "#d4a24c" : "#f7f3ea",
  };
}

export function DomBoard({
  snapshot,
  previews,
}: {
  snapshot: CanonicalSnapshot;
  previews: LegalMovePreview[];
}) {
  const view = buildGuiViewModel(snapshot);
  const { geometry } = view;
  const gridStyle = { "--grid-size": geometry.size } as CSSProperties;
  const starts = new Set(view.start_tiles);
  const safe = new Set(view.safe_tiles);
  const targets = new Set(previews.map((preview) => targetCell(preview, view).join(",")));
  const stacks = new Map<string, BoardMarker[]>();
  for (const marker of view.markers) {
    const key = marker.cell.join(",");
    const stack = stacks.get(key) ?? [];
    stack.push(marker);
    stacks.set(key, stack);
  }

  return (
    <div
      className={styles.board}
      style={gridStyle}
      data-testid="dom-board"
      data-mode={snapshot.config.mode}
      role="group"
      aria-label={`${snapshot.config.mode} Ludo board. ${snapshot.players[snapshot.current_player]!.name} to play.`}
    >
      {geometry.yard_boxes.map((box, playerIndex) => {
        const player = snapshot.players[playerIndex]!;
        return (
          <div
            className={styles.yard}
            key={`yard-${playerIndex}`}
            style={{
              gridColumn: `${box[0] + 1} / ${box[2] + 2}`,
              gridRow: `${box[1] + 1} / ${box[3] + 2}`,
              borderColor: player.color,
              background: `color-mix(in srgb, ${player.color} 11%, var(--ivory))`,
            }}
          >
            <span style={{ background: player.color }} aria-hidden="true" />
            <strong>{player.name}</strong>
          </div>
        );
      })}

      {geometry.track_cells.map((cell, tileIndex) => (
        <div
          className={`${styles.cell} ${styles.track} ${safe.has(tileIndex) ? styles.safe : ""}`}
          style={cellStyle(cell)}
          key={`track-${tileIndex}`}
          aria-label={`Track tile ${tileIndex}${safe.has(tileIndex) ? ", safe" : ""}${starts.has(tileIndex) ? ", start" : ""}`}
        >
          <small>{String(tileIndex).padStart(2, "0")}</small>
          {safe.has(tileIndex) ? <i aria-hidden="true" /> : null}
          {starts.has(tileIndex) ? <b aria-hidden="true" /> : null}
        </div>
      ))}

      {geometry.home_cells.map((lane, playerIndex) => {
        const player = snapshot.players[playerIndex]!;
        return lane.map((cell, laneIndex) => (
          <div
            className={`${styles.cell} ${styles.home}`}
            style={{
              ...cellStyle(cell),
              background: `color-mix(in srgb, ${player.color} 22%, #fffdf8)`,
            }}
            key={`home-${playerIndex}-${laneIndex}`}
            aria-label={`${player.name} Home lane ${laneIndex + 1}`}
          >
            <small>{laneIndex + 1}</small>
          </div>
        ));
      })}

      <div className={styles.center} style={cellStyle(geometry.home_center)}>
        <span>Ludo</span>
        <small>Home</small>
      </div>

      {previews.map((preview) => (
        <span
          className={styles.target}
          style={cellStyle(targetCell(preview, view))}
          key={`target-${preview.token_idx}`}
          aria-hidden="true"
        />
      ))}

      {view.markers.map((marker) => {
        const stack = stacks.get(marker.cell.join(","))!;
        const stackIndex = stack.findIndex(
          (item) =>
            item.player_index === marker.player_index && item.token_idx === marker.token_idx,
        );
        const position = markerPosition(marker, geometry.size, stackIndex, stack.length);
        const targetKey = targets.has(marker.cell.join(","));
        return (
          <span
            className={`${styles.token} ${targetKey ? styles.targetToken : ""}`}
            style={position}
            key={`${marker.player_index}-${marker.token_idx}`}
            aria-hidden="true"
          >
            {marker.label}
          </span>
        );
      })}

      <ol className={styles.hiddenTokens}>
        {view.markers.map((marker) => (
          <li key={`position-${marker.player_index}-${marker.token_idx}`}>
            {snapshot.players[marker.player_index]!.name}, {marker.label}: {marker.location}
            {marker.global_pos === null ? "" : `, track tile ${marker.global_pos}`}
          </li>
        ))}
      </ol>
    </div>
  );
}
