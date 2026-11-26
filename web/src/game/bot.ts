import { getGlobalPos, isSafeTile, previewMove } from "./queries";
import type { BotDecision, BotReason, InternalGame } from "./types";

function canBeCaptured(game: InternalGame, playerIndex: number, globalPos: number | null): boolean {
  if (globalPos === null || isSafeTile(game, globalPos)) return false;
  for (const opponent of game.players) {
    if (opponent.index === playerIndex) continue;
    for (const token of opponent.tokens) {
      const opponentPos = getGlobalPos(
        opponent.start_index,
        token.steps,
        game.config.track_len,
        game.config.outer_last_step,
      );
      if (opponentPos === null) continue;
      const trackLength = game.config.track_len;
      const distance = (((globalPos - opponentPos) % trackLength) + trackLength) % trackLength;
      if (distance >= 1 && distance <= 6) return true;
    }
  }
  return false;
}

function tokenInDanger(game: InternalGame, playerIndex: number, tokenIndex: number): boolean {
  const player = game.players[playerIndex]!;
  const token = player.tokens[tokenIndex]!;
  const globalPos = getGlobalPos(
    player.start_index,
    token.steps,
    game.config.track_len,
    game.config.outer_last_step,
  );
  return canBeCaptured(game, playerIndex, globalPos);
}

export function scoreMove(
  game: InternalGame,
  playerIndex: number,
  tokenIndex: number,
  roll: number,
): [number, number, number, number, number, number, number] {
  const player = game.players[playerIndex]!;
  const preview = previewMove(game, playerIndex, tokenIndex, roll);
  if (!preview.legal) throw new Error("Bot score requires a legal move");
  const captured = preview.captured.length;
  const unlock = game.config.kill_to_enter && player.captures_made === 0 && captured > 0;
  const escape =
    tokenInDanger(game, playerIndex, tokenIndex) &&
    !canBeCaptured(game, playerIndex, preview.global_pos);
  const progress = preview.new_steps + (preview.wrapped ? game.config.track_len : 0);
  return [
    Number(preview.reached_home),
    captured,
    Number(unlock),
    Number(preview.safe),
    Number(escape),
    progress,
    tokenIndex === 0 ? 0 : -tokenIndex,
  ];
}

function compareScores(left: number[], right: number[]): number {
  for (let index = 0; index < left.length; index += 1) {
    const difference = left[index]! - right[index]!;
    if (difference !== 0) return difference;
  }
  return 0;
}

export function decisionDetails(
  game: InternalGame,
  playerIndex: number,
  roll: number,
  validMoves: number[],
): BotDecision {
  if (validMoves.length === 0) return { token_idx: null, reason: "No legal moves" };
  let tokenIndex = validMoves[0]!;
  let bestScore = scoreMove(game, playerIndex, tokenIndex, roll);
  for (const candidate of validMoves.slice(1)) {
    const candidateScore = scoreMove(game, playerIndex, candidate, roll);
    if (compareScores(candidateScore, bestScore) > 0) {
      tokenIndex = candidate;
      bestScore = candidateScore;
    }
  }

  const player = game.players[playerIndex]!;
  const preview = previewMove(game, playerIndex, tokenIndex, roll);
  if (!preview.legal) throw new Error("Bot decision requires a legal move");
  let reason: BotReason;
  if (preview.reached_home) {
    reason = "Finish Home";
  } else if (
    preview.captured.length > 0 &&
    game.config.kill_to_enter &&
    player.captures_made === 0
  ) {
    reason = "Unlock Kill-to-Enter";
  } else if (preview.captured.length > 0) {
    reason = "Capture";
  } else if (preview.safe) {
    reason = "Safe tile";
  } else if (
    tokenInDanger(game, playerIndex, tokenIndex) &&
    !canBeCaptured(game, playerIndex, preview.global_pos)
  ) {
    reason = "Escape danger";
  } else {
    reason = "Advance furthest";
  }
  return { token_idx: tokenIndex, reason };
}

export function chooseMove(
  game: InternalGame,
  playerIndex: number,
  roll: number,
  validMoves: number[],
): number | null {
  return decisionDetails(game, playerIndex, roll, validMoves).token_idx;
}
