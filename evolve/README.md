# Evolve

A hair care studio landing page — React + TypeScript + Vite, Tailwind CSS v4, GSAP/ScrollTrigger, Framer Motion, and a small hand-rolled shadcn-style Button.

## Setup

```bash
npm install
npm run dev
```

Then open the local URL Vite prints (usually http://localhost:5173).

To build for production:

```bash
npm run build
npm run preview
```

## How it's put together

- **`src/components/Landing.tsx`** — the page shell. It owns the scroll-jacked hero sequence: on scroll, the logo `<img>` (which physically lives in `Navbar.tsx`, always fixed to the top-left) animates from a huge, centered position in the hero down to its real navbar spot, while the tagline drifts down and settles into `Discovery.tsx`'s slot. This is a single GSAP timeline pinned to the hero section (`ScrollTrigger`, `scrub: 1`, moderate pacing).
- **`src/components/Navbar.tsx`** — fixed nav, forwards a ref to the logo `<img>` so `Landing` can measure and animate it.
- **`src/components/Discovery.tsx`** — forwards a ref to the "slot" div where the tagline visually lands.
- **`src/components/Philosophy.tsx`** — dark tonal-break section with a decorative strand line drawn in via `stroke-dashoffset`, scrubbed to scroll.
- **`src/components/Services.tsx`**, **`Testimonial.tsx`**, **`CallToAction.tsx`**, **`Footer.tsx`** — straightforward sections, revealed with Framer Motion's `whileInView`.
- **`src/index.css`** — Tailwind v4 theme tokens (`@theme`) for the Evolve palette and fonts, plus the `Kugile` `@font-face`.
- **`src/components/ui/button.tsx`** — a small shadcn-style `Button` (cva variants: `primary`, `outline`, `ghost`).

Respects `prefers-reduced-motion`: the scroll-jack and strand-draw are skipped entirely, and the logo/tagline just sit in their natural positions.

## Swapping content

- Logo: `src/assets/evolvelogo-transparent.png`
- Display font: `src/assets/fonts/Kugile-Regular.ttf`
- Copy for each section lives directly in its component file.
