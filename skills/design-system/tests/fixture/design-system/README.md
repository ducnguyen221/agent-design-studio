Fixture Studio is a small, original design system that exists to test the design-system skill. It has a light and a dark theme, one blue accent and a single Button, and nothing in it comes from a real product.

## Content fundamentals

Write short, plain English in sentence case. A button names the action it starts, such as "Show validation", never "Click here". An error says what to fix: "Error: enter a value before continuing." Avoid exclamation marks and jargon.

## Visual foundations

Body copy is set in `text` on `bg`; cards and panels use `surface`, separated by a `border` hairline. Secondary lines use `muted`. The `accent` colour is reserved for the one primary action on a screen, with `accent-text` on top of it. Use `danger` for errors and `success` for confirmations. Type is the system UI stack in six styles from `display` to `caption`. Spacing uses `space-1` to `space-4` and corners use `radius-sm`, `radius-md` and `radius-full`. Every colour has a light and a dark value.

## Iconography

The set holds one icon, a check mark drawn for this fixture with a single stroke in the `text` ink. See assets/Icons/README.md for its source and licence.
