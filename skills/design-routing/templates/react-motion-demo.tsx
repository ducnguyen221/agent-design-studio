import { useEffect, useLayoutEffect, useRef, useState } from "react";

/** Original client-side card → detail example. Render the destination before animating. */
export default function ReactMotionDemo() {
  const [open, setOpen] = useState(false);
  const [reduced, setReduced] = useState(() =>
    typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches
  );
  const detailRef = useRef<HTMLElement>(null);
  const cardButtonRef = useRef<HTMLButtonElement>(null);
  const backButtonRef = useRef<HTMLButtonElement>(null);
  const activeAnimation = useRef<Animation | null>(null);
  const hasInteracted = useRef(false);

  useEffect(() => {
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setReduced(query.matches);
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, []);

  useLayoutEffect(() => {
    if (!hasInteracted.current) return;
    // Focus moves even when the animation API throws or reduced motion is requested.
    if (open) backButtonRef.current?.focus();
    else cardButtonRef.current?.focus();
  }, [open]);

  useEffect(() => {
    const target = open ? detailRef.current : null;
    if (!target || reduced || !hasInteracted.current) return;
    let animation: Animation | null = null;
    try {
      // The element is never hidden in CSS. This small optional cue is interruptible.
      animation = target.animate(
        [{ opacity: 0.78, transform: "translateY(8px)" }, { opacity: 1, transform: "none" }],
        { duration: 180, easing: "ease-out" }
      );
      activeAnimation.current = animation;
      void animation.finished.catch(() => {
        // Cancellation or a runtime failure leaves the rendered destination visible.
        animation?.cancel();
      });
    } catch (_) {
      // Static content and focus already work.
    }
    return () => {
      animation?.cancel();
      if (activeAnimation.current === animation) activeAnimation.current = null;
    };
  }, [open, reduced]);

  function showDetail(next: boolean) {
    hasInteracted.current = true;
    activeAnimation.current?.cancel();
    setOpen(next);
  }

  return (
    <>
      <style>{`
        .motion-demo { min-height: 100vh; padding: clamp(1rem, 5vw, 4rem); background: #f3f4ed; color: #17302c; font: 16px/1.5 system-ui, sans-serif; }
        .motion-demo * { box-sizing: border-box; }
        .motion-demo__shell { max-width: 52rem; margin: 0 auto; }
        .motion-demo h1 { font-size: clamp(2rem, 6vw, 4rem); line-height: 1.05; letter-spacing: -.05em; }
        .motion-demo__card, .motion-demo__detail { padding: clamp(1.25rem, 4vw, 3rem); background: white; border: 1px solid #b9cec1; border-radius: 1rem; }
        .motion-demo__card { display: grid; grid-template-columns: 1fr auto; gap: 1.5rem; align-items: center; }
        .motion-demo__eyebrow { font-size: .85rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; color: #335e4b; }
        .motion-demo button { min-height: 2.75rem; padding: .6rem 1rem; font: inherit; font-weight: 700; color: #fff; background: #17674e; border: 0; border-radius: .6rem; cursor: pointer; }
        .motion-demo button:hover { background: #11553e; }
        .motion-demo button:active { background: #0b4431; }
        .motion-demo button:focus-visible { outline: 3px solid #0b6d52; outline-offset: 4px; }
        .motion-demo__detail p { max-width: 62ch; }
        @media (max-width: 650px) { .motion-demo__card { grid-template-columns: 1fr; } }
        @media print { .motion-demo { background: white; padding: 0; } .motion-demo button { display: none; } }
      `}</style>
      <main className="motion-demo">
        <div className="motion-demo__shell">
          <p className="motion-demo__eyebrow">Fieldnotes / interaction</p>
          <h1>Keep your place through a change.</h1>
          {open ? (
            <section className="motion-demo__detail" ref={detailRef} aria-label="Detail view">
              <p className="motion-demo__eyebrow">Detail / 01</p>
              <h2>A clear next step</h2>
              <p>The detail is readable before any animation starts. Close it at any time; the card returns and receives focus.</p>
              <button ref={backButtonRef} type="button" onClick={() => showDetail(false)}>Back to card</button>
            </section>
          ) : (
            <section className="motion-demo__card" aria-label="Card view">
              <div><p className="motion-demo__eyebrow">Card / 01</p><h2>A useful idea</h2><p>Open the detail to read what changed.</p></div>
              <button ref={cardButtonRef} type="button" onClick={() => showDetail(true)}>Open detail</button>
            </section>
          )}
          <p>Motion preference: {reduced ? "reduced" : "standard"}. The interaction works in either mode.</p>
        </div>
      </main>
    </>
  );
}
