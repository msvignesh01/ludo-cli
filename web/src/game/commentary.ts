import type { CommentaryMode, GameEvent } from "./types";

function playerName(playerNames: string[], playerIndex: unknown): string {
  if (
    typeof playerIndex !== "number" ||
    !Number.isInteger(playerIndex) ||
    playerIndex < 0 ||
    playerIndex >= playerNames.length
  ) {
    return "Game";
  }
  return playerNames[playerIndex]!;
}

export function gameplayMessage(event: GameEvent, playerNames: string[]): string {
  const player = playerName(playerNames, event.player);
  const data = event.data;
  switch (event.type) {
    case "GAME_STARTED":
      return "Match started.";
    case "DICE_ROLLED":
      return `${player} rolls ${data.roll}.`;
    case "NO_VALID_MOVES":
      return `${player} has no legal move and skips.`;
    case "TRIPLE_SIX_FORFEIT":
      return `${player} forfeits the third consecutive six.`;
    case "BOT_DECISION":
      return `${player} bot chooses ${data.token}: ${data.reason}.`;
    case "TOKEN_MOVED":
      return `${player} moves ${data.token} from steps ${data.old_steps} to ${data.new_steps}.`;
    case "TOKEN_CAPTURED":
      return `${player} captures ${playerName(playerNames, data.victim_player)}'s ${data.victim_token}.`;
    case "BLOCKADE_FORMED":
      return `${player} forms a blockade on T${String(Math.trunc(Number(data.tile ?? 0))).padStart(2, "0")}.`;
    case "PLAYER_FINISHED":
      return `${player} finishes in place ${data.place}.`;
    case "BONUS_TURN":
      return `${player} earns another roll.`;
    case "TURN_ADVANCED":
      return `Next turn: ${player}.`;
    case "GAME_WON":
      return `${player} wins!`;
    case "GAME_DRAW":
      return `Draw: ${data.reason}.`;
    case "GAME_QUIT":
      return "Game quit.";
    default:
      return `${event.type}.`;
  }
}

export function codeMessage(event: GameEvent, playerNames: string[]): string {
  void playerNames;
  const data = event.data;
  switch (event.type) {
    case "GAME_STARTED":
      return "Web: createGame(config, playerNames, seed)";
    case "DICE_ROLLED":
      return `Web: rollDie(game) -> processRoll(game, roll=${data.roll})`;
    case "NO_VALID_MOVES":
    case "TRIPLE_SIX_FORFEIT":
      return "Web: processRoll(game, roll) -> advanceTurn(game)";
    case "BOT_DECISION":
      return "Web: chooseMove(game, playerIndex, roll, validMoves)";
    case "TOKEN_MOVED":
      return `Web: applyMove(game, tokenIdx=${data.token_idx}, roll=${data.roll})`;
    case "TOKEN_CAPTURED":
      return "Web: applyMove() sets victim.steps = -1";
    case "BLOCKADE_FORMED":
      return "Web: applyMove() emits BLOCKADE_FORMED";
    case "PLAYER_FINISHED":
      return "Web: allFinished(player, homeFinish)";
    case "BONUS_TURN":
      return "Web: applyMove() -> bonusTurn";
    case "TURN_ADVANCED":
      return "Web: advanceTurn(game)";
    case "GAME_WON":
      return "Web: applyMove() sets status = WON";
    case "GAME_DRAW":
      return "Web: declareMutualDraw(game) or advanceTurn(game)";
    case "GAME_QUIT":
      return "Web: quitGame(game)";
    default:
      return `Web: ${event.type}`;
  }
}

export function formatCommentary(
  event: GameEvent,
  mode: CommentaryMode,
  gameplayText: string,
  codeText: string,
): string[] {
  void event;
  if (mode === "off") return [];
  if (mode === "gameplay") return [gameplayText];
  if (mode === "code") return [codeText];
  if (mode === "both") return [`[Gameplay] ${gameplayText}`, `[Code] ${codeText}`];
  throw new Error("Commentary must be gameplay, code, both, or off.");
}
