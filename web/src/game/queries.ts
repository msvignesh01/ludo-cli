import type {
  InternalGame,
  InternalPlayer,
  InternalToken,
  LegalMovePreview,
  MovePreview,
} from "./types";

export interface ComputedTarget {
  newSteps: number;
  wrapped: boolean;
  path: number[];
}

export function getGlobalPos(
  startIndex: number,
  steps: number,
  trackLen: number,
  outerLastStep: number,
): number | null {
  if (steps < 0 || steps > outerLastStep) return null;
  return (startIndex + steps) % trackLen;
}

export function isSafeTile(game: InternalGame, globalPos: number | null): boolean {
  return (
    game.config.safe_tiles_enabled &&
    globalPos !== null &&
    game.config.safe_tiles.includes(globalPos)
  );
}

export function formatPosition(game: InternalGame, startIndex: number, steps: number): string {
  const config = game.config;
  if (steps === -1) return "BASE";
  if (steps === config.home_finish) return "HOME";
  if (steps >= config.track_len - 1) {
    return `H${steps - (config.track_len - 1) + 1}`;
  }
  const globalPos = getGlobalPos(startIndex, steps, config.track_len, config.outer_last_step);
  return globalPos === null ? "BASE" : `T${String(globalPos).padStart(2, "0")}`;
}

export function allFinished(player: InternalPlayer, homeFinish: number): boolean {
  return player.tokens.every((token) => token.steps === homeFinish);
}

export function tokensAt(
  game: InternalGame,
  player: InternalPlayer,
  globalPos: number,
): InternalToken[] {
  const config = game.config;
  return player.tokens.filter(
    (token) =>
      getGlobalPos(player.start_index, token.steps, config.track_len, config.outer_last_step) ===
      globalPos,
  );
}

export function killLocked(game: InternalGame, player: InternalPlayer): boolean {
  return game.config.kill_to_enter && player.captures_made === 0;
}

export function computeTarget(
  game: InternalGame,
  player: InternalPlayer,
  token: InternalToken,
  roll: number,
): ComputedTarget | null {
  const config = game.config;
  if (token.steps === -1) {
    return roll === 6 ? { newSteps: 0, wrapped: false, path: [0] } : null;
  }
  if (token.steps === config.home_finish) return null;

  const oldSteps = token.steps;
  const rawTarget = oldSteps + roll;
  if (
    killLocked(game, player) &&
    oldSteps >= 0 &&
    oldSteps <= config.outer_last_step &&
    rawTarget >= config.track_len - 1
  ) {
    const lapLength = config.track_len - 1;
    const newSteps = rawTarget % lapLength;
    const path = Array.from(
      { length: config.outer_last_step - oldSteps },
      (_, index) => oldSteps + index + 1,
    );
    path.push(...Array.from({ length: newSteps + 1 }, (_, index) => index));
    return { newSteps, wrapped: true, path };
  }

  let newSteps: number;
  if (rawTarget > config.home_finish) {
    if (config.exact_home_roll) return null;
    newSteps = config.home_finish;
  } else {
    newSteps = rawTarget;
  }
  const path: number[] = [];
  for (let steps = oldSteps + 1; steps <= newSteps; steps += 1) {
    if (steps <= config.outer_last_step) path.push(steps);
  }
  return { newSteps, wrapped: false, path };
}

function globalPath(game: InternalGame, player: InternalPlayer, path: number[]): number[] {
  const positions: number[] = [];
  for (const steps of path) {
    const globalPos = getGlobalPos(
      player.start_index,
      steps,
      game.config.track_len,
      game.config.outer_last_step,
    );
    if (globalPos !== null) positions.push(globalPos);
  }
  return positions;
}

export function strictPathBlocked(
  game: InternalGame,
  player: InternalPlayer,
  path: number[],
): boolean {
  if (game.config.blockades !== "strict") return false;
  for (const globalPos of globalPath(game, player, path)) {
    for (const opponent of game.players) {
      if (opponent.index !== player.index && tokensAt(game, opponent, globalPos).length >= 2) {
        return true;
      }
    }
  }
  return false;
}

export function capturableTokens(
  game: InternalGame,
  player: InternalPlayer,
  globalPos: number | null,
): Array<[InternalPlayer, InternalToken]> {
  if (globalPos === null || isSafeTile(game, globalPos)) return [];
  const captured: Array<[InternalPlayer, InternalToken]> = [];
  for (const opponent of game.players) {
    if (opponent.index === player.index) continue;
    const tokens = tokensAt(game, opponent, globalPos);
    if (game.config.blockades === "safe_pair" && tokens.length >= 2) continue;
    captured.push(...tokens.map((token): [InternalPlayer, InternalToken] => [opponent, token]));
  }
  return captured;
}

export function previewMove(
  game: InternalGame,
  playerIndex: number,
  tokenIndex: number,
  roll: number,
): MovePreview {
  const player = game.players[playerIndex]!;
  const token = player.tokens[tokenIndex]!;
  const target = computeTarget(game, player, token, roll);
  if (target === null) {
    return { legal: false, reason: "Move is not legal for this roll." };
  }
  if (strictPathBlocked(game, player, target.path)) {
    return { legal: false, reason: "A strict blockade blocks the path." };
  }

  const globalPos = getGlobalPos(
    player.start_index,
    target.newSteps,
    game.config.track_len,
    game.config.outer_last_step,
  );
  const captured = capturableTokens(game, player, globalPos);
  const friendlyBefore = globalPos === null ? 0 : tokensAt(game, player, globalPos).length;
  const blockadeFormed = globalPos !== null && friendlyBefore < 2 && friendlyBefore + 1 >= 2;
  const preview: LegalMovePreview = {
    legal: true,
    label: token.label,
    token_idx: tokenIndex,
    old_steps: token.steps,
    new_steps: target.newSteps,
    old_position: formatPosition(game, player.start_index, token.steps),
    new_position: formatPosition(game, player.start_index, target.newSteps),
    global_pos: globalPos,
    captured: captured.map(([owner, victim]) => `${owner.name}'s ${victim.label}`),
    reached_home: target.newSteps === game.config.home_finish,
    safe: isSafeTile(game, globalPos),
    wrapped: target.wrapped,
    blockade_formed: blockadeFormed,
  };
  return preview;
}

export function getValidMoves(game: InternalGame, playerIndex: number, roll: number): number[] {
  const player = game.players[playerIndex]!;
  return player.tokens
    .filter((token) => previewMove(game, playerIndex, token.token_idx, roll).legal)
    .map((token) => token.token_idx);
}
