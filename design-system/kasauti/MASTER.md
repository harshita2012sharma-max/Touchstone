# Design System Master File

> **LOGIC:** When building a specific page, first check `design-system/pages/[page-name].md`.
> If that file exists, its rules **override** this Master file.
> If not, strictly follow the rules below.

---

**Project:** kasauti
**Generated:** 2026-11-19 11:53:17
**Category:** Analytics Dashboard
**Design Dials:** Variance 3/10 (Centered / Minimal) | Motion 3/10 (Subtle) | Density 7/10 (Standard)

---

## Project decisions (override the generated rules below where they conflict)

Chosen from ui-ux-pro-max results: **Data-Dense Dashboard** + **Comparative Analysis Dashboard** styles, **Developer Tool / IDE** palette. The generated "Exaggerated Minimalism" style and landing-page pattern are not used, because this is a local app, not a marketing page.

**Product rules**
- Neutral benchmark: no "winner" badges, trophies, crowns, or green-up/red-down "good vs bad" model colors. Compare models with two neutral series colors.
- Every score shows its `n`. Every run view shows date, the model id the provider reported, and settings.
- Unreviewed runs always show an amber banner: "UNREVIEWED DATA, do not publish".
- API keys appear only as "set / not set". Never render a key value.

**Fonts** (self-hosted through `@fontsource`, OFL license; no Google Fonts CDN, so the app works offline and makes no third-party requests)
- UI and body: `Noto Sans` + `Noto Sans Devanagari` (Fira Sans has no Devanagari glyphs)
- Code, ids, numbers in tables: `Fira Code` (tabular figures)
- Base 14px for dense tables, 16px for body text, line-height 1.5. Devanagari needs line-height of at least 1.6.

**Theme: "paper and touchstone"** (changed on request: the generic blue felt too common)
A kasauti is a black touchstone; gold is tested by the streak it leaves. Surfaces are warm paper (light) and stone black (dark); scores are gold streaks. Results open with a stone hero panel: a large mean score that counts up, bars that sweep in with one shine pass, and highlight cards (strongest task, hardest task, toughest item). Highlights describe one model's own results, report ties as ties, and never rank models.

**Color tokens** (semantic; components never use raw hex; source of truth is `ui/src/styles.css`)

| Token | Light | Dark | Use |
|---|---|---|---|
| `--bg` | `#faf8f3` | `#12110f` | page |
| `--surface` / `--surface-2` | `#ffffff` / `#f3efe6` | `#1c1a17` / `#2a2722` | cards / muted fill |
| `--stone` / `--stone-2` | `#1c1a17` / `#2a2722` | `#0b0a09` / `#23201c` | hero panel / bar track |
| `--text` / `--text-muted` | `#1c1a17` / `#5c564b` | `#f5f1e8` / `#b3ab9c` | body / meta |
| `--accent` / `--on-accent` | `#1c1a17` / `#f5f1e8` | `#e0a526` / `#1c1a17` | the Run button |
| `--gold` / `--gold-bright` | `#a8701a` / `#e0a526` | `#c98500` / `#f0b93a` | score streaks, hero number |
| `--warn-bg` / `--warn-text` | `#fdecd3` / `#8a3b0c` | `#3d2410` / `#fdba74` | unreviewed banner |
| `--series-1..3` | `#a8701a`, `#6250d6`, `#169e6e` | `#c98500`, `#9085e9`, `#199e70` | compare runs 1-3 |

Series colors were validated with the dataviz validator (`--pairs all`): light passes every check including 3:1 contrast; dark passes every check on the stone surface. A 4th color fails, so Compare is capped at 3 runs. Every bar keeps a visible value label and Compare has a table view.

**Layout**
- Top bar (56px): logo wordmark, nav (Runs, New run, Compare, About), theme toggle. Max width 1200px, 16px gutter on mobile.
- Dense tables: 36px rows, sticky header, sortable columns, horizontal scroll inside the card on mobile (never the page).
- Spacing scale 4/8/12/16/24/32.
- Icons: Lucide (SVG). No emoji as icons.

**Motion:** 150-200ms color/opacity transitions only; progress bar animates width. All motion is off under `prefers-reduced-motion`.

**Pages**
1. **Runs**: table of saved runs (model, date, tasks, n, mean score, unreviewed badge).
2. **New run**: provider select (key status shown), model picker loaded live from the provider, task checkboxes, limit, max tokens, Start. Shows the fixed settings (temperature 0, seed 42) read-only.
3. **Run detail**: live progress (SSE) while running, then score table with bars, meta panel, limitations, link to HTML report.
4. **Sample explorer** (inside run detail): filter by task, wrong only, unparsed only; each row shows prompt, output, expected, parsed, score.
5. **Compare**: pick 2-3 runs (series colors validated all-pairs for colorblind safety with the dataviz validator in both modes; a 4th color fails, so the cap is 3). Every bar carries a visible value label and a table view sits below the chart (light-mode series-3 is below 3:1 contrast); grouped bars per task with two neutral series colors; warning if settings, data or task versions differ.
6. **About**: what kasauti is, limitations, licenses, related work.

---

## Global Rules

### Color Palette

| Role | Hex | CSS Variable |
|------|-----|--------------|
| Primary | `#1E293B` | `--color-primary` |
| On Primary | `#FFFFFF` | `--color-on-primary` |
| Secondary | `#334155` | `--color-secondary` |
| Accent/CTA | `#22C55E` | `--color-accent` |
| Background | `#0F172A` | `--color-background` |
| Foreground | `#F8FAFC` | `--color-foreground` |
| Muted | `#272F42` | `--color-muted` |
| Border | `#475569` | `--color-border` |
| Destructive | `#EF4444` | `--color-destructive` |
| Ring | `#1E293B` | `--color-ring` |

**Color Notes:** Code dark + run green

### Typography

- **Heading Font:** Fira Code
- **Body Font:** Fira Sans
- **Mood:** dashboard, data, analytics, code, technical, precise
- **Google Fonts:** [Fira Code + Fira Sans](https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Fira+Sans:wght@300;400;500;600;700&display=swap)

**CSS Import:**
```css
@import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Fira+Sans:wght@300;400;500;600;700&display=swap');
```

### Spacing Variables

*Density: 7/10 — Standard*

| Token | Value | Usage |
|-------|-------|-------|
| `--space-xs` | `4px` / `0.25rem` | Tight gaps |
| `--space-sm` | `8px` / `0.5rem` | Icon gaps, inline spacing |
| `--space-md` | `16px` / `1rem` | Standard padding |
| `--space-lg` | `24px` / `1.5rem` | Section padding |
| `--space-xl` | `32px` / `2rem` | Large gaps |
| `--space-2xl` | `48px` / `3rem` | Section margins |
| `--space-3xl` | `64px` / `4rem` | Hero padding |

### Shadow Depths

| Level | Value | Usage |
|-------|-------|-------|
| `--shadow-sm` | `0 1px 2px rgba(0,0,0,0.05)` | Subtle lift |
| `--shadow-md` | `0 4px 6px rgba(0,0,0,0.1)` | Cards, buttons |
| `--shadow-lg` | `0 10px 15px rgba(0,0,0,0.1)` | Modals, dropdowns |
| `--shadow-xl` | `0 20px 25px rgba(0,0,0,0.15)` | Hero images, featured cards |

---

## Component Specs

### Buttons

```css
/* Primary Button */
.btn-primary {
  background: #22C55E;
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  transition: all 200ms ease;
  cursor: pointer;
}

.btn-primary:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

/* Secondary Button */
.btn-secondary {
  background: transparent;
  color: #1E293B;
  border: 2px solid #1E293B;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  transition: all 200ms ease;
  cursor: pointer;
}
```

### Cards

```css
.card {
  background: #0F172A;
  border-radius: 12px;
  padding: 24px;
  box-shadow: var(--shadow-md);
  transition: all 200ms ease;
  cursor: pointer;
}

.card:hover {
  box-shadow: var(--shadow-lg);
  transform: translateY(-2px);
}
```

### Inputs

```css
.input {
  padding: 12px 16px;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  font-size: 16px;
  transition: border-color 200ms ease;
}

.input:focus {
  border-color: #1E293B;
  outline: none;
  box-shadow: 0 0 0 3px #1E293B20;
}
```

### Modals

```css
.modal-overlay {
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
}

.modal {
  background: white;
  border-radius: 16px;
  padding: 32px;
  box-shadow: var(--shadow-xl);
  max-width: 500px;
  width: 90%;
}
```

---

## Style Guidelines

**Style:** Exaggerated Minimalism

**Keywords:** Bold minimalism, oversized typography, high contrast, negative space, loud minimal, statement design

**Best For:** Fashion, architecture, portfolios, agency landing pages, luxury brands, editorial

**Key Effects:** font-size: clamp(3rem 10vw 12rem), font-weight: 900, letter-spacing: -0.05em, massive whitespace

### Page Pattern

**Pattern Name:** Real-Time / Operations Landing

- **Conversion Strategy:** For ops/security/iot products. Demo or sandbox link. Trust signals.
- **CTA Placement:** Primary CTA in nav + After metrics
- **Section Order:** 1. Hero (product + live preview or status), 2. Key metrics/indicators, 3. How it works, 4. CTA (Start trial / Contact)

---

## Motion

**Scroll Reveal** (Subtle) — Trigger: scroll (viewport enter) | Duration: 300-400ms | Easing: `power1.out`

```js
gsap.from(el, { opacity: 0, y: 12, duration: 0.35, ease: 'power1.out', scrollTrigger: { trigger: el, start: 'top 90%', toggleActions: 'play none none reverse' } });
```

**Framework notes:** Requires the ScrollTrigger plugin registered once via gsap.registerPlugin(ScrollTrigger)

- ✅ Keep the y offset small (8-16px) so it reads as a fade, not a slide
- ❌ Don't reveal below-the-fold content needed for SEO/crawlers as invisible-by-default without a no-JS fallback
- ⚡ toggleActions 'play none none reverse' avoids re-triggering on every scroll direction change

---

## Anti-Patterns (Do NOT Use)

- ❌ Ornate design
- ❌ No filtering

### Additional Forbidden Patterns

- ❌ **Emojis as icons** — Use SVG icons (Heroicons, Lucide, Simple Icons)
- ❌ **Missing cursor:pointer** — All clickable elements must have cursor:pointer
- ❌ **Layout-shifting hovers** — Avoid scale transforms that shift layout
- ❌ **Low contrast text** — Maintain 4.5:1 minimum contrast ratio
- ❌ **Instant state changes** — Always use transitions (150-300ms)
- ❌ **Invisible focus states** — Focus states must be visible for a11y

---

## Pre-Delivery Checklist

Before delivering any UI code, verify:

- [ ] No emojis used as icons (use SVG instead)
- [ ] All icons from consistent icon set (Heroicons/Lucide)
- [ ] `cursor-pointer` on all clickable elements
- [ ] Hover states with smooth transitions (150-300ms)
- [ ] Light mode: text contrast 4.5:1 minimum
- [ ] Focus states visible for keyboard navigation
- [ ] `prefers-reduced-motion` respected
- [ ] Responsive: 375px, 768px, 1024px, 1440px
- [ ] No content hidden behind fixed navbars
- [ ] No horizontal scroll on mobile
