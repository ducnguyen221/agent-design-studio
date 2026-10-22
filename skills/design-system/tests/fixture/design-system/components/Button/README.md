A button starts one action.

## Variants

Primary only. The source declares one `primary` class: an accent fill with a white label. There is no secondary, disabled or loading variant.

## States

- Default: accent fill, `label` type style.
- Focus: a 3px outline, declared in the entry page.
- Hover, disabled and loading: not implemented.

The source sets padding and corner radius as fixed values in the entry page. The intended mapping is `space-2` and `space-3` for padding and `radius-sm` for the corner.

## Accessibility

- Role `button`, from the native element.
- Enter and Space activate it, as for any native button.
- The visible label is the accessible name, so every button needs a meaningful label.
- Runtime keyboard and screen reader behaviour is not verified here.

Source: src/Button.js. Feedback after a click belongs to the pattern in patterns/ActionFeedback.md.
