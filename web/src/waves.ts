export const DEPART_TOO_MANY =
  "Trop de départs : il reste trop peu de personnes non réservées.";
export const DEPART_LEVEL_SHORT =
  "Le reste obligatoire dépasse les personnes présentes de ce niveau.";

export function computeWorstCaseRemaining(
  bag: number[],
  leaveCount: number,
  remainByLevel: Record<number, number>,
): { remaining: number[]; error: string | null } {
  const counts = new Map<number, number>();
  for (const level of bag) {
    counts.set(level, (counts.get(level) ?? 0) + 1);
  }
  const reserved: number[] = [];
  const others: number[] = [];
  for (const [level, count] of counts) {
    const need = remainByLevel[level] ?? 0;
    if (need > count) {
      return { remaining: [], error: DEPART_LEVEL_SHORT };
    }
    const reserveCount = need > 0 ? Math.min(need, count) : 0;
    for (let i = 0; i < reserveCount; i += 1) {
      reserved.push(level);
    }
    for (let i = 0; i < count - reserveCount; i += 1) {
      others.push(level);
    }
  }
  for (const [level, need] of Object.entries(remainByLevel)) {
    if (need > 0 && !counts.has(Number(level))) {
      return { remaining: [], error: DEPART_LEVEL_SHORT };
    }
  }
  if (leaveCount > others.length) {
    return { remaining: [], error: DEPART_TOO_MANY };
  }
  others.sort((a, b) => b - a);
  const leftover = others.slice(leaveCount);
  return { remaining: [...reserved, ...leftover].sort((a, b) => a - b), error: null };
}

export function formatBag(levels: number[]): string {
  if (levels.length === 0) {
    return "vide";
  }
  return levels.slice().sort((a, b) => a - b).join(", ");
}

export function levelsToCounts(levels: number[]): Record<number, number> {
  const out: Record<number, number> = {};
  for (const level of levels) {
    out[level] = (out[level] ?? 0) + 1;
  }
  return out;
}

export function countsToLevels(counts: Record<number, number>): number[] {
  const out: number[] = [];
  for (const level of Object.keys(counts)
    .map(Number)
    .sort((a, b) => a - b)) {
    for (let i = 0; i < (counts[level] ?? 0); i += 1) {
      out.push(level);
    }
  }
  return out;
}

export type ArrivalDraft = {
  time_minutes: number;
  post_levels: number[];
};

export type DepartureDraft = {
  time_minutes: number;
  leaveCount: number;
  remainByLevel: Record<number, number>;
};

export type WaveBag = {
  bag: number[];
  error: string | null;
};

export function simulateWaves(arrivals: ArrivalDraft[], departures: DepartureDraft[]): {
  afterArrival: WaveBag[];
  afterDeparture: WaveBag[];
} {
  type Event =
    | { kind: "arrival"; index: number; time: number }
    | { kind: "departure"; index: number; time: number };
  const events: Event[] = [
    ...arrivals.map((_, index) => ({ kind: "arrival" as const, index, time: arrivals[index].time_minutes })),
    ...departures.map((_, index) => ({
      kind: "departure" as const,
      index,
      time: departures[index].time_minutes,
    })),
  ];
  events.sort((a, b) => {
    if (a.time !== b.time) {
      return a.time - b.time;
    }
    if (a.kind === b.kind) {
      return a.index - b.index;
    }
    return a.kind === "arrival" ? -1 : 1;
  });
  const afterArrival: WaveBag[] = arrivals.map(() => ({ bag: [], error: null }));
  const afterDeparture: WaveBag[] = departures.map(() => ({ bag: [], error: null }));
  let bag: number[] = [];
  let blocked: string | null = null;
  for (const event of events) {
    if (blocked) {
      if (event.kind === "arrival") {
        afterArrival[event.index] = { bag: [], error: blocked };
      } else {
        afterDeparture[event.index] = { bag: [], error: blocked };
      }
      continue;
    }
    if (event.kind === "arrival") {
      bag = [...bag, ...arrivals[event.index].post_levels].sort((a, b) => a - b);
      afterArrival[event.index] = { bag: [...bag], error: null };
      continue;
    }
    const keep = Object.values(departures[event.index].remainByLevel).reduce((sum, n) => sum + n, 0);
    const leaveCount = Math.max(0, bag.length - keep);
    const result = computeWorstCaseRemaining(bag, leaveCount, departures[event.index].remainByLevel);
    if (result.error) {
      blocked = result.error;
      afterDeparture[event.index] = { bag: [], error: result.error };
      continue;
    }
    bag = result.remaining;
    afterDeparture[event.index] = { bag: [...bag], error: null };
  }
  return { afterArrival, afterDeparture };
}

export function remainFromBag(remaining: number[]): Record<number, number> {
  const out: Record<number, number> = {};
  for (const level of remaining) {
    out[level] = (out[level] ?? 0) + 1;
  }
  return out;
}

export function inferLeaveCount(bagBefore: number[], remaining: number[]): number {
  return Math.max(0, bagBefore.length - remaining.length);
}
