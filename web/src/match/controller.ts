import { decisionDetails } from "../game/bot";
import { codeMessage, formatCommentary, gameplayMessage } from "../game/commentary";
import { configFromDict } from "../game/config";
import {
  applyMove,
  createGame,
  declareMutualDraw,
  exportCanonicalState,
  previewMove,
  processRoll,
  quitGame,
  recordBotDecision,
  rollDie,
} from "../game/engine";
import { cloneEvent, cloneValue } from "../game/transitions";
import { SPEED_DELAYS } from "../game/presets";
import { deserializeRandom, serializeRandom } from "../game/rng";
import type { SerializedRandom } from "../game/rng";
import type {
  CanonicalSnapshot,
  CommentaryMode,
  InternalGame,
  MovePreview,
  MoveResult,
  PlayerKind,
  RollResult,
  Speed,
} from "../game/types";
import type { SavedMatch } from "./persistence";

export interface MatchControllerOptions {
  autoplay?: boolean;
  paused?: boolean;
  speed?: Speed;
  commentary?: CommentaryMode;
  reducedMotion?: boolean;
}

const COMMENTARY_MODES: CommentaryMode[] = ["gameplay", "code", "both", "off"];

function validateSpeed(speed: Speed): Speed {
  if (!(speed in SPEED_DELAYS)) throw new Error("Speed must be slow, normal, or fast.");
  return speed;
}

function validateCommentary(mode: CommentaryMode): CommentaryMode {
  if (!COMMENTARY_MODES.includes(mode)) {
    throw new Error("Commentary must be gameplay, code, both, or off.");
  }
  return mode;
}

export function restoreGame(snapshot: CanonicalSnapshot, rngState: SerializedRandom): InternalGame {
  const config = configFromDict(snapshot.config);
  const names = snapshot.players.map((player) => player.name);
  const kinds = snapshot.players.map((player) => player.kind);
  const game = createGame(config, names, 0n, kinds);
  game.rng = deserializeRandom(rngState);
  game.max_turns = snapshot.max_turns;
  game.turn_count = snapshot.turn_count;
  game.current_player = snapshot.current_player;
  game.consecutive_sixes = snapshot.consecutive_sixes;
  game.status = snapshot.status;
  game.winner_index = snapshot.winner_index;
  game.draw_reason = snapshot.draw_reason;
  game.finish_order = [...snapshot.finish_order];
  game.last_event = snapshot.last_event;
  game.events = snapshot.events.map(cloneEvent);
  game.players.forEach((player, playerIndex) => {
    const savedPlayer = snapshot.players[playerIndex]!;
    player.captures_made = savedPlayer.captures_made;
    player.tokens.forEach((token, tokenIndex) => {
      token.steps = savedPlayer.tokens[tokenIndex]!.steps;
    });
  });
  return game;
}

export class MatchController {
  private game: InternalGame;
  private pendingRoll: number | null = null;
  private validMoves: number[] = [];
  private previews: MovePreview[] = [];
  private paused: boolean;
  private autoplay: boolean;
  private speed: Speed;
  private commentaryMode: CommentaryMode;
  private reducedMotion: boolean;
  private eventCursor = 0;
  private revision = 0;
  private readonly listeners = new Set<() => void>();

  constructor(
    config: Parameters<typeof createGame>[0],
    playerNames: string[],
    seed?: bigint | null,
    playerKinds?: PlayerKind[],
    options: MatchControllerOptions = {},
  ) {
    this.game = createGame(config, playerNames, seed, playerKinds);
    this.paused = options.paused ?? false;
    this.autoplay = options.autoplay ?? false;
    this.speed = validateSpeed(options.speed ?? "normal");
    this.commentaryMode = validateCommentary(options.commentary ?? config.commentary);
    this.reducedMotion = options.reducedMotion ?? false;
  }

  static restore(saved: SavedMatch): MatchController {
    const snapshot = saved.snapshot;
    const controller = new MatchController(
      saved.config,
      snapshot.players.map((player) => player.name),
      0n,
      snapshot.players.map((player) => player.kind),
      {
        paused: saved.preferences.paused,
        autoplay: saved.preferences.autoplay,
        speed: saved.preferences.speed,
        commentary: saved.preferences.commentary,
        reducedMotion: saved.preferences.reduced_motion,
      },
    );
    controller.game = restoreGame(snapshot, saved.rng);
    controller.pendingRoll = saved.pending_roll;
    controller.validMoves = [...saved.valid_moves];
    controller.previews = cloneValue(saved.previews);
    controller.eventCursor = snapshot.events.length;
    return controller;
  }

  readonly subscribe = (listener: () => void): (() => void) => {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  };

  readonly getRevision = (): number => this.revision;

  private publish(): void {
    this.revision += 1;
    for (const listener of [...this.listeners]) listener();
  }

  private clearChoices(): void {
    this.pendingRoll = null;
    this.validMoves = [];
    this.previews = [];
  }

  private setChoices(roll: number, validMoves: number[]): void {
    this.pendingRoll = validMoves.length > 0 ? roll : null;
    this.validMoves = [...validMoves];
    this.previews = validMoves.map((tokenIndex) =>
      previewMove(this.game, this.game.current_player, tokenIndex, roll),
    );
  }

  private canAutomateCurrentSeat(): boolean {
    const player = this.game.players[this.game.current_player]!;
    return player.kind === "bot" || this.autoplay;
  }

  private runOneAutomatedTurn(ignorePause: boolean): boolean {
    if (this.game.status !== "PLAYING") return false;
    if (this.paused && !ignorePause) return false;
    if (this.pendingRoll !== null) return false;
    if (!this.canAutomateCurrentSeat()) return false;

    const playerIndex = this.game.current_player;
    const roll = rollDie(this.game);
    const result = processRoll(this.game, roll);
    this.setChoices(roll, result.valid_moves);
    if (result.valid_moves.length === 0) {
      this.publish();
      return true;
    }

    const decision = decisionDetails(this.game, playerIndex, roll, result.valid_moves);
    if (decision.token_idx === null) throw new Error("Bot decision did not select a legal move");
    recordBotDecision(this.game, decision.token_idx, roll, decision.reason);
    applyMove(this.game, decision.token_idx, roll);
    this.clearChoices();
    this.publish();
    return true;
  }

  rollHuman(): RollResult | null {
    if (this.game.status !== "PLAYING" || this.pendingRoll !== null) return null;
    if (this.game.players[this.game.current_player]!.kind !== "human") return null;
    const roll = rollDie(this.game);
    const result = processRoll(this.game, roll);
    this.setChoices(roll, result.valid_moves);
    this.publish();
    return result;
  }

  selectMove(tokenIndex: number): MoveResult | null {
    if (this.game.status !== "PLAYING" || this.pendingRoll === null) return null;
    if (this.game.players[this.game.current_player]!.kind !== "human") return null;
    if (!this.validMoves.includes(tokenIndex)) return null;
    const result = applyMove(this.game, tokenIndex, this.pendingRoll);
    this.clearChoices();
    this.publish();
    return result;
  }

  runAutomatedTurn(): boolean {
    return this.runOneAutomatedTurn(false);
  }

  step(): boolean {
    if (this.pendingRoll !== null) return false;
    return this.runOneAutomatedTurn(true);
  }

  setPaused(paused: boolean): void {
    if (this.paused === paused) return;
    this.paused = paused;
    this.publish();
  }

  isPaused(): boolean {
    return this.paused;
  }

  setAutoplay(autoplay: boolean): void {
    if (this.autoplay === autoplay) return;
    this.autoplay = autoplay;
    this.publish();
  }

  getAutoplay(): boolean {
    return this.autoplay;
  }

  setSpeed(speed: Speed): void {
    const validated = validateSpeed(speed);
    if (this.speed === validated) return;
    this.speed = validated;
    this.publish();
  }

  getSpeed(): Speed {
    return this.speed;
  }

  getScheduleDelayMs(): number {
    return SPEED_DELAYS[this.speed] * 1000;
  }

  setCommentary(mode: CommentaryMode): void {
    const validated = validateCommentary(mode);
    if (this.commentaryMode === validated) return;
    this.commentaryMode = validated;
    this.publish();
  }

  getCommentaryMode(): CommentaryMode {
    return this.commentaryMode;
  }

  cycleCommentary(): CommentaryMode {
    const index = COMMENTARY_MODES.indexOf(this.commentaryMode);
    const next = COMMENTARY_MODES[(index + 1) % COMMENTARY_MODES.length]!;
    this.setCommentary(next);
    return next;
  }

  setReducedMotion(reducedMotion: boolean): void {
    if (this.reducedMotion === reducedMotion) return;
    this.reducedMotion = reducedMotion;
    this.publish();
  }

  getReducedMotion(): boolean {
    return this.reducedMotion;
  }

  declareDraw(): void {
    if (this.game.status !== "PLAYING") return;
    this.clearChoices();
    declareMutualDraw(this.game);
    this.publish();
  }

  quit(): void {
    if (this.game.status !== "PLAYING") return;
    this.clearChoices();
    quitGame(this.game);
    this.publish();
  }

  getSnapshot(): CanonicalSnapshot {
    return exportCanonicalState(this.game);
  }

  getRngState(): SerializedRandom {
    return serializeRandom(this.game.rng);
  }

  getPendingRoll(): number | null {
    return this.pendingRoll;
  }

  getValidMoves(): number[] {
    return [...this.validMoves];
  }

  getPreviews(): MovePreview[] {
    return cloneValue(this.previews);
  }

  drainCommentary(): string[] {
    const playerNames = this.game.players.map((player) => player.name);
    const pending = this.game.events.slice(this.eventCursor);
    this.eventCursor = this.game.events.length;
    return pending.flatMap((event) =>
      formatCommentary(
        event,
        this.commentaryMode,
        gameplayMessage(event, playerNames),
        codeMessage(event, playerNames),
      ),
    );
  }
}
