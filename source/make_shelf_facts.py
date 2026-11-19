"""C4 Mechanical Design Basics - SHELF BRACKET facts generator (learner exercises).
Computes every per-variant answer the shelf-bracket worksheets need and writes, from ONE spec, three files that
always agree: Facts_C4_shelf.md (tables for people), facts_c4_shelf.json (named values for scripts and answer keys,
same structure as facts_c4.json: key -> value, unit, formula, spoken, plus printed = the exact string printed in the
Markdown; value is rounded to the printed decimals and stored as an int when whole) and shelf_variants.csv (one row per variant).
Deterministic: the only random choice (which number-format errors appear in the Ep 15 worksheet) uses a fixed seed.
Prints ONE line: PASS / n self-check failures.

The bend K-factor is NOT typed here: it is read from the course facts file (key K_bend in facts_c4.json), looked
for next to this script, then in ../7_Open_Release/source/, or at the path in the environment variable C4_FACTS_JSON.

usage: python3 make_shelf_facts.py                       (6 course variants)
       python3 make_shelf_facts.py --own load_kg depth t upright env qty
         e.g.  python3 make_shelf_facts.py --own 7 180 3.0 6061-T6 indoor_dry 400
         (variant 7: your own numbers; writes Facts_C4_shelf_own.md and facts_c4_shelf_own.json in the current
          folder, does not touch the course files)

JSON keys: shelf_<name> (fixed inputs), V<n>_<name> (variant inputs), V<n>_EpNN_<name> (per-episode answers).
Keys contain letters, digits and _ only, so that fill_facts.py placeholders [F: key] work.

Illustrative values for education. Simplified teaching models - not a design method for real
wall shelves. Every assumption is stated in ASSUMPTIONS and printed into the Facts file."""
import sys
import os
import re
import math
import csv
import json
import random

SEED = 4104          # fixed seed: Ep 15 number-format error selection only
G = 9.81             # m/s^2
HERE = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------- course facts (shared values are read, not typed)
def load_course_facts():
    cands = [os.environ.get('C4_FACTS_JSON'), os.path.join(HERE, 'facts_c4.json'),
             os.path.join(HERE, '..', '7_Open_Release', 'source', 'facts_c4.json')]
    for p in cands:
        if p and os.path.isfile(p):
            with open(p, encoding='utf-8') as f:
                return os.path.normpath(p), json.load(f)
    sys.exit('FAIL: facts_c4.json not found (needed for K_bend). Put it next to this script or set C4_FACTS_JSON.')


COURSE_PATH, COURSE = load_course_facts()

# ---------------------------------------------------------------- fixed inputs (same for every variant)
FIXED = dict(
    b=50.0,            # bracket width, both flanges, mm
    H=100.0,           # wall-flange outside height, mm (top outside face to bottom edge = heel)
    front_gap=20.0,    # shelf flange stops this far short of the shelf front edge, mm
    hole1=25.0,        # upper screw hole centre from top outside face, mm
    hole2=80.0,        # lower screw hole centre from top outside face, mm
    n_brackets=2,      # brackets per shelf
    k_design=1.5,      # design factor on the shelf load (course default, illustrative)
    gate=2.5,          # FOS gate on yield (same gate as the course PDR)
    droop_limit=4.0,   # PDS: front-edge droop under design load, mm (course default, illustrative)
    d=5.0,             # screw nominal diameter, mm (M5 coarse, class 8.8, zinc-flake coated)
    clear=5.5,         # clearance hole diameter in the bracket (nominal), mm
    clear_tol=0.10,    # +/- mm, clearance hole size tolerance (laser-cut, typical): callout 2X DIA 5.5 +/-0.1 (no THRU on sheet metal, Ep 12)
    bend_tol=1.0,      # +/- deg, bend angle tolerance (typical press-brake capability): BEND 90 deg +/-1 deg
    washer=1.0,        # plain washer thickness, mm
    washer_od=10.0,    # mm plain washer outside diameter, ISO 7089 size 5 (d2 = 10 mm)
    washer_id=5.3,     # mm plain washer hole diameter, ISO 7089 size 5 (d1 = 5.3 mm min)
    tap_depth=12.0,    # full-thread depth of the tapped hole in the upright, mm
    drill_depth=15.0,  # tap-drill depth, mm
    tap_drill=4.2,     # tap drill diameter, mm
    bottom_gap=1.0,    # thread depth must be >= engagement + this, mm (course rule)
    As=14.2,           # M5 tensile stress area, mm^2 (same value as Facts_C4)
    proof=580.0,       # class 8.8 proof strength, typical, MPa (same as Facts_C4)
    preload=4000.0,    # illustrative preload per M5 screw, N (same as Facts_C4)
    K_nut=0.2,         # illustrative nut factor (same as Facts_C4)
    R_over_t=1.0,      # inside bend radius = t (illustrative course value for 5052-H32 and low-carbon steel; the supplier's value wins)
    K_factor=float(COURSE['K_bend']['value']),   # course bend K-factor, read from facts_c4.json (course decision)
    Sy_min=float(COURSE['Sy_min']['value']),     # specified minimum yield of 5052-H32 sheet, read from facts_c4.json (R1: compulsory gate step)
    tol_laser=0.10,    # +/- mm, laser-cut hole position, features in one flat (as Facts_C4)
    tol_cnc=0.05,      # +/- mm, CNC-drilled tapped hole position (as Facts_C4)
    tol_hand=0.25,     # +/- mm, hole drilled by hand from a template (illustrative)
    hand_qty=200,      # below this quantity the upright holes are drilled by hand from a template
    P_M5=0.8,          # mm M5 coarse pitch (ISO 261)
    tol_gen_m=float(COURSE['tol_gen_m']['value']),   # +/- mm ISO 2768-m, over 6 up to 30 mm, read from facts_c4.json
    zinc_um=float(COURSE['zinc_um']['value']), zinc_um_max=float(COURSE['zinc_um_max']['value']),   # um zinc electroplate min / max (course practice, facts_c4.json)
    cr_t_max=3.0,      # mm thickest low-carbon steel bought as cold-rolled sheet; thicker as hot-rolled, pickled and oiled (course assumption; the stockist confirms)
    powder_um=60.0,    # um minimum polyester powder coat over zinc, humid or outdoor (typical; the coater confirms)
    powder_um_max=120.0,   # um maximum powder film (typical upper limit for one coat; keeps outside sizes bounded; the coater confirms)
    powder_ral='9005',     # RAL colour: jet black (course decision D103: black semi-matt, a common stock powder)
    powder_gloss=30, powder_gloss_tol=5, powder_gloss_angle=60,   # GU at 60 deg (ISO 2813): semi-matt 30 +/- 5 (course decision D103; the powder maker's data sheet states it)
    a1011_t_max=6.0,   # mm upper thickness of ASTM A1011 sheet (0.230 in); thicker is A1018 or plate
    htb_tight_band=0.5,    # mm hole-to-bend is "tight" when the largest passing inside R is below R + this (course rule, D106)
    sup_die_factor=8.0,    # SAMPLE supplier reply (D106): air-bend die opening = 8 t
    sup_R_ratio=0.16,      # SAMPLE: inside R in air bending is about 0.16 x die opening (typical rule; the supplier's tooling wins); rounded up to 0.5
    lig_factor=1.5,        # lower-hole ligament to the flange end >= 1.5 t (typical; the supplier's guide wins; D106)
    sems_std='ISO 10644',  # screw and captive plain washer assembly (hexagon socket head screw + plain washer, washer = shelf_washer_od / _id); D108
    upright_part_number='SHB-200',   # shelf upright: part number so that it can carry a revision (D108)
    part_next_dash=8,      # next free dash number for a new part number (-1..-6 course variants, -7 the learner's own; never reused)
)
# Finish per (material, environment): ONE drawing callout each (course decisions D101, D103 for the six variants).
# Anodize classes ISO 7599 (minimum film thickness = class number in um): AA10 indoor, AA15 outdoor, AA25 salt air (typical guidance; the finisher wins).
ANODIZE_CLASS = dict(indoor_dry=None, indoor_humid=10, outdoor_covered=15, outdoor_coastal=25)   # coastal: AA25, roofed salt air is never rain-washed
# Ep 22 change raised against Rev A (course decision D106): these variants get a given field problem / supplier reply;
# every other variant raises the change for the checks still open at Rev A
ECO_KIND = {2: 'captive_washer', 5: 'supplier_R', 6: 'galvanic'}
# values this file shares with facts_c4.json: checked on every run (drift = self-check failure, never silently changed)
SHARED = dict(Sy=('Sy', None), E=('E', None), gate=('FOS_gate', None), preload=('preload_M5', None), K_nut=('K', None),
              washer=('washer_M5', None))

# Preferred M5 screw lengths on the course SAMPLE catalogue card (course decision; original short list, not a standard table)
SCREW_LENGTHS = [8, 10, 12, 16, 20, 25]
THICKNESSES = [2.0, 3.0, 4.0, 5.0, 6.0]   # stock sheet thicknesses offered in the brief, mm

def material_callout(mat, t, fx=None):
    """Drawing title-block field 7: grade + condition + form + thickness + the standard it is bought to (course decision D101)."""
    fx = fx or FIXED
    if mat == BASE_MAT:
        return f"5052-H32 ALUMINIUM SHEET PER ASTM B209/B209M, t = {t:g}"
    if mat == STEEL:
        if t <= fx['cr_t_max'] + 1e-9:
            return f"COLD-ROLLED LOW-CARBON STEEL SHEET PER ASTM A1008/A1008M SS GRADE 30 [205], t = {t:g}"
        return f"HOT-ROLLED LOW-CARBON STEEL SHEET, PICKLED AND OILED, PER ASTM A1011/A1011M SS GRADE 30 [205], t = {t:g}"
    return f"304 STAINLESS STEEL SHEET PER ASTM A240/A240M, 2B FINISH, t = {t:g}"


def finish_callout(mat, env, fx=None):
    """Drawing title-block field 8: ONE finish, no alternatives (course decision D101)."""
    fx = fx or FIXED
    zinc = f"ZINC PLATE AFTER FORMING, {fx['zinc_um']:.0f}-{fx['zinc_um_max']:.0f} {chr(181)}m, Cr(VI)-FREE PASSIVATION (ISO 19598)"
    if mat == BASE_MAT:
        aa = ANODIZE_CLASS[env]
        return 'NONE (BARE; DEBURR)' if aa is None else f"CLEAR ANODIZE AFTER FORMING, ISO 7599 AA{aa} ({aa} {chr(181)}m MIN), SEALED"
    if mat == STEEL:
        if env == 'indoor_dry':
            return zinc
        if env == 'outdoor_coastal':
            return 'NOT RELEASED: LOW-CARBON STEEL FAILS THE CORROSION GATE HERE'
        zp = zinc.replace('Cr(VI)-FREE PASSIVATION (ISO 19598)', 'Cr(VI)-FREE PASSIVATION SUITABLE FOR POWDER COATING, NO SEALER, NO TOPCOAT (ISO 19598)')
        return zp + (f", THEN POLYESTER POWDER COAT, RAL {fx['powder_ral']}, GLOSS {fx['powder_gloss']} {chr(177)}{fx['powder_gloss_tol']} GU AT {fx['powder_gloss_angle']}{chr(176)}, "
                     f"{fx['powder_um']:.0f}-{fx['powder_um_max']:.0f} {chr(181)}m; MASK THE 2 HOLES")
    return 'PASSIVATE (ASTM A967)'


# Typical material values (illustrative teaching values, not a datasheet). cost = relative part cost, 5052-H32 = 1.0
# (illustrative). rho = density, g/cm^3 (typical). Ep 07 compares these three only (course decision: no plastic).
MATERIALS = {
    '5052-H32 aluminium': dict(Sy=193.0, E=70300.0, cost=1.0, form=5, rho=2.68, key='al'),
    'Low-carbon steel, cold-rolled': dict(Sy=210.0, E=200000.0, cost=0.7, form=5, rho=7.85, key='steel'),
    '304 stainless steel': dict(Sy=215.0, E=193000.0, cost=4.0, form=3, rho=7.90, key='ss'),
}
BASE_MAT = '5052-H32 aluminium'
STEEL = 'Low-carbon steel, cold-rolled'

# Upright alloy -> minimum engagement as a multiple of D (class 8.8 screws). Course rule, one wording everywhere (wave 4):
# 1D in steel, 1.5D in 6061-T6, 2D in softer alloys such as 6063-T5. Published guides vary; the screw or insert maker wins.
UPRIGHTS = {'6061-T6': 1.5, '6063-T5': 2.0}
ENG_STEEL = 1.0
ENG_RULE = (f"{ENG_STEEL:.0f}D in steel, {UPRIGHTS['6061-T6']:.1f}D in 6061-T6, {UPRIGHTS['6063-T5']:.0f}D in softer alloys such as 6063-T5")
CKPT_FOS = 2.50    # shelf checkpoint (Ep 05): a FOS exactly on the gate

# Environment -> (corrosion score 1 poor .. 5 excellent, finish that score assumes, finish cost added to the
# relative part cost - illustrative) per material.
ENVS = {
    'indoor_dry': ('Indoor, dry, heated room',
                   {'5052-H32 aluminium': (5, 'none needed (clear anodize optional for looks)', 0.0),
                    'Low-carbon steel, cold-rolled': (4, 'zinc plating or powder coat', 0.1),
                    '304 stainless steel': (5, 'passivated, no coating', 0.1)}),
    'indoor_humid': ('Indoor, humid (kitchen or bathroom, splashes, cleaning sprays)',
                     {'5052-H32 aluminium': (4, 'anodize', 0.2),
                      'Low-carbon steel, cold-rolled': (2, 'zinc plating + powder coat', 0.4),
                      '304 stainless steel': (4, 'passivated; isolating washer at the aluminium upright', 0.1)}),
    'outdoor_covered': ('Outdoor under a roof, rain splash, daily temperature swings',
                        {'5052-H32 aluminium': (4, 'anodize or powder coat', 0.2),
                         'Low-carbon steel, cold-rolled': (2, 'zinc plating + powder coat', 0.4),
                         '304 stainless steel': (3, 'passivated; isolate from the aluminium upright (galvanic pair when wet)', 0.1)}),
    'outdoor_coastal': ('Outdoor under a roof near the sea (salt air)',
                        {'5052-H32 aluminium': (3, 'anodize + seal, or powder coat', 0.3),
                         'Low-carbon steel, cold-rolled': (1, 'not recommended even when coated', 0.4),
                         '304 stainless steel': (2, 'surface staining likely; isolate from the aluminium upright', 0.1)}),
}
WEIGHTS = dict(strength=0.25, stiffness=0.25, cost=0.20, process=0.15, corrosion=0.15)
CRIT = ['strength', 'stiffness', 'cost', 'process fit', 'corrosion']
# Ep 07 score rules (score, bound): the first bound met gives the score, otherwise 1. Strength: FOS >= bound;
# stiffness: droop <= bound; cost: relative part cost incl. finish <= bound. Strength and stiffness bounds follow the
# FOS gate and the droop limit; the cost bounds are illustrative course values.
SCORE_STR = [(5, 2 * FIXED['gate']), (4, FIXED['gate']), (2, 1.5)]
SCORE_STF = [(5, 0.5 * FIXED['droop_limit']), (4, FIXED['droop_limit']), (2, 1.5 * FIXED['droop_limit'])]
SCORE_COST = [(5, 0.8), (4, 1.2), (2, 2.5)]
MAT_SOURCE = 'input; source: typical, see Material_Matrix_SAMPLE'


def score(x, rules, higher_is_better):
    for s, bound in rules:
        if (x >= bound if higher_is_better else x <= bound):
            return s
    return 1

# Ep 03 / Ep 19 concept and casting costs (ILLUSTRATIVE prices, currency units, not quotes)
CONCEPTS = {'Bent sheet metal (laser + press brake)': (300.0, 4.0, 'sheet'),
            'Sand casting + machining': (1500.0, 9.0, 'sand'),
            'Die casting + light machining': (18000.0, 2.2, 'die'),
            'Injection-molded glass-filled nylon (needs ribs)': (14000.0, 1.2, 'molded')}

# ---------------------------------------------------------------- the 6 course variants
VARIANTS = [
    dict(v=1, name='Home-office book shelf', load_kg=5.5, depth=150.0, t=3.0, upright='6063-T5', env='indoor_dry', qty=50),
    dict(v=2, name='Kitchen spice shelf', load_kg=4.0, depth=120.0, t=2.0, upright='6061-T6', env='indoor_humid', qty=2000),
    dict(v=3, name='Garage tool shelf', load_kg=12.0, depth=200.0, t=3.0, upright='6061-T6', env='indoor_dry', qty=150),
    dict(v=4, name='Bathroom towel shelf', load_kg=5.0, depth=150.0, t=3.0, upright='6063-T5', env='indoor_humid', qty=5000),
    dict(v=5, name='Shop display shelf', load_kg=6.0, depth=250.0, t=5.0, upright='6061-T6', env='indoor_dry', qty=20000),
    dict(v=6, name='Covered seaside balcony plant shelf', load_kg=8.0, depth=180.0, t=4.0, upright='6061-T6', env='outdoor_coastal', qty=500),
]

ASSUMPTIONS = [
    'Shelf load is spread evenly over the shelf; each of the 2 brackets carries half, so the load per bracket acts at the middle of the shelf depth (e = depth / 2), measured from the wall face.',
    f"Design load F = load per bracket x {FIXED['k_design']} (illustrative design factor for uneven sharing between brackets and for setting items down; course default accepted by the course team).",
    'Lever arm measured from the wall face (outside face of the wall flange), not from the bend: slightly conservative and easy to measure.',
    'Both flanges carry the same moment M = F x e at the bend (same idea as the course bracket). Stress is checked at the bend: sigma = 6M / (b t^2).',
    f"Net section (Ep 05, section 2): the section through the upper screw hole, the hole nearest the bend ({FIXED['hole1']:.0f} mm below the top outside face; in a redesign, the moved hole). Between the bend and the upper screw no other force acts on the wall flange (worst case: it can lift off the upright there, as in the stiffness model), so this section carries the full moment M = F e (lever arm from the wall face, as above). The clearance hole removes {FIXED['clear']:.1f} mm of the width: b_net = b - {FIXED['clear']:.1f} mm and sigma_net = 6M / (b_net t^2), the nominal net-section bending stress (nominal hole size; the largest hole, {FIXED['clear'] + FIXED['clear_tol']:.1f} mm, raises sigma_net by under 0.3%). FOS_net = Sy / sigma_net is checked against the same gate. Section 2 is always the more highly stressed one (sigma_net / sigma = b / b_net), so the strength verdict is set by the lower FOS; the redesign and the thinnest-t rows use both sections. The Ep 07 strength score uses the section-1 FOS (the matrix compares materials, and the ratio between the sections is the same for each).",
    'Stress raisers at the bend and holes (including the stress peak at the edge of the screw hole) are NOT in the hand number (pictures only in Ep 06), so the FOS gate of 2.5 must cover them.',
    'Stiffness: shelf-flange rotation at the load = M e / (2 E I) (cantilever with an end load: the moment falls from M to 0, so the average is M/2); wall-flange rotation = M Lv / (E I) over the free length Lv from the top outside face to the upper screw (worst case: the flange can lift off between the bend and the screw).',
    f"Front-edge droop = (sum of rotations) x shelf depth, checked against the illustrative PDS limit of {FIXED['droop_limit']} mm (course default accepted by the course team). The shelf board is treated as rigid; this slightly overestimates the droop (on the safe side).",
    'Screw forces: the wall flange tips about its bottom edge (heel). Screw tension from the moment T_i = M y_i / (y1^2 + y2^2), y from the heel; the heel force C = T1 + T2. The vertical load F is shared as shear by the 2 screws (friction ignored). Shear of the M5 screw is not a concern at these loads and is not checked further. Which way this errs: tipping about the heel is the least conservative pivot (longest lever arms, lowest screw tension); if the flange flexes (prying), the contact moves inward and the screw tension can rise several times. Here T1 stays below a tenth of the preload for every course variant (Ep 08 row T1 / preload; self-checked), so the conclusion "the joint stays closed" holds. The weight of the bracket itself is neglected: slightly non-conservative, and small next to F.',
    f'Engagement rule (class 8.8 screws, course rule): {ENG_RULE}. Published guides vary; the screw or insert maker wins. Thread depth must be >= engagement + 1 mm so the screw cannot bottom out.',
    'Screw length = grip (t) + washer (1.0 mm) + engagement; pick the shortest preferred length (8, 10, 12, 16, 20, 25 mm, SAMPLE card) that gives enough engagement without bottoming.',
    f"Stack-up: one direction only (along the line of the 2 holes), worst case. Pitch error of a part = 2 x the position tolerance of one hole. Both screws fit when the total pitch mismatch <= smallest clearance hole - screw diameter. The holes are {chr(216)}{FIXED['clear']:.1f} {chr(177)}{FIXED['clear_tol']:.1f}, so the stack uses the smallest hole, {FIXED['clear'] - FIXED['clear_tol']:.1f} mm (the worst case for fit), not the nominal size.",
    'Upright holes: CNC-drilled (+/-0.05 mm) at 200 parts or more; drilled by hand from a template (+/-0.25 mm, illustrative) below 200. Bracket holes laser-cut (+/-0.10 mm).',
    f"Flat pattern: 90 deg bend, inside radius R = t, course K-factor {FIXED['K_factor']:.2f} (key K_bend in facts_c4.json, the same value as the motor bracket; illustrative, the supplier confirms). Flat length = (A - t - R) + (H - t - R) + pi/2 x (R + K t).",
    'Hole-to-bend rule (strict reading, as in Facts_C4): hole edge from the outside face >= (t + R) + 2.5t + R.',
    f"Bend callout: BEND 90{chr(176)} {chr(177)}{FIXED['bend_tol']:.0f}{chr(176)}, INSIDE R = t (the same pattern as the course bracket drawing, note 2). The angle tolerance is written on purpose: without it the general tolerance (ISO 2768-m) would set a tighter angle on these leg lengths than a press brake holds (typical, confirm with the supplier).",
    'Bracket mass (Ep 07) = flat length x b x t x density; the 2 small screw holes are ignored (they change the mass by less than 1%).',
    'Material, density, cost and casting prices are typical or illustrative teaching values, not datasheet or quote values.',
]


# ---------------------------------------------------------------- engineering
def mech(F, e, depth, t, mat, Lv=None, fx=FIXED):
    """Stress, FOS, rotations and droop for one thickness and material (Lv = upper hole from top outside face)."""
    m = MATERIALS[mat]
    b = fx['b']
    M = F * e
    I = b * t ** 3 / 12
    sigma = 6 * M / (b * t ** 2)
    fos = m['Sy'] / sigma
    # section 2: through the upper screw hole (the hole nearest the bend), same M, width reduced by the clearance hole
    b_net = b - fx['clear']
    sigma_net = 6 * M / (b_net * t ** 2)
    fos_net = m['Sy'] / sigma_net
    Lv = fx['hole1'] if Lv is None else Lv
    th_shelf = M * e / (2 * m['E'] * I)
    th_wall = M * Lv / (m['E'] * I)
    th = th_shelf + th_wall
    droop = th * depth
    return dict(M=M, I=I, sigma=sigma, FOS=fos, th_shelf=th_shelf, th_wall=th_wall, th=th, tilt_deg=math.degrees(th),
                droop=droop, strength='PASS' if fos >= fx['gate'] else 'FAIL',
                b_net=b_net, sigma_net=sigma_net, FOS_net=fos_net, strength_net='PASS' if fos_net >= fx['gate'] else 'FAIL',
                strength_both='PASS' if min(fos, fos_net) >= fx['gate'] else 'FAIL',
                stiffness='PASS' if droop <= fx['droop_limit'] else 'FAIL')


def hole_to_bend(t, hole1=None, fx=FIXED):
    R = t * fx['R_over_t']
    req = (t + R) + 2.5 * t + R
    edge = (fx['hole1'] if hole1 is None else hole1) - fx['clear'] / 2
    return req, edge, 'PASS' if edge >= req else 'FAIL'


def screw_choice(t, upright, fx=FIXED):
    need = UPRIGHTS[upright] * fx['d']
    max_eng = fx['tap_depth'] - fx['bottom_gap']
    for L in SCREW_LENGTHS:
        eng = L - t - fx['washer']
        if eng >= need and eng <= max_eng:
            return dict(L=L, eng=eng, engD=eng / fx['d'], need=need, max_eng=max_eng, status='PASS', fix='-')
    # no preferred length fits: smallest length giving enough engagement, and the thread depth it needs
    L = next(L for L in SCREW_LENGTHS if L - t - fx['washer'] >= need)
    eng = L - t - fx['washer']
    depth_needed = eng + fx['bottom_gap']
    return dict(L=L, eng=eng, engD=eng / fx['d'], need=need, max_eng=max_eng, status='FAIL',
                fix=f"no preferred length fits a {fx['tap_depth']:.0f} mm thread: use M5 x {L} and tap {depth_needed:.0f} mm deep "
                    f"(drill {depth_needed + 3:.0f} mm), if the upright is thick enough")


def redesign(F, e, depth, upright, fx=FIXED):
    """Thinnest stock thickness that passes strength (bend and net section), stiffness and hole-to-bend. Where the holes are too close
    to the bend they move down (pitch kept at 55 mm, position rounded up to 0.5 mm) and the stiffness is re-checked
    with the longer free length."""
    pitch = fx['hole2'] - fx['hole1']
    for t in THICKNESSES:
        req = hole_to_bend(t)[0]
        h1 = max(fx['hole1'], math.ceil((req + fx['clear'] / 2) * 2) / 2)
        r = mech(F, e, depth, t, BASE_MAT, Lv=h1)
        if r['strength_both'] == 'PASS' and r['stiffness'] == 'PASS':
            y1, y2 = fx['H'] - h1, fx['H'] - h1 - pitch
            T1 = F * e * y1 / (y1 ** 2 + y2 ** 2)
            return dict(t=t, hole1=h1, hole2=h1 + pitch, moved=h1 > fx['hole1'], sigma=r['sigma'], FOS=r['FOS'], FOS_net=r['FOS_net'],
                        droop=r['droop'], T1=T1, screw=screw_choice(t, upright))
    return None


def compute(v, fx=FIXED):
    o = dict(v)
    W_total = v['load_kg'] * G
    W = W_total / fx['n_brackets']
    F = W * fx['k_design']
    e = v['depth'] / 2
    A = v['depth'] - fx['front_gap']
    o.update(W_total=W_total, W=W, F=F, e=e, A=A)
    # Ep 04 reactions (screw forces about the heel)
    y1 = fx['H'] - fx['hole1']
    y2 = fx['H'] - fx['hole2']
    M = F * e
    T1 = M * y1 / (y1 ** 2 + y2 ** 2)
    T2 = M * y2 / (y1 ** 2 + y2 ** 2)
    o.update(M=M, y1=y1, y2=y2, T1=T1, T2=T2, C=T1 + T2, V_each=F / 2, R_vert=F)
    # Ep 05 / 06 with the base material and the variant thickness
    o['base'] = mech(F, e, v['depth'], v['t'], BASE_MAT)
    o['rd'] = redesign(F, e, v['depth'], v['upright'])
    o['t_min'] = o['rd']['t'] if o['rd'] else None
    o['t_strength'] = next((t for t in THICKNESSES if mech(F, e, v['depth'], t, BASE_MAT)['strength_both'] == 'PASS'), None)
    # Ep 05 compulsory minimum-yield gate step (R1): the lower FOS (section 2) re-done on the specified minimum yield
    o['FOS_min'] = fx['Sy_min'] / max(o['base']['sigma'], o['base']['sigma_net'])
    o['strength_min'] = 'PASS' if o['FOS_min'] >= fx['gate'] else 'FAIL'
    o['t_strength_min'] = next((t for t in THICKNESSES
                                if fx['Sy_min'] / mech(F, e, v['depth'], t, BASE_MAT)['sigma_net'] >= fx['gate']), None)
    # Ep 17 flat pattern and DFM (needed before Ep 07 for the mass)
    R = v['t'] * fx['R_over_t']
    BA = math.pi / 2 * (R + fx['K_factor'] * v['t'])
    flat = (A - v['t'] - R) + (fx['H'] - v['t'] - R) + BA
    req, edge, htb = hole_to_bend(v['t'])
    o.update(R=R, BA=BA, flat=flat, BD=A + fx['H'] - flat, htb_req=req, htb_edge=edge, htb=htb,
             min_flange=4 * v['t'], flange_ok='PASS' if min(A, fx['H']) >= 4 * v['t'] else 'FAIL')
    # Ep 07 material matrix at the variant thickness
    env_name, corr = ENVS[v['env']][0], ENVS[v['env']][1]
    rows = []
    for mat, mp in MATERIALS.items():
        r = mech(F, e, v['depth'], v['t'], mat)
        s_str = score(r['FOS'], SCORE_STR, True)
        s_stf = score(r['droop'], SCORE_STF, False)
        cost = mp['cost'] + corr[mat][2]
        s_cost = score(cost, SCORE_COST, False)
        s_proc = mp['form']
        s_corr = corr[mat][0]
        total = (WEIGHTS['strength'] * s_str + WEIGHTS['stiffness'] * s_stf + WEIGHTS['cost'] * s_cost
                 + WEIGHTS['process'] * s_proc + WEIGHTS['corrosion'] * s_corr)
        mass = flat * fx['b'] * v['t'] * mp['rho'] / 1000.0      # mm^3 -> cm^3, x g/cm^3 = g
        rows.append(dict(mat=mat, key=mp['key'], cost=cost, ok=s_corr > 1, FOS=r['FOS'], droop=r['droop'],
                         s=(s_str, s_stf, s_cost, s_proc, s_corr), total=total, finish=corr[mat][1], mass=mass))
    o['env_name'] = env_name
    o['mat_rows'] = rows
    o['mat'] = {r['key']: r for r in rows}
    o['mat_best'] = max((r for r in rows if r['ok']), key=lambda r: (round(r['total'], 6), -r['cost']))
    o['mat_note'] = ('meets both checks at this t' if (o['mat_best']['FOS'] >= fx['gate'] and o['mat_best']['droop'] <= fx['droop_limit'])
                     else 'still fails a check at this t: thicker stock or a formed rib needed')
    o['mat_why'] = mat_why(o)
    # Ep 08 screws
    o['screw'] = screw_choice(v['t'], v['upright'])
    o['pre_ratio'] = fx['preload'] / (fx['proof'] * fx['As'])
    o['torque'] = fx['K_nut'] * fx['preload'] * fx['d'] / 1000
    o['T1_over_pre'] = T1 / fx['preload']
    # Ep 12 callouts
    sc = o['screw']
    tap = fx['tap_depth'] if sc['status'] == 'PASS' else sc['eng'] + fx['bottom_gap']
    o['callout_hole_iso'] = f"2X {chr(216)}{fx['clear']:.1f} {chr(177)}{fx['clear_tol']:.1f}"   # no THRU: every hole in a sheet goes through (Ep 12 S12; C4-DWG-001, C4-DWG-009)
    o['callout_thread_iso'] = f"2X M5-6H, depth {tap:.0f} / drill {fx['tap_drill']:.1f}, depth {tap + 3:.0f}"
    o['callout_thread_asme'] = (f"2X M5 X {fx['P_M5']:.1f} - 6H {chr(0x2913)} {tap:.0f} / {chr(216)}{fx['tap_drill']:.1f} {chr(0x2913)} {tap + 3:.0f}")
    o['material_callout'] = material_callout(o['mat_best']['mat'], v['t'], fx)
    o['finish_callout'] = finish_callout(o['mat_best']['mat'], v['env'], fx)
    o['callout_bend'] = f"BEND 90{chr(176)} {chr(177)}{fx['bend_tol']:.0f}{chr(176)}, INSIDE R{v['t'] * fx['R_over_t']:.0f} (= t)"
    # Ep 13 stack
    hand = v['qty'] < fx['hand_qty']
    tol_u = fx['tol_hand'] if hand else fx['tol_cnc']
    mismatch = 2 * fx['tol_laser'] + 2 * tol_u
    hole_min = fx['clear'] - fx['clear_tol']          # stack at the smallest hole
    allow = hole_min - fx['d']
    o.update(upright_process='hand-drilled from a template' if hand else 'CNC-drilled', tol_u=tol_u, mismatch=mismatch,
             allow=allow, stack_margin=allow - mismatch, stack='PASS' if mismatch <= allow + 1e-9 else 'FAIL',
             hole_min=hole_min, hole_needed=fx['d'] + mismatch, hole_nominal_needed=fx['d'] + mismatch + fx['clear_tol'])
    # drawn hole after the Ep 13 fix (as the Ep 20 ECR writes it); no THRU on a sheet-metal hole (Ep 12)
    hd = fx['clear'] if o['stack'] == 'PASS' else math.ceil(o['hole_nominal_needed'] * 10 - 1e-9) / 10
    o['hole_callout_fix'] = f"2X {chr(216)}{hd:.1f} {chr(177)}{fx['clear_tol']:.1f}"
    o['bend_line'] = (fx['H'] - v['t'] - R) + BA / 2
    o['htb_shortfall'] = req - edge if htb == 'FAIL' else None
    o['upper_swing'] = fx['hole1'] - v['t']
    # Ep 03 / 19 costs (illustrative)
    o['concept_cost'] = {k: (tool + v['qty'] * pc) / v['qty'] for k, (tool, pc, _) in CONCEPTS.items()}
    o['concept_best'] = min(o['concept_cost'], key=o['concept_cost'].get)
    sand, die = CONCEPTS['Sand casting + machining'], CONCEPTS['Die casting + light machining']
    o['cast_breakeven'] = (die[0] - sand[0]) / (sand[1] - die[1])
    o['cast_choice'] = 'die casting' if v['qty'] > o['cast_breakeven'] else 'sand casting'
    # Ep 15 conversions
    o['inch'] = dict(depth=v['depth'] / 25.4, t=v['t'] / 25.4, b=fx['b'] / 25.4, H=fx['H'] / 25.4, A=A / 25.4,
                     F_lbf=F / 4.4482216152605, load_lb=v['load_kg'] * 2.2046226218, M_lbfin=M / 4.4482216152605 / 25.4,
                     sigma_ksi=o['base']['sigma'] / 6.894757293168, droop=o['base']['droop'] / 25.4,
                     torque_lbfin=o['torque'] / 4.4482216152605 / 0.0254)
    o['format_errors'] = format_errors(o)
    o['fails'] = fails(o) or 'none'
    o['ecr'] = ecr(o)
    o['rel'] = released(o, v, fx)
    o['revA'] = rev_a(o, v, fx)
    o['ep22'] = ep22_d109(o, v, fx)
    return o


def mat_why(o):
    """One worksheet sentence per variant: who wins the matrix and on which criteria."""
    al, st = o['mat']['al'], o['mat']['steel']
    st_up = [c for c, a, s in zip(CRIT, al['s'], st['s']) if s > a]
    al_up = [c for c, a, s in zip(CRIT, al['s'], st['s']) if a > s]
    best = o['mat_best']
    out = (f"{best['mat']} wins ({best['total']:.2f}). Steel vs aluminium: steel scores higher on "
           f"{', '.join(st_up) or 'nothing'}; aluminium scores higher on {', '.join(al_up) or 'nothing'}; "
           f"aluminium is lighter ({al['mass']:.0f} g vs {st['mass']:.0f} g per bracket).")
    if not st['ok']:
        out += ' Steel is out on the corrosion gate in this environment.'
    two = sorted((r for r in o['mat_rows'] if r['ok']), key=lambda r: -r['total'])[:2]
    if len(two) == 2 and two[0]['total'] - two[1]['total'] <= 0.05 * two[0]['total']:
        out += (f" Close call: {two[1]['mat']} ({two[1]['total']:.2f}) is within 5%, so treat it as a tie and decide"
                " on weight, corrosion margin and supplier.")
    return out


def released(o, v, fx=FIXED):
    """Course decision D105: Parts 2 and 3 use the RELEASED geometry of Part 1: thickness = Ep 06 redesign t, holes as
    placed by the Ep 06 redesign (moved down for V3 and V5). Material = the Ep 07 choice. None if no stock t passes."""
    rd = o['rd']
    if not rd:
        return None
    t, h1, h2 = rd['t'], rd['hole1'], rd['hole2']
    R = t * fx['R_over_t']
    BA = math.pi / 2 * (R + fx['K_factor'] * t)
    flat = (o['A'] - t - R) + (fx['H'] - t - R) + BA
    req, edge, htb = hole_to_bend(t, h1, fx)
    mat = o['mat_best']['mat']
    sc = screw_choice(t, v['upright'], fx)
    tap = fx['tap_depth'] if sc['status'] == 'PASS' else sc['eng'] + fx['bottom_gap']
    r = dict(t=t, hole1=h1, hole2=h2, moved='yes' if rd['moved'] else 'no', R=R, BA=BA, flat=flat, BD=o['A'] + fx['H'] - flat,
             bend_line=(fx['H'] - t - R) + BA / 2, htb_req=req, htb_edge=edge, htb=htb, min_flange=4 * t,
             flange_ok='PASS' if min(o['A'], fx['H']) >= 4 * t else 'FAIL',
             mass=flat * fx['b'] * t * MATERIALS[mat]['rho'] / 1000.0,
             material_callout=material_callout(mat, t, fx), finish_callout=o['finish_callout'],
             callout_bend=f"BEND 90{chr(176)} {chr(177)}{fx['bend_tol']:.0f}{chr(176)}, INSIDE R{R:g} (= t)",
             callout_thread=f"2X M5-6H, depth {tap:.0f} / drill {fx['tap_drill']:.1f}, depth {tap + 3:.0f}",
             callout_thread_asme=f"2X M5 X {fx['P_M5']:.1f} - 6H {chr(0x2913)} {tap:.0f} / {chr(216)}{fx['tap_drill']:.1f} {chr(0x2913)} {tap + 3:.0f}",
             screw=f"M5 x {sc['L']}", screw_check=sc['status'], upper_swing=h1 - t,
             sigma=rd['sigma'], FOS=rd['FOS'], droop=rd['droop'])
    # D106: back-check of the brief hole position at the released t; margin and the largest supplier inside R that still passes
    req_b, edge_b, htb_b = hole_to_bend(t, fx['hole1'], fx)
    r.update(htb_brief=htb_b, htb_shortfall_brief=req_b - edge_b if htb_b == 'FAIL' else None, move=h1 - fx['hole1'],
             htb_margin=edge - req, htb_R_max=math.floor((edge - 3.5 * t) / 2 * 10 + 1e-9) / 10)
    r['htb_tight'] = 'yes' if r['htb_R_max'] < R + fx['htb_tight_band'] - 1e-9 else 'no'
    # D108: worst case at the drawing tolerances (top face profile, hole position zone, hole size: each takes half its band off the edge)
    wc = wc_loss(fx)
    r.update(htb_edge_wc=edge - wc, htb_margin_wc=edge - wc - req, htb_wc='PASS' if edge - wc >= req - 1e-9 else 'FAIL')
    # D108: the course SAMPLE supplier (air bend, die opening = sup_die_factor x t) at this t
    die = fx['sup_die_factor'] * t
    Rs = math.ceil(fx['sup_R_ratio'] * die * 2 - 1e-9) / 2
    r.update(sup_die=die, sup_R=Rs, htb_req_supR=3.5 * t + 2 * Rs, htb_supR='PASS' if edge >= 3.5 * t + 2 * Rs - 1e-9 else 'FAIL')
    r['query_tight'] = (f"Our hole-to-bend passes only with inside R <= {r['htb_R_max']:.1f} mm at nominal sizes: please confirm your inside R "
                        f"and your thickness tolerance at t = {t:g} mm.") if r['htb_tight'] == 'yes' else None
    # D106 Ep 20 card: checks failing as given that the released design closed, and checks still open at Rev A
    asg = [x.strip() for x in o['fails'].split(',')] if o['fails'] != 'none' else []
    opn = (['screw length / thread depth'] if sc['status'] == 'FAIL' else []) + (['hole stack-up'] if o['stack'] == 'FAIL' else []) \
        + (['hole-to-bend'] if htb == 'FAIL' else [])
    closed = [x for x in asg if x not in opn]
    if htb_b == 'FAIL' and 'hole-to-bend' not in closed:
        closed.append('hole-to-bend')
    why = [f"t {t:.1f}"] if t != o['t'] else []
    why += ['holes moved'] if rd['moved'] else []
    r['closed'] = (', '.join(closed) + (f" ({', '.join(why)})" if why else '')) if closed else 'none'
    r['closed_list'], r['open_list'] = closed, opn
    r['open'] = ', '.join(opn) if opn else 'none'
    r['sigma_ksi'] = rd['sigma'] / 6.894757293168
    r['droop_in'] = rd['droop'] / 25.4
    r['t_in'] = t / 25.4
    # Ep 15 number-format items at the released geometry: same seeded choice, released numbers
    ob = dict(o, t=t, flat=flat, base=dict(o['base'], sigma=rd['sigma']), inch=dict(o['inch'], t=t / 25.4))
    r['format_errors'] = format_errors(ob)
    return r


SYMPTOM = {   # illustrative field reports, one per check still open at Rev A (same wording as the Ep 22 worksheet)
    'screw length / thread depth': 'the screws stop turning before the bracket is clamped tight, and the bracket can rock on the upright',
    'hole stack-up': 'on some shelves the second screw will not start in its tapped hole; installers forced it in or left it out',
}


def wc_loss(fx=FIXED):
    """D108 worst case on the hole-to-bend edge at the C4-DWG-009 tolerances: profile 0.4 on the top face (half off), position zone
    2 x tol_laser (radius off), hole size +clear_tol (half off)."""
    return fx['tol_gen_m'] + fx['tol_laser'] + fx['clear_tol'] / 2


# D109 (panel ruling, Facts batch 9): Rev A is released at the end of Part 2 and holds every Part 1/2 correction
# (Ep 12 thread callout, Ep 13 hole size). Ep 22 changes per variant: V1/V4 captive-washer screw (joint bottoms without
# the washer), V3 holes made after forming (supplier sample report), V6 adds the same hole-to-bend ECO to its galvanic ECO.
D109_KIND = {1: 'washer_bottoming', 3: 'supplier_R', 4: 'washer_bottoming'}
# D133 (amends D109 s5): the washer-dependent joint is open wherever the joint bottoms without its loose washer (rule, not a list)
D109_HTB_AFTER = (3, 6)        # panel ruling: holes made after forming (V3: a hole move fails droop; V6: recorded judgement at 500/yr)
HTB_FIX_RULE = ("1. A tolerance cannot fix a hole that sits on its hole-to-bend limit. 2. Never go below R = t. "
                "3. Move the holes (pitch kept) when every re-run check still passes and the volume is high: a move costs nothing per part. "
                "4. Otherwise make the holes after forming: a hole made after bending is not pulled oval, no geometry changes, "
                "so nothing is re-run and interchangeability is kept; the cost is one operation per part.")
HOLE_NOTE = '2X HOLES MADE AFTER FORMING, BEFORE FINISHING'


def rev_a(o, v, fx=FIXED):
    """D109: the learner's released Rev A = released geometry (D105) + Ep 13 hole size + Ep 12 thread callout."""
    r = o['rel']
    if not r:
        return None
    t = r['t']
    hd = fx['clear'] if o['stack'] == 'PASS' else math.ceil(o['hole_nominal_needed'] * 10 - 1e-9) / 10
    edge = r['hole1'] - hd / 2
    req = r['htb_req']
    wc = wc_loss(fx)
    sc = o['screw']
    thread = fx['tap_depth'] if sc['status'] == 'PASS' else sc['eng'] + fx['bottom_gap']      # = Ep12_callout_thread depth
    L = int(re.search(r'M5 x (\d+)', r['screw']).group(1))
    need = UPRIGHTS[v['upright']] * fx['d']
    eng = L - t - fx['washer']
    eng0 = L - t
    a = dict(hole_d=hd, hole_callout=o['hole_callout_fix'], htb_edge=edge, htb_margin=edge - req,
             htb_R_max=math.floor((edge - 3.5 * t) / 2 * 10 + 1e-9) / 10, htb_edge_wc=edge - wc, htb_margin_wc=edge - wc - req,
             htb_wc='PASS' if edge - wc >= req - 1e-9 else 'FAIL', thread_depth=thread, drill_depth=thread + 3, eng=eng,
             screw_check='PASS' if need <= eng <= thread - fx['bottom_gap'] + 1e-9 else 'FAIL', nowasher_eng=eng0)
    a['htb_R_max_wc'] = math.floor((edge - wc - 3.5 * t) / 2 * 10 + 1e-9) / 10 if a['htb_wc'] == 'FAIL' else None
    a['nowasher_check'] = ('FAIL' if thread < eng0 + fx['bottom_gap'] - 1e-9 else
                           'PASS (limit)' if abs(thread - eng0 - fx['bottom_gap']) < 1e-9 else 'PASS')
    a['query_tight'] = (f"Our hole-to-bend passes by only {a['htb_margin']:.2f} mm at nominal sizes and fails at the drawing tolerances: "
                        f"please tell us the inside R you get at t = {t:g} mm on your standard die, your thickness tolerance, and whether "
                        "you can make the 2 holes after forming, at what cost.") if a['htb_wc'] == 'FAIL' else None
    # Ep 20 card: closed in Rev A / open at the review
    closed = [('hole-to-bend at the brief position' if x == 'hole-to-bend' else x) for x in r['closed_list']]
    why = ([f"t {t:.1f}"] if t != o['t'] else []) + (['holes moved'] if r['moved'] == 'yes' else [])
    parts = [', '.join(closed) + (f" ({', '.join(why)})" if why else '')] if closed else []
    if r['screw_check'] == 'FAIL' or sc['status'] == 'FAIL':
        parts.append(f"screw length / thread depth (Ep 08 fix, Ep 12 callout: thread {thread:g} mm)")
    if o['stack'] == 'FAIL':
        parts.append(f"hole stack-up (Ep 13 hole {o['hole_callout_fix']})")
    opn = []
    if a['nowasher_check'] == 'FAIL':      # every Rev A kit has a loose plain washer (brief)
        opn.append(f"washer-dependent joint: without the {fx['washer']:g} mm washer the screw bottoms")
    if a['htb_wc'] == 'FAIL':
        opn.append('hole-to-bend: no margin at the drawing tolerances (supplier R to confirm)')
    if ECO_KIND.get(v['v']) == 'galvanic':
        opn.append('galvanic isolation not in the kit')
    a['closed'] = '; '.join(parts) if parts else 'none'
    a['open'] = '; '.join(opn) if opn else 'none'
    a['closed_topics'] = ['thread' if 'thread' in x else 'stack' if 'stack' in x else 'htb_brief' if 'hole-to-bend' in x else x for x in closed + [p for p in parts[1 if closed else 0:]]]
    a['open_topics'] = ['washer' if 'washer' in x else 'htb_wc' if 'hole-to-bend' in x else 'galvanic' for x in opn]
    return a


def after_forming(o, t, edge, Rs, die, part_number, fx=FIXED):
    """D109 hole-to-bend ECO by holes made after forming at the supplier's standard R (V3, V6)."""
    Rl = t * fx['R_over_t']
    req = 3.5 * t + 2 * Rs
    BA = math.pi / 2 * (Rs + fx['K_factor'] * t)
    return dict(sup_die=die, sup_R=Rs, htb_req=req, htb_edge=edge, htb='PASS' if edge >= req - 1e-9 else 'FAIL',
                htb_margin=edge - req, shortfall=req - edge if edge < req - 1e-9 else None, fix='holes made after forming',
                callout_bend=f"BEND 90{chr(176)} {chr(177)}{fx['bend_tol']:.0f}{chr(176)}, INSIDE R{Rl:g} TO R{Rs:g}", hole_note=HOLE_NOTE,
                BA=BA, flat=(o['A'] - t - Rs) + (fx['H'] - t - Rs) + BA,
                flat_R_low=(o['A'] - t - Rl) + (fx['H'] - t - Rl) + math.pi / 2 * (Rl + fx['K_factor'] * t),
                bendzone_clear=edge - (t + Rs), part_number=f"{part_number} (Rev B)",
                problem=(f"the supplier's sample parts, bent at their standard inside R{Rs:g} (die opening {die:g} mm), have oval upper holes "
                         "pulled toward the bend, and some screws will not start"),
                fa_check=(f"First article: measure the inside R; accept R{Rl:g} to R{Rs:g} (bend note); the 2 holes are round, in size and "
                          "in position (made after forming)"))


def ep22_d109(o, v, fx=FIXED):
    e = ep22(o, v, fx)
    a, r = o['revA'], o['rel']
    e.update(hole_note=None, bendzone_clear=None, alt_thread_need=None, tw_min=None, tw_max=None)
    b = {k: None for k in ('problem', 'sup_die', 'sup_R', 'htb_req', 'htb_edge', 'htb', 'shortfall', 'fix', 'callout_bend', 'hole_note',
                           'BA', 'flat', 'flat_R_low', 'bendzone_clear', 'part_number', 'ecr')}
    e['b'] = b
    if not a or v['v'] not in range(1, 7):
        return e
    t = r['t']
    kind = D109_KIND.get(v['v'])
    if kind == 'washer_bottoming':
        keep = {'kind', 'b'}
        for k in list(e):
            if k not in keep:
                e[k] = None
        L = int(re.search(r'M5 x (\d+)', r['screw']).group(1))
        need = UPRIGHTS[v['upright']] * fx['d']
        e.update(kind=kind, screw=f"M5 x {L} hexagon socket head screw with captive plain washer ({fx['sems_std']})", eng=a['eng'],
                 screw_check=a['screw_check'], washer_od=fx['washer_od'], alt_thread_need=a['nowasher_eng'] + fx['bottom_gap'])
        e['kind'] = kind
        e['problem'] = SYMPTOM['screw length / thread depth'] + '; on those shelves the plain washer was left out'
        Ls = max(x for x in SCREW_LENGTHS if x < L)     # next shorter preferred length
        e['ecr'] = (f"Kit: M5 x {L} hexagon socket head screw with captive plain washer ({fx['sems_std']}; washer ISO 10673 type N, {chr(216)}{fx['washer_od']:g} x {fx['washer']:g}) instead of a loose screw + plain washer, so the washer cannot be left out; "
                    f"engagement {a['eng']:g} mm (>= {need:g}, <= {a['thread_depth']:g} - {fx['bottom_gap']:g}): PASS, the same as Rev A; same hex key "
                    f"(Ep 21 unchanged). Rejected: deepen the thread to {e['alt_thread_need']:g} mm (the field uprights are already tapped to "
                    f"{a['thread_depth']:g} mm and it does not stop the omission); M5 x {Ls} ({Ls:g} - {t:g} - {fx['washer']:g} = {Ls - t - fx['washer']:g} < {need:g}). "
                    "Bracket and upright unchanged; kit next revision, same kit number, screw assembly new part number; "
                    "field: inspect the affected shelves, fit the captive-washer screws where a washer is missing, record the serials")
    elif kind == 'supplier_R':      # V3 (V5 keeps its D108 branch: ECO_KIND)
        die = fx['sup_die_factor'] * t
        Rs = math.ceil(fx['sup_R_ratio'] * die * 2 - 1e-9) / 2
        f = after_forming(o, t, a['htb_edge'], Rs, die, f"SHB-100-{v['v']}", fx)
        e.update({k: f[k] for k in f})
        e['kind'] = kind
        e['ecr'] = (f"C4-DWG-009 row -{v['v']}: note '{HOLE_NOTE}'; bend note {f['callout_bend']} so the supplier's standard die conforms; holes stay "
                    f"{chr(216)}{a['hole_d']:.1f} at {r['hole1']:.1f} / {r['hole2']:.1f} with the same position frame. Not chosen: move the holes to "
                    f"{e['alt_hole1']:.1f} / {e['alt_hole2']:.1f} (passes hole-to-bend, ligament and droop {e['alt_droop']:.2f} mm, but the shelf rises "
                    f"{e['alt_raise']:g} mm: new part number {e['alt_part_number']} and 'replace both brackets'; at {v['qty']} a year one more operation per part "
                    f"is the smaller change). Rejected: INSIDE R <= {a['htb_R_max_wc']:.1f} "
                    f"(below R = t); a tighter tolerance (still fails by {f['shortfall']:.2f} at R{Rs:g}). Re-run: flat pattern (REF) at R{t:g} and R{Rs:g}; "
                    f"hole clear of the bend zone {a['htb_edge']:.2f} >= t + R = {t + Rs:g}; Ep 05, 06, 08, 13 and 21 unchanged. Form, fit and function "
                    f"unchanged: Rev B, same part number {f['part_number'].split(' ')[0]}. The R{Rs:g} samples do not conform to Rev A: reject, no deviation")
    if e['kind'] == 'galvanic':                       # D133: the insulating washer stays in the grip (thickness window)
        L = int(re.search(r'M5 x (\d+)', r['screw']).group(1))
        need = UPRIGHTS[v['upright']] * fx['d']
        e['tw_min'] = a['nowasher_eng'] - (a['thread_depth'] - fx['bottom_gap'])
        e['tw_max'] = a['nowasher_eng'] - need
        e['ecr'] = (f"Kit: captive (or bonded) insulating washers under the screw heads, {e['tw_min']:g} to {e['tw_max']:g} mm thick, so the washer stays in the grip "
                    f"(M5 x {L}: engagement {L} - {t:g} - washer between {need:g} and {a['thread_depth'] - fx['bottom_gap']:g} mm; thinner than {e['tw_min']:g} mm, or left out, "
                    f"and the screw bottoms), and sealant on the screw threads in the tapped holes of the upright; washer material and thickness from the maker; "
                    "re-check that the preload holds. One kit change answers both root causes (galvanic corrosion; washer-dependent joint), each stated in the ECO")
    else:
        e['tw_min'] = e['tw_max'] = None
    if v['v'] in D109_HTB_AFTER and v['v'] == 6:
        die = r['sup_die']
        Rs = r['sup_R']
        f = after_forming(o, t, a['htb_edge'], Rs, die, f"SHB-100-{v['v']}", fx)
        b.update({k: f.get(k) for k in b if k in f})
        b['ecr'] = (f"C4-DWG-009 row -{v['v']}: note '{HOLE_NOTE}'; bend note {f['callout_bend']}; holes unchanged. Re-run: flat pattern (REF) "
                    f"at R{t:g} and R{Rs:g}; hole clear of the bend zone {a['htb_edge']:.2f} >= t + R = {t + Rs:g}; no other check changes. "
                    f"Rev B, same part number SHB-100-{v['v']}. One change per ECO: the galvanic kit change is a separate ECO")
    return e


def ep22(o, v, fx=FIXED):
    """Course decision D106: the change each variant raises against Rev A (released geometry) in Ep 22."""
    r = o['rel']
    e = dict(kind=None, problem=None, ecr=None)
    keys = ('htb_req', 'htb_edge', 'htb', 'htb_margin', 'shortfall', 'R_max', 'sup_die', 'sup_R', 'hole1', 'hole2', 'raise', 'htb_new_edge',
            'htb_new', 'BA', 'flat', 'callout_bend', 'droop', 'T1', 'FOS_net', 'screw_check', 'upper_swing', 'lower_edge', 'lig_ok', 'fix',
            'part_number', 'screw', 'eng', 'washer_od', 'hole_d', 'R_max_wc', 'htb_new_edge_wc', 'htb_new_wc', 'htb_R_low', 'flat_R_low', 'fa_check',
            'htb_supR_req', 'htb_supR', 'alt_hole1', 'alt_hole2', 'alt_part_number', 'alt_raise', 'alt_lower_edge', 'alt_lig_ok', 'alt_droop', 'alt_upper_swing',
            'alt_edge_wc', 'alt_htb_wc', 'alt_ok')
    e.update({k: None for k in keys})
    if not r:
        return e
    t, h1 = r['t'], r['hole1']
    kind = ECO_KIND.get(v['v']) if v['v'] in ECO_KIND else ('open_checks' if r['open_list'] else 'none')
    e['kind'] = kind
    part = 'SHB-100'
    if kind == 'supplier_R':
        die = fx['sup_die_factor'] * t
        Rs = math.ceil(fx['sup_R_ratio'] * die * 2 - 1e-9) / 2
        req = 3.5 * t + 2 * Rs                                  # (t + R) + 2.5t + R at the supplier's R
        edge = h1 - fx['clear'] / 2
        h1n = max(h1, math.ceil((req + fx['clear'] / 2 + wc_loss(fx)) * 2 - 1e-9) / 2)   # D108: passes at R_sup at the drawing tolerances
        h2n = h1n + (fx['hole2'] - fx['hole1'])
        BA = math.pi / 2 * (Rs + fx['K_factor'] * t)
        flat = (o['A'] - t - Rs) + (fx['H'] - t - Rs) + BA
        m = mech(o['F'], o['e'], v['depth'], t, BASE_MAT, Lv=h1n, fx=fx)
        y1, y2 = fx['H'] - h1n, fx['H'] - h2n
        lower = fx['H'] - h2n - fx['clear'] / 2
        ok = (h1n - fx['clear'] / 2 >= req - 1e-9) and m['droop'] <= fx['droop_limit'] and lower >= fx['lig_factor'] * t - 1e-9
        e.update(sup_die=die, sup_R=Rs, htb_req=req, htb_edge=edge, htb='PASS' if edge >= req else 'FAIL', shortfall=req - edge if edge < req else None,
                 hole1=h1n, hole2=h2n, raise_=None, htb_new_edge=h1n - fx['clear'] / 2, htb_new='PASS' if h1n - fx['clear'] / 2 >= req - 1e-9 else 'FAIL',
                 R_max=math.floor((h1n - fx['clear'] / 2 - 3.5 * t) / 2 * 10 + 1e-9) / 10, BA=BA, flat=flat,
                 callout_bend=f"BEND 90{chr(176)} {chr(177)}{fx['bend_tol']:.0f}{chr(176)}, INSIDE R{t * fx['R_over_t']:g} TO R{Rs:g}", droop=m['droop'],
                 T1=o['M'] * y1 / (y1 ** 2 + y2 ** 2), FOS_net=m['FOS_net'], screw_check=r['screw_check'], upper_swing=h1n - t,
                 lower_edge=lower, lig_ok='PASS' if lower >= fx['lig_factor'] * t - 1e-9 else 'FAIL',
                 fix='move the holes' if ok else 'drill the holes after forming', part_number=f"{part}-{fx['part_next_dash']}")
        e['raise'] = h1n - h1
        Rl = t * fx['R_over_t']
        e_new = h1n - fx['clear'] / 2
        e.update(R_max_wc=math.floor((e_new - wc_loss(fx) - 3.5 * t) / 2 * 10 + 1e-9) / 10, htb_new_edge_wc=e_new - wc_loss(fx),
                 htb_new_wc='PASS' if e_new - wc_loss(fx) >= req - 1e-9 else 'FAIL',
                 htb_R_low='PASS' if e_new >= 3.5 * t + 2 * Rl - 1e-9 else 'FAIL',
                 flat_R_low=(o['A'] - t - Rl) + (fx['H'] - t - Rl) + math.pi / 2 * (Rl + fx['K_factor'] * t))
        e['fa_check'] = (f"First article: measure the inside R; accept R{Rl:g} to R{Rs:g} (bend note); the holes pass hole-to-bend up to "
                         f"R{e['R_max_wc']:.1f} at the drawing tolerances")
        e['problem'] = (f"the supplier's sample parts, bent at their standard inside R{Rs:g} (die opening {die:g} mm), have oval upper holes pulled toward the bend, "
                        "and some screws will not start")
        if ok:
            e['ecr'] = (f"Bend note INSIDE R{t * fx['R_over_t']:g} TO R{Rs:g} (the supplier's standard die is inside it) and both holes moved down to {h1n:.1f} / {h2n:.1f} mm "
                        f"from the top (pitch kept): hole-to-bend {h1n - fx['clear'] / 2:.2f} >= {req:.1f} at R{Rs:g}, also at the drawing tolerances; the shelf rises "
                        f"{h1n - h1:g} mm, so a new part number {part}-{fx['part_next_dash']} with the rule 'replace both brackets of a shelf'; first article measures the inside R; "
                        "the R" + f"{Rs:g} samples on the Rev A drawing are rejected (no deviation)")
        else:
            e['ecr'] = f"Drill the holes after forming (drawing note; Rev B, same part number); the R{Rs:g} samples are rejected (no deviation)"
    elif kind == 'captive_washer':
        sc = screw_choice(t, v['upright'], fx)       # the captive washer keeps the washer thickness in the grip: same Ep 08 rule
        e.update(screw=f"M5 x {sc['L']} hexagon socket head screw with captive plain washer ({fx['sems_std']})", eng=sc['eng'],
                 screw_check=sc['status'], washer_od=fx['washer_od'])
        e['problem'] = ('loose washers are dropped and lost from the kits, some brackets are fitted without washers, '
                        'and the screw heads mark the powder coat round the holes')
        e['ecr'] = (f"Kit: M5 x {sc['L']} hexagon socket head screw with captive plain washer ({fx['sems_std']}; washer ISO 10673 type N, {chr(216)}{fx['washer_od']:g} x {fx['washer']:g}) "
                    f"instead of a loose screw + plain washer; same hex key (no new tool, Ep 21 access unchanged); plain bearing face on the powder coat; bracket unchanged; "
                    f"engagement {sc['eng']:g} mm (>= {UPRIGHTS[v['upright']] * fx['d']:g}, below the {fx['tap_depth']:g} mm thread); kit next revision, screw assembly new part number")
    elif kind == 'galvanic':
        e['problem'] = ('after the first winter on the seaside balconies, white powder and rust streaks appear around the screw heads and washers; '
                        'the bracket finish away from the screws is fine')
        e['ecr'] = ('Insulating washers under the screw heads and sealant on the screw threads in the tapped holes of the upright; '
                    're-check the screw length for the washer thickness')
    else:
        if 'hole stack-up' in r['open_list']:
            d = math.ceil(o['hole_nominal_needed'] * 10 - 1e-9) / 10
            edge = h1 - d / 2
            e.update(hole_d=d, htb_req=r['htb_req'], htb_edge=edge, htb='PASS' if edge >= r['htb_req'] - 1e-9 else 'FAIL',
                     htb_margin=edge - r['htb_req'], R_max=math.floor((edge - 3.5 * t) / 2 * 10 + 1e-9) / 10,
                     htb_supR_req=r['htb_req_supR'], htb_supR='PASS' if edge >= r['htb_req_supR'] - 1e-9 else 'FAIL')
            e.update(htb_new_edge_wc=edge - wc_loss(fx), htb_new_wc='PASS' if edge - wc_loss(fx) >= r['htb_req'] - 1e-9 else 'FAIL',
                     R_max_wc=math.floor((edge - wc_loss(fx) - 3.5 * t) / 2 * 10 + 1e-9) / 10)
            if e['htb_supR'] == 'FAIL' or e['htb_new_wc'] == 'FAIL':
                # D108: the larger hole fails at the course SAMPLE supplier R or at the drawing tolerances: move both holes as V5 does,
                # so that hole-to-bend passes at the supplier R at the drawing tolerances (one change on one part: the bracket holes)
                a1 = max(h1, math.ceil((r['htb_req_supR'] + d / 2 + wc_loss(fx)) * 2 - 1e-9) / 2)
                a2 = a1 + (fx['hole2'] - fx['hole1'])
                ma = mech(o['F'], o['e'], v['depth'], t, o['mat_best']['mat'], Lv=a1, fx=fx)   # D133: E of the released material
                low = fx['H'] - a2 - d / 2
                e.update(alt_hole1=a1, alt_hole2=a2, alt_part_number=f"{part}-{fx['part_next_dash'] + 1}", alt_raise=a1 - h1, alt_lower_edge=low,
                         alt_lig_ok='PASS' if low >= fx['lig_factor'] * t - 1e-9 else 'FAIL', alt_droop=ma['droop'], alt_upper_swing=a1 - t,
                         alt_edge_wc=a1 - d / 2 - wc_loss(fx), alt_htb_wc='PASS' if a1 - d / 2 - wc_loss(fx) >= r['htb_req_supR'] - 1e-9 else 'FAIL')
                e['alt_ok'] = 'PASS' if (e['alt_htb_wc'] == 'PASS' and e['alt_lig_ok'] == 'PASS' and e['alt_droop'] <= fx['droop_limit']) else 'FAIL'
        e['problem'] = '; and '.join(SYMPTOM[x] for x in r['open_list']) if r['open_list'] else None
        chg = []
        sc = screw_choice(t, v['upright'], fx)
        if 'screw length / thread depth' in r['open_list']:
            chg.append(f"upright {fx['upright_part_number']} (next revision): tapped holes {sc['eng'] + fx['bottom_gap']:.0f} mm deep")
        if e['hole_d'] is not None:
            if e['alt_hole1'] is None:
                txt = (f"bracket (Rev B, same part number): clearance holes {chr(216)}{e['hole_d']:.1f} {chr(177)}{fx['clear_tol']:.1f}; hole-to-bend {e['htb_edge']:.2f} >= {e['htb_req']:.1f} "
                       f"at R = t, also at the drawing tolerances and at the course SAMPLE supplier's R{r['sup_R']:g}")
            else:
                why = []
                if e['htb_new_wc'] == 'FAIL':
                    why.append(f"at the drawing tolerances ({e['htb_new_edge_wc']:.2f} < {e['htb_req']:.1f})")
                if e['htb_supR'] == 'FAIL':
                    why.append(f"at the course SAMPLE supplier's R{r['sup_R']:g} ({e['htb_edge']:.2f} < {e['htb_supR_req']:.1f})")
                if e['alt_ok'] == 'PASS':
                    txt = (f"bracket: clearance holes {chr(216)}{e['hole_d']:.1f} {chr(177)}{fx['clear_tol']:.1f} at {e['alt_hole1']:.1f} / {e['alt_hole2']:.1f} mm from the top (pitch kept), "
                           f"because the larger hole at {h1:.1f} mm fails hole-to-bend " + ' and '.join(why) + f"; the shelf rises {e['alt_raise']:g} mm, so a new part number "
                           f"{e['alt_part_number']} with the rule 'replace both brackets of a shelf'; bend note INSIDE R{r['R']:g} TO R{r['sup_R']:g}")
                else:
                    txt = (f"bracket (Rev B, same part number): clearance holes {chr(216)}{e['hole_d']:.1f} {chr(177)}{fx['clear_tol']:.1f}; the larger hole fails hole-to-bend "
                           + ' and '.join(why) + f", and moving both holes to {e['alt_hole1']:.1f} / {e['alt_hole2']:.1f} fails droop ({e['alt_droop']:.2f} > {fx['droop_limit']:g} mm); "
                           f"so approval needs the supplier to hold inside R <= {e['R_max_wc']:.1f} at t = {t:g} mm (tighter than R = t: a narrow die, confirmed at first article). "
                           "Open for an engineering ruling")
            chg.append(txt)
        if chg:
            e['ecr'] = ('One ECO per part: ' + '; '.join(chg) + ('. A drilling fixture for the upright was considered and rejected: the uprights in the field are already drilled'
                                                               if e['hole_d'] is not None else ''))
        else:
            e['ecr'] = o['ecr']
    return e


def rel_get(k, i=None):
    def f(o):
        if not o['rel']: return None
        x = o['rel'][k]
        return x[i[0]][i[1]] if i else x
    return f


def format_errors(o):
    """Seeded choice of 5 number-format errors built from this variant's own numbers (Ep 15)."""
    i = o['inch']
    ksi = f"{o['base']['sigma'] / 6.894757293168:.2f}"      # the ksi value as printed
    pool = [
        (f"Inch drawing shows thickness as {i['t']:.3f}", f".{round(i['t'] * 1000):03d} (no leading zero on inch values)"),
        (f"mm drawing shows a 0.5 mm chamfer as .5 x 45{chr(176)}", f"0.5 x 45{chr(176)} (mm values below 1 need a leading zero)"),
        ("English-language drawing writes the thickness as " + f"{o['t']:.1f}".replace('.', ','),
         f"{o['t']:g} (dot decimal for this customer; never mix; a whole mm size takes no trailing zero)"),
        (f"Shelf depth on an inch drawing: {i['depth']:.3f} +/- .01",
         f"{i['depth']:.2f} +/- .01, or {i['depth']:.3f} +/- .010 (decimal places must match the tolerance)"),
        ("Revision date written 03/04/2026 (meant 4 March 2026)", "2026-03-04 (ISO 8601)"),
        (f"Design load written {o['F'] / 4.4482216152605:.1f} lb", f"{o['F'] / 4.4482216152605:.1f} lbf (force is lbf, mass is lb)"),
        (f"Bending stress written {ksi} psi", f"{ksi} ksi (= {round(float(ksi) * 1000):.0f} psi)"),   # psi = printed ksi x 1000, as a learner gets it from the card
        (f"Flat length written {o['flat']:.1f} on a sheet with no units note", f"add the units note 'Dimensions in mm' in the title block; value {o['flat']:.1f}"),
    ]
    rng = random.Random(SEED + o['v'])
    return rng.sample(pool, 5)


def fails(o):
    f = []
    if o['base']['strength_both'] == 'FAIL': f.append('strength')
    if o['base']['stiffness'] == 'FAIL': f.append('stiffness')
    if o['screw']['status'] == 'FAIL': f.append('screw length / thread depth')
    if o['stack'] == 'FAIL': f.append('hole stack-up')
    if o['htb'] == 'FAIL': f.append('hole-to-bend')
    return ', '.join(f)


def ecr(o):
    """One change per failed check, in the order a reviewer would raise them."""
    out, rd = [], o['rd']
    if o['base']['stiffness'] == 'FAIL' or o['base']['strength_both'] == 'FAIL':
        if not rd:
            return 'No stock thickness passes: add a formed rib or gusset (new concept)'
        extra = f", holes moved to {rd['hole1']:.1f} / {rd['hole2']:.1f} mm from the top" if rd['moved'] else ''
        out.append(f"increase thickness to {rd['t']:.1f} mm{extra}; screw M5 x {rd['screw']['L']}")
    elif o['htb'] == 'FAIL' and rd:
        out.append(f"move the screw holes down to {rd['hole1']:.1f} / {rd['hole2']:.1f} mm from the top (hole-to-bend); droop re-checked {rd['droop']:.2f} mm")
    sc = rd['screw'] if rd else o['screw']
    if sc['status'] == 'FAIL':
        out.append(f"deepen the tapped holes in the upright to {sc['eng'] + FIXED['bottom_gap']:.0f} mm")
    if o['stack'] == 'FAIL':
        out.append(f"clearance holes {chr(216)}{o['hole_nominal_needed']:.1f} {chr(177)}{FIXED['clear_tol']:.1f} (smallest hole {o['hole_needed']:.1f} mm), or a drilling fixture for the upright")
    if not out:
        return 'Field problem given on the worksheet (no design check fails)'
    s = '; '.join(out)
    return s[0].upper() + s[1:]


# ---------------------------------------------------------------- spoken form (same style as facts_c4.json)
ONES = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve', 'thirteen',
        'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen']
TENS = ['', '', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety']
UNIT_WORDS = {'N': ('newton', 'newtons'), 'mm': ('millimetre', 'millimetres'), 'MPa': ('megapascal', 'megapascals'),
              'N.mm': ('newton millimetre', 'newton millimetres'), 'N.m': ('newton metre', 'newton metres'),
              'deg': ('degree', 'degrees'), 'rad': ('radian', 'radians'), 'ksi': ('k s i', 'k s i'),
              'D': ('times the diameter', 'times the diameter'), 'kg': ('kilogram', 'kilograms'), 'lb': ('pound', 'pounds'),
              'lbf': ('pound-force', 'pounds-force'), 'lbf.in': ('pound-force inch', 'pound-force inches'),
              'in': ('inch', 'inches'), 'um': ('micrometre', 'micrometres'), 'GU': ('gloss unit', 'gloss units'), 'mm^4': ('millimetre to the fourth', 'millimetres to the fourth'), 'g': ('gram', 'grams'),
              'g/cm^3': ('gram per cubic centimetre', 'grams per cubic centimetre'),
              'm/s^2': ('metre per second squared', 'metres per second squared'), 'parts': ('part', 'parts'),
              'brackets': ('bracket', 'brackets'), 'cost units': ('cost unit', 'cost units')}


def whole(n):
    if n < 20: return ONES[n]
    if n < 100: return TENS[n // 10] + ('' if n % 10 == 0 else '-' + ONES[n % 10])
    if n < 1000: return ONES[n // 100] + ' hundred' + ('' if n % 100 == 0 else ' and ' + whole(n % 100))
    if n < 1000000:
        r = n % 1000
        return whole(n // 1000) + ' thousand' + ('' if r == 0 else (' and ' if r < 100 else ' ') + whole(r))
    raise ValueError(n)


def spoken(text, unit):
    """text = the number exactly as printed (e.g. '2.44', '-0.20', '.157'). Trailing zeros are not spoken."""
    s = text.strip()
    neg = s.startswith('-')
    s = s.lstrip('-')
    if s.startswith('.'):
        s = '0' + s
    w, _, f = s.partition('.')
    f = f.rstrip('0')
    out = ('minus ' if neg else '') + whole(int(w)) + ((' point ' + ' '.join(ONES[int(c)] for c in f)) if f else '')
    words = UNIT_WORDS.get(unit)
    if words:
        out += ' ' + (words[0] if (float(s) == 1.0 and not neg) else words[1])
    return out


def unspoken(s):
    """Inverse of spoken() for the self-check: words back to a number (unit words ignored)."""
    vals = {w: i for i, w in enumerate(ONES)}
    vals.update({w: 10 * i for i, w in enumerate(TENS) if w})
    toks = s.replace('-', ' ').split()
    neg = toks[:1] == ['minus']
    toks = toks[1:] if neg else toks
    total = cur = 0
    frac = ''
    i = 0
    while i < len(toks):
        t = toks[i]
        if t == 'point':
            frac = ''.join(str(vals[x]) for x in toks[i + 1:] if x in ONES)
            break
        if t in vals: cur += vals[t]
        elif t == 'hundred': cur *= 100
        elif t == 'thousand': total += cur * 1000; cur = 0
        elif t == 'and': pass
        else: break      # unit words
        i += 1
    x = float(f"{total + cur}.{frac or '0'}")
    return -x if neg else x


# ---------------------------------------------------------------- one spec drives the Markdown, the JSON and the CSV
def show(val, nd):
    """The value exactly as printed in the Markdown (and as stored / spoken in the JSON)."""
    if val is None: return 'none'
    if nd == 'str': return str(val)
    if nd == 'int': return f'{int(val)}'
    if nd == 'in': return f'{val:.3f}'.lstrip('0') if val < 1 else f'{val:.3f}'
    return f'{val:.{nd}f}'


def num_value(txt):
    """The JSON value of a printed number: rounded to the printed decimals; whole numbers stored as int (150, not 150.0)."""
    x = float('0' + txt if txt.startswith('.') else txt)
    return int(round(x)) if x == round(x) else x


def entry(val, nd, unit, formula):
    """JSON entry. value = number rounded to the printed decimals (int when whole); printed = the exact string printed in
    the Markdown (keeps trailing zeros, e.g. 3.60, 3.0, .157); spoken = printed string read aloud."""
    txt = show(val, nd)
    if val is None or nd == 'str':
        return dict(value=txt, unit='', formula=formula, spoken='', printed=txt)
    return dict(value=num_value(txt), unit=unit, formula=formula, spoken=spoken(txt, unit), printed=txt)


def R(key, label, unit, fn, nd, formula=None):
    return (key, label, unit, fn, nd, formula or label)


def rd_get(k, sub=None):
    def f(o):
        if not o['rd']: return None
        x = o['rd'][k]
        return x[sub] if sub else x
    return f


def spec(fx=FIXED):
    """(episode tag, heading, intro lines, rows). Each row -> one Markdown row and one JSON key per variant."""
    k = fx['K_factor']
    S = []
    S.append(('Ep02', 'Ep 02 - numbers used in the PDS lines (per variant)', [], [
        R('W', 'Load per bracket W = m g / 2', 'N', lambda o: o['W'], 1),
        R('F', f"Design load F = {fx['k_design']} W", 'N', lambda o: o['F'], 1),
        R('FOS_gate', 'FOS gate on yield', '-', lambda o: fx['gate'], 1, 'input (course PDR gate)'),
        R('droop_limit', 'Front-edge droop limit', 'mm', lambda o: fx['droop_limit'], 1, 'input (illustrative PDS limit)'),
        R('pitch', 'Screw pitch on the upright', 'mm', lambda o: fx['hole2'] - fx['hole1'], 0, 'hole2 - hole1'),
    ]))
    S.append(('Ep03', 'Ep 03 - concept cost per bracket at the variant quantity (illustrative prices, not quotes)',
              ['Cost per part = (tooling + quantity x piece price) / quantity, in illustrative cost units. Feeds the "cost" row of the Pugh matrix.'],
              [R(f'cost_{tag}', f'{name} (tooling {tool:.0f}, piece {pc:.2f})', 'cost units',
                 (lambda name: lambda o: o['concept_cost'][name])(name), 2, '(tooling + qty x piece) / qty')
               for name, (tool, pc, tag) in CONCEPTS.items()]
              + [R('cheapest', 'Cheapest concept', '-', lambda o: o['concept_best'], 'str', 'lowest cost per part')]))
    S.append(('Ep04', 'Ep 04 - FBD and reactions (per-variant table)',
              [f"Heel = bottom edge of the wall flange. Screw distances from the heel: y1 = {fx['H'] - fx['hole1']:.0f} mm (upper), y2 = {fx['H'] - fx['hole2']:.0f} mm (lower)."], [
        R('W_total', 'Shelf weight W_total = m g', 'N', lambda o: o['W_total'], 1),
        R('W', 'Load per bracket W = W_total / 2', 'N', lambda o: o['W'], 1),
        R('F', f"Design load F = {fx['k_design']} W", 'N', lambda o: o['F'], 1),
        R('e', 'Lever arm e = depth / 2', 'mm', lambda o: o['e'], 0),
        R('M', 'Moment at the wall M = F e', 'N.mm', lambda o: o['M'], 0),
        R('R_vert', 'Vertical reaction at the wall (= F)', 'N', lambda o: o['R_vert'], 1),
        R('V_each', 'Shear per screw F / 2', 'N', lambda o: o['V_each'], 1),
        R('y1', 'Upper screw distance from the heel y1', 'mm', lambda o: o['y1'], 0, 'H - hole1'),
        R('y2', 'Lower screw distance from the heel y2', 'mm', lambda o: o['y2'], 0, 'H - hole2'),
        R('T1', 'Upper screw tension T1 = M y1 / (y1^2 + y2^2)', 'N', lambda o: o['T1'], 1),
        R('T2', 'Lower screw tension T2 = M y2 / (y1^2 + y2^2)', 'N', lambda o: o['T2'], 1),
        R('C', 'Heel compression C = T1 + T2', 'N', lambda o: o['C'], 1),
    ]))
    S.append(('Ep05', 'Ep 05 - bending stress and FOS, base material 5052-H32 (per-variant table)', [], [
        R('t', 'Thickness t', 'mm', lambda o: o['t'], 1, 'variant input'),
        R('M', 'M = F e', 'N.mm', lambda o: o['base']['M'], 0),
        R('I', 'I = b t^3 / 12', 'mm^4', lambda o: o['base']['I'], 1),
        R('sigma', 'sigma = 6M / (b t^2)', 'MPa', lambda o: o['base']['sigma'], 1),
        R('FOS', 'FOS = Sy / sigma', '-', lambda o: o['base']['FOS'], 2),
        R('strength', f"Strength vs gate {fx['gate']}, section 1 (bend)", '-', lambda o: o['base']['strength'], 'str', 'PASS if FOS >= gate'),
        R('b_net', f"Section 2 (upper screw hole): b_net = b - {fx['clear']:.1f}", 'mm', lambda o: o['base']['b_net'], 1, 'b - clearance hole diameter'),
        R('sigma_net', 'Section 2: sigma_net = 6M / (b_net t^2)', 'MPa', lambda o: o['base']['sigma_net'], 1, '6M / ((b - clear) t^2), M at the upper hole = F e'),
        R('FOS_net', 'Section 2: FOS_net = Sy / sigma_net', '-', lambda o: o['base']['FOS_net'], 2, 'Sy / sigma_net'),
        R('strength_net', f"Strength vs gate {fx['gate']}, section 2 (net section)", '-', lambda o: o['base']['strength_net'], 'str', 'PASS if FOS_net >= gate'),
        R('t_strength', 'Thinnest stock t passing strength (sections 1 and 2)', 'mm', lambda o: o['t_strength'], 1, 'first stock t with FOS and FOS_net >= gate'),
        R('FOS_min', f"Minimum-yield gate: FOS_min = Sy_min / sigma_net, Sy_min = {fx['Sy_min']:.1f}", '-', lambda o: o['FOS_min'], 2, 'Sy_min / sigma_net (Sy_min from facts_c4.json)'),
        R('strength_min', f"Strength vs gate {fx['gate']} on the specified minimum yield", '-', lambda o: o['strength_min'], 'str', 'PASS if FOS_min >= gate'),
        R('t_strength_min', 'Thinnest stock t passing on the specified minimum yield', 'mm', lambda o: o['t_strength_min'], 1, 'first stock t with Sy_min / sigma_net >= gate'),
    ]))
    S.append(('Ep06', 'Ep 06 - rotation and front-edge droop, 5052-H32 (per-variant table)', [], [
        R('th_shelf', 'Shelf-flange rotation M e / (2 E I)', 'rad', lambda o: o['base']['th_shelf'], 4),
        R('th_wall', f"Wall-flange rotation M Lv / (E I), Lv = {fx['hole1']:.0f}", 'rad', lambda o: o['base']['th_wall'], 4),
        R('th', 'Total rotation', 'rad', lambda o: o['base']['th'], 4, 'th_shelf + th_wall'),
        R('tilt_deg', 'Shelf tilt', 'deg', lambda o: o['base']['tilt_deg'], 2, 'total rotation x 180 / pi'),
        R('droop', 'Front-edge droop = rotation x depth', 'mm', lambda o: o['base']['droop'], 2),
        R('stiffness', f"Stiffness vs {fx['droop_limit']:.1f} mm limit", '-', lambda o: o['base']['stiffness'], 'str', 'PASS if droop <= limit'),
        R('rd_t', 'Redesign: thinnest stock t passing all checks', 'mm', rd_get('t'), 1, 'first stock t passing strength, stiffness and hole-to-bend'),
        R('rd_hole1', 'Redesign: upper hole from top outside face', 'mm', rd_get('hole1'), 1, 'max(25, hole-to-bend edge + clear/2, rounded up to 0.5)'),
        R('rd_hole2', 'Redesign: lower hole from top outside face', 'mm', rd_get('hole2'), 1, 'rd_hole1 + 55 (pitch kept)'),
        R('rd_moved', 'Redesign: holes moved?', '-', lambda o: ('yes' if o['rd']['moved'] else 'no') if o['rd'] else None, 'str', 'rd_hole1 > 25'),
        R('rd_sigma', 'Redesign: sigma at that t', 'MPa', rd_get('sigma'), 1, '6M / (b t^2) at rd_t'),
        R('rd_FOS', 'Redesign: FOS at that t', '-', rd_get('FOS'), 2, 'Sy / rd_sigma'),
        R('rd_droop', 'Redesign: droop at that t (with that Lv)', 'mm', rd_get('droop'), 2, '(M e / (2EI) + M Lv / (EI)) x depth, Lv = rd_hole1'),
        R('rd_T1', 'Redesign: upper screw tension', 'N', rd_get('T1'), 1, 'M y1 / (y1^2 + y2^2) with the redesign hole positions'),
        R('rd_screw', 'Redesign: screw (Ep 08 rule)', '-', lambda o: f"M5 x {o['rd']['screw']['L']}" if o['rd'] else None, 'str', 'Ep 08 rule at rd_t'),
        R('rd_screw_check', 'Redesign: screw check', '-', lambda o: o['rd']['screw']['status'] if o['rd'] else None, 'str', 'Ep 08 rule at rd_t'),
    ]))
    mrows = []
    for mat, mp in MATERIALS.items():
        kk = mp['key']
        g = (lambda kk: lambda f: (lambda o: f(o['mat'][kk])))(kk)
        mrows += [
            R(f'{kk}_total', f'{mat}: weighted total', '-', g(lambda r: r['total']), 2, 'sum of weight x score'),
            R(f'{kk}_scores', f'{mat}: scores strength/stiffness/cost/process/corrosion', '-', g(lambda r: '/'.join(str(x) for x in r['s'])), 'str', 'score rules above'),
            R(f'{kk}_gate', f'{mat}: corrosion gate', '-', g(lambda r: 'in' if r['ok'] else 'OUT'), 'str', 'OUT if corrosion score = 1'),
            R(f'{kk}_FOS', f'{mat}: FOS at variant t', '-', g(lambda r: r['FOS']), 2, 'Sy(material) / sigma'),
            R(f'{kk}_droop', f'{mat}: droop at variant t', 'mm', g(lambda r: r['droop']), 2, 'Ep 06 droop with E(material)'),
            R(f'{kk}_cost', f'{mat}: relative part cost incl. finish', '-', g(lambda r: r['cost']), 2, 'relative material cost + finish (illustrative)'),
            R(f'{kk}_mass', f'{mat}: mass per bracket', 'g', g(lambda r: r['mass']), 0, 'flat length x b x t x density'),
        ]
    mrows += [
        R('choice', 'Matrix choice (highest total that passes the corrosion gate)', '-', lambda o: o['mat_best']['mat'], 'str', 'highest total among materials not OUT'),
        R('choice_FOS', 'Choice: FOS at variant t', '-', lambda o: o['mat_best']['FOS'], 2, 'Sy / sigma'),
        R('choice_droop', 'Choice: droop at variant t', 'mm', lambda o: o['mat_best']['droop'], 2, 'Ep 06 droop with E(choice)'),
        R('choice_finish', 'Choice: finish', '-', lambda o: o['mat_best']['finish'], 'str', 'environment table'),
        R('choice_note', 'Choice: note', '-', lambda o: o['mat_note'], 'str', 'both checks at variant t'),
        R('mass_ratio', 'Mass ratio steel / aluminium', '-', lambda o: o['mat']['steel']['mass'] / o['mat']['al']['mass'], 2, 'rho steel / rho aluminium'),
        R('droop_ratio', 'Droop ratio aluminium / steel', '-', lambda o: o['mat']['al']['droop'] / o['mat']['steel']['droop'], 2, 'E steel / E aluminium'),
        R('why', 'Worksheet sentence (why this choice)', '-', lambda o: o['mat_why'], 'str', 'generated from the scores and masses'),
    ]
    al, st, ss = (MATERIALS[m] for m in MATERIALS)
    S.append(('Ep07', 'Ep 07 - material matrix at the variant thickness (typical values; illustrative costs)', [
        'Compared materials (course decision): 5052-H32 aluminium, low-carbon steel (cold-rolled) and 304 stainless steel. No plastic: a plastic bracket needs a ribbed shape, so comparing it at the same flat thickness is not fair.',
        'Weights: strength 0.25, stiffness 0.25, cost 0.20, process fit 0.15, corrosion 0.15. Scores 1-5.',
        'Strength score: 5 if FOS >= 5.0, 4 if >= 2.5, 2 if >= 1.5, else 1. ' + f"Stiffness score: 5 if droop <= {0.5 * fx['droop_limit']:.1f} mm, 4 if <= {fx['droop_limit']:.1f}, 2 if <= {1.5 * fx['droop_limit']:.1f}, else 1.",
        'Corrosion gate (applied before scoring): a corrosion score of 1 means not acceptable in that environment, so that material is out whatever its total.',
        'Cost score uses relative part cost INCLUDING the finish (5052-H32 bare = 1.0; illustrative): 5 if <= 0.8, 4 if <= 1.2, 2 if <= 2.5, else 1. Process fit: bends easily at R = t: 5 (aluminium, low-carbon steel), 3 (stainless: more springback, harder on tools).',
        'Corrosion score depends on the environment (scored with the finish shown).',
        f"Typical densities: aluminium {al['rho']:.2f}, low-carbon steel {st['rho']:.2f}, 304 stainless {ss['rho']:.2f} g/cm^3. Mass is shown for the discussion; it is not one of the 5 weighted criteria.",
        '',
        '**Worksheet wording (Ep 07; put this on the worksheet and in the answer key):**',
        '',
        f"- Why steel can win indoors - stiffness: steel's elastic modulus E ({st['E']:.0f} MPa) is about {st['E'] / al['E']:.1f} times aluminium's ({al['E']:.0f} MPa), so at the same thickness a steel bracket droops about {st['E'] / al['E']:.1f} times less. Droop is usually the first check to fail on this bracket, so steel gets the better stiffness score.",
        f"- Why steel can win indoors - cost: cold-rolled steel sheet is cheaper than aluminium sheet (illustrative relative cost {st['cost']:.1f} vs {al['cost']:.1f}), and indoors a cheap zinc plating or powder coat is enough, so steel gets the better cost score.",
        f"- Why aluminium wins on weight: aluminium's density is about one third of steel's ({al['rho']:.2f} vs {st['rho']:.2f} g/cm^3), so the same bracket is about {st['rho'] / al['rho']:.1f} times lighter. Weight is not one of the 5 criteria here because a wall bracket does not move; if your PDS makes weight matter (shipping cost, carrying, a weight limit), add it as a criterion and the answer can swing back to aluminium.",
        "- Why aluminium wins on corrosion: aluminium protects itself with a thin oxide skin, so a scratch does not start rust; steel relies on its coating, and a scratch, cut edge or worn spot rusts once it gets wet. In humid rooms steel's corrosion score drops (it can still win there when the aluminium bracket at that thickness fails droop, but then the coating must stay intact: say so in your log), and near the sea it fails the corrosion gate.",
        '- So the matrix answer may differ from the 5052-H32 baseline used in Ep 05-06. That is intended: the matrix can overturn a baseline. Write the reason in your decisions log, and note that the Ep 17 bend radius R = t and K-factor are illustrative course values for both materials, so ask the supplier for the values for your material and thickness.',
        '- Galvanic note: steel or stainless next to an aluminium upright is a galvanic pair; it only matters when wet (humid, outdoor, coastal). Isolate with a nylon washer or sleeve, or keep the same metal family.',
    ], mrows))
    S.append(('Ep08', 'Ep 08 - screw choice and engagement (per-variant table)', [], [
        R('grip', 'Grip t', 'mm', lambda o: o['t'], 1, 'variant input'),
        R('upright', 'Upright alloy', '-', lambda o: o['upright'], 'str', 'variant input'),
        R('need', 'Engagement needed (1.5D in 6061-T6, 2D in 6063-T5)', 'mm', lambda o: o['screw']['need'], 1),
        R('max_eng', 'Most engagement without bottoming (thread depth - 1)', 'mm', lambda o: o['screw']['max_eng'], 1),
        R('screw', 'Screw chosen', '-', lambda o: f"M5 x {o['screw']['L']}", 'str', 'shortest preferred length that passes (or the Ep 08 fix)'),
        R('screw_L', 'Screw length L', 'mm', lambda o: o['screw']['L'], 'int', 'from 8, 10, 12, 16, 20, 25'),
        R('eng', 'Engagement = L - t - washer', 'mm', lambda o: o['screw']['eng'], 1),
        R('engD', 'Engagement / D', 'D', lambda o: o['screw']['engD'], 2),
        R('screw_check', 'Engagement and bottoming check', '-', lambda o: o['screw']['status'], 'str', 'need <= eng <= thread depth - 1'),
        R('T1', 'Upper screw tension from load T1', 'N', lambda o: o['T1'], 1, 'Ep 04'),
        R('T1_over_pre', f"T1 / preload ({fx['preload']:.0f} N)", '-', lambda o: o['T1_over_pre'], 3),
        R('pre_ratio', 'Preload / proof load', '-', lambda o: o['pre_ratio'], 2, 'preload / (proof x As)'),
        R('torque', 'Illustrative torque T = K F d', 'N.m', lambda o: o['torque'], 1),
        R('fix', 'Fix if no preferred length fits', '-', lambda o: o['screw']['fix'], 'str', 'Ep 08 rule'),
    ]))
    S.append(('Ep11', 'Ep 11 - title-block material and finish (one callout each; course decisions D101, D103)', [], [
        R('material_callout', 'Material (field 7): grade, condition, form, t, purchase standard', '-', lambda o: o['material_callout'], 'str', 'Ep 07 choice + t + purchase standard; course decision D101'),
        R('rel_material_callout', 'Material at the released t (course decision D105)', '-', rel_get('material_callout'), 'str', 'material_callout(Ep 07 choice, rel_t); course decisions D101, D105'),
        R('finish_callout', 'Finish (field 8): one finish, no alternatives', '-', lambda o: o['finish_callout'], 'str', 'Ep 07 choice + environment; course decisions D101, D103'),
    ]))
    S.append(('Ep12', 'Ep 12 - callouts (ISO form; per-variant table)', [], [
        R('callout_holes', 'Bracket holes', '-', lambda o: o['callout_hole_iso'], 'str', 'ISO form; hole size tolerance stated (laser-cut, typical); no THRU on a sheet-metal part (Ep 12)'),
        R('callout_thread', 'Upright thread', '-', lambda o: o['callout_thread_iso'], 'str', 'ISO form; depth from Ep 08'),
        R('callout_thread_asme', 'Upright thread, ASME form (pitch written, depth symbol)', '-', lambda o: o['callout_thread_asme'], 'str', 'same depths as callout_thread; pitch shelf_P_M5'),
        R('rel_callout_bend', 'Bend at the released t (D105)', '-', rel_get('callout_bend'), 'str', 'callout_bend with R = rel_t'),
        R('callout_bend', 'Bend', '-', lambda o: o['callout_bend'], 'str', 'angle tolerance stated (ISO 2768-m alone would set a tighter angle than a press brake holds); same pattern as ACT-103 note 2'),
    ]))
    S.append(('Ep13', 'Ep 13 - worst-case stack, hole pitch of bracket vs upright (per-variant table)', [], [
        R('process', 'Upright holes made by', '-', lambda o: o['upright_process'], 'str', 'CNC at >= 200 parts, else by hand'),
        R('tol_bracket', 'Bracket hole position tolerance (+/-)', 'mm', lambda o: fx['tol_laser'], 2, 'input (laser-cut)'),
        R('tol_upright', 'Upright hole position tolerance (+/-)', 'mm', lambda o: o['tol_u'], 2, 'input by process'),
        R('mismatch', 'Worst pitch mismatch 2(0.10) + 2(tol_u)', 'mm', lambda o: o['mismatch'], 2),
        R('hole_min', f"Smallest clearance hole ({fx['clear']:.1f} - {fx['clear_tol']:.1f})", 'mm', lambda o: o['hole_min'], 2, 'nominal - size tolerance'),
        R('allow', 'Allowed = smallest hole - screw diameter', 'mm', lambda o: o['allow'], 2),
        R('margin', 'Margin', 'mm', lambda o: o['stack_margin'], 2, 'allowed - mismatch'),
        R('stack', 'Result', '-', lambda o: o['stack'], 'str', 'PASS if margin >= 0'),
        R('hole_needed', 'Smallest clearance hole that works (zero margin)', 'mm', lambda o: o['hole_needed'], 2, 'd + mismatch'),
        R('hole_nominal_needed', f"Nominal hole needed (zero margin, +/-{fx['clear_tol']:.1f})", 'mm', lambda o: o['hole_nominal_needed'], 2, 'd + mismatch + size tolerance'),
        R('hole_callout', 'Drawn hole after the Ep 13 fix', '-', lambda o: o['hole_callout_fix'], 'str', 'PASS: clear; FAIL: hole_nominal_needed rounded up to 0.1; +/- clear_tol; no THRU on sheet metal (Ep 12)'),
    ]))
    S.append(('Ep15', 'Ep 15 - inch and lbf conversions (per-variant table)',
              ['1 in = 25.4 mm (exact); 1 lbf = 4.448 N; 1 ksi = 6.895 MPa; 1 kg = 2.205 lb (mass).'], [
        R('depth_in', 'Shelf depth', 'in', lambda o: o['inch']['depth'], 'in', 'depth / 25.4'),
        R('t_in', 'Thickness t', 'in', lambda o: o['inch']['t'], 'in', 't / 25.4'),
        R('b_in', 'Width b', 'in', lambda o: o['inch']['b'], 'in', 'b / 25.4'),
        R('H_in', 'Wall flange H', 'in', lambda o: o['inch']['H'], 'in', 'H / 25.4'),
        R('A_in', 'Shelf flange A', 'in', lambda o: o['inch']['A'], 'in', 'A / 25.4'),
        R('load_lb', 'Shelf load (mass)', 'lb', lambda o: o['inch']['load_lb'], 1, 'kg x 2.205'),
        R('F_lbf', 'Design load F', 'lbf', lambda o: o['inch']['F_lbf'], 1, 'N / 4.448'),
        R('M_lbfin', 'Moment M', 'lbf.in', lambda o: o['inch']['M_lbfin'], 1, 'N.mm / 4.448 / 25.4'),
        R('sigma_ksi', 'Bending stress', 'ksi', lambda o: o['inch']['sigma_ksi'], 2, 'MPa / 6.895'),
        R('droop_in', 'Front-edge droop', 'in', lambda o: o['inch']['droop'], 'in', 'mm / 25.4'),
        R('torque_lbfin', 'Illustrative torque', 'lbf.in', lambda o: o['inch']['torque_lbfin'], 1, 'N.m / 4.448 / 0.0254'),
    ] + [R(f'err{n}_{side}', f"Format error {n}: {'as written' if side == 'wrong' else 'correct form'}", '-',
           (lambda n, i: lambda o: o['format_errors'][n - 1][i])(n, i), 'str', 'seeded selection')
         for n in range(1, 6) for i, side in enumerate(('wrong', 'right'))]
      + [R('rel_t_in', 'Thickness t at the released t (D105)', 'in', rel_get('t_in'), 'in', 'rel_t / 25.4'),
         R('rel_sigma_ksi', 'Bending stress at the released t', 'ksi', rel_get('sigma_ksi'), 2, 'Ep06_rd_sigma / 6.895'),
         R('rel_droop', 'Front-edge droop at the released geometry (rel_t, rel_hole1)', 'mm', rel_get('droop'), 2, 'Ep06_rd_droop (released t and hole positions, D105)'),
         R('rel_droop_in', 'Front-edge droop at the released geometry', 'in', rel_get('droop_in'), 'in', 'rel_droop / 25.4')]
      + [R(f'rel_err{n}_{side}', f"Format error {n} at the released geometry: {'as written' if side == 'wrong' else 'correct form'}", '-',
           rel_get('format_errors', (n - 1, i)), 'str', 'seeded selection (same items as err1..5), released numbers')
         for n in range(1, 6) for i, side in enumerate(('wrong', 'right'))]))
    S.append(('Ep17', 'Ep 17 - flat pattern and DFM checks (per variant)', [
        f"K-factor {k:.2f} is the course value (key K_bend in facts_c4.json), the same as for the motor bracket; illustrative course value for 5052-H32 and low-carbon steel (it agrees with DIN 6935 for steel at R = t); the supplier confirms."], [
        R('A', 'Shelf flange A (outside)', 'mm', lambda o: o['A'], 1, 'depth - 20'),
        R('H', 'Wall flange H (outside)', 'mm', lambda o: fx['H'], 1, 'input'),
        R('R', 'Inside radius R = t', 'mm', lambda o: o['R'], 1),
        R('K', 'K-factor (course, K_bend)', '-', lambda o: k, 2, 'input from facts_c4.json K_bend'),
        R('BA', f'Bend allowance pi/2 (R + {k:.2f} t)', 'mm', lambda o: o['BA'], 2, 'pi/2 x (R + K t)'),
        R('flat', 'Flat length (A - t - R) + (H - t - R) + BA', 'mm', lambda o: o['flat'], 2),
        R('BD', 'Bend deduction A + H - flat', 'mm', lambda o: o['BD'], 2),
        R('bend_line', 'Bend line on the flat pattern from the wall-flange end (H - t - R) + BA/2', 'mm', lambda o: o['bend_line'], 1, '(shelf_H - t - R) + BA / 2, rounded to 0.1 (REF on the flat pattern)'),
        R('flat_1dp', 'Flat length as drawn (REF)', 'mm', lambda o: o['flat'], 1, 'flat rounded to 0.1'),
        R('htb_req', 'Hole-to-bend required (t+R) + 2.5t + R', 'mm', lambda o: o['htb_req'], 1),
        R('htb_edge', 'Upper hole edge from outside face', 'mm', lambda o: o['htb_edge'], 2, 'hole1 - clear / 2'),
        R('htb', 'Hole-to-bend check', '-', lambda o: o['htb'], 'str', 'PASS if edge >= required'),
        R('htb_shortfall', 'Hole-to-bend shortfall (FAIL only)', 'mm', lambda o: o['htb_shortfall'], 2, 'htb_req - htb_edge when the check fails; none when it passes'),
        R('min_flange', 'Minimum flange 4t', 'mm', lambda o: o['min_flange'], 1),
        R('flange_ok', 'Flange length check', '-', lambda o: o['flange_ok'], 'str', 'PASS if A and H >= 4t'),
    ]))
    S.append(('Ep19', 'Ep 19 - casting choice for the quantity (illustrative prices)', [], [
        R('qty', 'Quantity', 'brackets', lambda o: o['qty'], 'int', 'variant input'),
        R('breakeven', 'Break-even sand vs die = (die tooling - sand tooling) / (sand piece - die piece)', 'parts', lambda o: o['cast_breakeven'], 0),
        R('cast_choice', 'Casting choice', '-', lambda o: o['cast_choice'], 'str', 'die casting if qty > break-even'),
    ]))
    S.append(('Ep20', 'Ep 20 / Ep 22 - inputs for the DFA audit and the ECR / ECO', [], [
        R('fails', 'Checks that fail as given', '-', lambda o: o['fails'], 'str', 'Ep 05, 06, 08, 13, 17 results'),
        R('ecr', 'Suggested ECR subject (Ep 22)', '-', lambda o: o['ecr'], 'str', 'one change per failed check'),
        R('closed_rel', 'Closed before release (in Rev A)', '-', lambda o: o['revA']['closed'] if o['revA'] else None, 'str', 'D109: failing as given and closed in Part 1/2 (Ep 06 redesign, Ep 08/12 thread, Ep 13 hole)'),
        R('open_rel', 'Still open at the review (Rev A)', '-', lambda o: o['revA']['open'] if o['revA'] else None, 'str', 'D109: washer-dependent joint (V1, V4), revA_htb_wc = FAIL, galvanic (V6)'),
    ]))
    g22 = lambda k: (lambda o: o['ep22'][k])
    S.append(('Ep22', 'Ep 22 - the change raised against Rev A (course decision D106; supplier data SAMPLE)', [], [
        R('kind', 'Change type', '-', g22('kind'), 'str', 'supplier_R / captive_washer / galvanic (given, D106, D108) or open_checks'),
        R('problem', 'Field problem (illustrative)', '-', g22('problem'), 'str', 'illustrative field reports (D106)'),
        R('ecr', 'Suggested ECR subject (replaces Ep20_ecr in Part 3)', '-', g22('ecr'), 'str', 'D106 R4'),
        R('sup_die', 'SAMPLE supplier die opening', 'mm', g22('sup_die'), 0, 'sup_die_factor x rel_t'),
        R('sup_R', 'SAMPLE supplier inside R', 'mm', g22('sup_R'), 1, 'sup_R_ratio x die opening, rounded up to 0.5'),
        R('htb_req', 'Hole-to-bend required (at the supplier R or rel R)', 'mm', g22('htb_req'), 1, '(t + R) + 2.5t + R'),
        R('htb_edge', 'Upper hole edge before the change (or at the larger hole)', 'mm', g22('htb_edge'), 2, 'hole1 - hole / 2'),
        R('htb', 'Hole-to-bend check', '-', g22('htb'), 'str', 'PASS if edge >= required'),
        R('htb_margin', 'Hole-to-bend margin', 'mm', g22('htb_margin'), 2, 'edge - required'),
        R('shortfall', 'Hole-to-bend shortfall at the supplier R', 'mm', g22('shortfall'), 2, 'required - edge'),
        R('R_max', 'Largest inside R that passes after the change', 'mm', g22('R_max'), 1, '(edge - 3.5t) / 2, rounded down to 0.1'),
        R('hole_d', 'Clearance hole after the change', 'mm', g22('hole_d'), 1, 'Ep13_hole_nominal_needed rounded up to 0.1'),
        R('hole1', 'Upper hole after the change', 'mm', g22('hole1'), 1, 'max(rel_hole1, required + clear/2 rounded up to 0.5)'),
        R('hole2', 'Lower hole after the change', 'mm', g22('hole2'), 1, 'hole1 + 55 (pitch kept)'),
        R('raise', 'Shelf rises by', 'mm', g22('raise'), 1, 'new hole1 - rel_hole1'),
        R('htb_new_edge', 'Upper hole edge after the move', 'mm', g22('htb_new_edge'), 2, 'new hole1 - clear/2'),
        R('htb_new', 'Hole-to-bend after the move', '-', g22('htb_new'), 'str', 'PASS if edge >= required'),
        R('BA', 'Bend allowance at the supplier R', 'mm', g22('BA'), 2, 'pi/2 (R + K t)'),
        R('flat', 'Flat length at the supplier R (REF)', 'mm', g22('flat'), 1, '(A - t - R) + (H - t - R) + BA'),
        R('callout_bend', 'Bend note after the change', '-', g22('callout_bend'), 'str', 'INSIDE R = supplier R'),
        R('droop', 'Droop with the moved holes', 'mm', g22('droop'), 2, 'Ep 06 model, Lv = new hole1'),
        R('T1', 'Upper screw tension with the moved holes', 'N', g22('T1'), 1, 'M y1 / (y1^2 + y2^2)'),
        R('FOS_net', 'Net-section FOS at the released t', '-', g22('FOS_net'), 2, 'Sy / sigma_net'),
        R('screw_check', 'Screw check after the change', '-', g22('screw_check'), 'str', 'Ep 08 rule'),
        R('upper_swing', 'Room above the upper screw after the change (Ep 21)', 'mm', g22('upper_swing'), 1, 'new hole1 - t'),
        R('lower_edge', 'Lower-hole ligament to the flange end', 'mm', g22('lower_edge'), 2, 'H - hole2 - clear/2'),
        R('lig_ok', 'Ligament check (>= 1.5t)', '-', g22('lig_ok'), 'str', 'lower_edge >= lig_factor x t'),
        R('fix', 'Model change (fallback: drill after forming)', '-', g22('fix'), 'str', 'move the holes if htb, droop and ligament pass'),
        R('part_number', 'New part number (form-fit change)', '-', g22('part_number'), 'str', 'next free dash number (never -7, never reused)'),
        R('screw', 'Kit screw after the change', '-', g22('screw'), 'str', 'shortest preferred length with need <= L - t <= thread depth - 1'),
        R('eng', 'Engagement with the flange screw (no washer)', 'mm', g22('eng'), 1, 'L - rel_t'),
        R('washer_od', 'Captive washer outside diameter', 'mm', g22('washer_od'), 1, '= shelf_washer_od (ISO 7089 size 5)'),
        R('R_max_wc', 'Largest inside R that passes after the move, at the drawing tolerances', 'mm', g22('R_max_wc'), 1, '(new edge - wc_loss - 3.5t) / 2, rounded down'),
        R('htb_new_edge_wc', 'New upper hole edge, worst case', 'mm', g22('htb_new_edge_wc'), 2, 'htb_new_edge - shelf_htb_wc_loss'),
        R('htb_new_wc', 'Hole-to-bend after the move at the drawing tolerances (supplier R)', '-', g22('htb_new_wc'), 'str', 'PASS if worst-case edge >= required'),
        R('htb_R_low', 'Hole-to-bend after the move at the low end of the R range (R = t)', '-', g22('htb_R_low'), 'str', 'edge >= 3.5t + 2t'),
        R('flat_R_low', 'Flat length at R = t (REF, low end of the R range)', 'mm', g22('flat_R_low'), 1, '(A - t - R) + (H - t - R) + BA at R = t'),
        R('fa_check', 'First-article check', '-', g22('fa_check'), 'str', 'inside R measured against the bend note (D108)'),
        R('htb_supR_req', 'Required at the SAMPLE supplier R (larger hole)', 'mm', g22('htb_supR_req'), 1, '= rel_htb_req_supR'),
        R('htb_supR', 'Larger hole at the SAMPLE supplier R', '-', g22('htb_supR'), 'str', 'PASS if edge >= required'),
        R('alt_hole1', 'Moved holes (larger hole fails at the supplier R or the drawing tolerances): upper hole', 'mm', g22('alt_hole1'), 1, 'required at sup R + d/2 + wc_loss, rounded up to 0.5'),
        R('alt_hole2', 'Moved holes: lower hole', 'mm', g22('alt_hole2'), 1, 'alt_hole1 + 55'),
        R('alt_part_number', 'Moved holes: new part number', '-', g22('alt_part_number'), 'str', 'next free dash number after V5'),
        R('alt_raise', 'Moved holes: shelf rises by', 'mm', g22('alt_raise'), 1, 'alt_hole1 - rel_hole1'),
        R('alt_lower_edge', 'Moved holes: lower-hole ligament', 'mm', g22('alt_lower_edge'), 2, 'H - alt_hole2 - hole / 2'),
        R('alt_lig_ok', 'Moved holes: ligament >= 1.5t', '-', g22('alt_lig_ok'), 'str', 'lower edge >= lig_factor x t'),
        R('alt_droop', 'Moved holes: droop', 'mm', g22('alt_droop'), 2, 'Ep 06 model, Lv = alt_hole1'),
        R('alt_upper_swing', 'Moved holes: room above the upper screw (Ep 21)', 'mm', g22('alt_upper_swing'), 1, 'alt_hole1 - t'),
        R('alt_edge_wc', 'Moved holes: upper hole edge, worst case', 'mm', g22('alt_edge_wc'), 2, 'alt_hole1 - hole / 2 - wc_loss'),
        R('alt_htb_wc', 'Moved holes: hole-to-bend at the supplier R and the drawing tolerances', '-', g22('alt_htb_wc'), 'str', 'PASS if worst-case edge >= required at sup R'),
        R('alt_ok', 'Moved holes: hole-to-bend, ligament and droop all pass', '-', g22('alt_ok'), 'str', 'PASS if all three pass'),
        R('hole_note', 'Hole note after the change (holes made after forming)', '-', g22('hole_note'), 'str', 'D109'),
        R('bendzone_clear', 'Hole edge clear of the bend zone: edge - (t + R high)', 'mm', g22('bendzone_clear'), 2, 'revA_htb_edge - (rel_t + sup_R)'),
        R('alt_thread_need', 'Rejected alternative: thread depth needed without the washer', 'mm', g22('alt_thread_need'), 0, 'nowasher_eng + 1 (D109)'),
        R('tw_min', 'Insulating washer, thinnest that does not bottom', 'mm', g22('tw_min'), 1, 'nowasher_eng - (revA_thread_depth - 1) (D133)'),
        R('tw_max', 'Insulating washer, thickest that keeps the engagement', 'mm', g22('tw_max'), 1, 'nowasher_eng - engagement needed (D133)'),
    ]))
    gb = lambda k: (lambda o: o['ep22']['b'][k])
    S.append(('Ep22b', 'Ep 22 - second ECO of V6: hole-to-bend after the supplier sample report (D109; supplier data SAMPLE)', [], [
        R('problem', 'Supplier sample report (illustrative)', '-', gb('problem'), 'str', 'D109'),
        R('sup_die', 'SAMPLE supplier die opening', 'mm', gb('sup_die'), 0, '= rel_sup_die'),
        R('sup_R', 'SAMPLE supplier inside R', 'mm', gb('sup_R'), 1, '= rel_sup_R'),
        R('htb_req', 'Hole-to-bend required at the supplier R', 'mm', gb('htb_req'), 1, '3.5t + 2 sup_R'),
        R('htb_edge', 'Upper hole edge (Rev A)', 'mm', gb('htb_edge'), 2, '= revA_htb_edge'),
        R('htb', 'Hole-to-bend at the supplier R', '-', gb('htb'), 'str', 'PASS if edge >= required'),
        R('shortfall', 'Shortfall at the supplier R', 'mm', gb('shortfall'), 2, 'required - edge'),
        R('fix', 'Change chosen', '-', gb('fix'), 'str', 'shelf_htb_fix_rule step 4 (recorded judgement at the volume)'),
        R('callout_bend', 'Bend note after the change', '-', gb('callout_bend'), 'str', 'INSIDE R = t TO supplier R'),
        R('hole_note', 'Hole note after the change', '-', gb('hole_note'), 'str', 'D109'),
        R('BA', 'Bend allowance at the supplier R', 'mm', gb('BA'), 2, 'pi/2 (R + K t)'),
        R('flat', 'Flat length at the supplier R (REF)', 'mm', gb('flat'), 2, '(A - t - R) + (H - t - R) + BA'),
        R('flat_R_low', 'Flat length at R = t (REF)', 'mm', gb('flat_R_low'), 2, 'same at R = t'),
        R('bendzone_clear', 'Hole edge clear of the bend zone', 'mm', gb('bendzone_clear'), 2, 'edge - (t + sup_R)'),
        R('part_number', 'Part number after the change', '-', gb('part_number'), 'str', 'Rev B, same part number'),
        R('ecr', 'ECO text', '-', gb('ecr'), 'str', 'D109 section 5'),
    ]))
    ga = lambda k: (lambda o: o['revA'][k] if o['revA'] else None)
    S.append(('revA', "The learner's released Rev A (D109): released geometry + Ep 13 hole size + Ep 12 thread", [
        'Rev A is released at the end of Part 2: C4-DWG-009 table 1 plus the Ep 13 hole size (note 8); the upright carries the Ep 12 thread callout.'], [
        R('hole_d', 'Clearance hole at Rev A', 'mm', ga('hole_d'), 1, '= Ep 13 nominal needed rounded up to 0.1, at least shelf_clear'),
        R('hole_callout', 'Hole callout at Rev A', '-', ga('hole_callout'), 'str', '= Ep13_hole_callout'),
        R('htb_edge', 'Upper hole edge at Rev A', 'mm', ga('htb_edge'), 2, 'rel_hole1 - revA_hole_d / 2'),
        R('htb_margin', 'Hole-to-bend margin at nominal sizes', 'mm', ga('htb_margin'), 2, 'revA_htb_edge - rel_htb_req'),
        R('htb_R_max', 'Largest inside R that passes at nominal sizes', 'mm', ga('htb_R_max'), 1, '(edge - 3.5t) / 2, rounded down to 0.1'),
        R('htb_edge_wc', 'Upper hole edge at the drawing tolerances', 'mm', ga('htb_edge_wc'), 2, 'revA_htb_edge - shelf_htb_wc_loss'),
        R('htb_margin_wc', 'Margin at the drawing tolerances', 'mm', ga('htb_margin_wc'), 2, 'edge_wc - rel_htb_req'),
        R('htb_wc', 'Hole-to-bend at the drawing tolerances', '-', ga('htb_wc'), 'str', 'PASS if edge_wc >= required'),
        R('htb_R_max_wc', 'Largest inside R that passes at the drawing tolerances (FAIL only)', 'mm', ga('htb_R_max_wc'), 1, '(edge_wc - 3.5t) / 2, rounded down; < t wherever wc = FAIL'),
        R('query_tight', 'Supplier query line (wc = FAIL only)', '-', ga('query_tight'), 'str', 'D109: replaces rel_query_tight in Ep 17'),
        R('thread_depth', 'Upright thread depth at Rev A', 'mm', ga('thread_depth'), 0, 'from Ep12_callout_thread'),
        R('drill_depth', 'Upright tap-drill depth at Rev A', 'mm', ga('drill_depth'), 0, 'thread + 3'),
        R('eng', 'Engagement at Rev A with the washer', 'mm', ga('eng'), 1, 'L - t - washer'),
        R('screw_check', 'Screw check at Rev A', '-', ga('screw_check'), 'str', 'need <= eng <= thread - 1'),
    ]))
    S.append(('nowasher', 'Ep 20 task 1 re-check: the joint without the loose washer (D109)', [], [
        R('eng', 'Engagement without the washer', 'mm', ga('nowasher_eng'), 1, 'L - t'),
        R('check', 'Bottoming check without the washer', '-', ga('nowasher_check'), 'str', 'thread >= eng + 1: PASS; equal: PASS (limit); else FAIL'),
    ]))
    S.append(('rel', 'Released geometry from Part 1 (course decision D105): every Part 2 / Part 3 drawing value', [
        'Thickness = Ep 06 redesign t; holes as placed by the Ep 06 redesign (moved down for V3 and V5, pitch kept); material = Ep 07 choice. C4-DWG-009 tabulates these values.'], [
        R('t', 'Released thickness t', 'mm', rel_get('t'), 1, '= Ep06_rd_t'),
        R('hole1', 'Upper hole from top outside face', 'mm', rel_get('hole1'), 1, '= Ep06_rd_hole1'),
        R('hole2', 'Lower hole from top outside face', 'mm', rel_get('hole2'), 1, '= Ep06_rd_hole2 (pitch kept)'),
        R('moved', 'Holes moved from the brief?', '-', rel_get('moved'), 'str', '= Ep06_rd_moved'),
        R('R', 'Inside radius R = t', 'mm', rel_get('R'), 1, 'rel_t x R_over_t'),
        R('BA', 'Bend allowance', 'mm', rel_get('BA'), 2, 'pi/2 x (R + K t) at rel_t'),
        R('flat', 'Flat length', 'mm', rel_get('flat'), 2, '(A - t - R) + (H - t - R) + BA at rel_t'),
        R('flat_1dp', 'Flat length as drawn (REF)', 'mm', rel_get('flat'), 1, 'rel_flat rounded to 0.1'),
        R('bend_line', 'Bend line from the wall-flange end (REF)', 'mm', rel_get('bend_line'), 1, '(H - t - R) + BA / 2 at rel_t'),
        R('BD', 'Bend deduction', 'mm', rel_get('BD'), 2, 'A + H - rel_flat'),
        R('htb_req', 'Hole-to-bend required', 'mm', rel_get('htb_req'), 1, '(t+R) + 2.5t + R at rel_t'),
        R('htb_edge', 'Upper hole edge from outside face', 'mm', rel_get('htb_edge'), 2, 'rel_hole1 - clear / 2'),
        R('htb', 'Hole-to-bend check', '-', rel_get('htb'), 'str', 'PASS if edge >= required'),
        R('min_flange', 'Minimum flange 4t', 'mm', rel_get('min_flange'), 1),
        R('flange_ok', 'Flange length check', '-', rel_get('flange_ok'), 'str', 'PASS if A and H >= 4t'),
        R('mass', 'Mass (Ep 07 choice, released geometry)', 'g', rel_get('mass'), 0, 'rel_flat x b x rel_t x density of the Ep 07 choice'),
        R('material_callout', 'Material callout (field 7) at the released t', '-', rel_get('material_callout'), 'str', 'course decisions D101, D105'),
        R('finish_callout', 'Finish callout (field 8)', '-', rel_get('finish_callout'), 'str', '= Ep11_finish_callout (does not depend on t)'),
        R('callout_bend', 'Bend note', '-', rel_get('callout_bend'), 'str', 'R = rel_t'),
        R('callout_thread', 'Upright thread (ISO form) for the released screw', '-', rel_get('callout_thread'), 'str', 'Ep 08 rule at rel_t'),
        R('callout_thread_asme', 'Upright thread (ASME form)', '-', rel_get('callout_thread_asme'), 'str', 'same depths; pitch shelf_P_M5'),
        R('screw', 'Screw at the released t', '-', rel_get('screw'), 'str', 'Ep 08 rule at rel_t (= Ep06_rd_screw)'),
        R('screw_check', 'Screw check at the released t', '-', rel_get('screw_check'), 'str', 'Ep 08 rule at rel_t'),
        R('upper_swing', 'Room from the upper screw axis to the underside of the shelf flange (Ep 21)', 'mm', rel_get('upper_swing'), 1, 'rel_hole1 - rel_t'),
        R('htb_brief', 'Back-check: brief hole position at the released t (D106)', '-', rel_get('htb_brief'), 'str', 'Ep 17 rule with shelf_hole1 at rel_t'),
        R('htb_shortfall_brief', 'Back-check shortfall (FAIL only)', 'mm', rel_get('htb_shortfall_brief'), 2, 'rel_htb_req - (shelf_hole1 - clear/2) when the back-check fails'),
        R('move', 'Holes moved by the Part 1 redesign', 'mm', rel_get('move'), 1, 'rel_hole1 - shelf_hole1'),
        R('htb_margin', 'Hole-to-bend margin at the released geometry', 'mm', rel_get('htb_margin'), 2, 'rel_htb_edge - rel_htb_req'),
        R('htb_R_max', 'Largest supplier inside R that still passes', 'mm', rel_get('htb_R_max'), 1, '(rel_htb_edge - 3.5 rel_t) / 2, rounded down to 0.1'),
        R('htb_tight', 'Hole-to-bend tight (ask the supplier to confirm R)?', '-', rel_get('htb_tight'), 'str', 'yes if R_max < rel_R + shelf_htb_tight_band'),
        R('htb_edge_wc', 'Upper hole edge, worst case at the drawing tolerances', 'mm', rel_get('htb_edge_wc'), 2, 'rel_htb_edge - shelf_htb_wc_loss (D108)'),
        R('htb_margin_wc', 'Hole-to-bend margin, worst case', 'mm', rel_get('htb_margin_wc'), 2, 'rel_htb_edge_wc - rel_htb_req'),
        R('htb_wc', 'Hole-to-bend at the drawing tolerances', '-', rel_get('htb_wc'), 'str', 'PASS if worst-case edge >= required'),
        R('sup_die', 'Course SAMPLE supplier die opening at rel_t', 'mm', rel_get('sup_die'), 0, 'shelf_sup_die_factor x rel_t'),
        R('sup_R', 'Course SAMPLE supplier inside R at rel_t', 'mm', rel_get('sup_R'), 1, 'shelf_sup_R_ratio x die, rounded up to 0.5'),
        R('htb_req_supR', 'Hole-to-bend required at the SAMPLE supplier R', 'mm', rel_get('htb_req_supR'), 1, '3.5 rel_t + 2 rel_sup_R'),
        R('htb_supR', 'Hole-to-bend at the SAMPLE supplier R', '-', rel_get('htb_supR'), 'str', 'PASS if rel_htb_edge >= required'),
        R('query_tight', 'Supplier query line for a tight variant', '-', rel_get('query_tight'), 'str', 'asks for R and thickness tolerance (D108)'),
    ]))
    S.append(('Ep21', 'Ep 21 - tool access at the upper screw', [], [
        R('upper_swing', 'Room from the upper screw axis to the underside of the shelf flange', 'mm', lambda o: o['upper_swing'], 1, 'shelf_hole1 - t'),
    ]))
    return S


def fixed_spec(fx=FIXED):
    """Fixed inputs: (key, label, value, unit, nd, source)."""
    al = MATERIALS[BASE_MAT]
    return [
        ('b', 'Bracket width b (both flanges)', fx['b'], 'mm', 1, 'Brief'),
        ('H', 'Wall flange outside height H', fx['H'], 'mm', 1, 'Brief'),
        ('front_gap', 'Shelf flange stops short of shelf front', fx['front_gap'], 'mm', 1, 'Brief (A = depth - 20)'),
        ('hole1', 'Upper screw hole from top outside face', fx['hole1'], 'mm', 1, 'Brief'),
        ('hole2', 'Lower screw hole from top outside face', fx['hole2'], 'mm', 1, 'Brief'),
        ('n_brackets', 'Brackets per shelf', fx['n_brackets'], 'brackets', 'int', 'Brief'),
        ('g', 'Gravity g', G, 'm/s^2', 2, 'Brief'),
        ('k_design', 'Design factor on shelf load', fx['k_design'], '-', 1, 'Illustrative; course default accepted by the course team'),
        ('FOS_gate', 'FOS gate on yield', fx['gate'], '-', 1, 'Same as course PDR gate'),
        ('droop_limit', 'Front-edge droop limit (PDS)', fx['droop_limit'], 'mm', 1, 'Illustrative; course default accepted by the course team'),
        ('base_material', 'Base bracket material', BASE_MAT, '', 'str', 'Brief'),
        ('Sy', '5052-H32 yield strength Sy', al['Sy'], 'MPa', 0, 'Typical value'),
        ('Sy_min', '5052-H32 specified minimum yield Sy_min', fx['Sy_min'], 'MPa', 1, 'Specified minimum (same value as the lesson, facts_c4.json Sy_min)'),
        ('E', '5052-H32 elastic modulus E', al['E'], 'MPa', 0, 'Typical value'),
        ('screws', 'Screws', 'M5 class 8.8, zinc-flake coated, plain washer 1.0 mm', '', 'str', 'Brief'),
        ('washer', 'Washer thickness', fx['washer'], 'mm', 1, 'Brief'),
        ('washer_od', 'Washer outside diameter', fx['washer_od'], 'mm', 1, 'ISO 7089 size 5 (M5), d2'),
        ('washer_id', 'Washer hole diameter', fx['washer_id'], 'mm', 1, 'ISO 7089 size 5 (M5), d1 min'),
        ('htb_tight_band', 'Hole-to-bend tight band on R', fx['htb_tight_band'], 'mm', 1, 'course rule (D106)'),
        ('sup_die_factor', 'SAMPLE supplier die opening / t', fx['sup_die_factor'], '-', 0, 'SAMPLE supplier reply (D106)'),
        ('sup_R_ratio', 'SAMPLE inside R / die opening (air bend)', fx['sup_R_ratio'], '-', 2, 'typical rule; the supplier tooling wins'),
        ('lig_factor', 'Lower-hole ligament >= this x t', fx['lig_factor'], '-', 1, 'typical; the supplier guide wins'),
        ('sems_std', 'Screw and captive plain washer assembly standard', fx['sems_std'], '', 'str', 'D108: hexagon socket head screw + plain washer'),
        ('upright_part_number', 'Shelf upright part number', fx['upright_part_number'], '', 'str', 'identifier (D108): the upright gets a part number before a revision'),
        ('htb_wc_loss', 'Hole-to-bend edge lost at the drawing tolerances', wc_loss(fx), 'mm', 2, 'tol_gen_m (profile 0.4, half) + tol_laser (position zone radius) + clear_tol / 2', 'shelf_prof_outline / 2 + shelf_pos_holes / 2 + shelf_clear_tol / 2'),
        ('htb_fix_rule', 'Hole-to-bend fix rule (Ep 17 step 6, Ep 22)', HTB_FIX_RULE, '', 'str', 'D109 (E2, X1, L1)'),
        ('htb_basis_note', 'Label for hole-to-bend margins', 'Hole-to-bend margins are at nominal sizes; at the drawing tolerances (profile, position, hole size) the edge is shelf_htb_wc_loss smaller, and a thicker sheet within its mill tolerance raises the required distance by 3.5 x the extra thickness.', '', 'str', 'D108 (E2)'),
        ('Ep17_RK_note', 'Ep 17 note on R and K', 'The course R = t and K = 0.33 are illustrative course values for both 5052-H32 and low-carbon steel (K = 0.33 agrees with DIN 6935 for steel at R = t); your supplier\'s values for your material and thickness win.', '', 'str', 'D108 (E2 #10)'),
        ('Ep19_die_cast_note', 'Ep 19 note on die casting', 'Die casting means an aluminium or zinc casting alloy, not your sheet steel: the material changes, so the Ep 06 strength and stiffness checks and the finish are re-run. Sand-cast steel needs much thicker walls than your sheet.', '', 'str', 'D108 (E2 #6)'),
        ('part_next_dash', 'Next free dash number', fx['part_next_dash'], '', 'int', '-1..-6 course variants, -7 own variant; never reused'),
        ('clear', 'Clearance hole (nominal)', fx['clear'], 'mm', 1, 'Brief'),
        ('clear_tol', 'Clearance hole size tolerance (+/-)', fx['clear_tol'], 'mm', 2, 'Typical, laser-cut; confirm with supplier (brief)'),
        ('bend_tol', 'Bend angle tolerance (+/-)', fx['bend_tol'], 'deg', 0, 'Typical press-brake capability (brief)'),
        ('tap_depth', 'Tapped thread depth in upright', fx['tap_depth'], 'mm', 0, 'Brief'),
        ('tap_drill', 'Tap drill diameter', fx['tap_drill'], 'mm', 1, 'Brief'),
        ('drill_depth', 'Tap drill depth', fx['drill_depth'], 'mm', 0, 'Brief'),
        ('eng_steel', 'Engagement rule in steel', ENG_STEEL, 'D', 0, 'Course rule (Ep 08)'),
        ('eng_6061', 'Engagement rule in 6061-T6', UPRIGHTS['6061-T6'], 'D', 1, 'Course rule (Ep 08)'),
        ('eng_6063', 'Engagement rule in 6063-T5', UPRIGHTS['6063-T5'], 'D', 1, 'Course rule (Ep 08): softer alloys such as 6063-T5'),
        ('eng_rule', 'Engagement rule, course wording', ENG_RULE, '', 'str', 'Course rule (Ep 08); published guides vary, the screw or insert maker wins'),
        ('ckpt_FOS', 'Ep 05 checkpoint: FOS exactly on the gate', CKPT_FOS, '-', 2, 'Checkpoint value (illustrative)'),
        ('screw_lengths', 'Preferred M5 lengths (SAMPLE card)', ', '.join(str(x) for x in SCREW_LENGTHS), 'mm', 'str', 'Course SAMPLE list (confirmed by the course team)'),
        ('thicknesses', 'Stock thicknesses', ', '.join(f'{x:.1f}' for x in THICKNESSES), 'mm', 'str', 'Brief'),
        ('preload', 'Illustrative preload per M5 screw', fx['preload'], 'N', 0, 'Same as Facts_C4'),
        ('tol_laser', 'Bracket hole position tolerance (+/-)', fx['tol_laser'], 'mm', 2, 'Typical'),
        ('tol_cnc', 'Upright hole position tolerance, CNC (+/-)', fx['tol_cnc'], 'mm', 2, 'Typical'),
        ('tol_hand', 'Upright hole position tolerance, by hand (+/-)', fx['tol_hand'], 'mm', 2, 'Illustrative'),
        ('hand_qty', 'Upright holes CNC-drilled from this quantity', fx['hand_qty'], 'parts', 'int', 'Illustrative'),
        ('K_bend', 'K-factor (course value)', fx['K_factor'], '-', 2, 'facts_c4.json K_bend; illustrative, supplier confirms'),
        ('P_M5', 'M5 coarse pitch', fx['P_M5'], 'mm', 1, 'ISO 261 coarse pitch'),
        ('Ep13_zone_cnc', 'Upright hole position zone, CNC-drilled (diameter)', 2 * fx['tol_cnc'], 'mm', 1, '2 x tol_cnc (checker M2: zone form on the Ep 13 card)', '2 x shelf_tol_cnc'),
        ('Ep13_zone_hand', 'Upright hole position zone, drilled by hand (diameter)', 2 * fx['tol_hand'], 'mm', 1, '2 x tol_hand (checker M2: zone form on the Ep 13 card)', '2 x shelf_tol_hand'),
        ('pos_holes', 'Position zone of the clearance holes (diameter)', 2 * fx['tol_laser'], 'mm', 1, '2 x tol_laser (laser-cut, typical)', '2 x shelf_tol_laser'),
        ('pos_frame', 'Position frame of the clearance holes', f"{chr(0x2316)} | {chr(216)}{2 * fx['tol_laser']:.1f} {chr(0x24C2)} CZ | A", '', 'str', 'Ep 14 model answer', 'position, diameter zone 2 x shelf_tol_laser, MMC, common zone, datum A'),
        ('prof_outline', 'Profile tolerance of the outline', 2 * fx['tol_gen_m'], 'mm', 1, '2 x tol_gen_m (ISO 2768-m +/-0.2, over 6 up to 30 mm), as the profile on C4-DWG-001', '2 x tol_gen_m (facts_c4.json)'),
        ('basic_hole_column', 'Basic size: side edge to the hole column', fx['b'] / 2, 'mm', 0, 'b / 2 (holes on the centre line)', 'shelf_b / 2'),
        ('dwg_id', 'Shelf bracket detail drawing ID', 'C4-DWG-009', '', 'str', 'identifier (drawing ID register)'),
        ('dwg_title', 'Title block field 1', 'SHELF BRACKET', '', 'str', 'identifier'),
        ('dwg_owner', 'Title block field 2', 'ENGXTECH - fictional company', '', 'str', 'identifier (same fictional company as C4-DWG-001)'),
        ('part_number', 'Title block field 3 (tabulated SHB-100-1 ... SHB-100-6 = V1 ... V6)', 'SHB-100', '', 'str', 'identifier; dash number = variant'),
        ('dwg_sheet', 'Title block field 5', '1 OF 1', '', 'str', 'identifier'),
        ('dwg_size', 'Title block field 6', 'A2', '', 'str', 'identifier'),
        ('dwg_scale', 'Title block field 9', '1:1 (views drawn for SHB-100-1; detail Y 3:1; isometric 1:2)', '', 'str', 'identifier'),
        ('gen_tol', 'Title block field 12', 'ISO 2768-1:1989 - m; ISO 8015:2011', '', 'str', 'identifier, as on C4-DWG-001'),
        ('dwg_date', 'Title block field 16 (issue date)', '2026-11-14', '', 'str', 'identifier (issue date of the shelf sheets)'),
        ('cast_draft_sand', 'Casting draft, sand (typical; the foundry guide wins)', CAST['draft_sand'], 'deg', 'str', 'typical range'),
        ('cast_draft_die', 'Casting draft, die (typical; the foundry guide wins)', CAST['draft_die'], 'deg', 'str', 'typical range'),
        ('cast_wall_min_sand', 'Minimum wall, sand casting (typical)', CAST['wall_sand'], 'mm', 'str', 'typical range'),
        ('cast_wall_min_die', 'Minimum wall, die casting (typical)', CAST['wall_die'], 'mm', 'str', 'typical range'),
        ('cast_stock', 'Machining stock on cast faces (typical)', CAST['stock'], 'mm', 'str', 'typical range'),
        ('Ep20_kit', 'DFA kit per bracket: 1 bracket + 1 screw and 1 washer per hole', KIT['per_bracket'], 'parts', 'int', 'Ep 20 DFA', '1 + 2 x holes per bracket'),
        ('Ep20_kit_after', 'DFA kit per bracket with flanged-head screws (no washers)', KIT['after'], 'parts', 'int', 'Ep 20 DFA', '1 + holes per bracket'),
        ('Ep20_kit_shelf', 'DFA kit per shelf', KIT['per_bracket'] * fx['n_brackets'], 'parts', 'int', 'Ep 20 DFA', 'shelf_Ep20_kit x shelf_n_brackets'),
        ('Ep20_kit_after_shelf', 'DFA kit per shelf with flanged-head screws', KIT['after'] * fx['n_brackets'], 'parts', 'int', 'Ep 20 DFA', 'shelf_Ep20_kit_after x shelf_n_brackets'),
        ('cr_t_max', 'Thickest steel bought as cold-rolled sheet (thicker: hot-rolled, pickled and oiled)', fx['cr_t_max'], 'mm', 1, 'course assumption; the stockist confirms'),
        ('powder_um', 'Polyester powder coat over zinc, minimum', fx['powder_um'], 'um', 0, 'typical; the coater confirms'),
        ('powder_um_max', 'Polyester powder coat over zinc, maximum', fx['powder_um_max'], 'um', 0, 'typical upper limit for one coat; the coater confirms'),
        ('powder_ral', 'Powder colour (RAL)', f"RAL {fx['powder_ral']}", '', 'str', 'course decision D103: black semi-matt, a common stock powder'),
        ('powder_gloss', 'Powder gloss at 60 deg (ISO 2813)', fx['powder_gloss'], 'GU', 'int', 'course decision D103: semi-matt; the powder data sheet states it'),
        ('powder_gloss_tol', 'Powder gloss tolerance (+/-)', fx['powder_gloss_tol'], 'GU', 'int', 'course decision D103 (typical powder-maker band)'),
        ('a1011_t_max', 'Thickest sheet in ASTM A1011 (0.230 in)', fx['a1011_t_max'], 'mm', 1, 'ASTM A1011/A1011M scope'),
        ('Ep11_note_hot_rolled', 'Teaching line: why thick steel is bought hot-rolled (V5)',
         f"Above {fx['cr_t_max']:g} mm, low-carbon steel sheet is normally bought hot-rolled, pickled and oiled (ASTM A1011/A1011M, sheet up to {fx['a1011_t_max']:.1f} mm), "
         "not cold-rolled (ASTM A1008/A1008M). SS Grade 30 [205] has the same specified minimum yield in both standards, so every FOS stays the same; pickling removes the mill scale, so the sheet plates well. "
         "A1008 at this thickness is not wrong if a stockist has it.", '', 'str', 'course decision D101 (course assumption shelf_cr_t_max; the stockist confirms)'),
        ('Ep11_note_powder_joint', 'Teaching line: keep powder out of the clamped joint (V2)',
         f"Powder left under the screw heads and on the face against the upright sits inside the clamped joint: {fx['powder_um']:.0f}-{fx['powder_um_max']:.0f} {chr(181)}m of polymer creeps under the {fx['preload']:.0f} N preload and the preload relaxes. "
         "On a working joint, mask those faces (or the whole clamp area) as well as the holes. On this shelf the screw tension from the load is a few percent of the preload (Ep 08, T1 / preload), so the joint stays closed and the course masks only the 2 holes.",
         '', 'str', 'course decision D101; from shelf_powder_um, shelf_powder_um_max, shelf_preload'),
        ('Ep11_note_thread_sealant', 'Teaching line: break the galvanic pair at the threads (V6)',
         "In salt air the pair that matters is the steel screw in the bare aluminium tapped hole of the upright. Insulating washers under the heads do not break it: the threads still touch. "
         "Put a sealant on the screw threads as well, so no salt water can bridge screw and upright.", '', 'str', 'course decision D101'),
    ] + fixed_spec_ep03_ep07(fx)


CAST = dict(draft_sand='1-3', draft_die='0.5-2', wall_sand='3-5', wall_die='1.5-2.5', stock='1.5-3')   # typical casting rules (Ep 19); the foundry guide wins
KIT = dict(per_bracket=1 + 2 * len(('hole1', 'hole2')), after=1 + len(('hole1', 'hole2')))   # Ep 20 DFA: one screw and one washer per hole


def fixed_spec_ep03_ep07(fx=FIXED):
    """Fixed values the Ep 03 and Ep 07 worksheets print (prices, weights, score rules, material properties).
    Optional 7th element = JSON formula (default 'input')."""
    rows = []
    for name, (tool, pc, tag) in CONCEPTS.items():
        rows += [(f'Ep03_tooling_{tag}', f'Ep 03 tooling: {name}', tool, 'cost units', 0, 'Illustrative price, not a quote', 'input (illustrative price, not a quote)'),
                 (f'Ep03_piece_{tag}', f'Ep 03 piece price: {name}', pc, 'cost units', 2, 'Illustrative price, not a quote', 'input (illustrative price, not a quote)')]
    for (k, w), c in zip(WEIGHTS.items(), CRIT):
        rows.append((f'Ep07_w_{k}', f'Ep 07 course reference weight: {c}', w, '-', 2, 'Course reference weights (sum 1.00)', 'input (course reference weight)'))
    for lab, name, rules, unit, nd, src in (
            ('str', 'strength score {s} if FOS >=', SCORE_STR, '-', 1, 'Score rule; 2 x FOS gate, FOS gate, 1.5'),
            ('stf', 'stiffness score {s} if droop <=', SCORE_STF, 'mm', 1, 'Score rule; 0.5, 1.0 and 1.5 x droop limit'),
            ('cost', 'cost score {s} if relative cost incl. finish <=', SCORE_COST, '-', 1, 'Score rule; illustrative')):
        for s, bound in rules:
            rows.append((f'Ep07_{lab}{s}', 'Ep 07 ' + name.format(s=s), bound, unit, nd, src + ' (else 1)', 'input (Ep 07 score rule; else score 1)'))
    for mat, mp in MATERIALS.items():
        kk = mp['key']
        rows += [(f'Ep07_proc_{kk}', f'Ep 07 process-fit score: {mat}', mp['form'], '-', 'int', 'Score rule (bends at R = t)', 'input (Ep 07 score rule)'),
                 (f'Ep07_relcost_{kk}', f'Ep 07 relative material cost (5052-H32 bare = 1.0): {mat}', mp['cost'], '-', 1, 'Illustrative', 'input (illustrative)')]
    for env, (env_name, per) in ENVS.items():
        for mat, (sc, finish, add) in per.items():
            kk = MATERIALS[mat]['key']
            rows += [(f'Ep07_corr_{env}_{kk}', f'Ep 07 corrosion score, {env_name}: {mat}, finish: {finish}', sc, '-', 'int', 'Course key (1 = out, the corrosion gate)', 'input (Ep 07 corrosion score with the finish shown)'),
                     (f'Ep07_finish_{env}_{kk}', f'Ep 07 finish cost added, {env_name}: {mat}', add, '-', 1, 'Illustrative', 'input (illustrative finish cost)')]
    for mat, mp in MATERIALS.items():
        kk = mp['key']
        rows += [(f'{kk}_Sy', f'{mat}: yield strength Sy', mp['Sy'], 'MPa', 0, 'Typical; see Material_Matrix_SAMPLE', MAT_SOURCE),
                 (f'{kk}_E', f'{mat}: elastic modulus E', mp['E'], 'MPa', 0, 'Typical; see Material_Matrix_SAMPLE', MAT_SOURCE),
                 (f'{kk}_rho', f'{mat}: density', mp['rho'], 'g/cm^3', 2, 'Typical; see Material_Matrix_SAMPLE', MAT_SOURCE)]
    return rows


ND = {}   # JSON key -> printed decimals (used by the CSV sync check)


def build(os_):
    """Returns (facts dict for JSON, rendered spec sections for the Markdown)."""
    facts = {}
    ND.clear()
    for key, label, val, unit, nd, src, *frm in fixed_spec():
        facts[f'shelf_{key}'] = entry(val, nd, unit, frm[0] if frm else 'input')
        ND[f'shelf_{key}'] = nd
        if nd == 'str': facts[f'shelf_{key}']['unit'] = unit
    for o in os_:
        p = f"V{o['v']}_"
        for key, val, unit, nd in (('name', o['name'], '', 'str'), ('load_kg', o['load_kg'], 'kg', 1), ('depth', o['depth'], 'mm', 0),
                                   ('t', o['t'], 'mm', 1), ('upright', o['upright'], '', 'str'), ('env', o['env_name'], '', 'str'),
                                   ('qty', o['qty'], 'brackets', 'int')):
            facts[p + key] = entry(val, nd, unit, 'variant input')
    sections = []
    for ep, head, intro, rows in spec():
        table_rows = []
        for key, label, unit, fn, nd, formula in rows:
            cells = []
            for o in os_:
                val = fn(o)
                facts[f"V{o['v']}_{ep}_{key}"] = entry(val, nd, unit, formula)
                ND[f"V{o['v']}_{ep}_{key}"] = nd
                cells.append(show(val, nd))
            table_rows.append([key, label, unit] + cells)
        sections.append((ep, head, intro, table_rows))
    return facts, sections


# ---------------------------------------------------------------- Markdown
TEXT_ONLY = {'Worksheet sentence (why this choice)'}   # long text: JSON + bullet list below the table, not a table row

def table(head, rows):
    out = ['| ' + ' | '.join(head) + ' |', '|' + '|'.join(['---'] * len(head)) + '|']
    out += ['| ' + ' | '.join(str(c) for c in r) + ' |' for r in rows]
    return out


def facts_md(os_, sections, title='Facts_C4_shelf', json_name='facts_c4_shelf.json'):
    fx = FIXED
    V = [f"V{o['v']}" for o in os_]
    L = [f'# {title} - every shelf-bracket answer number (generated by make_shelf_facts.py; do not edit by hand)', '',
         'Illustrative values for education. Simplified teaching models: this is NOT a design for real wall shelves.', '',
         f'The same numbers, with units, formulas, spoken forms and the exact printed string, are in {json_name} (keys: shelf_<name> for fixed inputs, '
         'V<n>_<name> for variant inputs, V<n>_EpNN_<name> for the episode answers below; the Key column gives <name>). '
         'Ep 01, 09-11, 14, 16, 21 and 23 use these numbers but add none of their own.', '',
         '## Fixed inputs', '']
    L += table(['Key (shelf_...)', 'Input', 'Value', 'Unit', 'Source / assumption'],
               [[key, label, show(val, nd), unit or '-', src] for key, label, val, unit, nd, src, *_ in fixed_spec()])
    L += ['', '## Assumptions (every model used below)', ''] + [f'{n}. {a}' for n, a in enumerate(ASSUMPTIONS, 1)]
    L += ['', '## Variant inputs', '']
    L += table(['Variant', 'Use', 'Shelf load (kg, whole shelf)', 'Shelf depth (mm)', 't (mm)', 'Upright', 'Environment', 'Quantity'],
               [[f"V{o['v']}", o['name'], f"{o['load_kg']:.1f}", f"{o['depth']:.0f}", f"{o['t']:.1f}", o['upright'], o['env_name'], o['qty']] for o in os_])
    for ep, head, intro, rows in sections:
        L += ['', f'## {head}', '']
        if intro:
            L += intro + ['']
        L += table([f'Key (V<n>_{ep}_...)', 'Quantity', 'Unit'] + V, [r for r in rows if r[1] not in TEXT_ONLY])
        L += extra_md(ep, os_)
    return '\n'.join(L) + '\n' + FOOTER


# ---------------------------------------------------------------- learner-file notice footer (same lines as the worksheets)
# Verify line, ownership line, educational-example short form and the SHORT legal line (read from legal_notice.txt, one
# source). The same four lines end every worksheet.
LEGAL_FILE = next((p for p in (os.environ.get('C4_LEGAL_NOTICE'), os.path.join(HERE, 'legal_notice.txt'),
                               os.path.join(HERE, '..', '_pmo_tools', 'legal_notice.txt')) if p and os.path.isfile(p)),
                  os.path.join(HERE, 'legal_notice.txt'))


def _legal_short():
    lines = [ln.strip() for ln in open(LEGAL_FILE, encoding='utf-8')]
    i = next(k for k, ln in enumerate(lines) if ln.startswith('SHORT'))
    return next(ln for ln in lines[i + 1:] if ln)


VERIFY = 'Educational material - verify with current standards and your supplier.'
OWNERSHIP = '\u00a9 2026 Vijayakumar Yeddula \u00b7 CC BY 4.0 \u00b7 Mechanical Design Basics (C4)'
EDU_SHORT = 'Educational example - not for production, manufacture or legal use.'
FOOTER_MARK = '<!-- PDF footer: print the notice lines below in the footer of every page of the PDF. -->'
FOOTER = (f"\n---\n\n{FOOTER_MARK}\n{VERIFY}  \n{OWNERSHIP}  \n{EDU_SHORT}  \n{_legal_short()}\n")
# R3 close-out (L3-S7): notices inside the data files too. JSON: one "_notice" key (readers skip keys starting with "_");
# CSV: one first comment row starting with "#" (readers skip it). Same three lines as the footer, one source.
NOTICE_LINES = [OWNERSHIP, EDU_SHORT, _legal_short()]
CSV_NOTICE = '# ' + ' | '.join(NOTICE_LINES)


def stamp_brief(path=os.path.join(HERE, 'shelf_bracket_brief.md')):
    """The brief is written by hand; this replaces (or adds) its notice footer, so it always matches the worksheets.
    Returns a list of problems (empty = OK)."""
    if not os.path.exists(path):
        return [f'missing {path}']
    txt = open(path, encoding='utf-8').read()
    if FOOTER_MARK in txt:
        txt = txt[:txt.index(FOOTER_MARK)].rstrip()
        if txt.endswith('---'):
            txt = txt[:-3].rstrip()
    new = txt.rstrip() + '\n' + FOOTER
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new)
    back = open(path, encoding='utf-8').read()
    bad = [] if back.endswith(FOOTER) and back.count(FOOTER_MARK) == 1 else ['brief footer not written']
    bad += ['brief has old restrictive wording'] if re.search(r'\buse\s+' + 'only' + r'\b', back, re.I) else []
    return bad


def extra_md(ep, os_):
    fx = FIXED
    if ep == 'Ep02':
        L = ['']
        for o in os_:
            L += [f"**V{o['v']} {o['name']} - PDS lines**", '']
            L += table(['#', 'Requirement', 'Type', 'Verify by'], [
                [1, f"Carry {o['load_kg']:.1f} kg spread on a {o['depth']:.0f} mm deep shelf on 2 brackets ({o['W']:.1f} N per bracket) without yielding: FOS on yield >= {fx['gate']:.1f} at design load {o['F']:.1f} N", 'Functional / performance', 'Analysis (calc sheet), then load test'],
                [2, f"Front edge of the shelf drops <= {fx['droop_limit']:.1f} mm under the design load", 'Performance', 'Test (dial gauge or ruler at the front edge)'],
                [3, f"Fixes to the tapped aluminium upright ({o['upright']}) with 2 x M5 at {fx['hole2'] - fx['hole1']:.0f} mm pitch", 'Interface', 'Inspection (drawing check, trial fit)'],
                [4, f"Works in: {o['env_name']}, without visible corrosion for the stated life", 'Environmental', 'Inspection after a humidity / salt-spray test (supplier)'],
                [5, f"Quantity {o['qty']} brackets; piece cost target set by the customer", 'Manufacturing / cost', 'Inspection (quote review)'],
                [6, 'No sharp edges or burrs a hand can touch; screws do not loosen in use', 'Safety', 'Inspection (edge check), test (re-torque check)'],
            ]) + ['']
        return L
    if ep == 'Ep03':
        return ['', 'Note: the molded concept only becomes cheapest at high quantity and needs a ribbed shape that this course does not size. Where two concepts are within about 5% of each other, treat cost as a tie and decide on the other Pugh criteria.']
    if ep == 'Ep06':
        return ['', 'Redesign rows: if the holes must move away from the bend, they move down with the 55 mm pitch kept, and the droop is re-checked with the longer free length Lv.', '',
                'Stress raisers to mark (all variants): the bend (inside radius), the upper screw hole (closest to the bend, in the highest-moment zone of the wall flange), the corners where the flange edges meet the bend, and any burr or notch on the flange edges. Pictures only: no factor is applied in the hand number.']
    if ep == 'Ep07':
        return ['', '**Per-variant sentence for the answer key:**', ''] + [f"- V{o['v']}: {o['mat_why']}" for o in os_]
    if ep == 'Ep08':
        fixes = [f"V{o['v']}: {o['screw']['fix']}" for o in os_ if o['screw']['status'] == 'FAIL']
        return ['', 'Fix where no preferred length fits: ' + ('; '.join(fixes) if fixes else 'none') + '. Other honest options: a thicker washer or spacer under the head (for t = 3.0 mm, a 2.0 mm washer with M5 x 16 reaches the 11.0 mm limit at nominal: zero spare, so check it at the tolerance limits before choosing it), or a thread insert; record the choice as a judgement.', '',
                'Joint stays closed in every variant: the tension from the load is a few percent of the preload.']
    if ep == 'Ep12':
        return ['', 'Where Ep 08 found no preferred screw length (thread depth 12 mm), the thread callout above already shows the deepened hole from the Ep 08 fix.',
                'ASME form for US learners: the thread is written with its pitch, e.g. M5x0.8-6H; depths stay with the depth symbol.']
    if ep == 'Ep13':
        return ['', 'Fix for a FAIL: bigger clearance hole (check the washer still covers it) or a slot along the hole line, or drill the upright with a better fixture.']
    if ep == 'Ep15':
        return ['', 'The format-error rows above are the five errors chosen with a fixed seed from each variant\'s own numbers.']
    if ep == 'Ep17':
        return ['', 'Fix for a hole-to-bend FAIL: move both holes down by the shortfall (keep the 55 mm pitch so the upright does not change) and re-run the screw-tension numbers, or ask the supplier if their tooling allows it.']
    if ep == 'Ep19':
        return ['', f'All variants (typical rules, the foundry guide wins): parting plane through the middle of the width, parallel to the L-shaped side view, so each mould half pulls straight off; the flange faces then run along the pull and need draft (about {CAST["draft_sand"]} deg sand, {CAST["draft_die"]} deg die); generous fillet at the inside corner instead of a sharp bend; uniform wall, at least about {CAST["wall_sand"]} mm for sand and {CAST["wall_die"]} mm for die casting, so a 2 mm sheet thickness does not carry over to a sand casting; machining stock (about {CAST["stock"]} mm) on the wall face (datum A, which also removes the draft) and on the screw-hole spot faces; drill and tap the holes after casting, away from thick, porous zones. Die casting means an aluminium or zinc casting alloy, not your sheet steel: the material changes, so the Ep 06 strength and stiffness checks and the finish are re-run. Sand-cast steel needs much thicker walls than your sheet.']
    if ep == 'Ep20':
        return ['', f'DFA (all variants): kit per bracket = 1 bracket + 2 screws + 2 washers = {KIT["per_bracket"]} parts ({KIT["per_bracket"] * FIXED["n_brackets"]} per shelf); a flanged-head screw removes the washers ({KIT["after"]} per bracket, {KIT["after"] * FIXED["n_brackets"]} per shelf; re-check engagement, because the washer thickness was part of the screw length). The bracket is the same part on the left and the right (symmetric about its mid-width), which is good: one part number. It cannot be fitted upside down without the shelf flange pointing down, so no extra mistake-proofing feature is needed.']
    return []


# ---------------------------------------------------------------- CSV (one row per variant; values agree with the JSON)
CSV_COLS = ['v', 'name', 'load_kg', 'depth', 't', 'upright', 'env', 'qty', 'W', 'F', 'e', 'M', 'T1', 'T2', 'C',
            'sigma', 'FOS', 'strength', 'droop', 'tilt_deg', 'stiffness', 't_min', 'mat_choice', 'mass_al_g', 'mass_steel_g',
            'screw', 'eng', 'screw_check', 'mismatch', 'stack', 'K_bend', 'BA', 'flat', 'htb_req', 'htb_edge', 'htb', 'F_lbf',
            'sigma_ksi', 'cast_choice', 'b_net', 'sigma_net', 'FOS_net', 'strength_net']
# CSV column -> JSON key suffix (for the sync check)
CSV_JSON = dict(W='Ep04_W', F='Ep04_F', e='Ep04_e', M='Ep04_M', T1='Ep04_T1', T2='Ep04_T2', C='Ep04_C', sigma='Ep05_sigma',
                FOS='Ep05_FOS', strength='Ep05_strength', droop='Ep06_droop', tilt_deg='Ep06_tilt_deg', stiffness='Ep06_stiffness',
                t_min='Ep06_rd_t', mat_choice='Ep07_choice', mass_al_g='Ep07_al_mass', mass_steel_g='Ep07_steel_mass',
                screw='Ep08_screw', eng='Ep08_eng', screw_check='Ep08_screw_check', mismatch='Ep13_mismatch', stack='Ep13_stack',
                K_bend='Ep17_K', BA='Ep17_BA', flat='Ep17_flat', htb_req='Ep17_htb_req', htb_edge='Ep17_htb_edge', htb='Ep17_htb',
                F_lbf='Ep15_F_lbf', sigma_ksi='Ep15_sigma_ksi', cast_choice='Ep19_cast_choice', b_net='Ep05_b_net',
                sigma_net='Ep05_sigma_net', FOS_net='Ep05_FOS_net', strength_net='Ep05_strength_net')


def csv_row(o):
    return [o['v'], o['name'], o['load_kg'], o['depth'], o['t'], o['upright'], o['env'], o['qty'], round(o['W'], 2), round(o['F'], 2),
            o['e'], round(o['M'], 1), round(o['T1'], 2), round(o['T2'], 2), round(o['C'], 2), round(o['base']['sigma'], 2),
            round(o['base']['FOS'], 3), o['base']['strength'], round(o['base']['droop'], 3), round(o['base']['tilt_deg'], 3),
            o['base']['stiffness'], o['t_min'], o['mat_best']['mat'], round(o['mat']['al']['mass'], 1), round(o['mat']['steel']['mass'], 1),
            f"M5 x {o['screw']['L']}", o['screw']['eng'], o['screw']['status'],
            round(o['mismatch'], 2), o['stack'], FIXED['K_factor'], round(o['BA'], 3), round(o['flat'], 3), o['htb_req'], o['htb_edge'], o['htb'],
            round(o['inch']['F_lbf'], 2), round(o['inch']['sigma_ksi'], 3), o['cast_choice'], o['base']['b_net'],
            round(o['base']['sigma_net'], 2), round(o['base']['FOS_net'], 3), o['base']['strength_net']]


# ---------------------------------------------------------------- self-check
def self_check(os_, facts, md_text, csv_rows=None):
    """Independent re-derivations (different algebra) of key numbers, plus sync checks between the outputs."""
    bad = []
    # K-factor and shared values come from / agree with the course facts file
    if FIXED['K_factor'] != COURSE['K_bend']['value']:
        bad.append('K_factor differs from facts_c4.json K_bend')
    for mine, (theirs, _) in SHARED.items():
        mv = MATERIALS[BASE_MAT][mine] if mine in ('Sy', 'E') else FIXED[mine]
        if theirs not in COURSE or abs(float(COURSE[theirs]['value']) - mv) > 1e-9:
            bad.append(f'shared value {mine} != facts_c4.json {theirs}')
    for o in os_:
        F2 = o['load_kg'] * G * 0.75                     # 1.5 / 2 in one step
        s2 = F2 * o['depth'] / 2 / (FIXED['b'] * o['t'] ** 2 / 6)   # M / Z
        if abs(F2 - o['F']) > 1e-9 or abs(s2 - o['base']['sigma']) > 1e-9:
            bad.append(f"V{o['v']} load/stress")
        # moment balance about the heel: T1 y1 + T2 y2 = M
        if abs(o['T1'] * o['y1'] + o['T2'] * o['y2'] - o['M']) > 1e-6:
            bad.append(f"V{o['v']} moment balance")
        # flat length via the bend deduction: A + H - 2(t+R) + neutral-axis arc
        flat2 = o['A'] + FIXED['H'] - 2 * (o['t'] + o['R']) + (o['R'] + COURSE['K_bend']['value'] * o['t']) * math.pi / 2
        if abs(flat2 - o['flat']) > 1e-9:
            bad.append(f"V{o['v']} flat")
        # mass via the two flange strips plus the bend arc, in kg -> g
        for r in o['mat_rows']:
            vol = ((o['A'] - o['t'] - o['R']) + (FIXED['H'] - o['t'] - o['R']) + o['BA']) * FIXED['b'] * o['t']
            if abs(vol * MATERIALS[r['mat']]['rho'] * 1e-3 - r['mass']) > 1e-9:
                bad.append(f"V{o['v']} mass {r['key']}")
        # net section by the ratio test: sigma_net = sigma x b / b_net, FOS_net = FOS x b_net / b
        bn = FIXED['b'] - FIXED['clear']
        if (abs(o['base']['sigma'] * FIXED['b'] / bn - o['base']['sigma_net']) > 1e-9
                or abs(o['base']['FOS'] * bn / FIXED['b'] - o['base']['FOS_net']) > 1e-9 or o['base']['FOS_net'] >= o['base']['FOS']):
            bad.append(f"V{o['v']} net section")
        if o['rd'] and o['rd']['FOS_net'] < FIXED['gate']:
            bad.append(f"V{o['v']} redesign fails the net section")
        if o['v'] in STORY:
            got = (o['base']['strength_both'], o['base']['strength'], o['base']['stiffness'], o['fails'], o['t_strength'], o['t_min'])
            if got != STORY[o['v']]:
                bad.append(f"V{o['v']} variant story changed: {got} vs {STORY[o['v']]}")
        # stack at the smallest hole, other algebra: nominal hole = d + mismatch + margin + size tolerance
        if abs(FIXED['d'] + o['mismatch'] + o['stack_margin'] + FIXED['clear_tol'] - FIXED['clear']) > 1e-9:
            bad.append(f"V{o['v']} stack not at the smallest hole")
        if chr(177) not in o['callout_hole_iso'] or chr(177) not in o['callout_bend'] or not o['callout_bend'].startswith('BEND 90'):
            bad.append(f"V{o['v']} hole or bend callout lost its tolerance")
        sc = o['screw']
        if sc['status'] == 'PASS' and not (sc['need'] <= sc['eng'] <= FIXED['tap_depth'] - 1):
            bad.append(f"V{o['v']} screw")
        if o['T1_over_pre'] >= 0.1:
            bad.append(f"V{o['v']} 'joint stays closed' sentence no longer true")
        if MATERIALS[STEEL]['E'] <= MATERIALS[BASE_MAT]['E'] or MATERIALS[STEEL]['rho'] <= MATERIALS[BASE_MAT]['rho']:
            bad.append('Ep 07 wording (steel stiffer, aluminium lighter) no longer true')
        # batch 2 keys (FR-E01..E07, ws9 FR-01/03, ws11 FR-01/02), each re-derived another way
        if re.findall(r'\d+(?:\.\d+)?', o['callout_thread_asme'].split(' - 6H')[1]) != re.findall(r'\d+(?:\.\d+)?', o['callout_thread_iso'].split('6H')[1]):
            bad.append(f"V{o['v']} ASME thread callout depths differ from the ISO callout")
        hd = float(re.search(r'\d+\.\d', o['hole_callout_fix']).group())
        if (o['stack'] == 'PASS' and hd != FIXED['clear']) or (o['stack'] == 'FAIL' and (hd < o['hole_nominal_needed'] - 1e-9 or (o['rd'] and f"{chr(216)}{hd:.1f} {chr(177)}" not in o['ecr']))) or 'THRU' in o['hole_callout_fix'] \
                or 'THRU' in o['callout_hole_iso'] or (o['stack'] == 'PASS' and o['hole_callout_fix'] != o['callout_hole_iso']):
            bad.append(f"V{o['v']} Ep 12 / Ep 13 hole callouts (no THRU; PASS = the Ep 12 callout; FAIL >= nominal needed and as in the ECR)")
        if abs(o['bend_line'] + (o['A'] - o['t'] - o['R']) + o['BA'] / 2 - o['flat']) > 1e-9:
            bad.append(f"V{o['v']} bend line: both legs to the bend line add up to the flat length")
        if (o['htb'] == 'FAIL') != (o['htb_shortfall'] is not None) or (o['htb_shortfall'] is not None and (o['htb_shortfall'] <= 0 or (o['rd'] and o['rd']['t'] == o['t'] and o['rd']['hole1'] - FIXED['hole1'] < o['htb_shortfall'] - 1e-9))):
            bad.append(f"V{o['v']} hole-to-bend shortfall (FAIL only; the redesign moves the holes at least that far)")
        if f"t = {o['t']:g}" not in o['material_callout'] or ' OR ' in o['finish_callout'].upper() or o['finish_callout'].startswith('NOT RELEASED') or not (0 < o['upper_swing'] < FIXED['hole1']):
            bad.append(f"V{o['v']} Ep 11 callouts (t stated, one finish, released) / Ep 21 swing room")
    for o in os_:   # D105 released geometry, re-derived another way
        r, rd = o['rel'], o['rd']
        if not r:
            continue
        if (r['t'], r['hole1'], r['hole2']) != (rd['t'], rd['hole1'], rd['hole2']) or abs(r['hole2'] - r['hole1'] - (FIXED['hole2'] - FIXED['hole1'])) > 1e-9:
            bad.append(f"V{o['v']} released t / holes = Ep 06 redesign, pitch kept")
        flat2 = o['A'] + FIXED['H'] - 2 * (r['t'] + r['R']) + (r['R'] + FIXED['K_factor'] * r['t']) * math.pi / 2
        if abs(flat2 - r['flat']) > 1e-9 or abs(r['bend_line'] + (o['A'] - r['t'] - r['R']) + r['BA'] / 2 - r['flat']) > 1e-9:
            bad.append(f"V{o['v']} released flat / bend line")
        if r['htb'] != 'PASS' or r['flange_ok'] != 'PASS':
            bad.append(f"V{o['v']} released geometry fails hole-to-bend or flange length")
        if abs(r['sigma_ksi'] * 6.894757293168 - rd['sigma']) > 1e-9 or abs(r['droop_in'] * 25.4 - rd['droop']) > 1e-9:
            bad.append(f"V{o['v']} released ksi / droop")
        if r['t'] == o['t'] and r['moved'] == 'no' and (abs(r['flat'] - o['flat']) > 1e-9 or r['callout_bend'] != o['callout_bend']
                                                         or r['material_callout'] != o['material_callout'] or r['format_errors'] != o['format_errors']
                                                         or r['callout_thread'] != o['callout_thread_iso']):
            bad.append(f"V{o['v']} released = as-given keys when nothing changed")
        if 'M5 x ' + str(rd['screw']['L']) != r['screw']:
            bad.append(f"V{o['v']} released screw = Ep06_rd_screw")
        for w, rr in o['format_errors'] + r['format_errors']:   # L4 #6: psi = the printed ksi x 1000
            m = re.search(r'(\d+\.\d\d) ksi \(= (\d+) psi\)', rr)
            if m and int(m.group(2)) != round(float(m.group(1)) * 1000):
                bad.append(f"V{o['v']} psi not from the printed ksi")
    if 'steel' not in facts['shelf_Ep17_RK_note']['value'] or 'aluminium or zinc' not in facts['shelf_Ep19_die_cast_note']['value'] or facts['shelf_Ep19_die_cast_note']['value'] not in md_text:
        bad.append('D108 notes: R and K are course values for both materials; die casting is a non-ferrous alloy (also in the Ep 19 prose)')
    if not (FIXED['washer_od'] > max(FIXED['clear'] + FIXED['clear_tol'], max(math.ceil(o['hole_nominal_needed'] * 10 - 1e-9) / 10 + FIXED['clear_tol'] for o in os_))
            and FIXED['washer_id'] > FIXED['d']):
        bad.append('washer covers the largest clearance hole and passes the screw')
    for o in os_:   # D106 keys, each re-derived another way
        r, e = o['rel'], o['ep22']
        if not r:
            continue
        t = r['t']
        eb = FIXED['hole1'] - FIXED['clear'] / 2
        need = (t + r['R']) + 2.5 * t + r['R']
        if (r['htb_brief'] == 'FAIL') != (eb < need - 1e-9) or (r['htb_shortfall_brief'] is not None and (abs(r['htb_shortfall_brief'] - (need - eb)) > 1e-9 or r['move'] < r['htb_shortfall_brief'] - 1e-9)):
            bad.append(f"V{o['v']} D106 back-check of the brief holes (and the Part 1 move covers the shortfall)")
        if abs(r['htb_margin'] + r['htb_req'] - r['htb_edge']) > 1e-9 or not (3.5 * t + 2 * r['htb_R_max'] <= r['htb_edge'] + 1e-9 < 3.5 * t + 2 * (r['htb_R_max'] + 0.1) + 1e-9) \
                or (r['htb_tight'] == 'yes') != (r['htb_R_max'] < r['R'] + FIXED['htb_tight_band'] - 1e-9):
            bad.append(f"V{o['v']} D106 margin / R_max / tight")
        asg = set(x.strip() for x in o['fails'].split(',')) - {'none'}
        if set(r['open_list']) & set(r['closed_list']) or not asg <= set(r['open_list']) | set(r['closed_list']):
            bad.append(f"V{o['v']} D106 every as-given failure is either closed in Rev A or open, never both")
        if e['kind'] == 'supplier_R' and e['hole_note'] is None:
            Rs = e['sup_R']
            if abs(e['htb_req'] - ((t + Rs) + 2.5 * t + Rs)) > 1e-9 or e['htb_new_edge'] < e['htb_req'] - 1e-9 or abs(e['hole2'] - e['hole1'] - (FIXED['hole2'] - FIXED['hole1'])) > 1e-9 \
                    or abs(e['raise'] * 2 - round(e['raise'] * 2)) > 1e-9 or abs(e['raise'] - (e['hole1'] - r['hole1'])) > 1e-9 or Rs < FIXED['sup_R_ratio'] * e['sup_die'] - 1e-9:
                bad.append(f"V{o['v']} D106 supplier-R change: required, new holes, pitch, raise")
            flat2 = o['A'] + FIXED['H'] - 2 * (t + Rs) + (Rs + FIXED['K_factor'] * t) * math.pi / 2
            ok = e['htb_new'] == 'PASS' and e['droop'] <= FIXED['droop_limit'] and FIXED['H'] - e['hole2'] - FIXED['clear'] / 2 >= FIXED['lig_factor'] * t - 1e-9
            if abs(flat2 - e['flat']) > 1e-9 or (e['fix'] == 'move the holes') != ok or not e['part_number'].endswith(f"-{FIXED['part_next_dash']}") or FIXED['part_next_dash'] <= 7:
                bad.append(f"V{o['v']} D106 supplier-R change: flat, fallback rule, new part number")
        if e['kind'] == 'captive_washer':
            L = int(re.search(r'M5 x (\d+)', e['screw']).group(1))
            if abs(e['eng'] - (L - t - FIXED['washer'])) > 1e-9 or not (UPRIGHTS[o['upright']] * FIXED['d'] <= e['eng'] <= FIXED['tap_depth'] - FIXED['bottom_gap']) \
                    or e['washer_od'] != FIXED['washer_od'] or FIXED['sems_std'] not in e['screw'] or 'flange' in (e['ecr'] + e['screw']).lower():
                bad.append(f"V{o['v']} D108 captive-washer kit: engagement L - t - washer, washer from the shelf keys, no flange claim")
        # D108: worst case, SAMPLE supplier R, moved holes
        wc2 = facts['shelf_prof_outline']['value'] / 2 + facts['shelf_pos_holes']['value'] / 2 + facts['shelf_clear_tol']['value'] / 2
        if abs(wc2 - wc_loss()) > 1e-9 or abs(r['htb_edge'] - r['htb_edge_wc'] - wc2) > 1e-9 or (r['htb_wc'] == 'PASS') != (r['htb_edge_wc'] >= r['htb_req'] - 1e-9):
            bad.append(f"V{o['v']} D108 worst-case hole-to-bend edge from the drawing tolerance keys")
        if not (FIXED['sup_R_ratio'] * r['sup_die'] - 1e-9 <= r['sup_R'] < FIXED['sup_R_ratio'] * r['sup_die'] + 0.5) or (r['htb_supR'] == 'PASS') != (r['htb_edge'] >= (t + r['sup_R']) + 2.5 * t + r['sup_R'] - 1e-9):
            bad.append(f"V{o['v']} D108 SAMPLE supplier R and hole-to-bend at it")
        if e['kind'] == 'supplier_R' and e['hole_note'] is None:
            Rs, en = e['sup_R'], e['hole1'] - FIXED['clear'] / 2
            if en - wc2 < e['htb_req'] - 1e-9 or (e['hole1'] - 0.5 > r['hole1'] - 1e-9 and e['hole1'] - 0.5 - FIXED['clear'] / 2 - wc2 >= e['htb_req'] - 1e-9) \
                    or e['htb_R_low'] != 'PASS' or f"INSIDE R{t * FIXED['R_over_t']:g} TO R{Rs:g}" not in e['callout_bend'] or abs(e['flat_R_low'] - r['flat']) > 1e-9 \
                    or not (3.5 * t + 2 * e['R_max_wc'] <= en - wc2 + 1e-9 < 3.5 * t + 2 * (e['R_max_wc'] + 0.1) + 1e-9) or e['lower_edge'] < FIXED['lig_factor'] * t - 1e-9:
                bad.append(f"V{o['v']} D108 supplier-R change: smallest 0.5 step passing at the drawing tolerances, R range, flat at R = t, ligament")
        if e['alt_hole1'] is not None:
            a_ok = e['alt_htb_wc'] == 'PASS' and e['alt_lig_ok'] == 'PASS' and e['alt_droop'] <= FIXED['droop_limit']
            if (e['alt_ok'] == 'PASS') != a_ok or abs(e['alt_edge_wc'] - (e['alt_hole1'] - e['hole_d'] / 2 - wc2)) > 1e-9 or e['alt_part_number'] == e.get('part_number'):
                bad.append(f"V{o['v']} D108 moved-hole alternative")
        if e['hole_d'] is not None and (abs(e['htb_edge'] - (r['hole1'] - e['hole_d'] / 2)) > 1e-9 or f"{chr(216)}{e['hole_d']:.1f}" not in o['hole_callout_fix']
                                        or (e['htb'] == 'PASS') != (e['htb_edge'] >= e['htb_req'] - 1e-9)):
            bad.append(f"V{o['v']} D106 larger hole: hole-to-bend re-check at the Ep 13 hole")
    for o in os_:   # D109 batch 9: Rev A keys re-derived another way
        a, r, e, v = o['revA'], o['rel'], o['ep22'], o['v']
        if not a:
            continue
        t = r['t']
        hd = float(re.search(r'\d+\.\d', facts[f'V{v}_Ep13_hole_callout']['value']).group())
        edge = facts[f'V{v}_rel_hole1']['value'] - hd / 2
        req = 5.5 * t                                   # (t + t) + 2.5t + t at R = t
        wc2 = facts['shelf_htb_wc_loss']['value']
        if abs(a['hole_d'] - hd) > 1e-9 or hd < FIXED['clear'] - 1e-9 or abs(a['htb_edge'] - edge) > 1e-9 or abs(a['htb_margin'] - (edge - req)) > 1e-9 \
                or (a['htb_wc'] == 'FAIL') != (edge - wc2 < req - 1e-9) or not (3.5 * t + 2 * a['htb_R_max'] <= edge + 1e-9 < 3.5 * t + 2 * (a['htb_R_max'] + 0.1) + 1e-9):
            bad.append(f"V{v} D109 Rev A hole-to-bend (Ep 13 hole, nominal and worst case)")
        if a['htb_wc'] == 'FAIL' and not (a['htb_R_max_wc'] < t and 3.5 * t + 2 * a['htb_R_max_wc'] <= edge - wc2 + 1e-9):
            bad.append(f"V{v} D109 R_max at the tolerances must be below t where the worst case fails")
        thr = float(re.search(r'depth (\d+)', facts[f'V{v}_Ep12_callout_thread']['value']).group(1))
        L = int(re.search(r'M5 x (\d+)', facts[f'V{v}_rel_screw']['value']).group(1))
        need = UPRIGHTS[o['upright']] * FIXED['d']
        if a['thread_depth'] != thr or a['eng'] + FIXED['washer'] != a['nowasher_eng'] or a['nowasher_eng'] != L - t \
                or (a['screw_check'] == 'PASS') != (need <= a['eng'] <= thr - 1) or (a['nowasher_check'] == 'FAIL') != (thr < a['nowasher_eng'] + 1):
            bad.append(f"V{v} D109 Rev A thread, engagement and no-washer re-check")
        if set(a['open_topics']) & {'thread', 'stack'} or ('htb_wc' in a['open_topics']) != (a['htb_wc'] == 'FAIL') \
                or ('stack' in a['closed_topics']) != (o['stack'] == 'FAIL') or (a['nowasher_check'] == 'FAIL') != ('washer' in a['open_topics']):
            bad.append(f"V{v} D109 Ep 20 closed / open lists (never both; open = worst-case FAIL, V1/V4 washer)")
        if e['kind'] == 'washer_bottoming' and (not (need <= e['eng'] <= thr - 1) or e['alt_thread_need'] <= thr or 'SHB-200' in e['ecr'] or 'next revision' not in e['ecr']
                                                 or f"M5 x {max(x for x in SCREW_LENGTHS if x < L)}" not in e['ecr']):
            bad.append(f"V{v} D109 captive-washer ECO (engagement in range, deeper thread rejected, no upright revision)")
        for x in (e, e['b']):
            if x.get('hole_note'):
                Rs = x['sup_R']
                flat2 = o['A'] + FIXED['H'] - 2 * (t + Rs) + (Rs + FIXED['K_factor'] * t) * math.pi / 2
                if x['bendzone_clear'] < 0 or abs(x['bendzone_clear'] - (edge - t - Rs)) > 1e-9 or abs(flat2 - x['flat']) > 1e-9 or x['htb'] != 'FAIL' \
                        or f"R{t:g} TO R{Rs:g}" not in x['callout_bend'] or not x['part_number'].startswith(f'SHB-100-{v} '):
                    bad.append(f"V{v} D109 holes-after-forming ECO (bend zone, flat, R range, same part number)")
        if v == 3 and not (e['alt_raise'] > 0 and e['alt_part_number'] != 'SHB-100-3' and e['hole_note']):
            bad.append('V3 D133: after forming chosen on volume and interchangeability (the move raises the shelf: new part number)')
        if e['kind'] == 'galvanic' and not (e['tw_min'] <= e['tw_max'] and abs(e['tw_min'] - (a['nowasher_eng'] - (a['thread_depth'] - FIXED['bottom_gap']))) < 1e-9):
            bad.append(f'V{v} D133 insulating washer thickness window')
    for o in os_:   # E6 Must 1: every powder callout is quotable (colour, gloss, film range, powder-compatible zinc, masking)
        fc = o['finish_callout']
        if 'POWDER' in fc and not all(w in fc for w in ('RAL ', ' GU AT ', 'SUITABLE FOR POWDER COATING', 'MASK THE 2 HOLES', f"{FIXED['powder_um']:.0f}-{FIXED['powder_um_max']:.0f}")):
            bad.append(f"V{o['v']} powder callout not quotable")
    if abs(2 * FIXED['tol_laser'] - float(COURSE['tol_laser_pos']['value'])) > 1e-9 or KIT['per_bracket'] != 2 * KIT['after'] - 1:
        bad.append('shelf_pos_holes = 2 x tol_laser = lesson tol_laser_pos; DFA kit counts (washers = screws)')
    # JSON: structure, keys usable as [F: key], spoken form reads back to the value
    for k, d in facts.items():
        if not re.fullmatch(r'[A-Za-z0-9_]+', k):
            bad.append(f'json key {k}')
        if list(d) != ['value', 'unit', 'formula', 'spoken', 'printed']:
            bad.append(f'json fields {k}')
        elif isinstance(d['value'], str):
            if d['printed'] != d['value']:
                bad.append(f'printed {k}')
        elif (num_value(d['printed']) != d['value'] or type(num_value(d['printed'])) is not type(d['value'])
              or (isinstance(d['value'], float) and d['value'].is_integer())):
            bad.append(f'printed/value {k}: {d["printed"]!r} vs {d["value"]!r}')
        if isinstance(d['value'], (int, float)):
            if not d['spoken'] or abs(unspoken(d['spoken']) - d['value']) > 1e-9:
                bad.append(f'spoken {k}: {d["spoken"]!r} vs {d["value"]}')
    # fixed inputs: every shelf_ key is a row of the Markdown fixed-input table with its printed value
    for key, label, val, unit, nd, src, *_ in fixed_spec():
        if f"| {key} | {label} | {facts['shelf_' + key]['printed']} |" not in md_text:
            bad.append(f'md fixed row {key}')
    for kk in ('Sy', 'E'):
        if facts[f'shelf_al_{kk}']['value'] != facts[f'shelf_{kk}']['value']:
            bad.append(f'shelf_al_{kk} != shelf_{kk}')
    if abs(sum(WEIGHTS.values()) - 1) > 1e-9:
        bad.append('Ep 07 weights do not add up to 1')
    # JSON <-> Markdown: every value appears in the Markdown as printed
    for k, d in facts.items():
        if k.endswith('_name'):
            continue
        txt = show(d['value'], 'str') if isinstance(d['value'], str) else None
        if txt is None:
            continue
        if txt not in md_text:
            bad.append(f'md missing {k}')
    # JSON <-> CSV: same numbers within the JSON rounding
    for row in csv_rows or []:
        r = dict(zip(CSV_COLS, row))
        for col, suf in CSV_JSON.items():
            j = facts[f"V{r['v']}_{suf}"]['value']
            c = r[col]
            if isinstance(j, str):
                ok = str(c if c is not None else 'none') == j
            else:
                nd = ND[f"V{r['v']}_{suf}"]
                nd = 3 if nd == 'in' else 0 if nd == 'int' else nd
                ok = abs(float(c) - j) <= 0.5 * 10 ** -nd + 1e-9
            if not ok:
                bad.append(f"csv/json V{r['v']} {col}: {c} vs {j}")
    return bad


def numeric_md_check(facts, sections, os_):
    """Every numeric JSON value equals the printed Markdown cell of its row and variant."""
    bad = []
    for (ep, head, intro, rows), spec_sec in zip(sections, spec()):
        for row, (key, label, unit, fn, nd, formula) in zip(rows, spec_sec[3]):
            for i, o in enumerate(os_):
                d = facts[f"V{o['v']}_{ep}_{key}"]
                cell = row[3 + i]
                if d['printed'] != cell:
                    bad.append(f'md printed {ep} {key} V{o["v"]}')
                if isinstance(d['value'], str):
                    if d['value'] != cell: bad.append(f'md cell {ep} {key} V{o["v"]}')
                elif abs(float(cell if not cell.startswith('.') else '0' + cell) - d['value']) > 1e-9:
                    bad.append(f'md cell {ep} {key} V{o["v"]}')
    return bad


# The variant stories as published (wave 1), locked: (strength verdict over both sections, section-1 verdict,
# stiffness, checks that fail as given, thinnest t for strength, redesign t). A change is reported as a self-check
# failure and must be decided by the course team, never absorbed silently. Course variants only (not --own).
# 13 Nov (net section added): every verdict unchanged; the thinnest-t-for-strength row now includes section 2, which
# moves V5 and V6 from 3.0 to 4.0 mm (at t = 3 their net-section FOS is below the gate). Reported to the course team.
STORY = {
    1: ('PASS', 'PASS', 'PASS', 'screw length / thread depth, hole stack-up', 3.0, 3.0),
    2: ('PASS', 'PASS', 'FAIL', 'stiffness', 2.0, 3.0),
    3: ('FAIL', 'FAIL', 'FAIL', 'strength, stiffness, hole stack-up', 4.0, 5.0),
    4: ('PASS', 'PASS', 'PASS', 'screw length / thread depth', 3.0, 3.0),
    5: ('PASS', 'PASS', 'PASS', 'hole-to-bend', 4.0, 5.0),
    6: ('PASS', 'PASS', 'PASS', 'none', 4.0, 4.0),
}


def parse_own(argv):
    load, depth, t, upright, env, qty = argv
    if upright not in UPRIGHTS or env not in ENVS:
        sys.exit(f'upright must be one of {list(UPRIGHTS)}; env one of {list(ENVS)}')
    return dict(v=7, name='Your own numbers', load_kg=float(load), depth=float(depth), t=float(t), upright=upright, env=env, qty=int(qty))


def run(os_, md_path, json_path, csv_path=None, title='Facts_C4_shelf'):
    facts, sections = build(os_)
    md = facts_md(os_, sections, title, os.path.basename(json_path))
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({'_notice': NOTICE_LINES, **facts}, f, indent=1, ensure_ascii=False)
    rows = None
    if csv_path:
        rows = [csv_row(o) for o in os_]
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow([CSV_NOTICE])
            w.writerow(CSV_COLS)
            w.writerows(rows)
        with open(csv_path, encoding='utf-8') as f:      # check what was written, not what was meant
            rd = [r for r in csv.reader(f) if r and not r[0].startswith('#')]
            if rd[0] != CSV_COLS:
                return [f'csv header row {rd[0][:3]}...'], 0
            rd = rd[1:]
        rows = [[(int(x) if c in ('v', 'qty') else x) for c, x in zip(CSV_COLS, r)] for r in rd]
        rows = [[(None if x == '' else x) for x in r] for r in rows]
    with open(json_path, encoding='utf-8') as f:
        facts_all = json.load(f)
    notice_bad = [] if facts_all.get('_notice') == NOTICE_LINES else ['json _notice missing or changed']
    if csv_path and next(csv.reader(open(csv_path, encoding='utf-8', newline='')), None) != [CSV_NOTICE]:
        notice_bad.append('csv notice row missing or changed')
    facts_back = {k: d for k, d in facts_all.items() if not k.startswith('_')}
    bad = notice_bad + self_check(os_, facts_back, md, rows) + numeric_md_check(facts_back, sections, os_)
    return bad, len(facts_back)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--own':
        bad, n = run([compute(parse_own(sys.argv[2:8]))], 'Facts_C4_shelf_own.md', 'facts_c4_shelf_own.json',
                     title='Facts_C4_shelf_own (variant 7)')
        print(f'PASS 0 self-check failures (Facts_C4_shelf_own.md, facts_c4_shelf_own.json, {n} keys)' if not bad
              else f'FAIL {len(bad)}: {bad}')
        sys.exit(1 if bad else 0)
    bad, n = run([compute(v) for v in VARIANTS], os.path.join(HERE, 'Facts_C4_shelf.md'),
                 os.path.join(HERE, 'facts_c4_shelf.json'), os.path.join(HERE, 'shelf_variants.csv'))
    bad += stamp_brief()
    print(f'PASS 0 self-check failures ({n} JSON keys; K_bend {FIXED["K_factor"]} from {COURSE_PATH})' if not bad
          else f'FAIL {len(bad)} self-check failures: {bad}')
    sys.exit(1 if bad else 0)
