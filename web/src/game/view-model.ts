import { getStartIndices } from "./config";
import { buildBoardGeometry } from "./geometry";
import type { BoardGeometry, Cell } from "./geometry";
import { PLAYER_SPECS } from "./presets";
import type { CanonicalPlayer, CanonicalSnapshot, MatchConfig, MatchStatus } from "./types";

export type MarkerLocation = "base" | "track" | "home" | "finished";

export interface BoardMarker {
  player_index: number;
  token_idx: number;
  label: string;
  steps: number;
  location: MarkerLocation;
  global_pos: number | null;
  cell: Cell;
  color: string;
  color_hex: string;
  prefix: string;
}

export interface ViewPlayer extends CanonicalPlayer {
  color_hex: string;
  prefix: string;
}

export interface BoardViewModel {
  config: MatchConfig;
  geometry: BoardGeometry;
  markers: BoardMarker[];
  players: ViewPlayer[];
  safe_tiles: number[];
  start_tiles: number[];
  current_player: number;
  turn_count: number;
  status: MatchStatus;
  winner_index: number | null;
  draw_reason: string | null;
  last_event: string;
}

export function buildGuiViewModel(
  snapshot: CanonicalSnapshot,
  geometry?: BoardGeometry,
): BoardViewModel {
  const config = snapshot.config;
  const board = geometry ?? buildBoardGeometry(config);
  const markers: BoardMarker[] = [];

  for (const player of snapshot.players) {
    const playerIndex = player.index;
    const spec = PLAYER_SPECS[playerIndex]!;
    for (let tokenIndex = 0; tokenIndex < player.tokens.length; tokenIndex += 1) {
      const token = player.tokens[tokenIndex]!;
      const steps = token.steps;
      let globalPos: number | null = null;
      let location: MarkerLocation;
      let cell: Cell;
      if (steps === -1) {
        location = "base";
        const box = board.yard_boxes[playerIndex]!;
        cell = [(box[0] + box[2]) / 2, (box[1] + box[3]) / 2];
      } else if (steps === config.home_finish) {
        location = "finished";
        cell = [...board.home_center];
      } else if (steps >= config.track_len - 1) {
        location = "home";
        const laneIndex = steps - (config.track_len - 1);
        cell = [...board.home_cells[playerIndex]![laneIndex]!];
      } else {
        location = "track";
        globalPos = (player.start_index + steps) % config.track_len;
        cell = [...board.track_cells[globalPos]!];
      }
      markers.push({
        player_index: playerIndex,
        token_idx: tokenIndex,
        label: token.label,
        steps,
        location,
        global_pos: globalPos,
        cell,
        color: player.color,
        color_hex: spec.hex,
        prefix: spec.prefix,
      });
    }
  }

  return {
    config,
    geometry: board,
    markers,
    players: snapshot.players.map((player) => ({
      ...player,
      color_hex: PLAYER_SPECS[player.index]!.hex,
      prefix: PLAYER_SPECS[player.index]!.prefix,
    })),
    safe_tiles: config.safe_tiles_enabled ? [...config.safe_tiles] : [],
    start_tiles: getStartIndices(config),
    current_player: snapshot.current_player,
    turn_count: snapshot.turn_count,
    status: snapshot.status,
    winner_index: snapshot.winner_index,
    draw_reason: snapshot.draw_reason,
    last_event: snapshot.last_event,
  };
}
