# Briefing the studio — how to get great results

The process is only as good as what you feed it. This page shows exactly what to say,
what to hand over, and what happens at the two moments where you decide.
🇻🇳 [Tiếng Việt](GUIDE.vi.md)

## The six inputs that matter

Give these six things and the agent can run the whole process well. Miss them and it
will stop and ask — which also works, but costs a round trip.

| # | Input | Why it matters | Example |
| --- | --- | --- | --- |
| 1 | **What it is, for whom** | Everything else derives from this | "A landing page for a scheduling tool, for clinic owners" |
| 2 | **The one job** | A page that tries to do three things does none | "Get them to book a demo" |
| 3 | **Real content** | Real headlines and real numbers shape real layouts; placeholder text produces placeholder design | Paste your actual copy, product names, prices, screenshots |
| 4 | **Brand — or none** | With a brand, colors are *extracted* from your real assets, never guessed. Without one, say so — the agent derives a palette from the subject | A logo file, your site URL, or "no brand yet" |
| 5 | **Where it lives** | A standalone page and a screen inside your app are different jobs with different rules | "One HTML file" vs "inside our React app, repo attached" |
| 6 | **Speed vs. care** | The three-options checkpoint is the default. You can skip it | "Show me options" or "no options, just build it" |

## Prompt templates — copy, fill, send

**A new page or site**

> Design and build a landing page for **[product]**, aimed at **[audience]**.
> The one thing it must do: **[action]**.
> Here is the real content: **[paste copy / attach files]**.
> Brand: **[logo/site link — or "none, derive it"]**.
> Show me three directions before building.

**A redesign**

> Redesign **[URL or file]**. Keep the content, rethink the design.
> What bothers me today: **[honest list]**.
> What must not change: **[constraints]**.
> Show me three directions before building.

**A screen inside a real app**

> Design the **[screen]** in our app (repo at **[path]**). Follow the project's
> existing stack and components. The user's goal on this screen: **[goal]**.
> States that matter: **[loading / empty / error / …]**.

## What good inputs look like

- **Real text beats lorem ipsum, every time.** Even rough real sentences.
- **Show, don't describe.** One link to a site you love says more than five adjectives.
  The agent verifies real examples exist, then dissects what makes them work.
- **Name what you hate.** "No dark theme, no giant gradients" is extremely useful input.
- **Screenshots of your product** let real UI appear in the design instead of grey boxes.

## The two moments you decide

**Checkpoint 1 — pick a direction.** You get three genuinely different versions, built
for real, with screenshots. Pick by the *idea*, not the polish — finishing is the next
step's job. Say what you like and dislike in plain words; "B, but calmer" is a
perfectly good answer. Not sure? Ask for a mix, or another round.

**Checkpoint 2 — accept the work.** You get the finished build plus an honest
self-inspection report: scores, what was fixed, what was left and why. Everything the
run produced sits in one folder — a status page written for people who don't read code,
and a file for every step.

## Where to look for inspiration

- **The built-in style catalogue** — 40 named styles across pages, decks and
  infographics, inside this pack (`references/direction-gate.md`). The agent draws from
  it when generating options.
- **Award galleries** — [Awwwards](https://www.awwwards.com),
  [CSS Design Awards](https://www.cssdesignawards.com), [FWA](https://thefwa.com),
  [Godly](https://godly.website) for websites; [Land-book](https://land-book.com) and
  [SaaS Landing Page](https://saaslandingpage.com) for landing pages;
  [Mobbin](https://mobbin.com) for app UI patterns.
- **Your own field.** The best directions often come from the subject's real world —
  a coffee brand's packaging, a clinic's paperwork, a festival's posters. Point the
  agent at them.
- **A finished run of this process** — [`docs/example/`](docs/example/), published at
  [ducnguyen.vn/agent-design-studio/example](https://ducnguyen.vn/agent-design-studio/example/).
  Useful in a different way from a gallery: it shows what a brief, a direction decision and
  a review report actually look like when written well, so you can see the shape of a good
  answer before you write your own.

Pick one or two references, not ten. A pile of links averages into mush; one loved
example gives the agent something to dissect.

## Common mistakes

1. **Adjectives instead of content.** "Modern, clean, professional" describes every
   page ever made. Real copy + one reference beats any adjective list.
2. **Choosing at Checkpoint 1 by color.** Colors are easy to change; the underlying
   idea is not. Pick the concept.
3. **Skipping the checkpoints to save time, then redesigning twice.** The checkpoint
   exists because rework after build costs more than a decision before it.
4. **No audience.** "For everyone" designs are for no one. Name a person.
5. **Withholding the bad news.** Budget limits, a logo you're stuck with, a CEO who
   hates purple — the agent designs around constraints it knows about.
