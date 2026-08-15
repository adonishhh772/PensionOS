---
name: best-frontend-designs
description: A reusable workflow for producing distinctive, non-templated frontend designs — guides brainstorming, type and color tokenization, layout exploration, and a single signature risk suitable for the brief.
license: Complete terms in LICENSE.txt
---

# Best Frontend Designs

Use when: the user asks for an intentional, studio-quality frontend design direction, a token system, or a compact buildable spec (colors, type, layout, signature) for a single page or product surface.

## Purpose

This skill codifies a two-pass, design-led process to produce a distinct visual direction that resists templated defaults. It produces:
- a one-paragraph subject definition (audience, subject, page job)
- a 4–6 color token palette with named hex values
- a type system (display, body, utility) with scale and weight choices
- two concise layout options with ASCII wireframes
- a single signature element and one justified aesthetic risk
- an accessibility checklist and reduced-motion variant

## Process (step-by-step)

1. Clarify scope
   - Prompt the user (or infer) for subject, audience, and primary page job.
   - Decide: single page vs. multi-page surface.

2. Inventory subject cues
   - Extract subject materials, tools, vernacular, and emotional register.
   - Identify three visual motifs (textures, objects, gestures).

3. Generate seed concepts (3x)
   - For each seed: 1-line thesis, 4-color palette, display + body face suggestion, one-line layout concept.

4. Choose direction and refine
   - Select the strongest seed, then expand tokens to full system (add utility color, alpha accents).
   - Set a type scale (H1, H2, H3, body, caption) and suggested metrics (size, line-height, weight).

5. Propose two layouts
   - Primary: the chosen direction executed as a homepage/hero wireframe.
   - Alternative: a contrasting layout that reveals a different tradeoff (e.g., editorial vs. app-like).

6. Define the signature element
   - One striking, repeatable visual device (animated emblem, interactive demo, typographic treatment).
   - Explain how it embodies the subject and why the risk is justified.

7. Accessibility & motion
   - Contrast checks, keyboard focus styles, reduced-motion variant description.

8. Deliverables & prompts
   - Provide code-ready tokens (CSS variables or JSON), font stack suggestions, and short example copy.

## Decision points & branching logic

- If the brief names a visual reference, match its scale and texture; if not, pick a reference from the subject's own artifacts.
- If content is sequential (process/timeline), use numbered markers; otherwise, avoid ordinal cues.
- If performance constraints are tight (mobile-first, legacy browsers), reduce animation and prefer typographic flair over heavy assets.

## Quality criteria / completion checks

- The hero must state the page's job in 6 words or fewer.
- Color palette includes at least one accessible combination (AA large text) and token names tied to meaning (e.g., `accent-action`, `paper-backdrop`).
- Type scale is explicit with px/rem values for H1–body–caption.
- Signature is described, not merely named, with an integration plan (where it appears, how it behaves).
- Reduced-motion and keyboard focus behaviours specified.

## Prompts & examples to try

- "Design direction for a ritual tea subscription landing page — audience: urban professionals aged 30–50; job: convert signups."  
- "Produce a bold, editorial homepage for an experimental instrument maker; include palette, fonts, and hero wireframe."  
- "Create a compact token system for a fintech dashboard where clarity and calm are required; propose one unique typographic treatment."

## Templates (outputs)

- Color tokens (CSS variables)
  - `--color-bg: #...; --color-paper: #...; --color-accent: #...; --color-accent-2: #...;`

- Type scale (example)
  - `H1: 48px / 1.04 / 700`  
  - `H2: 32px / 1.08 / 600`  
  - `Body: 16px / 1.5 / 400`  

- ASCII hero wireframe
  - [Logo] [Nav]  
  - H1 – eye-catching line  
  - SUB – one-line explanation  
  - [Signature Device]  [CTA]

## Ambiguities to clarify (questions the skill will ask)

- Single-page or multi-page surface?  
- Who is the primary user (age, intent, device)?  
- Any strict brand constraints (existing colors, fonts)?  
- Performance or accessibility hard constraints?

## Follow-ups & customization

- Offer a coded starter (HTML/CSS) for the chosen direction.  
- Generate responsive CSS variables and an accessible color contrast report.  
- Produce a short Figma file spec (layers and tokens) if requested.

## Example output (short)

Subject: Modern craft distillery — audience: curious home bartenders; page job: get first purchase.  
Palette: `paper:#FAF8F6`, `ink:#0D0B0A`, `ember:#C2472C`, `moss:#2E5B3A`, `muted:#BFB7AE`.  
Type: Display `Recoleta` (restraint), Body `Inter/16/1.5`.  
Signature: a slow parallax grain overlay pulled from the texture of oak barrels — low opacity, reduced-motion variant removes it.  
Hero wireframe: Logo | Nav — H1 — sub — [Signature] [Buy CTA].
