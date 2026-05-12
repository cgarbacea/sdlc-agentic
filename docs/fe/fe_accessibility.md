---
tags: [accessibility, ARIA, a11y, keyboard navigation, semantic HTML, alt text, focus, screen reader]
executor: fe
---

# Accessibility (a11y) Rules

## Rules

- **Semantic HTML** — `<button>` for actions, `<a>` for navigation, `<nav>`, `<main>`, `<section>`, `<h1>`–`<h6>` for structure. Never `<div onClick>` where a `<button>` is appropriate.
- **Every image needs `alt`** — descriptive for meaningful images, empty string (`alt=""`) for decorative ones
- **Icon-only buttons need `aria-label`** — `<Button aria-label="Close dialog">✕</Button>`
- **Form inputs need associated labels** — use `htmlFor` + `id` pairing or `aria-labelledby`; never rely on placeholder text as the only label
- **Never convey meaning through colour alone** — always pair colour with text, icon, or pattern
- **Keyboard navigation** — all interactive elements reachable by Tab; focus order must follow visual order; focus ring must be visible (never `outline: none` without a replacement)
- **Check the design system first** — design system components are built with accessibility in mind; using them correctly satisfies most requirements automatically

## Quick Reference

```tsx
// ✅ Icon button with label
<Button aria-label="Delete item" variant="ghost">
  <TrashIcon />
</Button>

// ✅ Form field with label
<label htmlFor="email">Email</label>
<input id="email" type="email" />

// ✅ Decorative image
<img src="/hero.jpg" alt="" />

// ✅ Meaningful image
<img src="/chart.jpg" alt="Bar chart showing 42% increase in Q1 2026" />
```
