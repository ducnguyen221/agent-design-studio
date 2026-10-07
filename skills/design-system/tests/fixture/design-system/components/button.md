# Button — as-is component spec

Implementation: [Button export](../../src/Button.js), native button with label argument,
textContent and primary class. Anatomy: one text label; no icon/slots. Variant: primary
only; no disabled/loading API declared. Token: accent via primary selector in
[HTML](../../index.html), with white label and hardcoded padding/radius.

Use for the demo action. Do: supply a meaningful label; avoid claiming validation logic
is part of Button. Default/focus are declared in source; keyboard activation derives
from native semantics but runtime verification is recorded separately. Hover/disabled/
loading variants are N/A: not implemented. Responsive size follows content; dedicated
breakpoints unknown/not declared. Content and states belong to the
[action feedback pattern](../patterns/action-feedback.md).
