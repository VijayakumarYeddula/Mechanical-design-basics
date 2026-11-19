# Mechanical Design Basics: From Requirement to Release - open course files

© 2026 Vijayakumar Yeddula · CC BY 4.0 (content) · MIT (code) · Mechanical Design Basics (C4) · version 1.0.0

Educational example - not for production, manufacture or legal use.

These are the free learner files of the YouTube course **"Mechanical Design Basics: From Requirement to Release"** from the channel *Vijayakumar Yeddula | Engineering & Career Skills*. The course is free and not monetised. It follows one small part, a sheet-metal motor bracket (ACT-103), from requirement to release, and you practise every step on your own shelf bracket.

- Course playlist: https://www.youtube.com/playlist?list=PLbxTiMPUncZo
- This release (DOI): https://doi.org/10.5281/zenodo.24382553

## Fictional company, synthetic data

- The product used throughout the course, the belt-driven actuator **ACT-100** and its parts (ACT-101, ACT-103 and others), is **fictional**. It is original and unbranded and does not describe any real product, employer or client. ENGXTECH is a fictional company.
- All loads, prices, quantities, supplier replies, field reports and stories are **synthetic and illustrative**. Files marked SAMPLE do not describe real products or suppliers. Files marked TRAINING COPY or TEACHING SAMPLE contain planted errors or another convention on purpose.
- Material properties are typical published values or specified minimum values from the standards named in the files. They are given so the worked examples can be checked, not as design data.
- In short: fictional company, synthetic data.

## The course: three parts, 24 episodes

**Part 1: Define & Make It Strong (Ep 00-08)**

- Ep 00 - Start here: who this free mechanical design course is for
- Ep 01 - What is mechanical design? Design process, lifecycle, cost of change
- Ep 02 - Engineering requirements: how to write a product design specification
- Ep 03 - Concept selection: morphological chart and Pugh matrix
- Ep 04 - Free-body diagrams for machine design: find the load path
- Ep 05 - Bending stress and factor of safety by hand: a bracket example
- Ep 06 - Deflection, stress raisers and fatigue basics for designers
- Ep 07 - Material selection and finishes: aluminium, steel or plastic?
- Ep 08 - Bolts, thread engagement and standard parts in aluminium

**Part 2: Drawings, Tolerances & GD&T (Ep 09-16)**

- Ep 09 - Types of engineering drawings and what each one contains
- Ep 10 - Angle of projection: 1st angle vs 3rd angle explained
- Ep 11 - Drawing basics: views, line types, sections and title block
- Ep 12 - Drawing symbols and dimensions: holes, threads, bends, surface finish
- Ep 13 - Tolerances, fits and tolerance stack-up basics
- Ep 14 - GD&T basics: datums and position tolerance
- Ep 15 - Inch vs mm and number formats: reading US and ISO drawings
- Ep 16 - Checking a drawing like a checker

**Part 3: Make It Buildable & Release It (Ep 17-23)**

- Ep 17 - Sheet metal design rules (DFM) and talking to suppliers
- Ep 18 - Plastic part design rules: walls, draft, ribs and bosses
- Ep 19 - Casting design basics: sand, die and investment casting
- Ep 20 - Design for assembly (DFA), mistake-proofing and design reviews
- Ep 21 - Design for service and safety: tool access, repair time and guarding
- Ep 22 - Change control: ECR, ECO, deviations and revisions
- Ep 23 - Build and present your design package

## What is in each folder

| Folder | What it holds |
|---|---|
| `learner-pack/Part1/` | Part 1 files (Ep 00-08): `Am_I_Ready.pdf`, study plan, glossary, the `Shelf_Bracket_Brief.pdf` (pick your exercise variant here), a worksheet and an answer key for every episode (`Worksheet_EpNN.pdf`, `Answers_EpNN.pdf`), reference cards, the bracket load sketch, SAMPLE datasheets and the spreadsheets (PDS, morphological chart, Pugh matrix, calculation sheet, material matrix, bolt check). |
| `learner-pack/Part2/` | Part 2 files (Ep 09-16): worksheets and answer keys, the ACT-103 bracket drawing and its ERRORS exercise sheet, the shelf-bracket detail, isometric and ERRORS drawings, projection samples, drawing, symbol, GD&T, units and inspection cards, the drawing check checklist and the stack-up spreadsheet. |
| `learner-pack/Part3/` | Part 3 files (Ep 17-23): worksheets and answer keys, the ACT-103 Rev A drawing and its flat pattern as DXF (`ACT-103_Rev_A_flat.dxf`), the shelf-bracket DFM and casting sheets, DFM, molding, casting and service checklists, RFQ and design-package templates, a scored example package, and the spreadsheets (flat pattern, DFA audit, action log, MTTR, ECR/ECO/deviation templates, supplier query). |
| `models/` | The released 3D models of the ACT-103 bracket as STEP (AP214) files: `ACT-103_motor_mounting_bracket_RevA_v09.step` (Rev A, as released) and `ACT-103_motor_mounting_bracket_RevB_v09.step` (Rev B, after the ECO in Ep 22: longer motor and pilot slots). One solid each, in mm, in the drawing coordinate system (origin at the outside corner of the bend). The drawing governs; the models are for reference. |
| `source/` | The Facts generator and its outputs (see below), the shelf-bracket generator, the placeholder filler and the legal notice. |

Each `learner-pack/partN/README.md` lists the files episode by episode. Do the worksheet first, in your notebook; then check with the Answers file for the same episode. No printing is needed: a squared notebook, a pencil and a calculator are enough.

### `source/` in detail

| File | What it is |
|---|---|
| `make_facts.py` | Facts generator: every number shown or spoken in the course is computed here from a short list of inputs, with self-checks. |
| `Facts_C4.md`, `facts_c4.json` | Generated table of named values (value, unit, spoken form, formula or source), in Markdown and JSON. Do not edit by hand. |
| `make_shelf_facts.py` | Shelf-bracket (learner exercise) generator: the six course variants, and your own variant 7 with `--own` (see the Shelf Bracket Brief, section 5). Needs `facts_c4.json` and `legal_notice.txt` in the same folder. |
| `Facts_C4_shelf.md`, `facts_c4_shelf.json`, `shelf_variants.csv` | Generated shelf-bracket values for the six course variants. Do not edit by hand. |
| `shelf_bracket_brief.md` | Text source of `Shelf_Bracket_Brief.pdf`; the shelf-bracket generator checks its notice footer. |
| `fill_facts.py` | Replaces `[F: name]` placeholders in Markdown files with values from one or more Facts JSON files. |
| `legal_notice.txt` | The full and short disclaimer used on every course file. |

## Regenerate the Facts

Python 3, standard library only. From the top folder of this release:

```
python3 source/make_facts.py source
```

This rewrites `source/Facts_C4.md` and `source/facts_c4.json`, writes `source/make_facts.log`, and prints one line: `PASS 0 failures` when every self-check holds (otherwise the failures are listed in `make_facts.log`). The regenerated files are identical to the published ones. (Without an output folder, `python3 source/make_facts.py` writes the same files into the current folder.)

Shelf-bracket values for the six course variants, or for your own variant 7:

```
python3 source/make_shelf_facts.py
python3 source/make_shelf_facts.py --own 7 180 3.0 6061-T6 outdoor_covered 400
```

The first command rewrites the shelf files in `source/` (identical to the published ones). The second writes `Facts_C4_shelf_own.md` and `facts_c4_shelf_own.json` in the current folder and does not change the course files. Arguments: load in kg, depth in mm, thickness in mm, upright, environment (`indoor_dry`, `indoor_humid`, `outdoor_covered`, `outdoor_coastal`), quantity.

To fill placeholders in your own Markdown notes:

```
python3 source/fill_facts.py <src_dir> <out_dir> source/facts_c4.json
```

Narration lines (starting with `>`) get the spoken form; all other lines get the printed value. It prints `PASS 0 unresolved` when every placeholder was found.

## Free tools

- **Spreadsheets (`.xlsx`, `.csv`):** Excel, LibreOffice Calc or Google Sheets. The spreadsheets are optional; every worksheet can be done on paper.
- **PDF files:** any PDF reader.
- **3D models (`.step`):** FreeCAD (free and open source) opens them; most other CAD programs can import STEP too. Note: on the Onshape Free plan, every document you create is public.
- **Flat pattern (`.dxf`):** FreeCAD or LibreCAD.
- **Generators (`.py`):** Python 3, standard library only.

## Standards

Standards are cited by number only, to name where a value or rule comes from. No text or tables from any standard are reproduced. Always use the current edition from the publisher. The Facts generator cites ISO 965, ISO 2081, ISO 4753, ISO 4759-1, ISO 4762, ISO 7089, ISO 7380-2, ISO 19598, ASTM A568, ASTM A1008/A1008M, ASTM B209, ASTM B633, EN 485-2, EN 485-4, EN 10130, EN 10131, EN 10204 and DIN 6935; the learner files also name drawing and tolerancing standards such as ISO 128, ISO 1101, ISO 2768-1, ISO 5456-2, ISO 8015 and ASME Y14.5.

## Licences

- Content (text, data, worksheets, answer keys, drawings, cards, spreadsheets, DXF and STEP models) is licensed under the Creative Commons Attribution 4.0 International licence (CC BY 4.0); see `LICENSE` and https://creativecommons.org/licenses/by/4.0/legalcode.
- Source code (`*.py`) is licensed under the MIT licence; see `LICENSE-CODE`.
- CC BY 4.0 covers the course content; it does not license the instructor's name, voice or likeness (CC BY 4.0 §2(b)(1)).
- © 2026 Vijayakumar Yeddula.
- This kit (version 1.0.0) is the release. Any other copy or earlier version of these files is not part of it.

## How to cite

Please cite this release as given in `CITATION.cff` (GitHub shows a "Cite this repository" button for it), for example:

> Yeddula, V. (2026). *Mechanical Design Basics: From Requirement to Release - open course files* (Version 1.0.0) [Data set and learner files]. https://doi.org/10.5281/zenodo.24382553

## Disclaimer

Disclaimer and limitation of liability. This course and its files are provided for general education only, "as is", without warranty of any kind. They are not professional engineering advice and do not replace the judgement of a qualified engineer, the applicable standards, codes and laws, or the manufacturer's data. The product, companies, parts and data are fictional; any resemblance to real products or companies is coincidental. Standards are referred to by number only; no standard text is reproduced, so always use the current official edition. Brand and product names belong to their owners and are used only for identification; no affiliation or endorsement is implied. To the extent permitted by law, the author accepts no liability for any loss, damage or injury arising from the use of this material. Use is at your own risk.

**Educational examples.** All drawings, calculations, data, models and files describe a fictional product for teaching. They are not production drawings, have not been checked or approved for manufacture, and must not be used for manufacturing, purchasing, certification, contractual or legal purposes.

No endorsement: product, company and standards-body names (for example NEMA, as in "NEMA 17-size", which describes a motor frame size) are used only to describe sizes, materials or tools and belong to their owners. Their mention does not imply affiliation with or endorsement by any of them, and the course is not endorsed by any standards body, vendor or supplier.
# Mechanical Design Basics: From Requirement to Release - open course files

© 2026 Vijayakumar Yeddula · CC BY 4.0 (content) · MIT (code) · Mechanical Design Basics (C4) · version 1.0.0

Educational example - not for production, manufacture or legal use.

These are the free learner files of the YouTube course **"Mechanical Design Basics: From Requirement to Release"** from the channel *Vijayakumar Yeddula | Engineering & Career Skills*. The course is free and not monetised. It follows one small part, a sheet-metal motor bracket (ACT-103), from requirement to release, and you practise every step on your own shelf bracket.

- Course playlist: {PLAYLIST_URL}
- This release (DOI): {DOI}

## Fictional company, synthetic data

- The product used throughout the course, the belt-driven actuator **ACT-100** and its parts (ACT-101, ACT-103 and others), is **fictional**. It is original and unbranded and does not describe any real product, employer or client. ENGXTECH is a fictional company.
- All loads, prices, quantities, supplier replies, field reports and stories are **synthetic and illustrative**. Files marked SAMPLE do not describe real products or suppliers. Files marked TRAINING COPY or TEACHING SAMPLE contain planted errors or another convention on purpose.
- Material properties are typical published values or specified minimum values from the standards named in the files. They are given so the worked examples can be checked, not as design data.
- In short: fictional company, synthetic data.

## The course: three parts, 24 episodes

**Part 1: Define & Make It Strong (Ep 00-08)**

- Ep 00 - Start here: who this free mechanical design course is for
- Ep 01 - What is mechanical design? Design process, lifecycle, cost of change
- Ep 02 - Engineering requirements: how to write a product design specification
- Ep 03 - Concept selection: morphological chart and Pugh matrix
- Ep 04 - Free-body diagrams for machine design: find the load path
- Ep 05 - Bending stress and factor of safety by hand: a bracket example
- Ep 06 - Deflection, stress raisers and fatigue basics for designers
- Ep 07 - Material selection and finishes: aluminium, steel or plastic?
- Ep 08 - Bolts, thread engagement and standard parts in aluminium

**Part 2: Drawings, Tolerances & GD&T (Ep 09-16)**

- Ep 09 - Types of engineering drawings and what each one contains
- Ep 10 - Angle of projection: 1st angle vs 3rd angle explained
- Ep 11 - Drawing basics: views, line types, sections and title block
- Ep 12 - Drawing symbols and dimensions: holes, threads, bends, surface finish
- Ep 13 - Tolerances, fits and tolerance stack-up basics
- Ep 14 - GD&T basics: datums and position tolerance
- Ep 15 - Inch vs mm and number formats: reading US and ISO drawings
- Ep 16 - Checking a drawing like a checker

**Part 3: Make It Buildable & Release It (Ep 17-23)**

- Ep 17 - Sheet metal design rules (DFM) and talking to suppliers
- Ep 18 - Plastic part design rules: walls, draft, ribs and bosses
- Ep 19 - Casting design basics: sand, die and investment casting
- Ep 20 - Design for assembly (DFA), mistake-proofing and design reviews
- Ep 21 - Design for service and safety: tool access, repair time and guarding
- Ep 22 - Change control: ECR, ECO, deviations and revisions
- Ep 23 - Build and present your design package

## What is in each folder

| Folder | What it holds |
|---|---|
| `learner-pack/Part1/` | Part 1 files (Ep 00-08): `Am_I_Ready.pdf`, study plan, glossary, the `Shelf_Bracket_Brief.pdf` (pick your exercise variant here), a worksheet and an answer key for every episode (`Worksheet_EpNN.pdf`, `Answers_EpNN.pdf`), reference cards, the bracket load sketch, SAMPLE datasheets and the spreadsheets (PDS, morphological chart, Pugh matrix, calculation sheet, material matrix, bolt check). |
| `learner-pack/Part2/` | Part 2 files (Ep 09-16): worksheets and answer keys, the ACT-103 bracket drawing and its ERRORS exercise sheet, the shelf-bracket detail, isometric and ERRORS drawings, projection samples, drawing, symbol, GD&T, units and inspection cards, the drawing check checklist and the stack-up spreadsheet. |
| `learner-pack/Part3/` | Part 3 files (Ep 17-23): worksheets and answer keys, the ACT-103 Rev A drawing and its flat pattern as DXF (`ACT-103_Rev_A_flat.dxf`), the shelf-bracket DFM and casting sheets, DFM, molding, casting and service checklists, RFQ and design-package templates, a scored example package, and the spreadsheets (flat pattern, DFA audit, action log, MTTR, ECR/ECO/deviation templates, supplier query). |
| `models/` | The released 3D models of the ACT-103 bracket as STEP (AP214) files: `ACT-103_motor_mounting_bracket_RevA_v09.step` (Rev A, as released) and `ACT-103_motor_mounting_bracket_RevB_v09.step` (Rev B, after the ECO in Ep 22: longer motor and pilot slots). One solid each, in mm, in the drawing coordinate system (origin at the outside corner of the bend). The drawing governs; the models are for reference. |
| `source/` | The Facts generator and its outputs (see below), the shelf-bracket generator, the placeholder filler and the legal notice. |

Each `learner-pack/partN/README.md` lists the files episode by episode. Do the worksheet first, in your notebook; then check with the Answers file for the same episode. No printing is needed: a squared notebook, a pencil and a calculator are enough.

### `source/` in detail

| File | What it is |
|---|---|
| `make_facts.py` | Facts generator: every number shown or spoken in the course is computed here from a short list of inputs, with self-checks. |
| `Facts_C4.md`, `facts_c4.json` | Generated table of named values (value, unit, spoken form, formula or source), in Markdown and JSON. Do not edit by hand. |
| `make_shelf_facts.py` | Shelf-bracket (learner exercise) generator: the six course variants, and your own variant 7 with `--own` (see the Shelf Bracket Brief, section 5). Needs `facts_c4.json` and `legal_notice.txt` in the same folder. |
| `Facts_C4_shelf.md`, `facts_c4_shelf.json`, `shelf_variants.csv` | Generated shelf-bracket values for the six course variants. Do not edit by hand. |
| `shelf_bracket_brief.md` | Text source of `Shelf_Bracket_Brief.pdf`; the shelf-bracket generator checks its notice footer. |
| `fill_facts.py` | Replaces `[F: name]` placeholders in Markdown files with values from one or more Facts JSON files. |
| `legal_notice.txt` | The full and short disclaimer used on every course file. |

## Regenerate the Facts

Python 3, standard library only. From the top folder of this release:

```
python3 source/make_facts.py source
```

This rewrites `source/Facts_C4.md` and `source/facts_c4.json`, writes `source/make_facts.log`, and prints one line: `PASS 0 failures` when every self-check holds (otherwise the failures are listed in `make_facts.log`). The regenerated files are identical to the published ones. (Without an output folder, `python3 source/make_facts.py` writes the same files into the current folder.)

Shelf-bracket values for the six course variants, or for your own variant 7:

```
python3 source/make_shelf_facts.py
python3 source/make_shelf_facts.py --own 7 180 3.0 6061-T6 outdoor_covered 400
```

The first command rewrites the shelf files in `source/` (identical to the published ones). The second writes `Facts_C4_shelf_own.md` and `facts_c4_shelf_own.json` in the current folder and does not change the course files. Arguments: load in kg, depth in mm, thickness in mm, upright, environment (`indoor_dry`, `indoor_humid`, `outdoor_covered`, `outdoor_coastal`), quantity.

To fill placeholders in your own Markdown notes:

```
python3 source/fill_facts.py <src_dir> <out_dir> source/facts_c4.json
```

Narration lines (starting with `>`) get the spoken form; all other lines get the printed value. It prints `PASS 0 unresolved` when every placeholder was found.

## Free tools

- **Spreadsheets (`.xlsx`, `.csv`):** Excel, LibreOffice Calc or Google Sheets. The spreadsheets are optional; every worksheet can be done on paper.
- **PDF files:** any PDF reader.
- **3D models (`.step`):** FreeCAD (free and open source) opens them; most other CAD programs can import STEP too. Note: on the Onshape Free plan, every document you create is public.
- **Flat pattern (`.dxf`):** FreeCAD or LibreCAD.
- **Generators (`.py`):** Python 3, standard library only.

## Standards

Standards are cited by number only, to name where a value or rule comes from. No text or tables from any standard are reproduced. Always use the current edition from the publisher. The Facts generator cites ISO 965, ISO 2081, ISO 4753, ISO 4759-1, ISO 4762, ISO 7089, ISO 7380-2, ISO 19598, ASTM A568, ASTM A1008/A1008M, ASTM B209, ASTM B633, EN 485-2, EN 485-4, EN 10130, EN 10131, EN 10204 and DIN 6935; the learner files also name drawing and tolerancing standards such as ISO 128, ISO 1101, ISO 2768-1, ISO 5456-2, ISO 8015 and ASME Y14.5.

## Licences

- Content (text, data, worksheets, answer keys, drawings, cards, spreadsheets, DXF and STEP models) is licensed under the Creative Commons Attribution 4.0 International licence (CC BY 4.0); see `LICENSE` and https://creativecommons.org/licenses/by/4.0/legalcode.
- Source code (`*.py`) is licensed under the MIT licence; see `LICENSE-CODE`.
- CC BY 4.0 covers the course content; it does not license the instructor's name, voice or likeness (CC BY 4.0 §2(b)(1)).
- © 2026 Vijayakumar Yeddula.
- This kit (version 1.0.0) is the release. Any other copy or earlier version of these files is not part of it.

## How to cite

Please cite this release as given in `CITATION.cff` (GitHub shows a "Cite this repository" button for it), for example:

> Yeddula, V. (2026). *Mechanical Design Basics: From Requirement to Release - open course files* (Version 1.0.0) [Data set and learner files]. {DOI}

## Disclaimer

Disclaimer and limitation of liability. This course and its files are provided for general education only, "as is", without warranty of any kind. They are not professional engineering advice and do not replace the judgement of a qualified engineer, the applicable standards, codes and laws, or the manufacturer's data. The product, companies, parts and data are fictional; any resemblance to real products or companies is coincidental. Standards are referred to by number only; no standard text is reproduced, so always use the current official edition. Brand and product names belong to their owners and are used only for identification; no affiliation or endorsement is implied. To the extent permitted by law, the author accepts no liability for any loss, damage or injury arising from the use of this material. Use is at your own risk.

**Educational examples.** All drawings, calculations, data, models and files describe a fictional product for teaching. They are not production drawings, have not been checked or approved for manufacture, and must not be used for manufacturing, purchasing, certification, contractual or legal purposes.

No endorsement: product, company and standards-body names (for example NEMA, as in "NEMA 17-size", which describes a motor frame size) are used only to describe sizes, materials or tools and belong to their owners. Their mention does not imply affiliation with or endorsement by any of them, and the course is not endorsed by any standards body, vendor or supplier.
