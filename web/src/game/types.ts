export type Mode = "quick" | "classic";
export type Profile = "showcase" | "classic";
export type Blockades = "none" | "strict" | "safe_pair";
export type CommentaryMode = "gameplay" | "code" | "both" | "off";
export type PlayerKind = "human" | "bot";
export type MatchStatus = "PLAYING" | "WON" | "DRAW" | "QUIT";
export type Speed = "slow" | "normal" | "fast";
export type UiMode = "cli" | "gui";

export interface MatchConfig {
  mode: Mode;
  profile: Profile;
  player_count: number;
  track_len: number;
  home_len: number;
  tokens_per_player: number;
  outer_last_step: number;
  home_finish: number;
  safe_tiles: number[];
  start_indices_2p: number[];
  start_indices_4p: number[];
  default_max_turns: number;
  auto_delay: number;
  commentary: CommentaryMode;
  ui: UiMode;
  seed: number | null;
  blockades: Blockades;
  kill_to_enter: boolean;
  podium_mode: boolean;
  exact_home_roll: boolean;
  triple_six_forfeit: boolean;
  safe_tiles_enabled: boolean;
  bonus_on_capture: boolean;
  bonus_on_home: boolean;
  max_turns: number;
}

export interface CanonicalToken {
  label: string;
  steps: number;
}

export interface CanonicalPlayer {
  index: number;
  name: string;
  kind: PlayerKind;
  color: string;
  start_index: number;
  captures_made: number;
  tokens: CanonicalToken[];
}

export interface GameEvent {
  type: string;
  turn: number;
  player: number | null;
  data: Record<string, unknown>;
}

export interface CanonicalSnapshot {
  config: MatchConfig;
  max_turns: number;
  turn_count: number;
  current_player: number;
  consecutive_sixes: number;
  status: MatchStatus;
  winner_index: number | null;
  draw_reason: string | null;
  finish_order: number[];
  last_event: string;
  events: GameEvent[];
  players: CanonicalPlayer[];
}

export interface InternalToken extends CanonicalToken {
  token_idx: number;
}

export interface InternalPlayer extends Omit<CanonicalPlayer, "tokens"> {
  color_hex: string;
  color_code: string;
  prefix: string;
  tokens: InternalToken[];
}

export interface IllegalMovePreview {
  legal: false;
  reason: string;
}

export interface LegalMovePreview {
  legal: true;
  label: string;
  token_idx: number;
  old_steps: number;
  new_steps: number;
  old_position: string;
  new_position: string;
  global_pos: number | null;
  captured: string[];
  reached_home: boolean;
  safe: boolean;
  wrapped: boolean;
  blockade_formed: boolean;
}

export type MovePreview = IllegalMovePreview | LegalMovePreview;

export interface RollResult {
  event: "SELECT_MOVE" | "NO_VALID_MOVES" | "TRIPLE_SIX_FORFEIT";
  valid_moves: number[];
}

export interface MoveResult {
  old_steps: number;
  new_steps: number;
  captured: string[];
  reached_home: boolean;
  wrapped: boolean;
  player_finished: boolean;
  won: boolean;
  bonus_turn: boolean;
  blockade_formed: boolean;
}

export interface ResolvedSetup {
  config: MatchConfig;
  names: string[];
  kinds: PlayerKind[];
  autoplay: boolean;
}

export type SetupInput = Record<string, unknown>;
