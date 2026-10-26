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

The rules under [Layout discipline](#layout-discipline) govern marketing surfaces:
landing pages, portfolios, event and product sites. A dashboard, admin screen, or other
dense product UI is still in this pack's scope, but it takes the quality floor and the
product's own system, not the hero, eyebrow, and section-count rules written for
persuasion pages.

## Ground everything in the subject

If the brief does not pin down the subject, pin it yourself and say so: one concrete
subject, its audience, and the page's single job.

Distinctive choices come from the subject's own world — its materials, instruments,
artifacts, vocabulary. A page about maritime logistics has a different set of available
gestures than one about early-childhood education, and the difference should be visible
before you read a word.

**Quiet constraints outrank taste.** Read the brief for the constraints that are easy to
miss: accessibility first, a public-sector or regulated service, trust-critical commerce,
children as the audience. They override aesthetic preference, and so does the audience:
the people who will use the page set the register, not the designer's own appetite.

**The hero is a thesis.** Open with the most characteristic thing in the subject's world,
in whatever form suits it: a headline, an image, an animation, a live demo, an interactive
moment. A large number with a small label, three supporting stats, and a gradient accent is
the template answer — use it only if it is genuinely the best answer here.

**Typography carries the personality.** Pair display and body deliberately, not the
families you would reach for on any project. Set a real type scale with intentional
weights, widths, and spacing. The type treatment is part of what makes the design
memorable, not a neutral delivery mechanism.
For English/Vietnamese work, use [typography-en-vi.md](typography-en-vi.md) to screen
the actual font files, compare scenario shortlists, and test the rendered scale.

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

Four more habits cluster the same way: three equal feature cards in a row; frosted glass
on every surface; small looping animations on content that is not live or changing; and a
centered hero over a dark mesh gradient. Each is fine when the brief or the subject asks
for it, and a default when nothing does.

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

### Quiet is not bare

Restraint is a discipline, not a budget cut. The two are easy to confuse because they
produce similar-looking code and completely different pages: a restrained page has
decided what to leave out, and a bare page has simply not put anything in.

**The rule: a restrained direction still owes at least one invested, unmistakably
designed moment per viewport.** Not per page — per *viewport*. Something in every screenful
a visitor scrolls past has to be visibly the work of someone who cared: a real
compositional idea, a piece of colour doing something, a considered image or object, type
set at a size that took nerve, a detail that could not have been produced by a default
stylesheet. Whitespace, hairlines, and a grid are the *frame* around that moment. They are
not the moment.

**The canonical failure.** A page whose skeleton was a bordered sheet divided into a grid
of hairline cells, each holding a short paragraph, with generous white space between
sections and almost no colour. Every measurable check passed. It scored respectably. Then
its own owner looked at the live page and read it not as a designed website but as a
wireframe someone had forgotten to finish — cells chopped into boxes, no colour, nothing
that felt paid for. The grid was doing the work an idea should have been doing, and even
spacing everywhere produced one flat rhythm with no accent in it.

Three checks that catch it before a stranger does:

- **Point at the moment.** For each viewport, name the one thing you invested in. If the
  answer is "the spacing is nice" or "the type is clean" for three viewports running, the
  page is bare.
- **Vary the rhythm.** If every section is the same height, the same density, and the same
  distance apart, the page has no emphasis — and a page with no emphasis reads as a
  document. Composition means some things are bigger, closer, denser, louder.
- **Emptiness must be composed.** Space is a design decision when something is placed
  against it. Space around evenly-distributed small elements is just a page that has not
  been filled in.

A minimal direction is the *hardest* one to execute, not the cheapest — there is nothing
to hide behind and every remaining decision is exposed. Choosing it commits you to more
precision, not less effort. When a quiet direction cannot carry one invested moment per
viewport, the honest conclusion is that the direction was wrong for this brief, not that
the page needs another round of tightening.

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
- **Audit every visible string before shipping.** Re-read the whole page as a stranger
  would. Rewrite anything grammatically broken, with an unclear referent, or clever at the
  reader's expense; plain and functional beats cute. Invented people and companies get
  realistic, locale-appropriate names, not the stock placeholders every template uses.
  Figures that look too exact or too round come from real data, are labeled as sample
  values, or are cut. Inflated marketing verbs are filler.
- **One label per intent, page-wide.** Two calls to action that mean the same thing under
  different names (in the nav, the hero, the footer) read as two different actions. Pick
  one label and use it everywhere. Keep one copy register per page unless the brand voice
  calls for a mix.

Placeholder copy makes a design feel as templated as placeholder layout does. When the
brief has no real content, writing the copy is part of the design work.

## Layout discipline

Concrete composition checks for marketing surfaces: landing pages, portfolios, event and
product sites. Every number in this section is a **starting point for persuasion pages,
not an accessibility rule**: exceed one on purpose and say why in the plan. Where this
overlaps *the hero is a thesis* above, the subject decides what the hero says and this
section only limits how much text and furniture gets packed into it. Dense product UI
does not use this section (see *Posture*).

### Composition

- **Do not center by reflex.** When the chosen direction is asymmetric, avoid defaulting
  to a centered hero and centered headings: use a split, a left-weighted layout, or
  deliberate empty space. Centering stays right for a manifesto, an editorial piece, or a
  launch where the message is the design.
- **Do not repeat a layout family back to back.** A family (a row of image cards, a
  full-width quote, a text-and-image split) may return later on the page but not in the
  next section; as a starting point, a page of eight sections draws on at least four
  distinct families. The section after a family breaks the pattern with a full-width
  block, a vertical stack, a bento, or another family.
- **Stack section headers by default.** A big headline on the left with a small explainer
  paragraph floating on the right is a template tell. Put the body under the headline at a
  readable measure, and split only when the second column carries a real visual or
  control.
- **Grids match their content.** Cell count equals item count: three items are one plus
  two, never a row of three with a blank tile. Give two or three cells of a multi-cell
  grid real variation (an image, a brand tint, a pattern) so the page is not a wall of
  identical white cards.

### The hero

- **It fits the first screenful.** At desktop: a headline of two lines or fewer,
  supporting text of about 20 words or fewer, and the primary action visible without
  scrolling. If it does not fit, cut copy or reduce the scale before cutting the image.
- **Plan the type with the asset.** A four-line headline is a size error; reserve the
  largest display sizes for very short headlines.
- **At most four text elements:** an optional eyebrow or brand strip, the headline, the
  supporting text, and the actions (one primary, at most one secondary). A tagline under
  the buttons, a trust strip, a pricing teaser, feature bullets, and an avatar row belong
  in the sections below.
- **Top padding is not breathing room.** Around 96px above the hero at desktop is a
  ceiling; more air comes from larger type or a larger asset.
- **A logo wall sits under the hero**, never in the same row as the hero copy, and holds
  logos only, with no category labels beneath them.
- **A hero needs a real visual.** Copy over a gradient blob is a placeholder.
- **Navigation stays on one line at desktop**, at most about 80px tall. Condense labels,
  drop secondary items, or collapse to a menu before it wraps.

### Eyebrows and labels

- Count the small tracked uppercase labels above headlines mechanically: at most one per
  three sections, and the hero counts. Past that, delete the label and let the headline
  carry the section.
- Numbered markers, tile pagination, date-range labels, and version tags on a hero are
  decoration unless the page really is a sequence or a launch (see *Structure is
  information*).

### Cards, depth, and shape

- **A card needs a reason.** Use one only when elevation communicates hierarchy; otherwise
  group with a rule, a divider, or space.
- **Tint shadows toward the background hue.** A pure-black drop shadow on a light surface
  looks pasted on.
- **Lists past five items** are not a default bullet list with a rule under every row.
  Group them into two columns, a card grid, tabs, a disclosure, or a scroll-snap strip. A
  specification table of ten ruled rows is the weakest layout for specs: feature three or
  four values and put the full table behind a link.
- **Do not draw a rule above and below every row.** Pick one and use it sparingly. A
  comparison bar with a filled track behind it adds noise: show the number, or a bar with
  no track.

### Content density

- A section's default shape is a headline of about eight words or fewer, a supporting
  line of about 25 words or fewer, and one visual or one action. More has to be justified
  by that section's job.
- Do not dump data on a persuasion page. Show the three to five strongest rows and link to
  the rest, or give the data its own page when the data is the product.

### Decoration that says nothing

Cut these unless they carry real information: tags or pills laid over images (put a
caption below instead); photo credits used as ornament; version or build stamps in a
marketing footer; a text strip at the hero's foot that links nowhere; scroll cues and
animated mouse icons; status dots that report no real status; clock, weather, or locale
strips; vertical rotated text; poetic section names where a plain one works (a plain
name for testimonials beats a coined phrase); generic numbered step labels where a verb
and a noun would do; and middle dots used as punctuation more than once per metadata
line.

### Locks

Choose each of these once per project and hold it everywhere. A late exception is a defect
unless a written rule allows it.

- **One theme per page.** A dark page is dark in every section; a warm-paper band in the
  middle of a dark scroll looks broken. Tints within one family are fine. One deliberate
  full switch is allowed only when the brief calls for it.
- **One accent color**, applied across the whole page, from the first section to the
  footer; a stray second accent in a late section is a defect. Size its chroma with the
  surface-area table in [color-protocol.md](color-protocol.md), and go beyond it only for a
  deliberately electric direction.
- **One corner-radius scale:** all sharp, all softly rounded, or all pill. A mixed set is
  acceptable only with a stated rule (for example, buttons pill, cards one radius, inputs
  a smaller one) that is followed everywhere.
- **One icon family and one stroke weight** (see [library-selection.md](library-selection.md)).
- **One design system per project.**

### Quotes and testimonials

- A quote fits in a glance: about three lines or fewer. Cut or excerpt longer ones.
- Attribute it with a name and a role, and the organization when there is one. A name
  alone is not evidence.
- Use real typographic quotation marks or none, never straight ASCII marks as display
  quotes.
- Real people only. If the page has no genuine testimonial yet, use the honest placeholder
  from *Restraint*, never an invented endorsement.
