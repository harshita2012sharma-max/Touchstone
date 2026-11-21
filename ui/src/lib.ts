import { useEffect, useState } from "react";

/** Format a 0-1 score as a percentage with one decimal. */
export function pct(value: number, digits = 1): string {
  return `${(value * 100).toFixed(digits)}%`;
}

/** Local date and time, e.g. "19 Nov 2026, 11:44". */
export function when(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export const SERIES = ["var(--series-1)", "var(--series-2)", "var(--series-3)"] as const;
export const MAX_COMPARE = SERIES.length;

/** Small fetch hook: { data, error, loading } with a reload function. */
export function useLoad<T>(load: () => Promise<T>, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);
  useEffect(() => {
    let alive = true;
    setError(null);
    load()
      .then((d) => alive && setData(d))
      .catch((e: unknown) => alive && setError(e instanceof Error ? e.message : String(e)));
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick]);
  return { data, error, loading: data === null && error === null, reload: () => setTick((t) => t + 1) };
}

/** Plain-language names for task ids, shown next to the technical name. */
export const TASK_LABELS: Record<string, string> = {
  hindi_comprehension: "Hindi reading",
  hinglish_understanding: "Hinglish chat",
  translation_hi_en: "Hindi to English translation",
  codemixed_instructions: "Following Hinglish instructions",
  hindi_reasoning: "Maths word problems in Hindi",
  cultural_context: "Facts about everyday India",
  hindi_grammar: "Hindi grammar",
  idioms_proverbs: "Idioms and proverbs",
  hindi_logic: "Logic puzzles in Hindi",
  translation_en_hi: "English to Hindi translation",
  hinglish_to_hindi: "Hinglish to Devanagari Hindi",
};

export function taskLabel(id: string): string {
  return TASK_LABELS[id] ?? id;
}

const RULE_WORDS: Record<string, string> = {
  item_count: "right number of items",
  max_words: "short enough",
  min_words: "long enough",
  contains_all: "uses the required words",
  contains_any: "uses a key word",
  contains_none: "avoids the banned word",
  script: "right script",
  starts_with: "right start",
  ends_with: "right ending",
};

/** Turn rule-check ids (e.g. "item_count, max_words") into plain English. */
export function plainRules(text: string): string {
  return text.replace(/(item_count|max_words|min_words|contains_all|contains_any|contains_none|script|starts_with|ends_with)/g, (m) => RULE_WORDS[m] ?? m);
}
