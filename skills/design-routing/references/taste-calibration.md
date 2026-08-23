# Taste calibration

Step 5, third part. The anti-generic pass: what to avoid because it is a default rather
than a decision, how to plan and critique before writing code, and how to treat words as
design material.

Output: the plan and self-critique recorded in `05-implementation.md`.

## Posture

Work as the design lead at a small studio known for giving every client an identity that
could not be mistaken for anyone else's. This client has already rejected proposals that
felt templated. Make deliberate, opinionated choices specific to this brief, and take
one real aesthetic risk you can defend.

Not taking a risk is itself a risk. A design that offends nobody is usually remembered
by nobody.

## Ground everything in the subject

If the brief does not pin down the subject, pin it yourself and say so: one concrete
subject, its audience, and the page's single job.

Distinctive choices come from the subject's own world — its materials, instruments,
artifacts, vocabulary. A page about maritime logistics has a different set of available
gestures than one about early-childhood education, and the difference should be visible
before you read a word.

**The hero is a thesis.** Open with the most characteristic thing in the subject's world,
in whatever form suits it: a headline, an image, an animation, a live demo, an interactive
moment. A large number with a small label, three supporting stats, and a gradient accent is
the template answer — use it only if it is genuinely the best answer here.

**Typography carries the personality.** Pair display and body deliberately, not the
families you would reach for on any project. Set a real type scale with intentional
weights, widths, and spacing. The type treatment is part of what makes the design
memorable, not a neutral delivery mechanism.

**Structure is information.** Numbering, eyebrows, dividers, and labels should encode
something true. Numbered markers belong on content that really is a sequence — a process,
a chronology — and read as decoration everywhere else.

**Match complexity to the vision.** Maximalist directions need elaborate execution;
minimal directions need precision in spacing, type, and detail. Elegance is executing the
chosen vision well, not choosing the least ambitious vision.

## The three defaults to spend your freedom elsewhere

Machine-generated design currently clusters around three looks. All three are legitimate
for some briefs. What makes them a problem is that they appear regardless of subject —
they are defaults, not choices.

1. **Warm cream background** (around `#F4F1EA`) with a high-contrast serif display and a
   terracotta accent.
2. **Near-black background** with a single bright acid-green or vermilion accent.
3. **Broadsheet layout**: hairline rules, zero border radius, dense newspaper columns.

Add two more that recur just as often:

4. **Uniform deep-navy surface with generic cyan or violet neon glow.** Note the
   precision: the problem is this *specific* combination, not dark design. Cinematic
   lighting, warm cyber palettes, and dark narrative pages are authored decisions and
   are welcome — they carry strong stylistic information, which is exactly the cure for
   sameness.
5. **Rounded card with a colored left border accent**, repeated down the page.

Also on sight: aggressive purple gradients as shorthand for "technology"; an emoji doing
the job of an icon; a gradient on every background; an icon beside every heading;
decorative numbers that count nothing; hand-drawn SVG people, whose faces are always
subtly wrong.

**Where the brief specifies a direction, follow it exactly — the brief's words always
win, including when it asks for one of these looks.** Where the brief leaves an axis
free, do not spend that freedom on a default.

**The one legitimate exception is the brand itself.** If the brand genuinely uses a
purple gradient, using it is not generic — it is the signature. Serving a real
specification is the positive form of avoiding generic work; the avoid-list is only the
negative form.

**Why any of this matters:** a client commissions design so their identity is
recognized. Default output is the average of everything, and the average recognizes
nobody. Avoiding it is not fastidiousness — it is protecting the thing the client is
paying for.

## Two passes: plan, critique the plan, then build

### Pass 1 — the plan

Before writing code, write a compact token system:

- **Color** — 4 to 6 named values, derived through the color protocol.
- **Type** — faces for at least two roles: a characterful display face used with
  restraint, a complementary body face, plus a utility face for captions or data if the
  content needs one.
- **Layout** — a layout concept, described in one-sentence prose and compared using ASCII
  wireframes. Cheap to write, cheap to throw away.
- **Signature** — the single element this page will be remembered by, and how it embodies
  the brief.

Five questions worth answering before the system, because they determine the form:

1. **Narrative role** — is this a hero, a transition, a data surface, a quote, a close?
2. **Viewing distance** — 10cm phone, 1m laptop, 10m projected? This sets type size and
   density.
3. **Emotional temperature** — quiet, energetic, authoritative, tender, sober?
4. **Capacity** — sketch it mentally at small scale: does the content actually fit?
5. **Visual motif** — what element, structure, or metaphor is unique to *this* content?

The fifth is the important one, and it is the hardest to fake. If you cannot name a
motif drawn from the content, the form is coming from a style label rather than from the
subject. Each delivered design should be able to state, in one line, where its form came
from in the content.

### Pass 2 — critique the plan before building

Review the plan against the brief. For each part, ask: *would I have produced this for
any similar brief?* A useful test is to imagine working a nearby prompt and seeing
whether you arrive somewhere similar. Where the answer is yes, revise that part, and
record what changed and why.

Only after the plan survives its own critique do you write code — and then you follow
the revised plan exactly, deriving every color and type decision from it.

Do this thinking privately. Show the user work only when confidence is high enough that
it will land.

## Restraint

**Spend your boldness in one place.** Let the signature element be the memorable thing
and keep everything around it quiet and disciplined. Cut every decoration that does not
serve the brief. Before delivering, look at the whole thing and remove one element — the
one you would defend least.

Two related disciplines:

- **Nothing is filler.** Every element earns its place. Emptiness is a composition
  problem, solved with composition — not by inventing content to fill it.
- **An honest placeholder beats a poor attempt.** A labeled grey block reading
  `[product photo — awaiting asset]` is better than a hand-drawn approximation, and a
  comment saying real data is pending is better than invented numbers that look like
  data. Fabricated content is the one failure a reviewer cannot detect and a user will.

Build to a quality floor without announcing it: responsive to mobile, visible keyboard
focus, reduced motion respected.

**Some directions cost more to make accessible. Choose them knowing that.** Fine-technical
registers — drafting sheets, terminal interfaces, dense data displays, archival labels —
get much of their character from very small monospace labels, 9 or 10 pixels, tightly
tracked. The floor forbids that: labels and captions stay at 12px or larger, and every
colour pairing clears 4.5:1, including the muted greys and the decorative accent that
directions like these want to set text in.

That is a real cost, and it lands late — usually at review, as a list of type sizes to raise
and two colours to darken. Budget for it when you pick the direction. What you must not do
is treat the floor as the thing that flexed: a direction whose identity survives only at
10px did not survive contact with users, and raising the size is the cheaper loss. In
practice the fix is to compensate elsewhere — tighten tracking, add a text-safe darker
variant of the decorative colour so it keeps its hue, and let density come from rules and
alignment rather than from tiny type.

Critique your own work as you build, and take screenshots if the environment allows it —
looking at a picture catches what reading code never will.

## Implementation trap: CSS specificity

Generated stylesheets very often contain rules that silently cancel each other — a
class-based selector and an element-based selector fighting over the same property.
Section padding and margins are where this bites most. Keep the specificity structure
deliberate and flat, and when spacing behaves inexplicably, suspect a collision before
suspecting the value.

## Words are design material

Words are in the interface for one reason: to make it easier to understand and therefore
easier to use. Bring the same intent to copy that you bring to spacing and color. Before
writing anything, ask what the design needs to say and how best to say it for someone
navigating this.

- **Write from the user's side of the screen.** Name things by what people control and
  recognize, never by how the system is built. A person manages notifications, not webhook
  configuration.
- **Describe, don't sell.** Plain terms beat marketing terms; specific beats clever.
- **Active voice by default.** A control says what happens: "Save changes", not "Submit".
- **One name per action, all the way through.** The button that says "Publish" produces a
  message that says "Published". An interface's vocabulary is its signage.
- **Failure and emptiness are direction, not mood.** An error explains what happened and
  how to fix it, in the interface's voice. Errors do not apologize and are never vague. An
  empty screen is an invitation to act.
- **Conversational register, tuned.** Plain verbs, sentence case, no filler, tone matched
  to brand and audience.
- **One job per element.** A label labels, an example demonstrates, nothing does double
  duty.

Placeholder copy makes a design feel as templated as placeholder layout does. When the
brief has no real content, writing the copy is part of the design work.
