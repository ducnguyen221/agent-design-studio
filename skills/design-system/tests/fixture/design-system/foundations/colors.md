# Colors and tokens

Canonical token source: [CSS variables](../../src/tokens.css). It declares accent,
gap, text and surface at :root. [Entry HTML](../../index.html) consumes accent on the
primary button, text/surface on body and gap on actions margin. These are declared
relationships; computed values require browser evidence. CSS remains canonical,
not a JSON export. DESIGN intentionally documents an accent drift; owner resolution
is pending. No alternate palette is introduced by extraction.

Focus outline, radius and padding are hardcodes in HTML; a migration would need a
run proposal and owner/reviewer approval. [Button spec](../components/button.md)
