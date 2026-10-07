# Action feedback pattern — declared as-is

- Task: demonstrate a button updating a feedback region.
- Information order/hierarchy: label/input, action, feedback; heading introduces the demo.
- Grid/breakpoints: vertical document flow; max60ch main/padded24px, no named breakpoint.
- Data formatting: plain English string; numeric/date/unit formatting N/A, no such data.
- States: initial empty message; click assigns an error message. Loading/permission N/A
  because there is no network or access-controlled operation. No success state modeled.
- Interaction: click handler always replaces feedback, regardless of input value; input
  validation/recovery logic unknown/not implemented. [Page source](../../src/page.js).
- Accessibility: native button and labeled input; role=status/aria-live=polite feedback;
  focus outline declared. Actual keyboard/announcement checks need browser evidence.
- Components: [Button](../components/button.md); consumer [entry screen](../surfaces/web/screens/index.md).

No template slots are defined: this is a pattern used by one concrete screen, not a kit.
