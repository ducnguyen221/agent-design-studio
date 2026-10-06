# Motion patterns — choose by user need

Load during Step 6 after the Step 5 static render works. These are decisions, not
components. Apply the four gates in `motion-playbook.md` first; a recipe never overrides
a refusal. Start with one pattern and preserve the static state if any animation API,
observer, callback, or script fails. Each ID maps to source and verification scope in
the private provenance ledger. A reviewed recipe is not a browser-tested implementation.

## MP01 — Encounter cue

- intent: Help a reader notice newly encountered content without withholding it.
- surface: One low-frequency supporting panel below the first viewport.
- trigger: First intersection with the viewport; never on every scroll reversal.
- reject_if: Content is critical, capture/print needs it immediately, or an observer could be the only path to visibility.
- mode: static-artifact or existing-product.
- minimum_tool: CSS or native WAAPI after the static content is visible; optional IntersectionObserver only as a trigger.
- fallback: Keep the panel fully visible and actionable when JS, observer, callback, or animation fails or is interrupted.
- reduced_motion: Show the final state immediately with no travel; preserve content and focus.
- verification: Test no-JS in static mode, observer absent and never-callback, interruption after start, print/full-page capture, keyboard focus, and 390/768/1440px.

## MP02 — Press acknowledgement

- intent: Confirm that a direct action registered without delaying its outcome.
- surface: A primary button or card control with visible focus and stable hit area.
- trigger: Pointer down/up or keyboard activation, once per action.
- reject_if: Activation is frequent, feedback delays navigation, target moves under the pointer, or keyboard focus becomes unclear.
- mode: static-artifact or existing-product.
- minimum_tool: CSS transition for the control's own visual state.
- fallback: Native focus/active state and the real action remain usable if CSS animation is disabled or interrupted.
- reduced_motion: Remove travel/scale but keep clear pressed, focus, and completion feedback.
- verification: Test keyboard Enter/Space, pointer/touch, rapid actions, focus, coarse pointer, and stable target position.

## MP03 — Card to detail continuity

- intent: Preserve orientation when opening a detail view from a card and returning.
- surface: Existing-product card to detail flow with a back control.
- trigger: Explicit open and close actions; interruption must leave a usable current view.
- reject_if: A simple instant swap is clearer, lifecycle cleanup is unavailable, or animation would obscure the active view/focus.
- mode: existing-product.
- minimum_tool: Native WAAPI or an already-installed engine; use no new package for a small fade/translate.
- fallback: Render the destination immediately; if animation throws, rejects, or is cancelled, the current view stays visible and focus moves correctly.
- reduced_motion: Instant view change with explicit focus placement and no spatial travel.
- verification: Test open/close rapidly, error after animation begins, unmount/remount cleanup, focus restoration, and 390/768/1440px.

## MP04 — Completion confirmation

- intent: Make one successful async completion legible without making success depend on animation.
- surface: Status line or progress region after a submitted action.
- trigger: Successful completion event once, never a decorative replay on every render.
- reject_if: Success is already obvious, task is frequent, or feedback would announce only through movement/color.
- mode: static-artifact or existing-product.
- minimum_tool: CSS transition on a nonessential accent; status text and live announcement do the real work.
- fallback: Success text and status semantics appear immediately when motion is unavailable.
- reduced_motion: Keep the status change and announcement, remove the moving accent.
- verification: Test interrupted completion, repeat submissions, screen reader announcement, focus, and no surprise layout shift; runtime not covered by bundled demos.

## MP05 — Bounded wait progress

- intent: Explain a known wait with truthful progress or discrete steps.
- surface: Task progress region with text describing current state.
- trigger: Start/update/end of an actual task; never invent percentage from elapsed time.
- reject_if: No measurable progress exists, motion distracts from another task, or an endless indicator is used as the only information.
- mode: static-artifact or existing-product.
- minimum_tool: Native progress element or text plus restrained CSS state transition.
- fallback: Text and progress semantics remain readable when transitions or scripts do not run.
- reduced_motion: Update progress/value and status text without animated travel.
- verification: Test start, stalled, error, completion, rapid updates, keyboard focus and unexpected layout movement; runtime not covered by bundled demos.

## MP06 — Pausable ambient texture

- intent: Add quiet background rhythm while foreground content stays the sole focus.
- surface: Decorative backdrop away from reading or primary controls.
- trigger: Optional autoplay only after content is available; never flashing or strobing.
- reject_if: Foreground contrast suffers, battery/performance budget fails, or nonessential autoplay lasts over 5 seconds alongside other content without keyboard-operable pause/stop/hide that stays stopped after focus moves.
- mode: static-artifact; existing-product only after its own accessibility and performance review.
- minimum_tool: CSS animation with an explicit pause control and persisted stopped state for the session.
- fallback: Static decorative frame; content and CTA never depend on motion, including when JS is absent.
- reduced_motion: Static frame at load and after a preference change; pause control still works independently in normal mode.
- verification: Test keyboard pause then focus transfer (must stay paused), normal and reduced preferences, no-JS, print, contrast, battery/frame budget, and no flashes; demo only checks the pause mechanism, not all ambient implementations.

## Coverage boundary

`static-motion-demo.html` exercises MP01 and the pause control required by MP06.
`react-motion-demo.tsx` exercises MP02 and MP03. MP04–MP05 are reviewed recipes
without bundled runtime coverage. For a real project, record browser evidence per
accepted item; do not promote documentation review to implementation QA.
