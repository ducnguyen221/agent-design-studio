---
version: alpha
name: "Fixture Studio"
colors:
  bg: "#ffffff"
  surface: "#f5f5f4"
  text: "#1c1917"
  muted: "#57534e"
  border: "#d6d3d1"
  accent: "#2563eb"
  accent-text: "#ffffff"
  focus: "{colors.accent}"
  danger: "#b91c1c"
  success: "#15803d"
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

Fixture Studio is an original, quiet system for tests: a light and a dark theme, `surface` panels on `bg`, and one blue accent `accent` for the primary action. It is a package that an audit can read and a code baseline that an audit can check it against.

- Read order: Claude Design → README.md → tokens.json → components/*/README.md; other agents → DESIGN.md → tokens.json → canonical-map.json → components/
- Owner: fixture author
- Version: 0.1.0
- Status: approved
- Canonical by domain: brand → README.md; tokens → tokens.json; components → src/Button.js (see canonical-map.json)

Start here: [Brand book](README.md), [Button](components/Button/README.md), [Action feedback](patterns/ActionFeedback.md), [Web surface rules](surfaces/web/rules.md), [Icons](assets/Icons/README.md).

Paths are relative to the fixture project root, one level above this folder. Extract and audit must leave this baseline unchanged. Intentional drift: the accent token here differs from the accent custom property in src/tokens.css. An audit must report both and keep the owner decision pending. Runtime, accessibility and token-to-render parity stay unverified until a browser run.

## Colors

- Page and panels: {colors.bg} is the page background; {colors.surface} holds cards and panels.
- Text: {colors.text} for body copy, {colors.muted} for secondary lines, {colors.accent-text} for text placed on the accent.
- Lines: {colors.border} for hairlines and dividers.
- Action and focus: {colors.accent} marks the single primary action and links; {colors.focus} is the focus ring and follows the accent.
- State: {colors.danger} for errors and destructive actions, {colors.success} for confirmations.
- Every colour has a light and a dark value; this file's front matter shows the light one.

## Typography

One font family, key `sans`, set as the system UI stack. Styles: {typography.display}, {typography.title} and {typography.heading} for headings from largest to smallest, {typography.body} for paragraphs, {typography.label} for buttons and form labels, {typography.caption} for hints.

## Layout

Spacing has four steps: {spacing.space-1} inside a control, {spacing.space-2} between elements, {spacing.space-3} between groups and {spacing.space-4} between blocks. The web surface is one centred column at most 60 characters wide with no named breakpoints; see [Web surface rules](surfaces/web/rules.md).

## Elevation & Depth

This fixture defines no shadow or layering tokens. Depth comes from {colors.surface} against {colors.bg}, with a hairline in {colors.border}.

## Shapes

Corners use three radii: {rounded.radius-sm} for inputs and buttons, {rounded.radius-md} for cards and {rounded.radius-full} for pills.

## Components

- Cover: the first card, with the name in {typography.display}, drawn with {colors.accent} and {colors.accent-text}.
- Button: starts one action, set in {typography.label} on {colors.accent} with {colors.accent-text}, intended corners {rounded.radius-sm}. Its source adds fixed padding and radius that bypass the spacing and radius tokens. See [Button](components/Button/README.md) and the [action feedback pattern](patterns/ActionFeedback.md).

## Do's and Don'ts

- Do keep {colors.accent} for one primary action per screen; don't use it as decoration.
- Do name the action on a button in {typography.label}; don't use vague labels.
- Do show errors in {colors.danger} next to the field; don't rely on colour alone.
- Do take gaps from {spacing.space-1} to {spacing.space-4}; don't hardcode padding in a component.
