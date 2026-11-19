# Shelf bracket brief - your exercise part for the whole course

Mechanical Design Basics: From Requirement to Release (C4)

**Illustrative values for education.**

**Safety note:** this shelf bracket is a teaching exercise with simplified models and illustrative numbers. It is **not** a design for real wall shelves. Do not use these numbers, drawings or results to build, sell or install shelves. Real shelves need the wall or upright maker's fixing rules, a proper load rating and testing.

No printing needed: a squared notebook, a pencil and a calculator are enough. A free spreadsheet helps but is optional.

---

## 1. What the shelf bracket does

In the lessons we follow one part, the motor mounting bracket. In your worksheets you follow your own part: a **shelf bracket**.

Two shelf brackets hold up one shelf board. Each bracket is a simple L-shape bent from one flat strip of sheet metal:

- the **wall flange** stands upright and is screwed to a **tapped aluminium upright** (a solid aluminium bar fixed to the wall, with threaded holes in it);
- the **shelf flange** sticks out level from the top of the wall flange, and the shelf board rests on it.

The things on the shelf push down on the shelf flange. The bracket must carry that load without bending permanently, without letting the front of the shelf drop too far, and without pulling its screws out of the upright.

## 2. Shape and dimensions (original teaching geometry; no CAD needed)

Side view, wall on the left (not to scale):

```
          shelf board (rests on the shelf flange)
   ===============================================   <- front edge of shelf
   +------------------------------------+            ^
   |  shelf flange, length A (outside)  |  20 mm     |  shelf depth (your variant)
   +--+---------------------------------+  gap to    |
   |  |  bend: 90 deg, inside radius R = t front     v
   |  |
   |  o  upper screw hole, 25 mm below the top outside face
   |  |
   |  |  wall flange, height H = 100 mm (outside)
   |  |
   |  o  lower screw hole, 80 mm below the top outside face
   |  |
   +--+  bottom edge of the wall flange ("heel")
   ^
   wall face of the bracket, screwed against the tapped aluminium upright
```

| Feature | Value | Note |
|---|---|---|
| Strip width b (both flanges) | 50 mm | Same for every variant |
| Wall flange height H (outside) | 100 mm | Measured from the top outside face of the shelf flange to the heel |
| Shelf flange length A (outside) | shelf depth - 20 mm | The bracket stops 20 mm short of the shelf front edge |
| Thickness t | from your variant | Stock sheet: 2.0, 3.0, 4.0, 5.0 or 6.0 mm |
| Bend | 90 deg ±1 deg, inside radius R = t; drawing callout "BEND 90° ±1°, INSIDE R = t" | Inside radius typical for 5052-H32 aluminium; ±1° is a typical press-brake capability (confirm with supplier). Write the angle tolerance: without it the general tolerance would ask for a tighter angle than a press brake holds |
| Screw holes in the wall flange | 2 holes, diameter 5.5 ±0.1 mm (callout "2X Ø5.5 ±0.1"; no THRU: every hole in a sheet goes through), on the centre line of the strip | 25 mm and 80 mm below the top outside face (pitch 55 mm). Laser-cut hole size ±0.1 is typical; confirm with supplier |
| Screws | M5, property class 8.8, zinc-flake coated, with a plain washer 1.0 mm thick | One screw per hole |
| Tapped holes in the upright | M5, full thread 12 mm deep, tap drill 4.2 mm, 15 mm deep | Upright alloy from your variant |
| Base bracket material | 5052-H32 aluminium sheet | You may propose another material in Ep 07 |

## 3. Fixed inputs (the same for every variant)

| Input | Value | Source |
|---|---|---|
| Brackets per shelf | 2 (each carries half of the shelf load) | This brief |
| Where the load acts | Spread evenly over the shelf, so it acts at the middle of the shelf depth | This brief (simplification) |
| Design factor on the shelf load | 1.5 (covers uneven sharing between the 2 brackets and setting things down) | Illustrative course default |
| Gravity g | 9.81 m/s^2 | - |
| Factor of safety (FOS) gate on yield | 2.5 | Same gate as the course Preliminary Design Review (PDR) |
| Front-edge droop limit | 4.0 mm under the design load | Illustrative course default for the PDS |
| 5052-H32: yield strength Sy | 193 MPa | Typical value |
| 5052-H32: elastic modulus E | 70300 MPa | Typical value |
| M5 preferred screw lengths (SAMPLE catalogue card) | 8, 10, 12, 16, 20, 25 mm | Course list; SAMPLE - not a real product range |
| Engagement rule (class 8.8 screws) | 1D in steel, 1.5D in 6061-T6, 2D in softer alloys such as 6063-T5 (this bracket: 6061-T6 or 6063-T5 upright) | Course rule from Ep 08; published guides vary, and the screw or insert maker wins |
| Thread depth rule | thread depth >= engagement + 1 mm (the screw must not bottom out) | Ep 08 |
| Bracket hole position (laser-cut) | +/- 0.10 mm | Typical; confirm with supplier |
| Bracket hole size (laser-cut) | 5.5 +/- 0.10 mm: the stack-up (Ep 13) uses the smallest hole, 5.4 mm, because that is the worst case for fit | Typical; confirm with supplier |
| Upright hole position | +/- 0.05 mm CNC-drilled (200 parts or more); +/- 0.25 mm drilled by hand from a template (fewer than 200) | Typical / illustrative |
| K-factor for the flat pattern | 0.33 | Course value, the same as for the motor bracket in the lessons; illustrative, your supplier confirms |

All values are typical or illustrative teaching values, not datasheet values.

## 4. Pick your variant

Each variant gives the same bracket shape a different job. The variants are chosen so that the answers differ: some brackets pass every check as given, and some need a change. Finding out which, and fixing it, is the point of the exercise.

| Variant | Use | Shelf load (whole shelf, kg) | Shelf depth (mm) | Bracket thickness t (mm) | Upright alloy | Environment | Quantity (brackets) |
|---|---|---|---|---|---|---|---|
| 1 | Home-office book shelf | 5.5 | 150 | 3.0 | 6063-T5 | Indoor, dry, heated room | 50 |
| 2 | Kitchen spice shelf | 4.0 | 120 | 2.0 | 6061-T6 | Indoor, humid (kitchen or bathroom, splashes, cleaning sprays) | 2000 |
| 3 | Garage tool shelf | 12.0 | 200 | 3.0 | 6061-T6 | Indoor, dry, heated room | 150 |
| 4 | Bathroom towel shelf | 5.0 | 150 | 3.0 | 6063-T5 | Indoor, humid (kitchen or bathroom, splashes, cleaning sprays) | 5000 |
| 5 | Shop display shelf | 6.0 | 250 | 5.0 | 6061-T6 | Indoor, dry, heated room | 20000 |
| 6 | Covered seaside balcony plant shelf | 8.0 | 180 | 4.0 | 6061-T6 | Outdoor under a roof near the sea (salt air) | 500 |
| 7 | Your own numbers | see section 5 | | | | | |

Not sure which to pick? Roll a die, or pick the shelf that looks most like one you have seen. Write your variant number at the top of every worksheet.

## 5. Variant 7: your own numbers

Variant 7 is for learners who want a shelf of their own, and it is the variant to use for the mini-project in Ep 23 if you want every decision to be yours.

1. Choose each input from these ranges, so the simple models in this course stay sensible:

   | Input | Allowed range |
   |---|---|
   | Shelf load (whole shelf) | 2 to 15 kg |
   | Shelf depth | 100 to 300 mm |
   | Thickness t | 2.0, 3.0, 4.0, 5.0 or 6.0 mm |
   | Upright alloy | 6061-T6 or 6063-T5 |
   | Environment | indoor dry; indoor humid; outdoor under a roof; outdoor under a roof near the sea |
   | Quantity | 10 to 50000 brackets |

2. Write your six inputs, and one line on why you chose each, in your assumptions and decisions log.
3. Keep every fixed input in section 3 unchanged, unless you write the change and the reason in your log.
4. Work every worksheet by hand with your numbers. There is no printed answer key for variant 7, so check yourself: re-do each key result a second way (for example, check the moment balance about the heel in Ep 04), and compare your trends with the nearest course variant.
5. Optional, if you use Python: the course generator (`make_shelf_facts.py`, in the `source` folder of the course's open release) can compute your numbers so you can compare after you have done them by hand:

   `python3 make_shelf_facts.py --own <load_kg> <depth_mm> <t_mm> <upright> <environment> <quantity>`

   for example `python3 make_shelf_facts.py --own 7 180 3.0 6061-T6 outdoor_covered 400`. Environment words: `indoor_dry`, `indoor_humid`, `outdoor_covered`, `outdoor_coastal`. It reads the course K-factor from `facts_c4.json` and the notice lines from `legal_notice.txt` (keep both files in the same folder; they are in the same `source` folder), writes two separate files (`Facts_C4_shelf_own.md` and `facts_c4_shelf_own.json`) and does not change the course files.

## 6. Where you use the bracket in the course

| Episode | Your task with the shelf bracket |
|---|---|
| Ep 01 | List 3 decisions for your bracket and the phase where each gets locked |
| Ep 02 | Write a 6-line PDS (product design specification) for your variant, with requirement types and verify-by methods |
| Ep 03 | Morphological chart and Pugh matrix (bent sheet, casting or molded part), with criteria from your PDS |
| Ep 04 | Free-body diagram (FBD): load, moment at the wall, screw forces and heel force |
| Ep 05 | Bending stress and FOS on the calc-sheet template, at the bend and through the upper screw hole (net section) |
| Ep 06 | Front-edge droop; mark the stress raisers |
| Ep 07 | Material choice with a 5-criteria weighted matrix: 5052-H32 aluminium, low-carbon steel and 304 stainless steel. Indoors, steel can win on cost and stiffness; aluminium wins on weight and corrosion. Say which matters for your variant |
| Ep 08 | Screw length from the preferred lengths; engagement and bottoming check |
| Ep 09 - 12 | Drawing list, views, line types, callouts for your holes (with their size tolerance), threads and bend (with its angle tolerance) |
| Ep 13 | Worst-case stack-up: bracket holes vs the tapped upright, at the smallest hole (5.4 mm) |
| Ep 14 | Choose datums and explain why |
| Ep 15 | Convert key dimensions and loads to inch and lbf; fix 5 number-format errors |
| Ep 16 | Redline the shelf-bracket "errors" drawing |
| Ep 17 | Flat-pattern length with the course K-factor (0.33); hole-to-bend check |
| Ep 19 | Casting sketch: parting line, draft, fillets, machining stock; sand or die casting for your quantity |
| Ep 20 | DFA (design for assembly) audit of your bracket kit; 3 review actions |
| Ep 21 | Service check |
| Ep 22 | ECR (engineering change request) and ECO (engineering change order) for a field problem |
| Ep 23 | Your design package, with every number traced back to your variant |

## 7. Rules for your answers

- Every number in your worksheets must come from your variant and this brief. Write the source next to each input.
- Units on every line; SI units (N, mm, MPa), with inch and lbf only where Ep 15 asks for them.
- The models are simplified on purpose. Write each simplification you use in your assumptions log (the worksheets tell you which ones).
- A FAIL is not a mistake. It is a finding: write what you would change and re-check it.

---

<!-- PDF footer: print the notice lines below in the footer of every page of the PDF. -->
Educational material - verify with current standards and your supplier.  
© 2026 Vijayakumar Yeddula · CC BY 4.0 · Mechanical Design Basics (C4)  
Educational example - not for production, manufacture or legal use.  
Provided "as is" for education, without warranty; not engineering advice; the author accepts no liability for any use.
