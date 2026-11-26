import type { GameEvent } from "./types";

export const EVENT_TYPES = [
  "GAME_STARTED",
  "DICE_ROLLED",
  "NO_VALID_MOVES",
  "TRIPLE_SIX_FORFEIT",
  "BOT_DECISION",
  "TOKEN_MOVED",
  "TOKEN_CAPTURED",
  "BLOCKADE_FORMED",
  "PLAYER_FINISHED",
  "BONUS_TURN",
  "TURN_ADVANCED",
  "GAME_WON",
  "GAME_DRAW",
  "GAME_QUIT",
] as const;

const EVENT_TYPE_SET = new Set<string>(EVENT_TYPES);

export function makeEvent(
  eventType: string,
  turn: number,
  player: number | null,
  data: Record<string, unknown> = {},
): GameEvent {
  if (!EVENT_TYPE_SET.has(eventType)) throw new Error(`unknown event type: ${eventType}`);
  return { type: eventType, turn, player, data: { ...data } };
}
