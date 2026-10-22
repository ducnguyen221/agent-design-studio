---
version: alpha
name: "Sample Studio"
colors:
  bg: "#ffffff"
  surface: "#f5f5f4"
  text: "#1c1917"
  muted: "#57534e"
  border: "#d6d3d1"
  accent: "#2563eb"
  accent-text: "#ffffff"
  focus: "{colors.accent}"
typography:
  display:
    fontFamily: "system-ui, -apple-system, \"Segoe UI\", Roboto, sans-serif"
    fontSize: "40px"
    fontWeight: 700
    lineHeight: "48px"
  title:
    fontFamily: "system-ui, -apple-system, \"Segoe UI\", Roboto, sans-serif"
    fontSize: "28px"
    fontWeight: 600
    lineHeight: "36px"
  heading:
    fontFamily: "system-ui, -apple-system, \"Segoe UI\", Roboto, sans-serif"
    fontSize: "20px"
    fontWeight: 600
    lineHeight: "28px"
  body:
    fontFamily: "system-ui, -apple-system, \"Segoe UI\", Roboto, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: "24px"
  label:
    fontFamily: "system-ui, -apple-system, \"Segoe UI\", Roboto, sans-serif"
    fontSize: "14px"
    fontWeight: 500
    lineHeight: "20px"
  caption:
    fontFamily: "system-ui, -apple-system, \"Segoe UI\", Roboto, sans-serif"
    fontSize: "12px"
    fontWeight: 400
    lineHeight: "16px"
rounded:
  radius-sm: "4px"
  radius-md: "8px"
  radius-full: "9999px"
spacing:
  space-1: "4px"
  space-2: "8px"
  space-3: "16px"
  space-4: "32px"
---
## Overview

Sample Studio is a plain, calm starter system with a single light theme. Pages sit on `bg`, panels on `surface`, and the one blue accent `accent` is kept for the primary action, so the eye always finds the next step first.

To grow this starter into profile `full`, add three sections to README.md: Content fundamentals (how copy is written: tone, casing, person and length, with two good and two bad example lines), Visual foundations (how colour, type, spacing, corners and surfaces are used, each naming the tokens that carry it) and Iconography (the icon set, its stroke and size, and the source and licence of every file).

- Read order: Claude Design → README.md → tokens.json → components/*/README.md; other agents → DESIGN.md → tokens.json → canonical-map.json → components/
- Owner: Sample Studio maintainers
- Version: 0.1.0
- Status: draft
- Canonical by domain: brand → README.md; tokens → tokens.json; components → none yet (Cover only)

## Colors

- Page and panels: {colors.bg} is the page background; {colors.surface} holds cards and panels.
- Text: {colors.text} for body copy, {colors.muted} for secondary lines, {colors.accent-text} for text placed on the accent.
- Lines: {colors.border} for hairlines and dividers.
- Action and focus: {colors.accent} marks the single primary action and links; {colors.focus} is the focus ring and follows the accent.

## Typography

One font family, key `sans`, set as the system UI stack. Styles: {typography.display} for the system name and one hero line, {typography.title} for page titles, {typography.heading} for section headings, {typography.body} for paragraphs, {typography.label} for buttons and form labels, {typography.caption} for hints and fine print.

## Layout

Spacing has four steps: {spacing.space-1} inside a control, {spacing.space-2} between elements, {spacing.space-3} between groups and {spacing.space-4} between blocks. Content sits in one centred column; this starter defines no grid and no breakpoints, so add them in words here when a real surface needs them.

## Elevation & Depth

This starter defines no shadow or layering tokens. Depth comes from {colors.surface} set against {colors.bg}, with a hairline in {colors.border}. Add a `shadow` family to tokens.json before using a shadow.

## Shapes

Corners use three radii: {rounded.radius-sm} for inputs, {rounded.radius-md} for cards and {rounded.radius-full} for pills.

## Components

- Cover: the card shown first in Claude Design; it carries the name in {typography.display} and one line of tagline, drawn with {colors.accent} and {colors.accent-text}.
- No other component exists in the minimal profile. Add one as components/<Name>/README.md plus preview.html, and list its source in canonical-map.json.

## Do's and Don'ts

- Do keep {colors.accent} for one primary action per screen; don't use it as decoration.
- Do set body copy in {colors.text} on {colors.bg}; don't use {colors.muted} for text a reader must not miss.
- Do pick spacing from the four {spacing.space-1} to {spacing.space-4} steps; don't invent in-between gaps.
- Do round inputs with {rounded.radius-sm} and cards with {rounded.radius-md}; don't mix radii inside one control.
