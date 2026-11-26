const STATE_SIZE = 624;
const STATE_OFFSET = 397;
const MATRIX_A = 0x9908b0df;
const UPPER_MASK = 0x80000000;
const LOWER_MASK = 0x7fffffff;

export interface SerializedRandom {
  seed: string | null;
  index: number;
  words: number[];
}

function seedWords(seed: bigint): number[] {
  let remaining = seed < 0n ? -seed : seed;
  const words: number[] = [];
  while (remaining > 0n) {
    words.push(Number(remaining & 0xffffffffn));
    remaining >>= 32n;
  }
  return words.length > 0 ? words : [0];
}

export class PythonRandom {
  private words: number[];
  private index: number;
  private readonly seed: string | null;

  constructor(seed: bigint, restored?: SerializedRandom) {
    this.seed = restored ? restored.seed : seed.toString();
    if (restored) {
      this.words = [...restored.words];
      this.index = restored.index;
      return;
    }
    const key = seedWords(seed);
    this.words = new Array<number>(STATE_SIZE).fill(0);
    this.words[0] = 19650218;
    for (let i = 1; i < STATE_SIZE; i += 1) {
      const previous = this.words[i - 1]!;
      this.words[i] = (Math.imul(previous ^ (previous >>> 30), 1812433253) + i) >>> 0;
    }
    let index = 1;
    let keyIndex = 0;
    for (let count = 0; count < STATE_SIZE; count += 1) {
      const previous = this.words[index - 1]!;
      this.words[index] =
        ((this.words[index]! ^ Math.imul(previous ^ (previous >>> 30), 1664525)) +
          key[keyIndex]! +
          keyIndex) >>>
        0;
      if (index + 1 === STATE_SIZE) {
        this.words[0] = this.words[STATE_SIZE - 1]!;
        index = 1;
      } else {
        index += 1;
      }
      keyIndex = (keyIndex + 1) % key.length;
    }
    for (let count = 0; count < STATE_SIZE - 1; count += 1) {
      const previous = this.words[index - 1]!;
      this.words[index] =
        ((this.words[index]! ^ Math.imul(previous ^ (previous >>> 30), 1566083941)) - index) >>> 0;
      if (index + 1 === STATE_SIZE) {
        this.words[0] = this.words[STATE_SIZE - 1]!;
        index = 1;
      } else {
        index += 1;
      }
    }
    this.words[0] = UPPER_MASK;
    this.index = STATE_SIZE;
  }

  serialize(): SerializedRandom {
    return {
      seed: this.seed,
      index: this.index,
      words: [...this.words],
    };
  }

  static fromState(state: SerializedRandom): PythonRandom {
    return new PythonRandom(0n, state);
  }

  private twist(): void {
    for (let i = 0; i < STATE_SIZE; i += 1) {
      const combined =
        (this.words[i]! & UPPER_MASK) | (this.words[(i + 1) % STATE_SIZE]! & LOWER_MASK);
      const shifted = combined >>> 1;
      this.words[i] =
        (this.words[(i + STATE_OFFSET) % STATE_SIZE]! ^ shifted ^ (combined & 1 ? MATRIX_A : 0)) >>>
        0;
    }
    this.index = 0;
  }

  nextUint32(): number {
    if (this.index >= STATE_SIZE) {
      this.twist();
    }
    let value = this.words[this.index]!;
    this.index += 1;
    value ^= value >>> 11;
    value ^= (value << 7) & 0x9d2c5680;
    value ^= (value << 15) & 0xefc60000;
    value ^= value >>> 18;
    return value >>> 0;
  }

  getrandbits(bits: number): bigint {
    if (!Number.isInteger(bits) || bits < 0) {
      throw new RangeError("bits must be a non-negative integer");
    }
    let result = 0n;
    let shift = 0;
    let remaining = bits;
    while (remaining > 0) {
      const width = Math.min(32, remaining);
      const word = this.nextUint32();
      const part = width === 32 ? BigInt(word) : BigInt(word >>> (32 - width));
      result |= part << BigInt(shift);
      shift += width;
      remaining -= width;
    }
    return result;
  }

  randbelow(limit: bigint): bigint {
    if (limit <= 0n) {
      throw new RangeError("randbelow limit must be positive");
    }
    const bits = limit.toString(2).length;
    while (true) {
      const candidate = this.getrandbits(bits);
      if (candidate < limit) {
        return candidate;
      }
    }
  }

  randint(minimum: number, maximum: number): number {
    if (!Number.isSafeInteger(minimum) || !Number.isSafeInteger(maximum)) {
      throw new RangeError("randint bounds must be safe integers");
    }
    if (maximum < minimum) {
      throw new RangeError("maximum must be at least minimum");
    }
    return minimum + Number(this.randbelow(BigInt(maximum - minimum + 1)));
  }
}

export function createPythonRandom(seed: bigint): PythonRandom {
  return new PythonRandom(seed);
}

export function serializeRandom(random: PythonRandom): SerializedRandom {
  return random.serialize();
}

export function deserializeRandom(value: unknown): PythonRandom {
  if (typeof value !== "object" || value === null) {
    throw new TypeError("serialized random state must be an object");
  }
  const candidate = value as Partial<SerializedRandom>;
  if (
    (candidate.seed !== null && typeof candidate.seed !== "string") ||
    (typeof candidate.seed === "string" && !/^-?\d+$/.test(candidate.seed))
  ) {
    throw new TypeError("seed must be a signed integer string or null");
  }
  if (!Array.isArray(candidate.words) || candidate.words.length !== STATE_SIZE) {
    throw new Error("random state must contain 624 words");
  }
  if (candidate.words.some((word) => !Number.isInteger(word) || word < 0 || word > 0xffffffff)) {
    throw new Error("random state words must be unsigned 32-bit integers");
  }
  if (
    !Number.isInteger(candidate.index) ||
    candidate.index === undefined ||
    candidate.index < 0 ||
    candidate.index > STATE_SIZE
  ) {
    throw new Error("random state index must be between 0 and 624");
  }
  return PythonRandom.fromState(candidate as SerializedRandom);
}
