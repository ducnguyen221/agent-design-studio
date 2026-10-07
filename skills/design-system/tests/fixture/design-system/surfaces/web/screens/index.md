# Entry screen — declared as-is

Task: inspect a source trace and trigger demo feedback. Information hierarchy: h1,
explanation, input label/input, action, status. Grid: main max60ch, auto margins,
24px padding, vertical input/actions. Breakpoints: no explicit viewport breakpoints;
input max-width100% is declared; overflow checks require browser evidence.

Data formatting: plain text; number/date/units N/A, no formatted business data. Initial
state is empty feedback; action produces error text. Loading/permission N/A: no request
or authorization logic. Interaction/recovery: button replaces feedback on every click,
no successful submit/conditional validation. Accessibility: lang=en, native controls,
label for input, live status and 3px focus outline; runtime behavior unverified here.

[HTML entry](../../../../index.html) · [Page module](../../../../src/page.js)
· [Button](../../../components/button.md) · [Action feedback](../../../patterns/action-feedback.md)
