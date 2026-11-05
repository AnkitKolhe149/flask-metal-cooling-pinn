# B.Tech Project Report — LaTeX Source

**Project:** Cloud-Based Food-Delivery Analytics Using Data Engineering and Large Language Models
**Programme:** B.Tech (Honor) in Computer Science and Engineering (Data Science), VII Semester
**University:** Ramdeobaba University, School of Computer Science and Engineering

## Files

| File | Purpose |
|---|---|
| `main.tex` | Complete report source (single file, no external images needed — all diagrams are TikZ) |
| `main.pdf` | Compiled 47-page report (verified: 0 errors, 0 unresolved references) |

## How to compile

Any LaTeX distribution works. Verified with Tectonic; also compatible with TeX Live / MiKTeX / Overleaf:

```bash
pdflatex main.tex   # (or: tectonic main.tex / xelatex main.tex)
pdflatex main.tex   # run twice so the TOC, LoF, LoT and cross-references resolve
```

On Overleaf: create a new project, upload `main.tex`, set the compiler to **XeLaTeX or pdfLaTeX**, and press Recompile (twice).

## Compliance with the university guidelines

- Structure in the required order: Cover → Certificate → Student Declaration → Approval Sheet → Acknowledgement → Abstract → ToC → List of Figures → List of Tables → List of Abbreviations → Chapters 1–6 → References → Appendix A → Annexures A–C.
- A4, Times New Roman (TeX Gyre Termes), 12 pt body, 16 pt bold uppercase chapter headings, 14 pt bold section headings, 12 pt bold subsection headings, 1.5 line spacing, justified, left 1.5″ / right 1″ / top 1″ / bottom 1″ margins, 6 pt after paragraphs.
- Page numbering: none on the cover, Roman numerals from the Student Declaration to the List of Abbreviations, Arabic from Chapter 1, no numbers on chapter separator pages.
- Every chapter starts on a new page with an unnumbered separator page.
- ~5,400 words of main text (within the 3,000–6,000 limit); 24 IEEE-style references (within the 20–25 guideline).

## Placeholders still to be filled (search for `[` or `\ph{`)

1. **Cover page** — university logo image; the three students' roll numbers; project guide's name.
2. **Certificate / Approval sheet** — date; guide's signature and name.
3. **Table 4.2 (tech stack)** and **Appendix A** — exact tool versions and the Grok model identifier.
4. **Chapter 5, Tables 5.1–5.3** — measured results from actual runs: functional test statuses, dataset row counts, dbt tests passed/failed, AI feature test outcomes. These are intentionally left as `\ph{record}` placeholders; the report makes no unmeasured claims.
5. **Figure 4.3** — replace the framed placeholder box with a real screenshot of the Text-to-SQL interaction (`\includegraphics`).
6. **Dataset details** — source, licence, row counts, date range (Section 3.2 and Appendix A).
7. **Annexure B** — confirm the student-contribution split matches the team's actual division of labour.

> Note: measured values must be inserted only after the experiments are actually run — both source documents (the project report draft and the IEEE paper) explicitly require this, and the Student Declaration states it.
