import { makeEvent } from "./events";
import { allFinished, capturableTokens, getValidMoves, previewMove } from "./queries";
import type { GameEvent, InternalGame, MoveResult, RollResult } from "./types";

function emit(
  game: InternalGame,
  eventType: string,
  playerIndex: number | null,
  data: Record<string, unknown> = {},
): void {
  game.events.push(makeEvent(eventType, game.turn_count, playerIndex, data));
}

export function processRoll(game: InternalGame, roll: number): RollResult {
  const playerIndex = game.current_player;
  emit(game, "DICE_ROLLED", playerIndex, { roll });
  if (roll === 6) {
    game.consecutive_sixes += 1;
    if (game.config.triple_six_forfeit && game.consecutive_sixes === 3) {
      game.consecutive_sixes = 0;
      game.last_event = "Third consecutive six forfeited.";
      emit(game, "TRIPLE_SIX_FORFEIT", playerIndex);
      advanceTurn(game);
      return { event: "TRIPLE_SIX_FORFEIT", valid_moves: [] };
    }
  } else {
    game.consecutive_sixes = 0;
  }

  const validMoves = getValidMoves(game, playerIndex, roll);
  if (validMoves.length === 0) {
    game.consecutive_sixes = 0;
    game.last_event = `No legal move for roll ${roll}; turn skipped.`;
    emit(game, "NO_VALID_MOVES", playerIndex, { roll });
    advanceTurn(game);
    return { event: "NO_VALID_MOVES", valid_moves: [] };
  }
  game.last_event = `Rolled ${roll}; choose a token.`;
  return { event: "SELECT_MOVE", valid_moves: validMoves };
}

export function applyMove(game: InternalGame, tokenIndex: number, roll: number): MoveResult {
  const playerIndex = game.current_player;
  const player = game.players[playerIndex]!;
  const token = player.tokens[tokenIndex]!;
  const preview = previewMove(game, playerIndex, tokenIndex, roll);
  if (!preview.legal) throw new Error("Illegal move");

  const oldSteps = token.steps;
  token.steps = preview.new_steps;
  emit(game, "TOKEN_MOVED", playerIndex, {
    token: token.label,
    token_idx: tokenIndex,
    roll,
    old_steps: oldSteps,
    new_steps: preview.new_steps,
    wrapped: preview.wrapped,
  });

  const capturedLabels: string[] = [];
  for (const [owner, victim] of capturableTokens(game, player, preview.global_pos)) {
    victim.steps = -1;
    player.captures_made += 1;
    capturedLabels.push(`${owner.name}'s ${victim.label}`);
    emit(game, "TOKEN_CAPTURED", playerIndex, {
      mover: token.label,
      victim_player: owner.index,
      victim_token: victim.label,
    });
  }

  if (preview.blockade_formed && preview.global_pos !== null) {
    emit(game, "BLOCKADE_FORMED", playerIndex, {
      tile: preview.global_pos,
      token: token.label,
    });
  }

  const reachedHome = preview.reached_home;
  if (reachedHome) game.consecutive_sixes = 0;
  const playerFinished = allFinished(player, game.config.home_finish);
  if (playerFinished && !game.finish_order.includes(playerIndex)) {
    game.finish_order.push(playerIndex);
    emit(game, "PLAYER_FINISHED", playerIndex, { place: game.finish_order.length });
  }

  const requiredFinishers = game.config.podium_mode ? game.config.player_count - 1 : 1;
  const won = playerFinished && game.finish_order.length >= requiredFinishers;
  let bonusTurn = false;
  if (won) {
    game.status = "WON";
    game.winner_index = game.finish_order[0]!;
    game.last_event = `${game.players[game.winner_index]!.name} wins!`;
    emit(game, "GAME_WON", game.winner_index, { finish_order: [...game.finish_order] });
  } else if (playerFinished) {
    game.last_event = `${player.name} finished; advancing to the remaining players.`;
    advanceTurn(game);
  } else {
    bonusTurn =
      roll === 6 ||
      (capturedLabels.length > 0 && game.config.bonus_on_capture) ||
      (reachedHome && game.config.bonus_on_home);
    if (bonusTurn) {
      game.last_event = `Bonus roll for ${player.name}.`;
      emit(game, "BONUS_TURN", playerIndex, { roll });
    } else {
      game.consecutive_sixes = 0;
      advanceTurn(game);
    }
  }

  return {
    old_steps: oldSteps,
    new_steps: preview.new_steps,
    captured: capturedLabels,
    reached_home: reachedHome,
    wrapped: preview.wrapped,
    player_finished: playerFinished,
    won,
    bonus_turn: bonusTurn,
    blockade_formed: preview.blockade_formed,
  };
}

export function recordBotDecision(
  game: InternalGame,
  tokenIndex: number,
  roll: number,
  reason: string,
): void {
  const player = game.players[game.current_player]!;
  emit(game, "BOT_DECISION", player.index, {
    token: player.tokens[tokenIndex]!.label,
    token_idx: tokenIndex,
    roll,
    reason,
  });
}

export function advanceTurn(game: InternalGame): void {
  if (game.status !== "PLAYING") return;
  game.consecutive_sixes = 0;
  for (let offset = 1; offset <= game.players.length; offset += 1) {
    const candidate = (game.current_player + offset) % game.players.length;
    if (!allFinished(game.players[candidate]!, game.config.home_finish)) {
      game.current_player = candidate;
      break;
    }
  }
  game.turn_count += 1;
  emit(game, "TURN_ADVANCED", game.current_player);
  if (game.turn_count >= game.max_turns) {
    game.status = "DRAW";
    game.draw_reason = "Maximum turn limit reached";
    game.last_event = game.draw_reason;
    emit(game, "GAME_DRAW", null, { reason: game.draw_reason });
  }
}

export function declareMutualDraw(game: InternalGame): void {
  game.status = "DRAW";
  game.draw_reason = "Mutual agreement";
  game.last_event = game.draw_reason;
  emit(game, "GAME_DRAW", null, { reason: game.draw_reason });
}

export function quitGame(game: InternalGame): void {
  game.status = "QUIT";
  game.last_event = "Game quit.";
  emit(game, "GAME_QUIT", null);
}

export function cloneEvent(event: GameEvent): GameEvent {
  return {
    type: event.type,
    turn: event.turn,
    player: event.player,
    data: cloneValue(event.data),
  };
}

export function cloneValue<T>(value: T): T {
  if (Array.isArray(value)) {
    return value.map((item) => cloneValue(item)) as T;
  }
  if (value !== null && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value).map(([key, item]) => [key, cloneValue(item)]),
    ) as T;
  }
  return value;
}
