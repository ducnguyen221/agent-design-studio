# Library selection

Loaded during Step 5 in `existing-product` mode, when a new front-end dependency is on
the table. A dependency is a permanent decision made in a temporary moment — this is the
five minutes that prevents years of maintenance.

## The order of questions

**1. Is a library needed at all?**

Not every problem is a package. A fade is a CSS transition. A tooltip on a static page is
a positioned element. A one-off animation is not a reason to install a motion library. Ask
what the platform gives you free first — modern CSS and native HTML elements cover far
more than they used to.

**2. Is something already installed that solves it?**

Read the manifest before searching the internet. If the project already uses a library in
this category, use it. If it uses a competitor to what you would have chosen, flag the
observation but **do not churn the dependency** without being asked. Two libraries doing
one job is worse than one imperfect library doing it.

**3. Is this actually a component problem or an animation problem?**

The most common mismatch in this whole area. "I need a dropdown to slide in" is not an
animation task — it is a component task, and the component brings focus management,
dismissal, and keyboard behavior with it. Hand-rolling an overlay to get the animation you
wanted produces something that animates nicely and traps keyboard users.

**4. What does the task actually belong to?**

Identify the category, not the library the user happened to name.

| Category | What to look for |
| --- | --- |
| Accessible primitives — dialogs, popovers, menus, selects, comboboxes | Unstyled and headless, so it inherits your design system rather than fighting it; focus trapping, dismissal, and keyboard interaction handled |
| Command palette | Keyboard-first, filtering built in, virtualized if the list is long |
| Notifications / toasts | A queue, stacking, swipe-to-dismiss, and correct announcement to assistive tech |
| Animation | Springs, layout animation, exit animation, gesture-driven values. Skip if you only need transitions |
| Charts | Distinguish streaming/real-time from static or interactive dashboards — the right answer differs |
| Drag and drop | Sensor abstraction (pointer, touch, keyboard), and a keyboard story that actually exists |
| Virtualization | Handles variable row heights and dynamic content, not just fixed rows |
| Forms and validation | Schema-driven, with error state that maps onto your components |
| State management | Only when prop-passing has genuinely failed. Prefer the smallest thing that works |
| Conditional class names | Trivial and boring; take the smallest one, or the variant-typed one if the component has real variants |
| Theme switching | Must set the theme before first paint, or every reload flashes |

**5. Evaluate the candidate.**

- **Maintained?** Recent releases, issues being answered, a resolved plan for the
  framework's current major version.
- **Accessible?** Keyboard operation and focus management are stated features with tests,
  not a section of the issue tracker.
- **Weight?** Check the actual bundle cost against what it replaces. A 40KB library
  replacing 200 lines of your code is a bad trade; the same library replacing a broken
  hand-rolled dialog is a good one.
- **Styling model compatible?** A library that ships opinionated CSS inside a project with
  its own design system will be fought forever.
- **Escapable?** How much code touches it directly, and how hard is it to leave? Prefer
  ones that stay behind a thin wrapper of your own.
- **Server rendering / hydration** behaves, if the product needs it.

**6. Recommend one.** State what it is for in one sentence and wire it up. Do not present
a menu when there is a clear answer — a menu just moves the decision to someone with less
context.

If the task genuinely falls outside anything you know well, say so explicitly, recommend
from general knowledge, and be clear that you have left familiar ground.

## Mismatches worth catching on sight

- Toasts built by hand, or built on top of a modal library.
- A `div`-based dropdown or dialog with manual focus handling.
- A number animated by re-rendering text — digit transitions are a solved problem.
- A list of a thousand-plus rows rendered directly, then "fixed" with pagination.
- A web of per-component state and prop-drilling standing in for shared state.
- Template-literal class-name ternaries three conditions deep.
- A motion library installed for a hover fade.

## Record it

Add to `05-implementation.md`:

```markdown
## Dependency added
**Package:** <name@version>  ·  **Category:** <from the table>
**Why not the platform:** <what CSS/HTML could not do>
**Why not what's installed:** <or "nothing installed covers this">
**Bundle cost:** <kB> · **Accessibility:** <what it handles for us>
**Exit plan:** <what wraps it, how contained the blast radius is>
```

In `static-artifact` mode the answer is almost always "no dependency": the deliverable is
a self-contained file with no build step, and every added package is another thing that
must be inlined or that breaks when the file is moved.
