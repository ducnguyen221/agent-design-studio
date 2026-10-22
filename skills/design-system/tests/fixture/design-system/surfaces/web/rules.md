# Web surface rules

- Task: inspect a source trace and trigger demo feedback on one screen.
- Layout: one column, `main` at most 60ch wide, centred, with 24px padding. No named breakpoints; the input is at most 100% wide.
- Order: heading, explanation, labelled input, action, status line.
- States: the status line starts empty and shows an error after a click. Loading and permission states do not apply, because nothing is requested or access-controlled.
- Accessibility: native controls, a label bound to the input, a live status region, a 3px focus outline. Runtime behaviour is not verified here.
- Links: [Entry screen](screens/index.md), [Button](../../components/Button/README.md), [Action feedback](../../patterns/ActionFeedback.md).
