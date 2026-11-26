import { describe, expect, it } from "vitest";
import fixture from "../../fixtures/rng.json";
import { createPythonRandom, deserializeRandom, serializeRandom } from "../../src/game/rng";

describe("Python-compatible RNG", () => {
  it.each(fixture.seeds)("matches 10,000 rolls for $seed", ({ seed, rolls }) => {
    const random = createPythonRandom(BigInt(seed));
    const actual = Array.from({ length: 10_000 }, () => random.randint(1, 6));
    expect(actual).toEqual(rolls);
  });

  it("restores the exact stream after serialization", () => {
    const original = createPythonRandom(42n);
    original.randint(1, 6);
    original.randint(1, 6);
    const restored = deserializeRandom(serializeRandom(original));
    const expected = Array.from({ length: 100 }, () => original.randint(1, 6));
    expect(Array.from({ length: 100 }, () => restored.randint(1, 6))).toEqual(expected);
  });

  it("rejects malformed serialized state", () => {
    const valid = serializeRandom(createPythonRandom(1n));
    expect(() => deserializeRandom({ ...valid, words: valid.words.slice(1) })).toThrow("624 words");
    expect(() =>
      deserializeRandom({ ...valid, words: [2 ** 32, ...valid.words.slice(1)] }),
    ).toThrow("unsigned 32-bit");
    expect(() => deserializeRandom({ ...valid, index: 625 })).toThrow("index");
  });
});
