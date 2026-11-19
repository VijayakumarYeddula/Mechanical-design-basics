# SPDX-License-Identifier: MIT
# © 2026 Vijayakumar Yeddula · MIT (code) · Mechanical Design Basics (C4). Educational example - not for production, manufacture or legal use.
"""C4 Mechanical Design Basics - Facts generator (open release).
Every number shown or spoken in the course comes from this file.
Final ACT-103: flat 2.5 mm cold-rolled low-carbon steel sheet, zinc plated after forming.

Teaching story locked by self_check():
  * Ep 05 strength (5052-H32 baseline from the concept): the quick bend check passes 1.5 and 2.0 mm; the LUMPED net
    section (every cut-out subtracted as if on one line - conservative) fails 1.5 mm; the REAL worst cut-out line
    passes both. Strength is not what decides this part.
  * (Updated by slot-zone stiffness model, minimum-yield gates, released thickness 2.5 mm steel, 12 GA deviation story.)
  * Ep 06 stiffness: pulley movement (1.5 mm fails, 2.0 mm passes) and SHAFT TILT (PDS R11, <= 0.25 deg)
    fails both. Three routes to stiffness, with real numbers:
      (a) thicker aluminium, 3.0 mm: passes tilt, +50 % metal, and no standard M3 motor screw then works;
      (b) stiffer material, 2.5 mm low-carbon steel, flat: passes with the largest margin (2.0 mm steel passes, no system margin);
      (c) shape, 2.0 mm aluminium + two 12 mm lips: passes, but the margin is thin once the motor shaft's own flex is added.
  * Ep 07: the weighted matrix (6 criteria incl. the heat path, PDS R10) picks steel, and no 10 % weight shift changes the leader.
  * Final design (Ep 08 onward): 2.5 mm steel passes every check at Rev A and Rev B; the heat path is judged adequate for a
    stepper and is confirmed by a motor-face temperature test (open action).
  * Ep 15 / Ep 22: a supplier's 12 gauge lot is re-checked on the screw stack and accepted on a one-lot deviation only
    below a measured-thickness limit; 13 gauge fails (thread below the tip).
Writes Facts_C4.md and facts_c4.json. Prints ONE line: PASS / n failures.
usage: python3 make_facts.py [out_dir] [--shelf facts_c4_shelf.json]   (--shelf: optional cross-check of the steel keys)"""
import json, math, os, sys

I = dict(
    F_max=24.0,            # N  working shaft (hub) load = both belt spans incl. pretension (illustrative)
    k_dyn=1.25,            # -  dynamic / uncertainty factor (illustrative)
    motor_weight=3.5,      # N  typical NEMA 17-size motor (about 0.35 kg)
    p=20.0,                # mm motor mounting face (motor-side face of the motor flange) to belt centre line
    b=50.0,                # mm flange width (both flanges)
    pilot_slot=23.0,       # mm clearance slot width for the 22 mm motor pilot
    m3_slot=3.4,           # mm M3 slot width
    m3_pat=31.0,           # mm motor M3 screw pattern (SAMPLE motor)
    Sy=193.0,              # MPa 5052-H32 yield, typical handbook value (Ep 05/06 baseline; = shelf_al_Sy)
    E=70300.0,             # MPa 5052-H32 modulus, typical (Ep 05/06 baseline; = shelf_al_E)
    rho_al=2.68,           # g/cm^3 5052 density, typical (= shelf_al_rho)
    Sy_steel=210.0,        # MPa cold-rolled low-carbon steel sheet, typical yield (= shelf_steel_Sy): Ep 07 comparison only
    # --- FOS gates use SPECIFIED MINIMUM yield from a material standard (cited by number only) ---
    Sy_min_ksi=23.0,       # ksi 5052-H32 sheet, specified minimum yield (0.2 % offset), ASTM B209 (Ep 05 baseline gates)
    Sy_min_EN485=130.0,    # MPa 5052 H32 sheet, specified minimum Rp0.2, EN 485-2 (information: the lower of the two)
    Sy_steel_min=205.0,    # MPa ASTM A1008/A1008M SS Grade 30 [205], specified minimum yield (released ACT-103 gates)
    Sy_steel_dc01_design=140.0,  # MPa EN 10130 DC01: no specified minimum; lower design value published by a mill (information only)
    E_steel=200000.0,      # MPa steel modulus, typical (= shelf_steel_E); also used for the motor shaft
    rho_steel=7.85,        # g/cm^3 steel density, typical (= shelf_steel_rho)
    Su_steel=300.0,        # MPa typical tensile strength of the same sheet (fatigue estimate only)
    FOS_gate=2.5, move_limit=0.5,
    t1=1.5, t2=2.0,        # mm aluminium baseline thickness options (Ep 05/06)
    t_steel=2.5,           # mm RELEASED ACT-103 thickness, flat low-carbon steel, inside R = t
    a=40.0, T=8.0, T_revB=10.0,   # mm motor centre from datum A (mid-travel), travel at Rev A and Rev B
    L1=20.0, y2=50.0,      # mm M5 bolt rows from datum A side of the bend
    motor_body=42.0,       # mm SAMPLE NEMA 17-size motor body, square across flats (42.3 typical; the maker's drawing wins)
    k_M5=5.0,              # mm ISO 4762 M5 socket head height k (max 5 mm)
    key_leg_M5=25.0,       # mm ISO 2936 hex key s = 4 mm (M5 socket head), short leg l2: 25 mm (the smaller of the published table values 25 / 29) so the 'shorter than the short leg' claim holds for any standard key
    act105_wall=2.2,       # mm ACT-105 top cover, ABS, nominal wall (Actuator EBOM v7_4)
    As=14.2, proof=580.0, preload_M5=4000.0, K=0.2, d_M5=5.0,
    L_M5=12.0, washer_M5=1.0, depth_M5=11.0, drill_M5=13.0,
    L_M3=6.0, L_M3_next=8.0, washer_M3=0.5, depth_M3=4.5, preload_M3=0.5 / (0.2 * 0.003), mu=0.2, head_M3=5.5,   # preload_M3 = torque_M3 / (K d) = 0.5 / (0.2 x 3 mm), UNROUNDED (833.33 N; printed 833)
    # --- M3 motor-screw stack at the tolerance limits (checked at every tolerance corner) ---
    t_tol=0.12,            # mm drawing thickness tolerance +/- for the 2.5 mm sheet = EN 10131 normal tolerance, 2.00 < t <= 2.50, Re < 260 MPa
    L_M3_tol=0.24, L_M3_next_tol=0.29,   # mm ISO 4762 length limits: M3 x 6 = 5.76-6.24, M3 x 8 = 7.71-8.29 (product grade A, ISO 4759-1)
    washer_M3_od=7.0,      # mm ISO 7089 size 3 washer outside diameter (clamp footprint; REVIEW_F11_CAE x_clamp_edge)
    washer_M3_tol=0.05,    # mm ISO 7089 size 3: h = 0.5 (0.45-0.55)
    torque_M3=0.5,         # N.m SAMPLE motor datasheet screw torque, used as the assembly torque (+/- torque_tol_pct); real maker wins
    thread_end_P=2.0,      # pitches: incomplete thread at the screw end, ISO 4753 allows u <= 2P (not counted in the strip check)
    lead_in_P=0.5,         # pitches: lead-in / countersink at the motor hole entry (not full thread; assumed, motor maker confirms)
    # --- ECO-001 load path: ACT-109 bolted to ACT-101 with 2x COTS-221 ---
    act109_t=5.0,          # mm ACT-109 clamp-flange thickness under the M4 heads
    L_M4=12.0, L_M4_tol=0.35, d_M4=4.0, P_M4=0.7, d_min_M4=3.838, D2_max_M4=3.663,   # ISO 4762 M4 x 12 (11.65-12.35); M4 6g / 6H limits
    depth_M4=9.0,          # mm full-thread depth of the 2x M4 in ACT-101 (to go on the ACT-101 Rev B drawing)
    tau_6061=207.0,        # MPa 6061-T6 typical shear strength (published typical value)
    preload_M4=2500.0,     # N  illustrative preload of the 2x M4 (COTS-221)
    act109_t_tol=0.1,      # mm ACT-109 clamp-flange thickness tolerance (machined, general tolerance)
    L_M4_short=10.0, L_M4_short_tol=0.29,   # mm the M4 x 10 first listed (TBC), for the record of the length choice
    K_min=0.15,            # -  low end of the nut-factor scatter (plated or lubricated screw; see note_K_dry): most preload at the same torque
    tau_motor=190.0,       # MPa SAMPLE motor housing: die-cast aluminium (A380 type), typical ultimate shear strength (published typical value)
    P_M3=0.5, d_min_M3=2.874, D2_max_M3=2.775,   # mm M3 pitch; 6g external major dia min; 6H internal pitch dia max (ISO 965 limits)
    strip_gate=1.5,        # -  thread-strip force at the worst corner / nominal assembly preload (illustrative course gate)
    t_alt2_tol=0.11,       # mm EN 485-4 Group II, 2.60-3.0 mm, width up to 1000 mm (route a, information)
    t1_tol=0.07,           # mm EN 485-4 thickness tolerance, Group II (5052), 1.21-1.50 mm, width up to 1000 mm (1250 mm wide: 0.11)
    shaft_radial_allowed=30.0, shaft_load_distance=20.0,   # SAMPLE datasheet values; the distance is from the motor mounting face (same reference as p)
    K_bend=0.33,           # bend K-factor (illustrative; for steel at R = t it agrees with the DIN 6935 correction-factor rule; supplier confirms)
    R_over_t=1.0,          # inside bend radius / t (R = t = 2.5 mm; low-carbon steel bends tighter, R = t keeps the flat pattern and hole-to-bend unchanged)
    hole_M5=5.5, drill_dia_M5=4.2,
    L_mount=62.0, L_motor=70.0,          # mm outside flange lengths (drawing; engineering)
    tol_laser=0.1, tol_across_bend=0.25, tol_bend_angle=1.0,   # mm / deg: laser hole SIZE +/-, across-bend +/-, bend angle +/- (typical, supplier to confirm)
    tol_laser_pos=0.2,     # mm laser hole centre within this DIAMETER of true position (typical, confirm with supplier)
    tol_tapped_pos=0.1,    # mm CNC tapped-hole centre within this DIAMETER of true position (typical, confirm with the machine shop)
    torque_tol_pct=10.0,   # %  assembly-note torque tolerance (illustrative)
    hook_ep05_load=100.0,  # N  illustrative hook story only (a different bracket, Ep 05)
    tilt_guide=0.25,       # deg published timing-belt guidance: misalignment under 1/4 deg (belt maker wins)
    tilt_limit=0.25,       # deg PDS R11: shaft tilt caused by the bracket under the design load (illustrative, from the guidance)
    # --- belt-alignment budget (alignment_study.md): the 1/4 deg is TOTAL angular misalignment between the pulleys ---
    perp_motor_seat=1.2, perp_seat_len=65.0,   # mm drawing: perpendicularity of the motor seat to datum A, over this length
    tol_bend_practical=0.5, tol_bend_best=0.2, # deg press brake: practical with calibration / specialised (active angle measurement, crowning)
    mis_mach_perp=0.02, mis_mach_len=50.0, mis_mach_n=3,   # mm, mm, - machined chain: ACT-101 end face, ACT-108 base, ACT-102 idler bore (illustrative CNC values)
    motor_perp_tir=0.075, motor_perp_dia=40.0, # mm SAMPLE motor: mounting-face perpendicularity to the shaft (T.I.R.), read at this diameter (assumed)
    pulley_bore_form=0.005, pulley_bore_len=14.0,   # mm pulley seated by its set screw: bore form error over the bore length (assumed), per pulley
    motor_play=0.025, motor_play_span=30.0,    # mm SAMPLE motor radial play at 5 N; taken over this bearing span (assumed)
    idler_clear=0.013, idler_span=20.0,        # mm 608 bearing radial clearance, normal group, upper value (bore 6-10 mm); bearing span in ACT-102 (assumed)
    adj_range=1.5,         # deg ACT-102 idler-angle adjustment range, +/- (design requirement)
    set_accept=0.04,       # deg assembly acceptance: angle between the pulley faces in the steering plane after setting
    dti_res=0.002, set_sweep=16.0,             # mm dial test indicator resolution; carriage travel across each pulley flange face
    # --- belt alignment, R2 (open-ended belt clamped to the carriage: EACH pulley and EACH clamp is set to the rail; alignment_study.md section R2) ---
    adj_range_drive=1.5,   # deg ACT-101 drive end block yaw adjustment range, +/- (design requirement)
    act101_dowel_span=40.0,  # mm ACT-101 pivot dowel to eccentric pin centre (design value for the ACT-101 Rev A drawing; illustrative)
    ecc_e=1.1,             # mm ACT-111 eccentric pin: eccentricity (design value)
    pulley_x=60.0,         # mm pivot dowel to drive pulley axis along the rail (layout value, illustrative): sets the axial shift of the pulley when the block turns
    dti_res_r2=0.001,      # mm digital indicator resolution used for the R2 alignment step (reading error taken as one resolution per reading)
    flange_flat=0.003,     # mm SAMPLE pulley spec: outer flange face turned with the bore, flatness over the reading zone (receiving check)
    travel_straight=0.001, # mm carriage running straightness over a 16-20 mm sweep (illustrative miniature-guide value)
    clamp_sweep=20.0,      # mm carriage travel along the machined reference side face of each belt clamp (ACT-107)
    clamp_face_par=0.003,  # mm ACT-107 reference side face parallel to the belt-tooth slot (machined in one set-up; drawing value)
    r2_accept_mm=0.005,    # mm acceptance: each pulley and each clamp, change over its sweep; also the drive-minus-idler difference
    clamp_adj_range=1.0,   # deg ACT-107 clamp yaw range on its screw holes, +/- (design requirement; confirm at the ACT-104/107 detail)
    span_min=30.0,         # mm shortest live belt span (carriage at the stroke end to the pulley tangent point; layout value, illustrative)
    peel_lam=0.05,         # mm lamination of a standard peel (laminated) shim, for the wedge-shim option
    zinc_um=8.0,           # um zinc electroplate, minimum, after forming, with Cr(VI)-free passivation
    zinc_um_max=12.0,      # um zinc electroplate, maximum on significant surfaces (course practice; ASTM B633 classes give minimums only)
    # --- route (c) lips, for the Ep 06 comparison only ---
    B_motor=58.0, H_lip=12.0, lip_start=8.0,
    t_alt1=2.5, t_alt2=3.0,  # mm thickness-only aluminium alternatives
    # --- pulley, belt, motor (SAMPLE / illustrative) ---
    pulley_teeth=20, belt_pitch=3.0, belt_width=6.0,
    T_motor_peak=0.45,     # N.m SAMPLE NEMA 17-size holding torque (motor datasheet wins)
    FOS_stall_gate=1.5,    # -  rare accidental load: stay clear of yield (illustrative gate)
    Sf_5052=117.0,         # MPa typical 5052-H32 fatigue strength at 5e8 cycles (handbook value)
    d_shaft=5.0, bearing_inset=5.0,   # SAMPLE motor shaft: front bearing 5 mm inside the face (assumed)
    # --- heat path (PDS R10) ---
    k_5052=138.0, k_steel=50.0,   # W/(m.K) typical thermal conductivity, 5052 and low-carbon steel
    fea_tilt_revA=0.094, fea_tilt_revB=None, fea_stress_revA=16.4, fea_stress_revB=None, fea_peak=None,   # FreeCAD FEM (CalculiX) results of ACT-103: filled after the run (deg, deg, MPa, MPa, MPa)
    fea_move_revA=0.041, fea_move_revB=None, fea_line2_revA=11.07, fea_line2_revB=None, fea_bend_lin=11.6, fea_mesh_delta_pct=None, fea_model_rev=None,   # mm, mm, MPa, MPa, MPa, %, text
    fea_band_tol=0.10, fea_stress_lo_factor=0.85, fea_mesh_limit_pct=3.0, fea_Kt=(2.0, 3.0),   # FEA cross-check: +/- band on the hand values; stress-raiser range at the slot ends (Ep 06: about 2-3x nominal)
    k_ss304=16.2, k_PA66=0.3,     # W/(m.K) typical: 304 stainless; PA66 dry, unfilled (published 0.24-0.36)
    ambient_min=5.0,       # degC PDS R7 lower ambient (Ep 02 slide S16_1, learner PDS template)
    ambient_max=40.0,      # degC PDS R7 upper ambient: the temperature test is run at (or corrected to) this
    motor_case_limit=80.0, # degC SAMPLE motor maker's case-temperature limit (datasheet wins)
    # --- sheet gauges (Ep 15): typical published nominal values; confirm with the supplier's gauge table ---
    ga14_steel_in=0.0747, ga14_galv_in=0.0785, ga14_al_in=0.0641, swg14_in=0.080,
    # --- thickness study ---
    ga12_steel_in=0.1046, ga13_steel_in=0.0897,   # in US manufacturers standard gauge, uncoated steel (typical published nominal; course decision)
    ga12_tol_in=0.006, ga13_tol_in=0.005,         # in +/- band of a supplier gauge table for A1008 sheet (12 GA 0.0986-0.1106; 13 GA 0.0847-0.0947); confirm with the supplier
    study_E_ss=193000.0,   # MPa 304 stainless, typical modulus (Ep 07 stiffness score only)
    study_a_alt=35.0,      # mm option 3: motor centre moved 5 mm toward the bend (2.0 mm steel)
    study_score_bands=(10.0, 20.0),   # % of tilt_limit: system margin below the first = thin (3), below the second = 4, else 5
    # --- other episodes ---
    be_tool_molded=8000.0, be_piece_molded=1.5, be_piece_sheet=6.0, be_piece_machined=18.0, be_qty=500.0,  # illustrative cost units
    qty_year=500.0, qty_year_cast=5000.0,   # parts per year (Ep 03, 18; Ep 19)
    pilot_slot_move=1.0,   # mm supplier query (Ep 22)
    # --- plating basis, basic dimensions and pilot-slot position (FreeCAD team review, 14 Nov) ---
    pilot_dia=22.0,        # mm SAMPLE motor pilot boss diameter, largest (the maker's drawing wins)
    tol_gen_m=0.2,         # mm ISO 2768-m linear general tolerance +/-, over 6 up to 30 mm (applies to the 23 mm pilot slot width)
    hole_pat_BC=30.0,      # mm basic spacing of the two M5 hole columns across the 50 mm flange (datum B column to datum C column)
    pilot_end_ext=0.5,     # mm released geometry: pilot slot longer than the motor travel by this much at EACH end (Rev A 23 x 32, Rev B 23 x 34)
    pilot_end_clear_min=0.2,  # mm course practice: least pilot-to-slot-end clearance (visible daylight)
    pos_pilot_slot=0.4,    # mm drawing choice: pilot-slot position zone WIDTH (width only, to A|B|C), chosen below the stack limit pilot_slot_pos_max
    mttr=[3, 2, 1, 2, 4, 8, 4, 5, 3],   # min, illustrative step times for the Ep 21 belt-replacement task list
    # --- Ep 07 materials (typical published values; supplier data wins) ---
    PA66_Sy=80.0, PA66_E=2800.0, PA66_rho=1.14,   # dry as moulded; lower when moist; creeps under steady load, more when warm
    anodize_um=10.0,       # um minimum clear anodize: ACT-101 end block (no longer the bracket)
    # Ep 07 weighted matrix: weights from the PDS, 1-5 scores
    mx_weights=dict(strength=0.15, stiffness=0.25, cost=0.20, process=0.15, corrosion=0.10, heat=0.15),
    mx_scores=dict(al=dict(strength=3, stiffness=3, cost=4, process=4, corrosion=4, heat=5),      # 5052-H32 2.0 mm + lips (its best route)
                   steel=dict(strength=3, stiffness=5, cost=5, process=5, corrosion=4, heat=3),   # low-carbon steel 2.0 mm flat, zinc plated
                   ss=dict(strength=4, stiffness=5, cost=1, process=3, corrosion=5, heat=1),      # 304 stainless 2.0 mm flat
                   pa66=dict(strength=1, stiffness=1, cost=3, process=1, corrosion=4, heat=1)),
)

UNIT_WORD = {'N': 'newtons', 'mm': 'millimetres', 'MPa': 'megapascals', 'N.mm': 'newton millimetres', 'N.m': 'newton metres',
             'deg': 'degrees', 'ksi': 'kips per square inch', 'D': 'times the diameter', 'in': 'inches', 'lbf': 'pounds-force',
             'lbf.in': 'pound-force inches', 'min': 'minutes', 'mm^4': 'millimetres to the fourth', 'mm^2': 'square millimetres', 'mm^2/mm': 'square millimetres per millimetre',
             '/year': 'per year', 'um': 'micrometres', '%': 'percent', 'x': 'times', 'parts': 'parts', 'years': 'years', 'g': 'grams',
             'degC': 'degrees Celsius', 'g/cm^3': 'grams per cubic centimetre', 'W/m.K': 'watts per metre kelvin'}

MODEL = ('simplified model, errs both ways: gross section elsewhere, net section in slot zone; mounting term upper bound (conservative); '
         'motor and screws rigid (non-conservative); confirm by test (PDS R11)')

ILLUS = {'torque_tol_pct', 'F_max', 'k_dyn', 'move_limit', 'tilt_guide', 'tilt_limit', 'shaft_radial_allowed', 'preload_M5', 'preload_M3', 'mu', 'K',
         'K_bend', 'hook_ep05_load', 'T_motor_peak', 'FOS_stall_gate', 'bearing_inset', 'motor_case_limit', 'K_min', 'strip_gate'}

REMOVED = {  # old key (current make_facts.py or the engineering lips proposal) -> replacement
    'move_motoronly_t1': 'tilt_motor_t1 (motor-flange share, in degrees)',
    'move_motoronly_t2': 'tilt_motor_t2',
    'side_t1': 'none',
    'side_t2': 'side_steel (speak only with tilt_steel)',
    'move_t2_revB': 'move_steel_revB (and tilt_steel_revB)',
    'BA_t2': 'BA_rel (released 2.5 mm part, course decision)',
    'flat_t2': 'flat_rel',
    'bend_line_t2': 'bend_line_rel',
    'R_t2': 'R_rel',
    'c_t2': 'c_rel',
}


def spoken(x, unit=''):
    ones = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve', 'thirteen',
            'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen']
    tens = ['', '', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety']

    def whole(n):
        if n < 20: return ones[n]
        if n < 100: return tens[n // 10] + ('' if n % 10 == 0 else '-' + ones[n % 10])
        if n < 1000: return ones[n // 100] + ' hundred' + ('' if n % 100 == 0 else ' and ' + whole(n % 100))
        return whole(n // 1000) + ' thousand' + ('' if n % 1000 == 0 else ' ' + whole(n % 1000))
    if x == 1 and unit.endswith('s'):
        unit = unit[:-1]
    neg = x < 0
    s = f'{abs(x)}'
    if '.' in s:
        w, f = s.split('.')
        f = f.rstrip('0')
        out = whole(int(w)) + ((' point ' + ' '.join(ones[int(c)] for c in f)) if f else '')
    else:
        out = whole(int(s))
    return (('minus ' if neg else '') + out + (' ' + unit if unit else '')).strip()


# ---------- geometry helpers ----------
def stadium_width(x, c1, c2, r):
    """Width (across z) of a slot of radius r whose end-centres run from c1 to c2 along x, cut by the line at x."""
    if c1 <= x <= c2: return 2 * r
    d = c1 - x if x < c1 else x - c2
    return 2 * math.sqrt(r * r - d * d) if d < r else 0.0


def worst_cut(i, travel):
    """Largest total cut-out width on any line across the motor flange (constant x), and where it is."""
    lo, hi = i['a'] - i['T'] / 2, i['a'] - i['T'] / 2 + travel      # motor-centre range; slots grow away from the bend
    h = i['m3_pat'] / 2
    best = (0.0, 0.0)
    for k in range(int(i['L_motor'] / 0.005) + 1):
        x = k * 0.005
        w = stadium_width(x, lo - i['pilot_end_ext'], hi + i['pilot_end_ext'], i['pilot_slot'] / 2) + 2 * stadium_width(x, lo - h, hi - h, i['m3_slot'] / 2) \
            + 2 * stadium_width(x, lo + h, hi + h, i['m3_slot'] / 2)
        if w > best[0] + 1e-9: best = (w, x)
    return best


def seg_dist(p1, p2, q1, q2):
    """Shortest distance between two 2-D segments (stadium centre lines)."""
    def pt_seg(p, a, b):
        ax, ay = b[0] - a[0], b[1] - a[1]
        L2 = ax * ax + ay * ay
        u = 0 if L2 == 0 else max(0, min(1, ((p[0] - a[0]) * ax + (p[1] - a[1]) * ay) / L2))
        return math.hypot(p[0] - a[0] - u * ax, p[1] - a[1] - u * ay)
    return min(pt_seg(p1, q1, q2), pt_seg(p2, q1, q2), pt_seg(q1, p1, p2), pt_seg(q2, p1, p2))


def channel(B, H, t):
    """Lipped flange = web B x t plus two lips t x (H - t); s from the motor seat face. Returns A, centroid, I (and I a second way)."""
    rows = [(B, t, t / 2), (t, H - t, t + (H - t) / 2), (t, H - t, t + (H - t) / 2)]
    A = sum(w * h for w, h, _ in rows)
    sbar = sum(w * h * s for w, h, s in rows) / A
    I = sum(w * h ** 3 / 12 + w * h * (s - sbar) ** 2 for w, h, s in rows)
    I_face = sum(w * h ** 3 / 12 + w * h * s * s for w, h, s in rows)
    return dict(A=A, sbar=sbar, I=I, I_check=I_face - A * sbar * sbar)


def cut_width(i, x, travel):
    """Total cut-out width (pilot slot + 4 M3 slots, full travel) on the line across the motor flange at x from datum A."""
    lo, hi = i['a'] - i['T'] / 2, i['a'] - i['T'] / 2 + travel      # motor-centre range; slots grow away from the bend
    h = i['m3_pat'] / 2
    return stadium_width(x, lo - i['pilot_end_ext'], hi + i['pilot_end_ext'], i['pilot_slot'] / 2) + 2 * stadium_width(x, lo - h, hi - h, i['m3_slot'] / 2) \
        + 2 * stadium_width(x, lo + h, hi + h, i['m3_slot'] / 2)


def stiffness(i, t, E, near_row, F, lipped=False, travel=None, slots=True, n=4000):
    """Shaft tilt = springs in series between the end face and the motor (rad), and pulley movement along the belt (mm).
    mount: mounting flange propped by the end face at the heel, clamped at the bolt row (gross section; upper bound);
    bend: bend zone (mid-plane arc, gross section); gap: unlipped strip (lipped route only);
    flange: motor flange from the bend tangent (or lip start) to the near screw row, integral of M dx / (E I(x)):
    gross section where there is no cut-out, NET section (real slot widths at each x, full travel) in the slot zone.
    Motor body and its screws are taken as rigid (non-conservative)."""
    travel = i['T'] if travel is None else travel
    R = i['R_over_t'] * t; c = t + R
    EI = E * i['b'] * t ** 3 / 12
    M = F * i['p']; Mh = F * (i['p'] + c)
    th = {'mount': Mh * (i['L1'] - c) / (4 * EI), 'bend': Mh * (math.pi / 2) * (R + t / 2) / EI}
    x0 = i['lip_start'] if lipped else c
    th['gap'] = M * (x0 - c) / EI if lipped else 0.0
    dx = (near_row - x0) / n; flex = 0.0                                    # midpoint rule, integral of dx / I(x)
    for k in range(n):
        x = x0 + (k + 0.5) * dx
        w = cut_width(i, x, travel) if slots else 0.0
        flex += dx / (channel(i['B_motor'] - w, i['H_lip'], t)['I'] if lipped else (i['b'] - w) * t ** 3 / 12)
    th['flange'] = M * flex / E
    tot = sum(th.values())
    return th, tot, tot * (i['p'] + c)


def strength(i, t, Sy, F, cut):
    """FOS of the flat bracket at thickness t: bend zone, lumped net section, real worst line, mounting flange through the M5 holes."""
    R = i['R_over_t'] * t; c = t + R
    M = F * i['p']; Mh = F * (i['p'] + c)
    b_net = i['b'] - i['pilot_slot'] - 2 * i['m3_slot']
    return dict(bend=Sy / (6 * M / (i['b'] * t ** 2)), net=Sy / (6 * M / (b_net * t ** 2)),
                real=Sy / (6 * M / ((i['b'] - cut) * t ** 2)), holes=Sy / (6 * Mh / ((i['b'] - 2 * i['hole_M5']) * t ** 2)))


# acceptance limits are printed so that they never accept a failing value: UPPER limits rounded DOWN, LOWER limits rounded UP (FOS keys: always down)
LIM_UPPER = {'stack_t_hi', 'stack_t_hi_zmax', 'stack_t_hi_zmin', 'stack_grip_hi', 'stack_allowed', 'stack_allowed_plated', 'slot_fit_allowed_plated',
             'zinc_um_stack_limit', 'misalign_budget', 'mis_static_budget', 'perp_motor_seat_needed', 'mis_set_accept_mm', 'mis_opt_b_range',
             'fea_tilt_hi_revA', 'fea_tilt_hi_revB', 'fea_move_hi_revA', 'fea_move_hi_revB', 'fea_stress_hi_revA', 'fea_stress_hi_revB',
             'fea_line2_hi_revA', 'fea_line2_hi_revB', 'fea_bend_hi', 'fea_peak_hi',
             'mis_p_accept_mm', 'mis_c_accept_mm', 'mis_d_accept_mm', 'mis_s1_margin', 'mis_s2_margin', 'mis_s3_margin', 'mis_drv_margin', 'mis_idl_margin',
             'mis_drv_margin_pct', 'mis_idl_margin_pct', 'mis_rep_spread_mm', 'mis_flat_accept_mm', 'mis_drv_range',
             'stack_margin', 'slot_fit_allowed', 'slot_fit_margin', 'motor_pat_pos_req', 'pilot_clear', 'pilot_clear_side', 'pilot_slot_pos_max',
             'pilot_slot_pos_margin', 'pilot_end_clear_nom_revA', 'pilot_end_clear_nom_revB', 'pilot_end_clear_worst_revA', 'pilot_end_clear_worst_revB', 'pilot_end_clear_move_nom_revA', 'pilot_end_clear_move_nom_revB', 'pilot_end_clear_move_worst_revA', 'pilot_end_clear_move_worst_revB', 'pilot_end_clear_corner_revA', 'pilot_end_clear_corner_revB', 'laser_cut_M5_max', 'laser_cut_M3_slot_max', 'laser_cut_pilot_max'}
# error totals are printed rounded UP, so a printed total never looks smaller than it is (margins: in LIM_UPPER, rounded DOWN)
ROUND_UP = {'mis_drv_static_worst', 'mis_idl_static_worst', 'mis_u_pulley', 'mis_u_clamp', 'mis_s1_total', 'mis_s2_total', 'mis_s3_total', 'mis_drv_total', 'mis_idl_total',
            'mis_s1_total_peak', 'mis_opt_noidl_total', 'mis_twist_worst', 'mis_twist_strain', 'mis_drv_shift_max'}
LIM_LOWER = {'stack_t_lo', 'eng_M3_req', 'engD_M3_req', 'eng_M3_full_req', 'hb_required', 'study_o1_hb_required', 'study_o2_hb_required', 'study_ga12_hb_required',
             'study_ga13_hb_required', 'study_o3_hb_required', 'fea_tilt_lo_revA', 'fea_tilt_lo_revB', 'fea_move_lo_revA', 'fea_move_lo_revB',
             'fea_stress_lo_revA', 'fea_stress_lo_revB', 'fea_line2_lo_revA', 'fea_line2_lo_revB', 'fea_bend_lo', 'fea_peak_lo',
             'laser_cut_M5_min', 'laser_cut_M3_slot_min', 'laser_cut_pilot_min', 'pilot_end_ecr_ext'}
RAW = {}   # unrounded value of every numeric key: every limit and gate computation reads these (printed values are rounded at output only)


def compute(i):
    v = {}
    RAW.clear()
    rv_ = lambda k: RAW[k] if k in RAW else v[k]['value']

    def put(name, val, unit, formula, nd=2, speak=True):
        if isinstance(val, (int, float)) and not isinstance(val, bool): RAW[name] = val
        if isinstance(val, float) and (name.startswith('FOS_') or '_FOS_' in name or name in LIM_UPPER):
            val_r = math.floor(val * 10 ** nd + 1e-9) / 10 ** nd      # every factor of safety and every UPPER acceptance limit is rounded DOWN
        elif isinstance(val, float) and (name in LIM_LOWER or name in ROUND_UP):
            val_r = math.ceil(val * 10 ** nd - 1e-9) / 10 ** nd       # every LOWER acceptance limit is rounded UP
        else:
            val_r = round(val, nd) if isinstance(val, float) else val
        if isinstance(val_r, float) and val_r.is_integer():
            val_r = int(val_r)
        v[name] = dict(value=val_r, unit=unit, formula=formula,
                       spoken=spoken(val_r, UNIT_WORD.get(unit, '')) if speak and isinstance(val_r, (int, float)) else '')

    def text(name, val, formula='input'):
        v[name] = dict(value=val, unit='', formula=formula, spoken='')

    def flag(name, ok, formula):
        v[name] = dict(value='PASS' if ok else 'FAIL', unit='', formula=formula, spoken='')

    units_in = {'F_max': 'N', 'motor_weight': 'N', 'p': 'mm', 'b': 'mm', 'Sy': 'MPa', 'E': 'MPa', 'rho_al': 'g/cm^3', 'Sy_min_ksi': 'ksi', 'Sy_min_EN485': 'MPa', 'Sy_steel_min': 'MPa', 'Sy_steel_dc01_design': 'MPa', 'tol_laser_pos': 'mm', 'tol_tapped_pos': 'mm', 'torque_tol_pct': '%', 'Sy_steel': 'MPa',
                'E_steel': 'MPa', 'rho_steel': 'g/cm^3', 'Su_steel': 'MPa', 'move_limit': 'mm', 't1': 'mm', 't2': 'mm', 't_steel': 'mm', 'a': 'mm', 'T': 'mm',
                'T_revB': 'mm', 'L1': 'mm', 'y2': 'mm', 'L_M5': 'mm', 'washer_M5': 'mm', 'depth_M5': 'mm', 'L_M3': 'mm', 'L_M3_next': 'mm',
                'washer_M3': 'mm', 'depth_M3': 'mm', 'head_M3': 'mm', 'preload_M5': 'N', 'preload_M3': 'N', 'shaft_radial_allowed': 'N',
                'shaft_load_distance': 'mm', 'pilot_slot': 'mm', 'm3_slot': 'mm', 'm3_pat': 'mm', 'hole_M5': 'mm', 'drill_M5': 'mm',
                'drill_dia_M5': 'mm', 'As': 'mm^2', 'proof': 'MPa', 'L_mount': 'mm', 'L_motor': 'mm', 'tol_laser': 'mm',
                'tol_across_bend': 'mm', 'tol_bend_angle': 'deg', 'tol_tapped': 'mm', 'tilt_guide': 'deg', 'tilt_limit': 'deg',
                'hook_ep05_load': 'N', 'zinc_um': 'um', 'B_motor': 'mm', 'H_lip': 'mm', 'lip_start': 'mm', 't_alt1': 'mm', 't_alt2': 'mm',
                'belt_pitch': 'mm', 'belt_width': 'mm', 'T_motor_peak': 'N.m', 'Sf_5052': 'MPa', 'd_shaft': 'mm', 'bearing_inset': 'mm',
                'k_5052': 'W/m.K', 'k_steel': 'W/m.K', 'k_ss304': 'W/m.K', 'k_PA66': 'W/m.K', 'ambient_min': 'degC', 'ambient_max': 'degC', 'motor_case_limit': 'degC', 'qty_year': '/year',
                'qty_year_cast': '/year', 'pilot_slot_move': 'mm',
                't_tol': 'mm', 'L_M3_tol': 'mm', 'L_M3_next_tol': 'mm', 'washer_M3_tol': 'mm', 'torque_M3': 'N.m', 'tau_motor': 'MPa',
                'P_M3': 'mm', 'd_min_M3': 'mm', 'D2_max_M3': 'mm', 't1_tol': 'mm', 't_alt2_tol': 'mm',
                'act109_t': 'mm', 'L_M4': 'mm', 'L_M4_tol': 'mm', 'd_M4': 'mm', 'P_M4': 'mm', 'd_min_M4': 'mm', 'D2_max_M4': 'mm', 'depth_M4': 'mm', 'tau_6061': 'MPa', 'preload_M4': 'N', 'act109_t_tol': 'mm', 'L_M4_short': 'mm', 'L_M4_short_tol': 'mm', 'motor_body': 'mm', 'k_M5': 'mm', 'key_leg_M5': 'mm', 'act105_wall': 'mm'}
    src_special = {
        'Sy': 'input: 5052-H32 sheet, typical published value (Ep 05/06 baseline); same as shelf_al_Sy',
        'E': 'input: 5052-H32, typical (Ep 05/06 baseline); same as shelf_al_E',
        'rho_al': 'input: 5052, typical; same as shelf_al_rho',
        'Sy_steel': 'input: cold-rolled low-carbon steel sheet, TYPICAL yield, for the Ep 07 comparison only (same as shelf_steel_Sy); FOS gates use Sy_steel_min',
        'Sy_min_ksi': 'input: 5052-H32 sheet, specified minimum yield (0.2 % offset) in ASTM B209; gate value for the Ep 05/06 baseline',
        'Sy_min_EN485': 'input (information): 5052 H32 sheet, specified minimum Rp0.2 in EN 485-2; lower than ASTM B209 - a part bought to EN 485-2 must be checked at this value',
        'Sy_steel_min': 'input: ASTM A1008/A1008M SS Grade 30 [205], specified minimum yield; gate value for the released ACT-103 (mill certificate EN 10204 3.1 shows the lot)',
        'Sy_steel_dc01_design': 'input (information): EN 10130 DC01 specifies no minimum yield; this lower design value is published by a steel mill, not a requirement of the standard',
        'tol_laser': 'input: laser-cut hole SIZE tolerance, +/- (typical, confirm with supplier); hole POSITION is tol_laser_pos (a diameter zone)',
        'tol_laser_pos': 'input: laser-cut hole centre within this diameter of true position (typical, confirm with supplier)',
        'tol_tapped_pos': 'input: CNC tapped-hole centre within this diameter of true position (typical, confirm with the machine shop)',
        't_steel': 'input: RELEASED ACT-103 thickness, flat cold-rolled low-carbon steel, inside R = t',
        't2': 'input: 2.0 mm, aluminium baseline thickness option (Ep 05/06) and the thinner steel option in Ep 06; NOT the released part (t_steel)',
        'p': 'input: motor mounting face (motor-side face of the motor flange) to belt centre line',
        'shaft_load_distance': 'input (SAMPLE datasheet): the allowed radial load is rated at this distance from the motor mounting face - the same reference as p',
        'E_steel': 'input: steel, typical; same as shelf_steel_E (also used for the motor shaft)',
        'rho_steel': 'input: steel, typical; same as shelf_steel_rho',
        'Su_steel': 'input: typical tensile strength of the same sheet (fatigue estimate only)',
        'tilt_guide': 'input: published synchronous-belt guidance: TOTAL angular misalignment between the pulleys (static + elastic) under 1/4 deg (belt maker wins)',
        'tilt_limit': 'input: PDS R11 limit, shaft tilt caused by the bracket under the design load (illustrative, set from the guidance)',
        'K_bend': 'input (illustrative): for steel at R = t this agrees with the DIN 6935 correction-factor rule; the supplier confirms on their tooling',
        'R_over_t': 'input: inside bend radius = 1 x t; low-carbon steel can bend tighter, R = t keeps the flat pattern and hole-to-bend rules unchanged',
        'zinc_um': 'input: zinc electroplate after forming, minimum local thickness, with Cr(VI)-free passivation (ISO 19598 or ASTM B633 Type V or VI; supplier states the designation)',
        'Sf_5052': 'input: typical handbook fatigue strength of 5052-H32 at 5 x 10^8 cycles',
        'k_5052': 'input: thermal conductivity of 5052-H32, typical; the maker\'s data governs (138 W/m.K in two published data sheets: Elgin 5052-H32 fact sheet; Austral Wright 5052)',
        'k_steel': 'input: thermal conductivity of low-carbon steel sheet, typical; the maker\'s data governs (published 49.8-51.9 W/m.K for 1008/1010: Industrial Metal Supply 1008 guide; Xmake 1010 data)',
        'k_ss304': 'input: thermal conductivity of 304 stainless, typical; the maker\'s data governs (16.2 W/m.K: Aalco 1.4301 data sheet; thyssenkrupp 1.4307/304L data sheet)',
        'k_PA66': 'input: thermal conductivity of PA66, dry, unfilled, typical; the maker\'s data governs (published 0.24-0.33 W/m.K, NETZSCH polymer database; 0.36, Ensinger TECAMID 66: typical value taken 0.3)',
        'ambient_min': 'input: PDS R7 lower ambient',
        'ambient_max': 'input: PDS R7 upper ambient',
        'motor_case_limit': 'input (SAMPLE motor datasheet value; the real motor maker wins)',
        'depth_M3': 'input (SAMPLE motor datasheet): full thread depth of the motor M3 holes, 4.5 mm min (typical of NEMA 17-size motors); the real motor maker wins',
        't_tol': 'input: drawing thickness tolerance +/- for the 2.5 mm sheet; equals the EN 10131 normal tolerance for 2.00 < t <= 2.50 mm (Re < 260 MPa, width up to 1200 mm); stated on the drawing so a mill tolerance (ASTM A568 for A1008 sheet) cannot be read two ways',
        'L_M3_tol': 'input: ISO 4762 length limits for M3 x 6, 5.76-6.24 mm (product grade A, ISO 4759-1)',
        'L_M3_next_tol': 'input: ISO 4762 length limits for M3 x 8, 7.71-8.29 mm',
        'washer_M3_tol': 'input: ISO 7089 size 3 washer thickness 0.5 mm, limits 0.45-0.55 mm',
        'torque_M3': 'input (SAMPLE motor datasheet): screw torque into the motor threads, used as the assembly torque; the real motor maker wins',
        'K_min': 'input (illustrative): low end of the nut-factor scatter, for a plated or lubricated screw (note_K_dry); gives the most preload at the same torque',
        'tau_motor': 'input (SAMPLE motor data): motor housing taken as die-cast aluminium of the A380 type, typical ultimate shear strength (published typical value; the motor maker wins)',
        'P_M3': 'input: M3 coarse pitch',
        'd_min_M3': 'input: M3 6g screw thread, smallest major diameter (ISO 965 limits): least-material screw',
        'D2_max_M3': 'input: M3 6H internal thread, largest pitch diameter (ISO 965 limits): least-material nut thread',
        'strip_gate': 'input (illustrative course gate): thread-strip force at the worst tolerance corner / nominal assembly preload',
        'thread_end_P': 'input: incomplete thread at the screw end, in pitches; ISO 4753 allows u <= 2P, so the strip check deducts it (full threads only)',
        'lead_in_P': 'input: lead-in / countersink at the motor hole entry, in pitches (not full thread; assumed, the motor maker confirms)',
        'act109_t': 'input: ACT-109 clamp-flange thickness under the 2x M4 heads (design value for the ACT-109 drawing)',
        'L_M4_tol': 'input: ISO 4762 length limits for M4 x 12, 11.65-12.35 mm',
        'd_min_M4': 'input: M4 6g screw thread, smallest major diameter (ISO 965 limits)', 'D2_max_M4': 'input: M4 6H internal thread, largest pitch diameter (ISO 965 limits)',
        'depth_M4': 'input: full-thread depth of the 2x M4 tapped holes in ACT-101 Rev B (drawing value)',
        'tau_6061': 'input: 6061-T6 typical shear strength (published typical value; information check only - the 1.5D rule is the gate)',
        'preload_M4': 'input (illustrative): preload of each COTS-221 M4 screw',
        't_alt2_tol': 'input (information, route a): EN 485-4 thickness tolerance +/-, Group II, 2.60-3.0 mm, width up to 1000 mm',
        'motor_body': 'input (SAMPLE motor data): NEMA 17-size motor body, square across flats, 42 mm (42.3 typical); the motor maker wins',
        'k_M5': 'input: ISO 4762 M5 socket head cap screw, head height k = 5 mm (max)',
        'key_leg_M5': 'input: ISO 2936 hexagon socket screw key s = 4 mm (for the M5 socket heads), short leg l2; tables in circulation give 25 mm and 29 mm, the smaller is used so the claim holds for any standard key',
        'act105_wall': 'input: ACT-105 protective top cover, ABS, nominal wall (Actuator EBOM)',
        't1_tol': 'input: EN 485-4 thickness tolerance +/-, Group II alloys (5052), 1.21-1.50 mm, width up to 1000 mm (0.11 at 1250 mm wide)',
    }
    order = ['F_max', 'k_dyn', 'motor_weight', 'p', 'b', 'Sy', 'E', 'rho_al', 'Sy_steel', 'Sy_min_ksi', 'Sy_min_EN485', 'Sy_steel_min', 'Sy_steel_dc01_design', 'E_steel', 'rho_steel', 'Su_steel', 'FOS_gate',
             'move_limit', 't1', 't2', 't_steel', 'a', 'T', 'T_revB', 'L1', 'y2', 'L_M5', 'washer_M5', 'depth_M5', 'L_M3', 'L_M3_next', 'washer_M3',
             'depth_M3', 'head_M3', 'preload_M5', 'preload_M3', 'mu', 'K', 'K_bend', 'R_over_t', 'shaft_radial_allowed', 'shaft_load_distance',
             'pilot_slot', 'm3_slot', 'm3_pat', 'hole_M5', 'drill_M5', 'drill_dia_M5', 'As', 'proof', 'L_mount', 'L_motor', 'tol_laser',
             'tol_laser_pos', 'tol_across_bend', 'tol_bend_angle', 'tol_tapped_pos', 'torque_tol_pct', 'tilt_guide', 'tilt_limit', 'hook_ep05_load', 'zinc_um', 'B_motor', 'H_lip',
             'lip_start', 't_alt1', 't_alt2', 'pulley_teeth', 'belt_pitch', 'belt_width', 'T_motor_peak', 'FOS_stall_gate', 'Sf_5052',
             'd_shaft', 'bearing_inset', 'k_5052', 'k_steel', 'k_ss304', 'k_PA66', 'ambient_min', 'ambient_max', 'motor_case_limit', 'qty_year', 'qty_year_cast', 'pilot_slot_move',
             't_tol', 'L_M3_tol', 'L_M3_next_tol', 'washer_M3_tol', 'torque_M3', 'K_min', 'tau_motor', 'P_M3', 'd_min_M3', 'D2_max_M3', 'strip_gate', 't1_tol', 't_alt2_tol',
             'thread_end_P', 'lead_in_P', 'act109_t', 'L_M4', 'L_M4_tol', 'd_M4', 'P_M4', 'd_min_M4', 'D2_max_M4', 'depth_M4', 'tau_6061', 'preload_M4', 'act109_t_tol', 'L_M4_short', 'L_M4_short_tol', 'motor_body', 'k_M5', 'key_leg_M5', 'act105_wall']
    for k in order:
        src = src_special.get(k, 'input (illustrative or typical value for teaching; see the course disclaimer)' if k in ILLUS else 'input')
        if k in ('T_motor_peak', 'd_shaft', 'bearing_inset', 'm3_pat'): src = 'input (SAMPLE motor / pulley data; maker wins)'
        if k in ('B_motor', 'H_lip', 'lip_start', 't_alt1', 't_alt2'): src = 'input: Ep 06 route comparison only (not on the released part)'
        put(k, i[k], units_in.get(k, '-'), src, nd=4 if k.endswith('_in') else 0 if k == 'preload_M3' else 3, speak=k not in ('k_5052', 'k_steel', 'k_ss304', 'k_PA66', 'Sy_min_ksi'))
    for k in ('rho_al', 'rho_steel'):
        v[k]['spoken'] = spoken(i[k], 'grams per cubic centimetre')

    fm = lambda x: f'{x:g}'
    put('tol_tapped', i['tol_tapped_pos'] / 2, 'mm', 'RETIRED (no script tag uses it; never show): tol_tapped_pos / 2, RADIUS of the tapped-hole position zone. Show the diameter zone tol_tapped_pos, never +/- per axis', 3)
    text('laser_capability', f"laser: hole size \u00b1{fm(i['tol_laser'])}; hole centre within \u00d8{fm(i['tol_laser_pos'])} of true position (typical, confirm with supplier)",
         'tol_laser (size) and tol_laser_pos (position, diameter zone)')
    text('tapped_capability', f"CNC tapped hole: hole centre within \u00d8{fm(i['tol_tapped_pos'])} of true position (typical, confirm with the machine shop)",
         'tol_tapped_pos (position, diameter zone; same method as the laser hole)')
    text('material', f"cold-rolled low-carbon steel sheet, {i['t_steel']:.1f} mm, ASTM A1008/A1008M SS Grade 30 [205] (specified minimum yield, used by every FOS gate); "
         "the drawing states the thickness in mm, never a gauge alone; equivalents are nearest, not identical (a commercial grade such as ASTM A1008 CS or EN 10130 DC01 has no specified minimum yield)",
         'course decision 13 Nov (steel); thickness grade course decision')
    text('finish', f"zinc electroplate after forming, {i['zinc_um']:.0f}-{i['zinc_um_max']:.0f} um on significant surfaces (minimum {i['zinc_um']:.0f}, maximum {i['zinc_um_max']:.0f}: course practice; ASTM B633 classes give minimums only; holes and threads normally exempt from the minimum), with Cr(VI)-free passivation (ISO 19598, or ASTM B633 Type V or VI); alternative: powder coat after forming. Deburr before finishing.",
         'course decision 13 Nov; finish chosen for an indoor, non-condensing environment (PDS R7); standard numbers checked: ISO 2081 now covers Cr(VI) treatments only')
    text('galvanic_note', 'Zinc-plated steel bracket on the anodized aluminium end block (ACT-101): zinc and aluminium sit close together in the galvanic series and the anodic film insulates, so the risk is low indoors and dry (PDS R7). Keep the joint dry; for humid or outdoor use, add an insulating washer or sealant. Low-carbon sheet at its low hardness needs no hydrogen-embrittlement bake after plating (that rule is for high-strength parts, for example class 10.9 screws).')
    text('Sy_source', "typical published value for 5052-H32 sheet: Ep 07 comparison only; the Ep 05/06 FOS gates use Sy_min, the specified minimum in ASTM B209 (lower, so every FOS is lower by the same ratio)")
    text('Sy_steel_source', "typical published value for cold-rolled low-carbon steel sheet: Ep 07 comparison only; FOS gates use Sy_steel_min (ASTM A1008/A1008M SS Grade 30 [205]); the mill certificate (EN 10204 3.1) shows the lot")
    put('Sy_min', i['Sy_min_ksi'] * 6.894757, 'MPa', 'Sy_min_ksi x 6.895: 5052-H32 specified minimum yield, ASTM B209 (FOS gate value, Ep 05/06 baseline)', 1)
    put('Sy_min_ratio', i['Sy_min_ksi'] * 6.894757 / i['Sy'], '-', 'Sy_min / Sy (typical): every aluminium FOS on the minimum is this fraction of the typical-value FOS', 2)
    put('Sy_steel_min_ratio', i['Sy_steel_min'] / i['Sy_steel'], '-', 'Sy_steel_min / Sy_steel (typical)', 2)
    Sa = i['Sy_min_ksi'] * 6.894757; Ss = i['Sy_steel_min']

    F = i['F_max'] * i['k_dyn']; t = i['t_steel']; R = i['R_over_t'] * t; c = t + R      # released part
    put('t_rel_in', t / 25.4, 'in', 't_steel / 25.4 (released thickness in inches)', 3)
    put('F_design', F, 'N', 'F_max x k_dyn')
    put('pulley_distance', i['p'], 'mm', 'same as p: motor mounting face (motor-side face of the motor flange) to belt centre line')
    M = F * i['p']; put('M', M, 'N.mm', 'F_design x p; constant along the motor flange from the bend to the near motor screws (slightly conservative: see M_mid)')
    Mh = F * (i['p'] + c); put('M_heel', Mh, 'N.mm', 'F_design x (p + c), c = t + R, released thickness: moment about the heel (conservative: see M_heel_exact)', 0)
    put('lever_mid', i['p'] - t / 2, 'mm', 'p - t/2: lever arm from the belt centre line to the motor-flange mid-plane (noted refinement, course decision)', 2)
    put('M_mid', F * (i['p'] - t / 2), 'N.mm', 'F_design x (p - t/2): exact bending moment at the flange mid-plane; M = F p overstates it slightly (conservative)', 0)
    put('M_heel_exact', F * (i['p'] + R), 'N.mm', 'F_design x (p + R): with p from the motor-side face, the pulley side is t further from the heel than p + c assumes; M_heel is conservative', 0)
    put('M_conserv_pct', (M / (F * (i['p'] - t / 2)) - 1) * 100, '%', 'M / M_mid - 1: how much M = F p overstates the mid-plane moment', 1)
    put('R_bend', R, 'mm', 'inside bend radius = R_over_t x t_steel (released part)', 1)
    put('R_rel', R, 'mm', 'R = R_over_t x t_steel: inside bend radius of the released part, used in BA_rel, flat_rel and hb_required (same value as R_bend)', 1)
    put('c_rel', c, 'mm', 'c = t + R: bend tangent from the outside face of the other flange (released part)', 1)

    # ---------- Ep 05: strength, 5052-H32 baseline ----------
    b_net = i['b'] - i['pilot_slot'] - 2 * i['m3_slot']
    put('b_net', b_net, 'mm', 'LUMPED: b - pilot slot - 2 x M3 slot, as if every cut-out lay on one line (conservative quick check)')
    cutA, xA = worst_cut(i, i['T']); cutB, xB = worst_cut(i, i['T_revB'])
    put('b_net_real', i['b'] - cutA, 'mm', f'b - widest real cut on one line across the flange (Rev A; line at {xA:.1f} mm from datum A)', 2)
    put('b_net_real_revB', i['b'] - cutB, 'mm', f'same, Rev B slots (line at {xB:.1f} mm from datum A)', 2)
    put('x_worst_line', xA, 'mm', 'position of the worst real cut-out line from datum A (Rev A)', 1)
    put('b_net_real_calc', i['b'] - cutA, 'mm', 'b_net_real to 0.001 mm for Calc_Sheet_Template.xlsx: the sheet writes sigma to 0.1 MPa, and the 0.01 mm print (24.52) would round sigma to 65.3 and the FOS to 2.42 instead of 65.2 / 2.43', 3, speak=False)
    for tag, tt in (('t1', i['t1']), ('t2', i['t2'])):
        sb = 6 * M / (i['b'] * tt ** 2); sn = 6 * M / (b_net * tt ** 2); sr = 6 * M / ((i['b'] - cutA) * tt ** 2)
        put(f'sigma_bend_{tag}', sb, 'MPa', '6M / (b t^2) at the bend (quick check)', 1)
        put(f'FOS_bend_{tag}', Sa / sb, '-', 'Sy_min / sigma_bend (5052-H32 baseline, specified minimum yield)')
        put(f'sigma_net_{tag}', sn, 'MPa', '6M / (b_net t^2), lumped net section (conservative)', 1)
        put(f'sigma_net_{tag}_ksi', sn / 6.894757, 'ksi', 'MPa / 6.895', 1)
        put(f'FOS_net_{tag}', Sa / sn, '-', 'Sy_min / sigma_net (lumped, 5052-H32 baseline, specified minimum yield)')
        put(f'sigma_netreal_{tag}', sr, 'MPa', '6M / (b_net_real t^2) on the real worst cut-out line', 1)
        put(f'FOS_netreal_{tag}', Sa / sr, '-', 'Sy_min / sigma_netreal (5052-H32 baseline, specified minimum yield)')
        put(f'FOS_netreal_{tag}_EN485', i['Sy_min_EN485'] / sr, '-', 'information: Sy_min_EN485 / sigma_netreal (if the sheet were bought to EN 485-2)')
        flag(f'bend_check_{tag}', Sa / sb >= i['FOS_gate'], 'FOS_bend >= gate')
        flag(f'net_check_{tag}', Sa / sn >= i['FOS_gate'], 'lumped FOS_net >= gate (conservative screen)')
        flag(f'netreal_check_{tag}', Sa / sr >= i['FOS_gate'], 'FOS on the real worst line >= gate')
        flag(f'strength_check_{tag}', min(Sa / sb, Sa / sr) >= i['FOS_gate'], 'min(bend, real net) FOS >= gate (specified minimum yield)')

    # Ep 05: 1.5 mm is below the gate on the real worst line at nominal (pilot slot 0.5 longer per end); show the number at the minimum thickness
    t1m = i['t1'] - i['t1_tol']
    put('t1_min', t1m, 'mm', 't1 - t1_tol: thinnest 1.5 mm 5052 sheet bought to EN 485-4 (Group II, width up to 1000 mm)', 2)
    put('FOS_netreal_t1_min', Sa / (6 * M / ((i['b'] - cutA) * t1m ** 2)), '-',
        'Sy_min / sigma_netreal at t1_min (FOS scales with t^2): below the gate as soon as the sheet is on the minus side', 2)
    flag('netreal_check_t1_min', Sa / (6 * M / ((i['b'] - cutA) * t1m ** 2)) >= i['FOS_gate'], 'FOS on the real worst line at t1_min >= gate (expected FAIL)')

    # ---------- Ep 06: stiffness, flat aluminium baseline (accurate model) ----------
    nearA = i['a'] + i['T'] / 2 - i['m3_pat'] / 2
    nearB = i['a'] - i['T'] / 2 + i['T_revB'] - i['m3_pat'] / 2
    put('L_near_row', nearA, 'mm', 'a + T/2 - pattern/2: near motor-screw row from datum A, motor at the far end (worst)', 1)
    put('L_near_row_revB', nearB, 'mm', 'a - T/2 + T_revB - pattern/2 (Rev B)', 1)
    for tag, tt in (('t1', i['t1']), ('t2', i['t2'])):
        th, tot, mv = stiffness(i, tt, i['E'], nearA, F)
        put(f'I_flat_{tag}', i['b'] * tt ** 3 / 12, 'mm^4', 'b t^3 / 12', 2)
        put(f'theta_motor_{tag}', th['flange'], 'rad', 'M x integral(dx / (E I(x))) from the bend tangent c to the near screws: ' + MODEL + ' (aluminium)', 5, speak=False)
        put(f'theta_corner_{tag}', th['mount'] + th['bend'], 'rad', 'M_heel (L1 - c)/(4 E I) + M_heel (pi/2)(R + t/2)/(E I), c = t + R: propped mounting flange (upper bound) + bend zone (aluminium)', 5, speak=False)
        put(f'tilt_motor_{tag}', math.degrees(th['flange']), 'deg', 'motor-flange share of the tilt, slot zone at net section (aluminium)')
        put(f'tilt_total_{tag}', math.degrees(tot), 'deg', 'total shaft tilt, flat aluminium: mounting (propped) + bend + motor flange; ' + MODEL)
        put(f'move_{tag}', mv, 'mm', 'tilt (rad) x (p + c): pulley movement along the belt, flat aluminium; ' + MODEL)
        flag(f'stiff_check_{tag}', mv <= i['move_limit'], 'move <= move_limit (PDS R5)')
        flag(f'tilt_check_{tag}', math.degrees(tot) <= i['tilt_limit'], 'tilt_total <= tilt_limit (PDS R11)')

    # ---------- motor shaft flex (needed for every route's margin) ----------
    Ish = math.pi * i['d_shaft'] ** 4 / 64; Lsh = i['p'] + i['bearing_inset']
    sl = F * Lsh ** 2 / (2 * i['E_steel'] * Ish)
    put('tilt_shaft_est', math.degrees(sl), 'deg', 'estimate: motor shaft slope at the pulley, F (p + inset)^2 / (2 E I_shaft), design load, bearing taken as rigid; motor-dependent, not the bracket', 3)
    work = i['F_max'] / F

    def route(prefix, tt, E, lipped, label):
        th, tot, mv = stiffness(i, tt, E, nearA, F, lipped)
        tilt = math.degrees(tot)
        put(f'{prefix}_t', tt, 'mm', f'{label}: thickness', 1)
        put(f'{prefix}_tilt', tilt, 'deg', f'{label}: shaft tilt from the bracket, design load, Rev A worst motor position; ' + MODEL)
        put(f'{prefix}_move', mv, 'mm', f'{label}: pulley movement along the belt, design load; ' + MODEL)
        put(f'{prefix}_margin', i['tilt_limit'] - tilt, 'deg', f'{label}: tilt_limit - tilt (bracket only, design load)', 2)
        put(f'{prefix}_margin_pct', (i['tilt_limit'] - tilt) / i['tilt_limit'] * 100, '%', f'{label}: margin as % of tilt_limit', 0)
        sysw = (tilt + math.degrees(sl)) * work
        put(f'{prefix}_sys_work', sysw, 'deg', f'{label}: (bracket tilt + tilt_shaft_est) x F_max / F_design: bracket + motor shaft at the working load, before assembly misalignment', 3)
        put(f'{prefix}_sys_margin', i['tilt_limit'] - sysw, 'deg', f'{label}: tilt_limit - sys_work: what is left for misalignment at assembly', 3)
        put(f'{prefix}_sys_design', tilt + math.degrees(sl), 'deg', f'{label}: bracket + motor shaft at the design load (information)', 2)
        flag(f'{prefix}_check', tilt <= i['tilt_limit'] and mv <= i['move_limit'], 'tilt <= tilt_limit (R11) and move <= move_limit (R5)')
        tw = max(tilt, math.degrees(stiffness(i, tt, E, nearB, F, lipped, travel=i['T_revB'])[1]))
        put(f'{prefix}_tilt_worst', tw, 'deg', f'{label}: bracket tilt, design load, WORST revision (Rev A or Rev B, motor at the far end)', 3)
        put(f'{prefix}_margin_worst', i['tilt_limit'] - tw, 'deg', f'{label}: tilt_limit - tilt_worst (bracket only): use in Ep 06/07/23 tables', 3)
        put(f'{prefix}_margin_worst_pct', (i['tilt_limit'] - tw) / i['tilt_limit'] * 100, '%', f'{label}: margin_worst as % of tilt_limit', 0)
        put(f'{prefix}_sys_margin_worst', i['tilt_limit'] - (tw + math.degrees(sl)) * work, 'deg', f'{label}: tilt_limit - (tilt_worst + tilt_shaft_est) x F_max/F_design: left for assembly misalignment, worst revision', 3)
        put(f'{prefix}_sys_margin_worst_pct', (i['tilt_limit'] - (tw + math.degrees(sl)) * work) / i['tilt_limit'] * 100, '%', f'{label}: sys_margin_worst as % of tilt_limit', 0)
        return th, tot, mv

    # ---------- Ep 06: the three routes ----------
    th25, tot25, _ = stiffness(i, i['t_alt1'], i['E'], nearA, F)
    put('tilt_total_t25', math.degrees(tot25), 'deg', 'thickness-only, flat 2.5 mm aluminium')
    flag('tilt_check_t25', math.degrees(tot25) <= i['tilt_limit'], 'tilt_total_t25 <= tilt_limit')
    route('route_thick', i['t_alt2'], i['E'], False, 'route (a) thicker aluminium, flat 3.0 mm 5052-H32')
    v['tilt_total_t3'] = dict(v['route_thick_tilt'], formula='same as route_thick_tilt (flat 3.0 mm aluminium)')
    flag('tilt_check_t3', rv_('route_thick_tilt') <= i['tilt_limit'], 'tilt_total_t3 <= tilt_limit')
    e3 = i['L_M3'] - i['t_alt2'] - i['washer_M3']; e3n = i['L_M3_next'] - i['t_alt2'] - i['washer_M3']
    put('route_thick_eng_M3', e3, 'mm', 'M3 x 6 through 3.0 mm sheet: L - t - washer', 1)
    put('route_thick_engD_M3', e3 / 3, 'D', 'engagement / 3 mm (below 1D)', 2)
    put('route_thick_eng_M3_next', e3n, 'mm', 'next standard length M3 x 8: L - t - washer (needs depth >= engagement + 1)', 1)
    flag('route_thick_M3_check', (e3 / 3 >= 1.0 and i['depth_M3'] >= e3 + 1) or (e3n / 3 >= 1.0 and i['depth_M3'] >= e3n + 1),
         'quick screen at nominal (Ep 06 concept route): some standard M3 length gives >= 1D and no bottoming in the 4.5 mm motor thread; corner check: route_thick_FOS_strip_min')
    put('route_thick_mass_pct', (i['t_alt2'] / i['t2'] - 1) * 100, '%', 'extra metal vs flat 2.0 mm aluminium (same outline)', 0)

    route('route_steel', i['t_steel'], i['E_steel'], False, 'route (b) stiffer material, flat 2.5 mm low-carbon steel')
    # "why not thinner": 2.0 mm steel passes the bracket check but leaves no system margin
    tn = i['t2']; ntA = math.degrees(stiffness(i, tn, i['E_steel'], nearA, F)[1])
    ntB = math.degrees(stiffness(i, tn, i['E_steel'], nearB, F, travel=i['T_revB'])[1])
    put('route_steel_thin_t', tn, 'mm', 'thinner steel option (why not thinner)', 1)
    put('route_steel_thin_tilt', ntA, 'deg', '2.0 mm steel: bracket tilt, design load, Rev A; ' + MODEL, 2)
    put('route_steel_thin_tilt_revB', ntB, 'deg', '2.0 mm steel: bracket tilt, design load, Rev B', 2)
    flag('route_steel_thin_check', max(ntA, ntB) <= i['tilt_limit'], '2.0 mm steel: bracket tilt <= tilt_limit, Rev A and Rev B')
    put('route_steel_thin_sys_margin', i['tilt_limit'] - (max(ntA, ntB) + math.degrees(sl)) * work, 'deg',
        '2.0 mm steel: tilt_limit - (worst bracket tilt + tilt_shaft_est) x F_max / F_design: left for assembly misalignment', 3)
    put('route_steel_E_ratio', i['E_steel'] / i['E'], 'x', 'E_steel / E: the same shape is this many times stiffer', 2)
    _, totst1, mvst1 = stiffness(i, i['t1'], i['E_steel'], nearA, F)
    put('route_steel_tilt_t1', math.degrees(totst1), 'deg', 'flat 1.5 mm steel, same model (information; the Ep 06 why-not-thinner line uses route_steel_thin_*)')
    flag('route_steel_check_t1', math.degrees(totst1) <= i['tilt_limit'], 'tilt <= tilt_limit')

    thl, totl, mvl = route('route_lips', i['t2'], i['E'], True, 'route (c) shape, 2.0 mm 5052-H32 + two 12 mm lips')
    t = i['t2']   # route (c) is 2.0 mm aluminium
    ch = channel(i['B_motor'], i['H_lip'], t)
    put('route_lips_I', ch['I'], 'mm^4', 'composite rectangles: web B_motor x t + 2 lips t x (H_lip - t); sum(b h^3/12 + A d^2) (gross; in the slot zone the web is reduced by the cut-outs)', 0)
    put('route_lips_s_bar', ch['sbar'], 'mm', 'neutral axis from the motor seat face = sum(A s)/sum(A)', 2)
    put('route_lips_I_ratio', ch['I'] / (i['b'] * t ** 3 / 12), 'x', 'route_lips_I / I_flat_t2', 0)
    # D156 (D155 standards A #4): route_lips_I_ratio compares the 58 mm lipped web with the 50 mm flat flange, so it also
    # counts the wider web. Shape alone = the same section against a FLAT flange of the same web width B_motor.
    put('route_lips_I_ratio_same_web', ch['I'] / (i['B_motor'] * t ** 3 / 12), 'x',
        'route_lips_I / (B_motor t^3 / 12): lips vs a flat flange of the same 58 mm width (shape alone; D156)', 0)
    put('route_lips_corner_pct', (thl['mount'] + thl['bend'] + thl['gap']) / totl * 100, '%', 'share of the lipped tilt from the unlipped corner (the next weak spring)', 0)
    put('route_lips_mass_pct', 2 * (math.pi / 2 * (t + i['K_bend'] * t) + i['H_lip'] - 2 * t - (i['B_motor'] - 4 * t - i['b']) / 2) * (i['L_motor'] - i['lip_start'])
        / (((i['L_mount'] - 2 * t) + (i['L_motor'] - 2 * t) + math.pi / 2 * (t + i['K_bend'] * t)) * i['b']) * 100, '%',
        'extra blank area for the lip ears vs the flat 2.0 mm blank', 0)
    t = i['t_steel']
    v['route_lips_process'] = dict(value='3 bends; lips first, then the main bend with segmented tooling', unit='', formula='engineering analysis', spoken='')

    # ---------- masses (Ep 06 / 07) ----------
    flat_len = (i['L_mount'] - t - R) + (i['L_motor'] - t - R) + math.pi / 2 * (R + i['K_bend'] * t)
    holes = (i['pilot_slot'] * (i['T'] + 2 * i['pilot_end_ext']) + math.pi * (i['pilot_slot'] / 2) ** 2) + 4 * (i['m3_slot'] * i['T'] + math.pi * (i['m3_slot'] / 2) ** 2) \
        + 4 * math.pi * (i['hole_M5'] / 2) ** 2
    vol = (flat_len * i['b'] - holes) * t / 1000                     # cm^3
    put('mass_steel_g', vol * i['rho_steel'], 'g', '(flat_rel x b - holes and slots, Rev A) x t_steel x rho_steel (released part)', 0)
    ta = i['t2']; fla = (i['L_mount'] - 2 * ta) + (i['L_motor'] - 2 * ta) + math.pi / 2 * (ta + i['K_bend'] * ta)
    put('mass_al_g', (fla * i['b'] - holes) * ta / 1000 * i['rho_al'], 'g', 'flat 2.0 mm 5052 blank of the same outline (aluminium concept)', 0)
    put('mass_ratio_rel', vol * i['rho_steel'] / ((fla * i['b'] - holes) * ta / 1000 * i['rho_al']), 'x', 'mass_steel_g / mass_al_g: released steel part vs the 2.0 mm aluminium concept', 2)
    put('mass_ratio', i['rho_steel'] / i['rho_al'], 'x', 'rho_steel / rho_al (same as shelf V*_Ep07_mass_ratio)', 2)

    # ---------- FINAL DESIGN: 2.0 mm steel, flat ----------
    fsA = strength(i, t, Ss, F, cutA); fsB = strength(i, t, Ss, F, cutB)
    put('FOS_bend_steel', fsA['bend'], '-', 'Sy_steel_min / (6M / (b t^2)), bend zone', 2)
    put('FOS_net_steel', fsA['net'], '-', 'Sy_steel_min / (6M / (b_net t^2)), lumped screen', 2)
    put('FOS_netreal_steel', fsA['real'], '-', 'Sy_steel_min / (6M / (b_net_real t^2)), real worst cut-out line, Rev A', 2)
    put('FOS_netreal_steel_revB', fsB['real'], '-', 'same on the Rev B worst line (b_net_real_revB)', 2)
    put('sigma_mount_holes', 6 * Mh / ((i['b'] - 2 * i['hole_M5']) * t ** 2), 'MPa', '6 M_heel / ((b - 2 x hole) t^2): mounting flange through the two M5 holes', 1)
    put('FOS_mount_holes_steel', fsA['holes'], '-', 'Sy_steel_min / sigma_mount_holes', 2)
    fmin = min(fsA['bend'], fsA['net'], fsA['real'], fsB['real'], fsA['holes'])
    put('FOS_min_steel', fmin, '-', 'smallest FOS of the steel bracket on the specified minimum yield Sy_steel_min (bend, lumped net, real lines Rev A/B, M5 hole section)', 2)
    flag('strength_check_steel', fmin >= i['FOS_gate'], 'every section FOS >= FOS_gate (PDS R4), Rev A and Rev B, specified minimum yield')
    put('FOS_min_steel_typ', fmin * i['Sy_steel'] / Ss, '-', 'information (Ep 07 comparison only): FOS_min_steel on the TYPICAL yield Sy_steel', 2)
    put('FOS_min_steel_dc01', fmin * i['Sy_steel_dc01_design'] / Ss, '-', 'information: FOS_min_steel if a DC01 lot were only at Sy_steel_dc01_design (no specified minimum in EN 10130)', 2)

    thS, totS, mvS = stiffness(i, t, i['E_steel'], nearA, F)
    thSB, totSB, mvSB = stiffness(i, t, i['E_steel'], nearB, F, travel=i['T_revB'])
    put('theta_mount_steel', thS['mount'], 'rad', 'M_heel (L1 - c) / (4 E_steel I), c = t + R: mounting flange propped by the end face (gross section; upper bound, conservative)', 6, speak=False)
    put('theta_bend_steel', thS['bend'], 'rad', 'M_heel (pi/2)(R + t/2) / (E_steel I): bend zone (gross section)', 6, speak=False)
    put('theta_motor_steel', thS['flange'], 'rad', 'M x integral(dx / (E_steel I(x))) from c to L_near_row: motor flange, gross section elsewhere, net section in slot zone', 6, speak=False)
    _, totS_g, _ = stiffness(i, t, i['E_steel'], nearA, F, slots=False)
    _, totSB_g, _ = stiffness(i, t, i['E_steel'], nearB, F, travel=i['T_revB'], slots=False)
    put('slot_zone_start', min(x for x in (k * 0.005 for k in range(int(i['L_motor'] / 0.005) + 1)) if cut_width(i, x, i['T']) > 0), 'mm',
        'first line across the motor flange that cuts a slot (= near M3 slot end, hb_slot_edge): the slot zone runs from here to the near screw row', 1)
    put('tilt_gross_steel', math.degrees(totS_g), 'deg', 'information: the same tilt with the slots ignored (gross section everywhere, the previous model), Rev A', 3)
    put('tilt_gross_steel_revB', math.degrees(totSB_g), 'deg', 'information: same, Rev B', 3)
    put('tilt_slot_pct', (totSB / totSB_g - 1) * 100, '%', 'tilt_steel_revB / tilt_gross_steel_revB - 1: what the slot zone adds (Rev B, worst)', 0)
    put('tilt_mount_steel', math.degrees(thS['mount']), 'deg', 'theta_mount_steel in degrees', 3)
    put('tilt_bend_steel', math.degrees(thS['bend']), 'deg', 'theta_bend_steel in degrees', 3)
    put('tilt_motor_steel', math.degrees(thS['flange']), 'deg', 'theta_motor_steel in degrees', 3)
    put('tilt_steel', math.degrees(totS), 'deg', 'PDS R11 value: shaft tilt from the steel bracket, design load, motor at the far end (Rev A); ' + MODEL)
    put('tilt_steel_revB', math.degrees(totSB), 'deg', 'same, Rev B far end (longer slots, longer slot zone)')
    put('move_steel', mvS, 'mm', 'PDS R5 value: tilt (rad) x (p + c), Rev A; ' + MODEL)
    put('move_steel_revB', mvSB, 'mm', 'same, Rev B far end')
    put('tilt_margin_steel', i['tilt_limit'] - math.degrees(max(totS, totSB)), 'deg', 'tilt_limit - worst of tilt_steel, tilt_steel_revB', 2)
    put('tilt_margin_steel_pct', (i['tilt_limit'] - math.degrees(max(totS, totSB))) / i['tilt_limit'] * 100, '%', 'margin as % of tilt_limit', 0)
    put('tilt_sys_work_steel', (math.degrees(max(totS, totSB)) + math.degrees(sl)) * work, 'deg',
        '(worst tilt_steel + tilt_shaft_est) x F_max / F_design: bracket + motor shaft at the working load, before assembly misalignment', 3)
    put('tilt_sys_margin_steel', i['tilt_guide'] - rv_('tilt_sys_work_steel'), 'deg', 'tilt_guide - tilt_sys_work_steel: left for every static misalignment, including the as-made bend angle, motor face and pulleys (Rev B, worst) = misalign_budget; met by setting each pulley and each belt clamp to the rail at assembly (asm_alignment_step)', 3)
    put('tilt_sys_design_steel', math.degrees(max(totS, totSB)) + math.degrees(sl), 'deg', 'bracket + motor shaft at the design load (information; below the guidance even at the design load)', 2)
    flag('tilt_check_steel', math.degrees(max(totS, totSB)) <= i['tilt_limit'], 'PDS R11: tilt_steel and tilt_steel_revB <= tilt_limit')
    flag('stiff_check_steel', max(mvS, mvSB) <= i['move_limit'], 'PDS R5: move_steel and move_steel_revB <= move_limit')
    put('side_steel', totS * (i['a'] + i['T'] / 2), 'mm', 'tilt (rad) x (a + T/2): sideways shift along the shaft, information (speak only with the tilt)')

    # ---------- FEA cross-check bands (FreeCAD FEM / CalculiX run of ACT-103; information only) ----------
    gv = lambda k: v[k]['value']
    sgA = 6 * M / ((i['b'] - cutA) * t ** 2); sgB = 6 * M / ((i['b'] - cutB) * t ** 2)
    put('sigma_netreal_steel', sgA, 'MPa', '6M / (b_net_real t^2): nominal stress on the worst real cut-out line, released 2.5 mm steel, Rev A (the value behind FOS_netreal_steel)', 1)
    put('sigma_netreal_steel_revB', sgB, 'MPa', '6M / (b_net_real_revB t^2): same, Rev B (the value behind FOS_netreal_steel_revB)', 1)
    bt = i['fea_band_tol']; gate_txt = 'information only: the gate stays the hand calculation (FOS, R5, R11) plus the R11 tilt test'
    for rv, tot_, mv_ in (('revA', totS, mvS), ('revB', totSB, mvSB)):
        lo_f = (tot_ - thS['mount']) / tot_
        put(f'fea_tilt_lo_{rv}', math.degrees(tot_ - thS['mount']) * (1 - bt), 'deg',
            f'{rv}: (hand tilt - mounting-flange term) x (1 - fea_band_tol): lower end, an FEA that clamps the mounting flange removes the upper-bound term; ' + gate_txt, 3)
        put(f'fea_tilt_hi_{rv}', math.degrees(tot_) * (1 + bt), 'deg', f'{rv}: hand tilt x (1 + fea_band_tol): upper end (the hand model is an upper bound except for the rigid-motor choice, which the FEA shares); ' + gate_txt, 3)
        put(f'fea_move_lo_{rv}', mv_ * lo_f * (1 - bt), 'mm', f'{rv}: pulley movement band, lower end, same factors as the tilt band; ' + gate_txt, 3)
        put(f'fea_move_hi_{rv}', mv_ * (1 + bt), 'mm', f'{rv}: pulley movement band, upper end; ' + gate_txt, 3)
    # (1) FEA comparison line = clamp edge (REVIEW_F11_CAE, 16 Nov): the last section where the full moment M = F p still acts,
    # x = near motor-screw row - washer radius. The worst real cut-out line (x_worst_line) lies inside the clamped footprint:
    # sigma_netreal_steel stays the hand GATE value there, a conservative bound (full moment carried to the screw row).
    for rv, near_, trav_, sgw in (('revA', nearA, i['T'], sgA), ('revB', nearB, i['T_revB'], sgB)):
        sfx = '' if rv == 'revA' else '_revB'
        xc = near_ - i['washer_M3_od'] / 2; bc = i['b'] - cut_width(i, xc, trav_); sc = 6 * M / (bc * t ** 2)
        put(f'x_clamp_edge{sfx}', xc, 'mm', f'{rv}: L_near_row{sfx} - washer_M3_od/2: motor-clamp edge from datum A, the last line where M = F p still acts (FEA comparison line)', 1)
        put(f'b_net_clamp_edge{sfx}', bc, 'mm', f'{rv}: b - real cut-out width on the clamp-edge line (pilot slot + M3 slots, full travel)', 2)
        put(f'sigma_clampedge_steel{sfx}', sc, 'MPa', f'{rv}: 6M / (b_net_clamp_edge t^2), released 2.5 mm steel: hand nominal stress on the clamp-edge line, compared with the FEA', 1)
        put(f'fea_stress_lo_{rv}', sc * (1 - bt), 'MPa', f'{rv}: sigma_clampedge_steel x (1 - fea_band_tol), i.e. -10 %, ends rounded inward: compare the FEA stress linearised (integrated) across the clamp-edge line; ' + gate_txt, 1)
        put(f'fea_stress_hi_{rv}', sc * (1 + bt), 'MPa', f'{rv}: sigma_clampedge_steel x (1 + fea_band_tol), i.e. +10 %, ends rounded inward; ' + gate_txt, 1)
        put(f'fea_stress_reason_below_{rv}', sgw, 'MPa', f'{rv}: sigma_netreal_steel{sfx} (hand worst line, gate value): an FEA line stress below it shows the reason line (always, at the clamp edge)', 1)
    text('fea_stress_reason', 'Reason line: the clamped motor takes part of the moment at the screw row, so the FEA there sits below the hand worst-line value: that value is a safe upper bound.',
         'REVIEW_F11_CAE finding 1 wording; shown when the FEA clamp-edge stress is below the hand worst-line value')
    # (2) full-moment line: gross section between the bend tangent and the first slot cut (no cut-out, full M = F p)
    xf = (c + rv_('slot_zone_start')) / 2
    sf = 6 * M / (i['b'] * t ** 2)
    put('x_fullM_line', xf, 'mm', '(c_rel + slot_zone_start) / 2: line in the full-moment zone with no cut-out, from datum A (Rev A = Rev B: the near slot end does not move)', 1)
    put('sigma_fullM_line_steel', sf, 'MPa', '6M / (b t^2) on the full-moment line (gross section, full M = F p); same at Rev A and Rev B', 1)
    for rv in ('revA', 'revB'):
        put(f'fea_line2_lo_{rv}', sf * (1 - bt), 'MPa', f'{rv}: sigma_fullM_line_steel x (1 - fea_band_tol), linearised across the line; close agreement expected; ' + gate_txt, 1)
        put(f'fea_line2_hi_{rv}', sf * (1 + bt), 'MPa', f'{rv}: sigma_fullM_line_steel x (1 + fea_band_tol); ' + gate_txt, 1)
    # (3) bend zone: linearised (straight-beam) stress and curved-beam inner fibre
    sbl = 6 * M / (i['b'] * t ** 2)
    ri, ro = R, R + t; rn = t / math.log(ro / ri); rc = R + t / 2; ecc = rc - rn
    Ki = ((rn - ri) / (i['b'] * t * ecc * ri)) / (6 / (i['b'] * t ** 2))
    put('sigma_bend_lin_steel', sbl, 'MPa', '6M / (b t^2) in the bend zone = Sy_steel_min / FOS_bend_steel: compare the through-thickness linearised (membrane + bending) FEA stress', 1)
    put('fea_bend_lo', sbl * (1 - bt), 'MPa', 'sigma_bend_lin_steel x (1 - fea_band_tol); ' + gate_txt, 1)
    put('fea_bend_hi', sbl * (1 + bt), 'MPa', 'sigma_bend_lin_steel x (1 + fea_band_tol); ' + gate_txt, 1)
    put('Ki_bend_inner', Ki, '-', 'curved-beam inner-fibre factor, rectangular section: (rn - ri) / (A e ri) over 6/(b t^2); rn = t / ln(ro/ri), e = rc - rn, ri = R, ro = R + t', 3)
    put('sigma_bend_inner_steel', sbl * Ki, 'MPa', 'sigma_bend_lin_steel x Ki_bend_inner: inner-fibre stress at the bend ("curved-beam effect"); information, not compared', 1)
    lo0 = i['a'] - i['T'] / 2
    xpe = lo0 - i['pilot_end_ext'] - i['pilot_slot'] / 2; xme = lo0 - i['m3_pat'] / 2 - i['m3_slot'] / 2
    sse = max(6 * M / ((i['b'] - cut_width(i, x_, i['T'])) * t ** 2) for x_ in (xpe, xme))
    put('x_slot_end_pilot', xpe, 'mm', 'near end of the pilot slot from datum A (a - T/2 - pilot_end_ext - pilot_slot/2); Rev A = Rev B', 1)
    put('x_slot_end_m3', xme, 'mm', 'near end of the near M3 slots from datum A (a - T/2 - m3_pat/2 - m3_slot/2); Rev A = Rev B', 1)
    put('sigma_slotend_steel', sse, 'MPa', 'largest 6M / (b_net(x) t^2) on the near slot-end lines (x_slot_end_pilot, x_slot_end_m3): local nominal under the full moment (REVIEW_F11_CAE finding 6)', 1)
    put('fea_peak_lo', sse * i['fea_Kt'][0], 'MPa', 'sigma_slotend_steel x 2: expected local peak at the slot ends, low end (Ep 06 stress raisers about 2-3x nominal); only after slot-end refinement converges; not a gate', 0)
    put('fea_peak_hi', sse * i['fea_Kt'][1], 'MPa', 'sigma_slotend_steel x 3: expected local peak, high end; still below Sy_steel_min; not a gate', 0)
    put('fea_mesh_limit_pct', i['fea_mesh_limit_pct'], '%', 'mesh study: the tilt must change by less than this at half element size', 0)
    fres = {}
    units = dict(fea_tilt_revA='deg', fea_tilt_revB='deg', fea_stress_revA='MPa', fea_stress_revB='MPa', fea_peak='MPa', fea_move_revA='mm', fea_move_revB='mm',
                 fea_line2_revA='MPa', fea_line2_revB='MPa', fea_bend_lin='MPa', fea_mesh_delta_pct='%', fea_model_rev='')
    for k, unit in units.items():
        if i[k] is None:
            v[k] = dict(value=None, unit=unit, formula='input placeholder: FreeCAD FEM (CalculiX) result of ACT-103, to be measured (filled after the run)', spoken='', printed='to be measured')
        elif k == 'fea_model_rev':
            text(k, str(i[k]), 'input: FEA model revision stamped on the model, mesh study, result table and plots')
        else:
            put(k, float(i[k]), unit, 'input: FreeCAD FEM (CalculiX) result of ACT-103', 3)
        fres[k] = i[k]
    if any(x is None for x in fres.values()):
        fv = 'PENDING'; rs = 'PENDING'
    else:
        r = fres; inb = lambda x, lo, hi: g(lo) <= x <= g(hi)
        ok = all([inb(r['fea_tilt_revA'], 'fea_tilt_lo_revA', 'fea_tilt_hi_revA'), inb(r['fea_tilt_revB'], 'fea_tilt_lo_revB', 'fea_tilt_hi_revB'),
                  inb(r['fea_move_revA'], 'fea_move_lo_revA', 'fea_move_hi_revA'), inb(r['fea_move_revB'], 'fea_move_lo_revB', 'fea_move_hi_revB'),
                  inb(r['fea_stress_revA'], 'fea_stress_lo_revA', 'fea_stress_hi_revA'), inb(r['fea_stress_revB'], 'fea_stress_lo_revB', 'fea_stress_hi_revB'),
                  inb(r['fea_line2_revA'], 'fea_line2_lo_revA', 'fea_line2_hi_revA'), inb(r['fea_line2_revB'], 'fea_line2_lo_revB', 'fea_line2_hi_revB'),
                  inb(r['fea_bend_lin'], 'fea_bend_lo', 'fea_bend_hi'), gv('fea_peak_lo') * 0.8 <= r['fea_peak'] <= gv('fea_peak_hi') * 1.2,
                  abs(r['fea_mesh_delta_pct']) < i['fea_mesh_limit_pct'], str(r['fea_model_rev']).strip() != ''])
        fv = 'AGREES' if ok else 'CHECK MODEL'
        rs = 'SHOW' if (r['fea_stress_revA'] < gv('fea_stress_reason_below_revA') or r['fea_stress_revB'] < gv('fea_stress_reason_below_revB')) else 'NOT NEEDED'
    text('fea_verdict', fv, 'PENDING until every fea_* result (tilt, movement, clamp-edge line, full-moment line, bend linearised, peak, mesh delta, model rev) is filled; then AGREES if each is in its band, the peak in fea_peak_lo..hi (+/-20 %) and the mesh delta under fea_mesh_limit_pct, else CHECK MODEL (find out why; never retune the model; the gate stays the hand calculation and the R11 test)')
    # Rev A rows shown on Ep07 S09_3 (REVIEW_F11_CAE "Review R1/R2": R2 compression-only support accepted; tilt 0.094, movement 0.041)
    rA = [('fea_tilt_revA', 'fea_tilt_lo_revA', 'fea_tilt_hi_revA'), ('fea_move_revA', 'fea_move_lo_revA', 'fea_move_hi_revA'),
          ('fea_stress_revA', 'fea_stress_lo_revA', 'fea_stress_hi_revA'), ('fea_line2_revA', 'fea_line2_lo_revA', 'fea_line2_hi_revA'),
          ('fea_bend_lin', 'fea_bend_lo', 'fea_bend_hi')]
    if any(i[k] is None for k, _, _ in rA):
        fva = 'PENDING'
    else:
        fva = 'AGREES' if all(gv(lo) <= i[k] <= gv(hi) for k, lo, hi in rA) else 'CHECK MODEL'
    text('fea_verdict_revA', fva, 'Rev A rows (tilt, movement, clamp-edge stress, full-moment line, bend linearised): AGREES if each FEA result is in its band (R2 compression-only support, REVIEW_F11_CAE R1/R2); fea_verdict (all rows, Rev B, peak, mesh) stays PENDING until those are filled')
    text('fea_stress_reason_show', rs, 'PENDING until filled; SHOW if a clamp-edge-line FEA stress is below fea_stress_reason_below (the reason line fea_stress_reason goes on screen)')

    # ---------- motor shaft, stall, fatigue (final design) ----------
    put('shaft_ratio', i['F_max'] / i['shaft_radial_allowed'], '-', 'working shaft load / allowed radial load at the same distance', 2)
    put('shaft_ratio_design', F / i['shaft_radial_allowed'], '-', 'design load / allowed radial load (rating is for bearing life: working load governs)', 2)
    flag('shaft_check', i['F_max'] <= i['shaft_radial_allowed'] and i['p'] <= i['shaft_load_distance'],
         'working load <= allowed radial load, applied no farther out than the rated distance (p and shaft_load_distance both from the motor mounting face, course decision)')
    r_p = i['pulley_teeth'] * i['belt_pitch'] / (2 * math.pi)
    put('r_pitch', r_p, 'mm', 'teeth x pitch / (2 pi)', 2)
    Fs = max(i['F_max'], i['T_motor_peak'] * 1000 / r_p)
    put('F_stall', Fs, 'N', 'crash / stall at the end stop: T_motor_peak / r_pitch (slack span goes slack), not less than F_max', 1)
    put('stall_ratio', Fs / F, 'x', 'F_stall / F_design', 2)
    ss = strength(i, t, Ss, Fs, max(cutA, cutB))
    put('FOS_stall_bend', ss['bend'], '-', 'Sy_steel_min / (6 F_stall p / (b t^2)), bend zone', 2)
    put('FOS_stall_real', ss['real'], '-', 'Sy_steel_min on the worst real cut-out line (Rev A or B, the wider cut), F_stall', 2)
    put('FOS_stall_mount', ss['holes'], '-', 'Sy_steel_min / (6 F_stall (p + c) / ((b - 2 hole) t^2)), mounting flange through the M5 holes', 2)
    put('FOS_stall_min', min(ss.values()), '-', 'smallest stall FOS (specified minimum yield)', 2)
    flag('stall_check', min(ss.values()) >= i['FOS_stall_gate'], 'min stall FOS (all sections) >= FOS_stall_gate (no yield)')
    put('shaft_ratio_stall', Fs / i['shaft_radial_allowed'], '-', 'F_stall / allowed radial load: above the continuous rating - ask the motor maker for the peak radial limit', 2)
    put('slip_margin_stall', 4 * i['mu'] * i['preload_M3'] / Fs, '-', 'slip_res / F_stall (static, full preload)', 0)
    put('tilt_stall', math.degrees(max(totS, totSB)) * Fs / F, 'deg', 'worst tilt_steel x stall_ratio: elastic, while stalled only', 2)
    srw = 6 * i['F_max'] * i['p'] / (i['b'] * t ** 2)
    put('sigma_range_work', srw, 'MPa', 'information: nominal stress range, 0 to working load, bend zone (gross section; not the worst line: see sigma_range_slot)', 1)
    put('Se_steel_est', 0.5 * i['Su_steel'], 'MPa', '0.5 x Su_steel: rough unfactored endurance-limit estimate for steel (before surface, size and stress-raiser factors)', 0)
    put('fatigue_ratio', 0.5 * i['Su_steel'] / srw, 'x', 'information: Se_steel_est / sigma_range_work, bend zone (Ep 06 S15 uses fatigue_ratio_slot)', 1)
    srs = 6 * i['F_max'] * i['p'] / ((i['b'] - max(cutA, cutB)) * t ** 2)
    put('sigma_range_slot', srs, 'MPa', 'worst nominal stress range, 0 to working load, on the worst real cut-out line (Rev B): 6 F_max p / (b_net_real_revB t^2); the slot ends are where cracks start (Ep 06 S15)', 1)
    put('fatigue_ratio_slot', 0.5 * i['Su_steel'] / srs, 'x', 'Se_steel_est / sigma_range_slot: before stress-raiser (about 2-3) and surface factors; low risk, not formally checked (Ep 06 S15)', 1)
    put('fatigue_ratio_slot_kt', 0.5 * i['Su_steel'] / (srs * i['fea_Kt'][1]), 'x', 'information: Se_steel_est / (sigma_range_slot x 3), the high end of the slot-end stress raiser, before the surface factor', 1)

    # ---------- Ep 08: bolts and screws (unchanged by the material) ----------
    put('bolt_T', Mh * (i['y2'] - c) / (2 * ((i['L1'] - c) ** 2 + (i['y2'] - c) ** 2)), 'N', 'M_heel (y2 - c) / (2 ((L1 - c)^2 + (y2 - c)^2)), 2 bolts per row', 1)
    put('pre_ratio', i['preload_M5'] / (i['proof'] * i['As']), '-', 'preload / (proof strength x As), target up to about 0.75')
    put('torque', i['K'] * i['preload_M5'] * i['d_M5'] / 1000, 'N.m', 'K x preload x d (illustrative; confirm with a supplier table)', 1)

    def screws(tt):
        e5 = i['L_M5'] - tt - i['washer_M5']; e3 = i['L_M3'] - tt - i['washer_M3']
        return e5, e3, i['depth_M5'] - e5, i['depth_M3'] - e3
    e5, e3, ro5, ro3 = screws(t)
    put('eng_M5', e5, 'mm', 'L - grip - washer (M5 x 12 into the tapped ACT-101 end block)', 1)
    put('engD_M5', e5 / 5, 'D', 'engagement / 5 mm', 1)
    flag('M5_check', e5 / 5 >= 1.5 and ro5 >= 1 - 1e-9, '>= 1.5D (tapped aluminium) and depth >= engagement + 1')
    put('eng_M3', e3, 'mm', 'L - grip - washer at nominal (M3 x 6 + ISO 7089 washer into the SAMPLE 4.5 mm motor thread)', 1)
    put('engD_M3', e3 / 3, 'D', 'eng_M3 / 3 mm at NOMINAL sheet, screw and washer: the 1D quick screen with no spare; the release check is at the tolerance corners (M3_check)', 2)
    # ---- the same stack at the tolerance limits ----
    d3 = 3.0; tlo, thi = t - i['t_tol'], t + i['t_tol']
    zg = 2 * i['zinc_um_max'] / 1000                  # worst corner everywhere: MAXIMUM zinc on both sheet faces adds to the grip (thick side only; it moves away from bottoming)
    zg8 = 2 * i['zinc_um'] / 1000                     # minimum plating: kept for the *_zmin information keys
    e3_lo = (i['L_M3'] - i['L_M3_tol']) - (thi + zg) - (i['washer_M3'] + i['washer_M3_tol'])   # shortest screw, thickest plated sheet and washer
    e3_hi = (i['L_M3'] + i['L_M3_tol']) - tlo - (i['washer_M3'] - i['washer_M3_tol'])          # longest screw, thinnest sheet and washer (plating ignored: errs safe)
    ro3_lo = i['depth_M3'] - e3_hi
    ded = (i['thread_end_P'] + i['lead_in_P']) * i['P_M3']      # not full thread: screw end (ISO 4753 u <= 2P) + hole lead-in
    ded1 = 1.0 * i['P_M3']                                       # information: one pitch only
    text('M3_stack', f"ISO 4762 M3 x {fm(i['L_M3'])} + ISO 7089 washer 3 (300 HV) under the head, through {fm(t)} ±{fm(i['t_tol'])} mm sheet (before plating), into the SAMPLE motor thread ({fm(i['depth_M3'])} mm min)",
         'released motor-screw stack, checked at every tolerance corner')
    put('t_steel_min', tlo, 'mm', 't_steel - t_tol: thinnest conforming sheet (bare, before plating)', 2)
    put('t_steel_max', thi, 'mm', 't_steel + t_tol: thickest conforming sheet (bare, before plating)', 2)
    put('grip_plating', zg, 'mm', '2 x zinc_um_max: MAXIMUM plating on both sheet faces, added to the grip on the short-engagement side (worst corner)', 3)
    text('drawing_t_note', f"SHEET THICKNESS {fm(t)} ±{fm(i['t_tol'])} BEFORE PLATING (OVERRIDES THE GENERAL TOLERANCE; A MILL TOLERANCE WIDER THAN THIS NEEDS A WRITTEN DEVIATION)",
         'drawing note for ACT-103; title-block thickness field reads "2.5 (SEE NOTE n)"')
    put('eng_M3_min', e3_lo, 'mm', '(L_M3 - L_M3_tol) - (t_steel_max + grip_plating) - (washer_M3 + washer_M3_tol): least engagement length of a conforming stack (gross)', 2)
    put('eng_M3_max', e3_hi, 'mm', '(L_M3 + L_M3_tol) - t_steel_min - (washer_M3 - washer_M3_tol): most engagement of a conforming stack', 2)
    put('engD_M3_min', e3_lo / d3, 'D', 'eng_M3_min / 3 mm (gross; full threads: eng_M3_full_min)', 2)
    put('engD_M3_max', e3_hi / d3, 'D', 'eng_M3_max / 3 mm', 2)
    put('runout_M3_min', ro3_lo, 'mm', 'depth_M3 - eng_M3_max: least thread left below the screw tip (rule >= 1, no bottoming)', 2)
    put('runout_M3_margin', ro3_lo - 1.0, 'mm', 'runout_M3_min - 1 mm rule: the margin at the worst stacked corner (thin-sheet side; on the 1 mm rule, not on bottoming)', 2)
    put('thread_ded_M3', ded, 'mm', '(thread_end_P + lead_in_P) x P: not full thread (screw end per ISO 4753 u <= 2P, plus the hole lead-in); deducted in the strip check', 2)
    put('eng_M3_full_min', e3_lo - ded, 'mm', 'eng_M3_min - thread_ded_M3: full-thread engagement at the short corner (strip-check basis)', 2)
    # thread strip in the motor (least-material threads, full threads only)
    n_thr = 1 / i['P_M3']
    A_mm = math.pi * n_thr * i['d_min_M3'] * (1 / (2 * n_thr) + 0.57735 * (i['d_min_M3'] - i['D2_max_M3']))
    put('A_strip_M3', A_mm, 'mm^2/mm', 'pi n d_min [1/(2n) + 0.57735 (d_min - D2_max)], n = 1/P: shear area of the internal thread per mm of FULL-thread engagement, least-material 6H/6g', 3)
    put('preload_M3_nom', i['torque_M3'] / (i['K'] * d3 / 1000), 'N', 'torque_M3 / (K d): preload from the SAMPLE assembly torque (= preload_M3)', 0)
    pmax = i['torque_M3'] * (1 + i['torque_tol_pct'] / 100) / (i['K_min'] * d3 / 1000)
    pmin = i['torque_M3'] * (1 - i['torque_tol_pct'] / 100) / (i['K'] * 1.25 * d3 / 1000)
    put('preload_M3_max', pmax, 'N', 'torque_M3 x (1 + torque_tol_pct) / (K_min d): most preload the assembly torque can give (top of torque tolerance, low K)', 0)
    put('preload_M3_min', pmin, 'N', 'torque_M3 x (1 - torque_tol_pct) / (1.25 K d): least preload (bottom of torque tolerance, K 25 % high; information for the slip check)', 0)
    put('preload_M3_max_pct', (pmax / i['preload_M3'] - 1) * 100, '%', 'preload_M3_max / preload_M3 - 1', 0)
    tA = i['tau_motor'] * A_mm
    Fst = tA * (e3_lo - ded)
    put('F_strip_M3_min', Fst, 'N', 'tau_motor x A_strip_M3 x eng_M3_full_min: thread-strip force at the worst corner, full threads only', 0)
    import math as _m
    _pl = i['torque_M3'] * 1000 / (i['K'] * 3) if 'torque_M3' in i and 'K' in i else i['preload_M3']
    put('FOS_strip_M3', _m.floor(Fst / _pl * 100) / 100, '-', 'F_strip_M3_min / preload (unrounded), full threads only (screw end 2P + lead-in 0.5P deducted); rounded DOWN (as every FOS key); gate strip_gate', 2)
    put('FOS_strip_M3_max', Fst / pmax, '-', 'F_strip_M3_min / preload_M3_max, full threads only (must stay above 1: no stripping at assembly)', 2)
    put('FOS_strip_M3_1P', tA * (e3_lo - ded1) / i['preload_M3'], '-', 'information: strip FOS at the worst corner with only 1 pitch deducted', 2)
    put('FOS_strip_M3_max_1P', tA * (e3_lo - ded1) / pmax, '-', 'information: same at preload_M3_max, 1 pitch deducted', 2)
    put('FOS_strip_M3_gross', tA * e3_lo / i['preload_M3'], '-', 'information: no deduction (the superseded basis)', 2)
    put('FOS_strip_M3_nom', tA * (e3 - ded) / i['preload_M3'], '-', 'information: full-thread basis at nominal engagement', 2)
    e_full_req = max(i['strip_gate'] * i['preload_M3'], pmax) / tA
    e_req = e_full_req + ded
    put('eng_M3_full_req', e_full_req, 'mm', 'max(strip_gate x preload_M3, preload_M3_max) / (tau_motor x A_strip_M3): full-thread engagement the strip check needs', 2)
    put('eng_M3_req', e_req, 'mm', 'eng_M3_full_req + thread_ded_M3: least engagement length (gross) the strip check accepts', 2)
    put('engD_M3_req', e_req / d3, 'D', 'eng_M3_req / 3 mm', 2)
    flag('strip_check_M3', Fst / i['preload_M3'] >= i['strip_gate'] - 1e-9 and Fst / pmax > 1, 'FOS_strip_M3 >= strip_gate and FOS_strip_M3_max > 1 (worst corner, full threads only)')
    # sheet-thickness window the stack tolerates (bare sheet, as measured at incoming inspection)
    t_win_lo = (i['L_M3'] + i['L_M3_tol']) - (i['washer_M3'] - i['washer_M3_tol']) - (i['depth_M3'] - 1.0)
    t_win_hi = (i['L_M3'] - i['L_M3_tol']) - (i['washer_M3'] + i['washer_M3_tol']) - zg - e_req
    put('stack_t_lo', t_win_lo, 'mm', 'thinnest bare sheet with run-out >= 1 at the longest screw and thinnest washer (bottoming side)', 2)
    put('stack_t_hi', t_win_hi, 'mm', 'thickest bare sheet that still passes the strip check (full threads) at the shortest screw, thickest washer, with plating', 3)
    put('stack_t_margin_lo', tlo - t_win_lo, 'mm', 't_steel_min - stack_t_lo: room on the thin side', 2)
    put('stack_t_margin_hi', t_win_hi - thi, 'mm', 'stack_t_hi - t_steel_max: room on the thick side', 2)
    put('grip_plating_max', zg, 'mm', 'same as grip_plating (the release stack uses the maximum plating)', 3)
    put('FOS_strip_M3_zmax', Fst / _pl, '-', 'same as FOS_strip_M3 (maximum plating on the grip, release basis)', 2)
    put('stack_t_hi_zmax', t_win_hi, 'mm', 'same as stack_t_hi (maximum plating, release basis)', 3)
    e8 = e3_lo + zg - zg8
    put('grip_plating_zmin', zg8, 'mm', 'information: 2 x zinc_um, plating at the minimum (the superseded basis)', 3)
    put('eng_M3_min_zmin', e8, 'mm', 'information: eng_M3_min at the minimum plating', 2)
    put('engD_M3_min_zmin', e8 / d3, 'D', 'information: engD_M3_min at the minimum plating', 2)
    put('F_strip_M3_min_zmin', tA * (e8 - ded), 'N', 'information: F_strip_M3_min at the minimum plating', 0)
    put('FOS_strip_M3_zmin', tA * (e8 - ded) / _pl, '-', 'information: FOS_strip_M3 at the minimum plating (the superseded basis, 1.67)', 2)
    put('stack_t_hi_zmin', t_win_hi + zg - zg8, 'mm', 'information: stack_t_hi at the minimum plating', 3)
    put('stack_t_margin_hi_zmin', t_win_hi + zg - zg8 - thi, 'mm', 'information: stack_t_margin_hi at the minimum plating', 2)
    put('ga12_max_measured_t_zmin', math.floor((t_win_hi + zg - zg8) * 100 + 1e-9) / 100, 'mm', 'information: bare-sheet 12 GA limit at the minimum plating (the superseded 2.75)', 2)
    put('stack_grip_hi', t_win_hi + zg, 'mm', 'stack_t_hi + grip_plating: thickest sheet MEASURED OVER THE PLATING that passes every gate (independent of the actual plating thickness)', 3)
    flag('M3_screen', e3 / d3 >= 1 - 1e-9 and i['depth_M3'] - e3 >= 1 - 1e-9, 'quick screen at nominal: >= 1D and run-out >= 1 (a failed screen calls for the corner check; it is not a reject)')
    flag('M3_check', ro3_lo >= 1 - 1e-9 and v['strip_check_M3']['value'] == 'PASS',
         'release check at every tolerance corner: runout_M3_min >= 1 (no bottoming) and strip_check_M3 on full threads (motor maker data govern)')
    text('note_M3_judgement', f"M3 x {fm(i['L_M3'])} with an ISO 7089 washer through {fm(t)} ±{fm(i['t_tol'])} mm sheet engages {fm(round(e3_lo / d3, 2))}-{fm(round(e3_hi / d3, 2))}D across the tolerance band "
         f"({fm(round(e3 / d3, 2))}D at nominal), with at least {fm(round(ro3_lo, 2))} mm of thread below the tip; it is accepted on a thread-strip check of the full threads only at the worst corner "
         f"(FOS {fm(v['FOS_strip_M3']['value'])} against {fm(i['strip_gate'])}, at the SAMPLE torque of {fm(i['torque_M3'])} N·m; the motor maker's data govern), not on the 1D screen. M3 x {fm(i['L_M3_next'])} would bottom.",
         'from eng_M3_min/max, runout_M3_min, FOS_strip_M3')
    text('note_M3_rule', "Our 1.5D rule is for tapped holes we design: it makes the screw, not the thread, the weak link at full screw strength. "
         "A bought motor's thread is the maker's design, so the maker's thread depth and screw torque govern; we check that its full threads carry the torque-limited preload (strip check) and that the screw cannot bottom, at every tolerance corner.",
         'how the course reconciles a motor maker\'s tapped holes with the 1.5D rule')
    text('note_K_strip', f"K scatter: at the same {fm(i['torque_M3'])} N·m, a plated or lubricated screw (K about {fm(i['K_min'])}) and the top of the torque tolerance give about {fm(round(pmax))} N, "
         f"{fm(round((pmax / i['preload_M3'] - 1) * 100))} % above the nominal preload; the full threads of the motor still hold at the worst corner (FOS {fm(round(Fst / pmax, 2))}).",
         'from preload_M3_max, FOS_strip_M3_max, K_min')
    text('note_strip_basis', f"Strip check on full threads only: from the engagement length we deduct the screw end ({fm(i['thread_end_P'])} pitches, the incomplete thread ISO 4753 allows) and the hole lead-in ({fm(i['lead_in_P'])} pitch): {fm(round(ded, 2))} mm. "
         f"With one pitch only, the worst-corner FOS would be {fm(round(tA * (e3_lo - ded1) / i['preload_M3'], 2))}; with the full allowance it is {fm(v['FOS_strip_M3']['value'])}. The housing strength is a typical value: the maker's data govern.",
         'course decision basis statement; from thread_ded_M3, FOS_strip_M3_1P, FOS_strip_M3')
    text('torque_note_M3', f"TIGHTEN MOTOR SCREWS M3 TO {fm(i['torque_M3'])} N·m ±{fm(i['torque_tol_pct'])}% (SAMPLE MOTOR DATA; THE MOTOR MAKER'S VALUE GOVERNS)",
         'assembly note from torque_M3, torque_tol_pct')
    # alternatives considered (same limits, same full-thread basis)
    for tag, lab, L, Lt, h, ht in (('nowasher', 'M3 x 6, no washer', i['L_M3'], i['L_M3_tol'], 0.0, 0.0),
                                   ('flange', 'ISO 7380-2 flanged button head M3 x 6 (flange replaces the washer)', i['L_M3'], i['L_M3_tol'], 0.0, 0.0),
                                   ('m3x8_spacer', 'M3 x 8 + 2.5 mm hardened spacer (+/-0.05)', i['L_M3_next'], i['L_M3_next_tol'], 2.5, 0.05)):
        lo_ = (L - Lt) - (thi + zg) - (h + ht); hi_ = (L + Lt) - tlo - (h - ht)
        put(f'm3alt_{tag}_engD_min', lo_ / d3, 'D', f'{lab}: least engagement / 3 mm at the tolerance limits (gross)', 2)
        put(f'm3alt_{tag}_runout_min', i['depth_M3'] - hi_, 'mm', f'{lab}: least run-out at the tolerance limits (rule >= 1)', 2)
        put(f'm3alt_{tag}_FOS_strip', tA * (lo_ - ded) / i['preload_M3'], '-', f'{lab}: strip FOS at the worst corner, full threads (gate strip_gate)', 2)
        flag(f'm3alt_{tag}_check', i['depth_M3'] - hi_ >= 1 - 1e-9 and tA * (lo_ - ded) / i['preload_M3'] >= i['strip_gate'], f'{lab}: run-out >= 1 and strip gate at every corner')
    ra = (i['L_M3'] - i['L_M3_tol']) - (i['t_alt2'] + i['t_alt2_tol']) - (i['washer_M3'] + i['washer_M3_tol'])
    put('route_thick_engD_M3_min', ra / d3, 'D', 'route (a) 3.0 mm aluminium, M3 x 6 + washer: least engagement at the tolerance limits (gross, information)', 2)
    put('route_thick_FOS_strip_min', tA * (ra - ded) / i['preload_M3'], '-', 'route (a): strip FOS at the worst corner, full threads (gate strip_gate); M3 x 8 bottoms (information)', 2)
    flag('route_thick_strip_check', tA * (ra - ded) / i['preload_M3'] >= i['strip_gate'], 'route (a): strip FOS at the worst corner >= strip_gate (information)')
    put('slip_res', 4 * i['mu'] * i['preload_M3'], 'N', '4 x mu x preload_M3 (four M3 motor screws, one friction face each)', 0)
    put('slip_margin', 4 * i['mu'] * i['preload_M3'] / F, '-', 'slip_res / F_design (static, at full preload; preload can drop in service - Ep 22)', 0)

    # ---------- assumption notes: printed form, every number taken from a key ----------
    g = lambda k: v[k]['value']
    put('bolt_T_pct_preload', g('bolt_T') / i['preload_M5'] * 100, '%', 'bolt_T / preload_M5: load tension as % of preload', 1)
    put('motor_weight_pct', i['motor_weight'] / F * 100, '%', 'motor_weight / F_design', 0)
    put('torque_tol', g('torque') * i['torque_tol_pct'] / 100, 'N.m', 'torque x torque_tol_pct / 100 (illustrative)', 1)
    text('note_heel_pivot', f"Tipping about the heel is the least conservative pivot: prying can raise the bolt tension several times; here the load tension ({fm(g('bolt_T'))} N) is about {fm(g('bolt_T_pct_preload'))} % of the preload, so the conclusion holds.",
         'from bolt_T, preload_M5')
    text('note_motor_weight', f"Motor weight {fm(i['motor_weight'])} N, about {fm(g('motor_weight_pct'))} % of F_design, acts at right angles to F and is neglected: this slightly understates stress and bolt load (non-conservative); note it for the reviewer.",
         'from motor_weight, F_design')
    # course team fix round 01 (A15, ENG LEAD S4): the weight screened by its MOMENT, not only its force ratio. The weight is parallel
    # to the bend line (no moment about the bend); about a horizontal axis through the M5 rows it lifts the upper bolts:
    # tipping about the lower flange edge, M5 columns at drw_ted_hole_edge and drw_ted_hole_edge + hole_pat_BC
    arm_A, arm_B = i['a'] + i['T'] / 2, i['a'] - i['T'] / 2 + i['T_revB']
    x1 = (i['b'] - i['hole_pat_BC']) / 2; x2 = x1 + i['hole_pat_BC']   # = drw_ted_hole_edge (computed further down)
    kb = x2 / (2 * (x1 ** 2 + x2 ** 2))
    put('arm_motor_weight', arm_A, 'mm', 'a + T/2: motor centre from datum A, far end of the Rev A travel', 0)
    put('arm_motor_weight_revB', arm_B, 'mm', 'a - T/2 + T_revB: motor centre from datum A, far end of the Rev B travel (worst)', 0)
    put('M_motor_weight', i['motor_weight'] * arm_A, 'N.mm', 'motor_weight x arm_motor_weight: about the M5 bolt rows (horizontal axis), Rev A; parallel to the bend line, so no moment about the bend', 0)
    put('M_motor_weight_revB', i['motor_weight'] * arm_B, 'N.mm', 'motor_weight x arm_motor_weight_revB (worst)', 0)
    put('bolt_T_motor_weight', i['motor_weight'] * arm_A * kb, 'N', 'M_motor_weight x2 / (2 (x1^2 + x2^2)), tipping about the lower flange edge, x1 = drw_ted_hole_edge, x2 = x1 + hole_pat_BC: added per upper bolt, Rev A', 2)
    put('bolt_T_motor_weight_revB', i['motor_weight'] * arm_B * kb, 'N', 'same, Rev B (worst)', 2)
    put('bolt_T_motor_weight_pct', i['motor_weight'] * arm_B * kb / g('bolt_T') * 100, '%', 'bolt_T_motor_weight_revB / bolt_T (worst)', 0)
    # course team (Ep14 graphics, computed): round vs square position zone, and the bend-angle drop over the motor seat
    put('zone_round_gain_pct', (math.pi / 2 - 1) * 100, '%', '(pi/2 - 1) x 100: area of a round position zone over the square inscribed in it, minus 1 (Ep14 S05)', 2)
    put('perp_bend_drop', i['perp_seat_len'] * math.tan(math.radians(i['tol_bend_angle'])), 'mm',
        'perp_seat_len x tan(tol_bend_angle): how far the motor seat end moves for the full bend-angle tolerance (Ep14 S12_1; spoken about 1.1)', 3)
    # Rev A keys (course team / ENG re-check): Ep 04 analyses Rev A; Rev B arrives with ECO-001 (Ep 22) - the Rev B keys stay for Ep 08 / Ep 22
    put('M_motor_weight_revA', i['motor_weight'] * arm_A, 'N.mm', 'motor_weight x arm_motor_weight: about the M5 bolt rows, Rev A (Ep 04)', 0)
    put('bolt_T_motor_weight_pct_revA', i['motor_weight'] * arm_A * kb / g('bolt_T') * 100, '%', 'bolt_T_motor_weight / bolt_T, Rev A (Ep 04)', 0)
    put('bolt_T_with_weight', g('bolt_T') + i['motor_weight'] * arm_B * kb, 'N', 'bolt_T + bolt_T_motor_weight_revB: worst upper bolt', 1)
    put('bolt_T_with_weight_pct_preload', (g('bolt_T') + i['motor_weight'] * arm_B * kb) / i['preload_M5'] * 100, '%', 'bolt_T_with_weight / preload_M5', 2)
    text('note_motor_weight_moment', f"Motor weight: about {fm(g('M_motor_weight_revA'))} N.mm about the bolt rows, in another plane; it adds about {fm(g('bolt_T_motor_weight_pct_revA'))} % to the upper-bolt load - still far below preload, so the conclusion holds (Ep 08 checks it).",
         'fix round 01 A15 (Rev A, Ep 04); from M_motor_weight_revA, bolt_T_motor_weight_pct_revA')
    # D156 (D155 instructor A, Ep04 S08/S10): not "slightly": the weight adds bolt_T_motor_weight_pct_revA % to the upper-bolt
    # load. Re-set here (same key, same place in the file) because the bolt keys are computed after the first definition.
    text('note_motor_weight', f"Motor weight {fm(i['motor_weight'])} N, about {fm(g('motor_weight_pct'))} % of F_design, acts at right angles to F and is neglected: this understates stress and bolt load (non-conservative): it would add about {fm(g('bolt_T_motor_weight_pct_revA'))} % (+{fm(g('bolt_T_motor_weight'))} N) to the upper-bolt load, still far below preload; note it for the reviewer.",
         'from motor_weight, F_design, bolt_T_motor_weight, bolt_T_motor_weight_pct_revA (D156)')
    # FIX_ENG Ep04 S-4 (reviewer 17 Nov): the motor stator reacts the drive torque about the shaft axis. The shaft is parallel
    # to the mounting flange and normal to the bend line, so this is the same axis as the motor-weight moment (in-plane of
    # the motor flange, tipping the mounting flange about its lower or upper edge, x1 / x2 as above): bolt share = T x kb.
    # It does not act in the plane of F, M or bolt_T (Ep 04 FBD), so Ep 04 states it as a simplification; Ep 08 closes it.
    put('bolt_T_motor_torque', i['T_motor_peak'] * 1000 * kb, 'N', 'T_motor_peak x 1000 x x2 / (2 (x1^2 + x2^2)): added per bolt on one row by the motor reaction torque at peak torque (about the shaft axis, same axis as M_motor_weight; sign follows the drive direction)', 2)
    put('bolt_T_motor_torque_pct_preload', i['T_motor_peak'] * 1000 * kb / i['preload_M5'] * 100, '%', 'bolt_T_motor_torque / preload_M5', 2)
    _bt_all = g('bolt_T') + i['motor_weight'] * arm_B * kb + i['T_motor_peak'] * 1000 * kb
    put('bolt_T_worst_all', _bt_all, 'N', 'bolt_T + bolt_T_motor_weight_revB + bolt_T_motor_torque: worst upper bolt with the belt moment, the motor weight (Rev B travel end) and the motor reaction torque at peak torque all adding (Ep 08)', 1)
    put('bolt_T_worst_all_pct_preload', _bt_all / i['preload_M5'] * 100, '%', 'bolt_T_worst_all / preload_M5', 2)
    text('note_motor_reaction_torque', f"Motor reaction torque: the motor body reacts the drive torque (up to {fm(i['T_motor_peak'])} N.m, SAMPLE) about the shaft axis, in another plane than F; it is not drawn in the Ep 04 FBD. It adds up to about {fm(g('bolt_T_motor_torque'))} N on one bolt row (about {fm(g('bolt_T_motor_torque_pct_preload'))} % of preload), so it errs unsafe but the conclusion holds (Ep 08 checks it).",
         'FIX_ENG Ep04 S-4; from T_motor_peak, bolt_T_motor_torque, preload_M5')
    text('note_crash_inertia', 'quasi-static: ignores rotor inertia, Ep 08', 'fix round 01 A16 (ENG LEAD S2): F_stall = T_motor_peak / r is the quasi-static stall value; a crash at speed adds rotor and pulley inertia')
    text('note_nominal_stress', 'Net-section stress is a nominal stress: the peaks at the slot ends (Ep 06) are not included; acceptable for a static yield check in a ductile metal, not for fatigue.',
         '')
    text('note_K_dry', f"K = {fm(i['K'])} assumes dry, unlubricated threads; coated or lubricated screws often have a lower K, which gives more preload at the same torque, so use the coating or screw maker's torque table.",
         'from K')
    text('torque_note', f"TIGHTEN M5 TO {fm(g('torque'))} N\u00b7m \u00b1{fm(i['torque_tol_pct'])}% (ILLUSTRATIVE)", 'assembly note from torque, torque_tol_pct')
    text('note_M3_motor_limit', f"The motor maker's maximum screw torque and preload govern the M3 motor screws: the {fm(round(i['preload_M3']))} N preload is illustrative and must not exceed that limit; put the datasheet torque on the assembly note.",
         'from preload_M3')
    text('note_lever_arms', f"p is measured from the motor mounting face; the exact lever arm to the motor-flange mid-plane is p - t/2 ({fm(g('lever_mid'))} mm), so M = F p is about {fm(g('M_conserv_pct'))} % high (conservative).",
         'from lever_mid, M_conserv_pct')
    text('note_tilt_model', f"Simplified model, errs both ways. Makes the tilt bigger (conservative): the mounting-flange term is an upper bound (propped at the heel, no help from face contact); M = F p overstates the mid-plane moment by about {fm(g('M_conserv_pct'))} %. "
         f"Makes it smaller (non-conservative): the motor body and its screws are rigid (no joint or flange compliance); the motor-shaft estimate takes the bearings as rigid; the motor weight ({fm(g('motor_weight_pct'))} % of F_design) is neglected. "
         f"The slot zone is included at its net section. PDS R11 stays open until it is confirmed by test: measured shaft tilt at F_design, motor at the Rev B far end, at most {fm(i['tilt_limit'])} deg (R11 open until the tilt test).",
         'course decision / from M_conserv_pct, motor_weight_pct, tilt_limit')

    # ---------- Ep 13: floating / fixed-fastener stack, course decision (diameter zones for both holes) ----------
    # course decision (4): drawing note 4 "DIMENSIONS APPLY AFTER PLATING" (sheet thickness excepted: before plating). Every fit is checked on the
    # DRAWING sizes (already after plating); the supplier's laser-cut size is derived from them (drawing size + plating allowance).
    # The plating is never subtracted again from a drawing size (the old *_plated keys did that: RETIRED below, values kept).
    RT = 'RETIRED (double count: subtracted the plating from a drawing size that already applies after plating, note 4; never show; replaced by {}; course decision course decision (4)): '
    hmin = i['hole_M5'] - i['tol_laser']
    put('hole_M5_min', hmin, 'mm', 'hole_M5 - tol_laser: smallest M5 clearance hole AS DRAWN (Ø5.5 ±0.1 applies after plating, note 4): the size the designer checks', 2)
    put('stack_allowed', hmin - i['d_M5'], 'mm', 'hole_M5_min - screw diameter: room available for position error, on the drawing size (after plating)', 2)
    put('stack_used', i['tol_laser_pos'] + i['tol_tapped_pos'], 'mm', 'tol_laser_pos + tol_tapped_pos: both position zones as diameters (fixed-fastener form, course decision)', 2)
    put('stack_margin', hmin - i['d_M5'] - i['tol_laser_pos'] - i['tol_tapped_pos'], 'mm', 'stack_allowed - stack_used: the release check on the drawing size (after plating, note 4); rounded down', 2)
    flag('stack_check', hmin - i['d_M5'] >= i['tol_laser_pos'] + i['tol_tapped_pos'] - 1e-9, 'stack_used <= stack_allowed on the drawing size (DIMENSIONS APPLY AFTER PLATING): the release check')
    put('stack_used_square', 2 * math.sqrt(2) * (i['tol_laser_pos'] / 2 + i['tol_tapped_pos'] / 2), 'mm', 'information (Ep 14 trap): if both capabilities were +/- per axis (squares), the circles around them add to this - more than stack_allowed', 2)
    flag('stack_check_square', hmin - i['d_M5'] >= 2 * math.sqrt(2) * (i['tol_laser_pos'] / 2 + i['tol_tapped_pos'] / 2), 'information: square-zone reading of the same numbers (expected FAIL)')
    zmx = 2 * i['zinc_um_max'] / 1000                 # plating on both walls, maximum: sets the SMALLEST laser-cut size (supplier allowance)
    zmn = 2 * i['zinc_um'] / 1000                     # plating on both walls, minimum: sets the LARGEST laser-cut size (supplier allowance)
    put('zinc_um_max', i['zinc_um_max'], 'um', 'input: zinc electroplate, maximum on significant surfaces (course practice; ASTM B633 classes give minimums only; holes and threads normally exempt from the minimum)', 0)
    hpl = hmin - zmx
    put('hole_M5_min_plated', hpl, 'mm', RT.format('hole_M5_min and laser_cut_M5_min') + 'hole_M5_min - 2 x zinc_um_max', 3)
    put('stack_allowed_plated', hpl - i['d_M5'], 'mm', RT.format('stack_allowed') + 'hole_M5_min_plated - screw diameter', 3)
    put('stack_margin_plated', hpl - i['d_M5'] - i['tol_laser_pos'] - i['tol_tapped_pos'], 'mm', RT.format('stack_margin') + 'stack_allowed_plated - stack_used', 3)
    put('stack_margin_plated_zmin', hmin - zmn - i['d_M5'] - i['tol_laser_pos'] - i['tol_tapped_pos'], 'mm', RT.format('stack_margin') + 'the same at the minimum plating zinc_um', 3)
    flag('stack_check_plated', hpl - i['d_M5'] >= i['tol_laser_pos'] + i['tol_tapped_pos'] - 1e-9, RT.format('stack_check') + 'stack_used <= stack_allowed_plated')
    smp = i['m3_slot'] - i['tol_laser'] - zmx
    put('slot_M3_mmc_plated', smp, 'mm', RT.format('slot_M3_mmc and laser_cut_M3_slot_min') + 'm3_slot - tol_laser - 2 x zinc_um_max', 3)
    put('slot_fit_allowed_plated', smp - 3.0, 'mm', RT.format('slot_fit_allowed') + 'slot_M3_mmc_plated - 3.0', 3)
    # slot fit on the drawing size (after plating): the slot zone is the laser position capability tol_laser_pos (drawing: 0.2 wide, note 5)
    smm = i['m3_slot'] - i['tol_laser']
    put('slot_M3_mmc', smm, 'mm', 'm3_slot - tol_laser: narrowest M3 slot AS DRAWN (3.4 ±0.1 applies after plating, note 4): the size the designer checks', 2)
    put('slot_fit_allowed', smm - 3.0, 'mm', 'slot_M3_mmc - 3.0 (M3 screw): room across the slot for position error, on the drawing size; rounded down', 3)
    put('slot_fit_margin', smm - 3.0 - i['tol_laser_pos'], 'mm', 'slot_fit_allowed - slot position zone (tol_laser_pos, 0.2 wide): left for the motor screw-pattern position; the release check on the drawing size (after plating, note 4); rounded down', 3)
    flag('slot_fit_check', smm - 3.0 - i['tol_laser_pos'] > 0, 'slot position zone fits inside the drawing slot width (after plating) with room left for the motor pattern: the release check')
    put('slot_fit_margin_plated', smp - 3.0 - i['tol_laser_pos'], 'mm', RT.format('slot_fit_margin; the SAMPLE datasheet now follows motor_pat_pos_req') + 'slot_fit_allowed_plated - tol_laser_pos', 3)
    put('slot_fit_margin_plated_zmin', i['m3_slot'] - i['tol_laser'] - zmn - 3.0 - i['tol_laser_pos'], 'mm', RT.format('slot_fit_margin') + 'the same at the minimum plating zinc_um', 3)
    flag('slot_fit_check_plated', smp - 3.0 - i['tol_laser_pos'] > 0, RT.format('slot_fit_check') + 'slot zone inside slot_M3_mmc_plated')
    put('motor_pat_pos_req', math.floor((smm - 3.0 - i['tol_laser_pos']) * 100 + 1e-9) / 100, 'mm',
        'slot_fit_margin rounded DOWN to 0.01: the largest 4X M3 pattern position tolerance (diameter, pattern to pilot) the SAMPLE motor datasheet may show; a real motor must be no larger', 2)
    put('zinc_um_stack_limit', (hmin - i['d_M5'] - i['tol_laser_pos'] - i['tol_tapped_pos']) / 2 * 1000, 'um',
        'information only: stack_margin / 2 - if the supplier made NO plating allowance (cut at the drawing size), the plating per hole wall that would use up the whole stack margin; the part would still be off the drawing (note 4)', 0)
    # supplier side (derived): laser-cut size BEFORE plating, so that the plated part meets the drawing size
    for nm, base, tol, lab in (('M5', i['hole_M5'], i['tol_laser'], 'M5 clearance hole'), ('M3_slot', i['m3_slot'], i['tol_laser'], 'M3 slot width'),
                               ('pilot', i['pilot_slot'], i['tol_gen_m'], 'pilot slot width (ISO 2768-m)')):
        put(f'laser_cut_{nm}_min', base - tol + zmx, 'mm', f'supplier allowance (derived, information): smallest laser-cut {lab} BEFORE plating = drawing minimum + 2 x zinc_um_max, so that the plated size stays at or above the drawing minimum; rounded UP', 3)
        put(f'laser_cut_{nm}_max', base + tol + zmn, 'mm', f'supplier allowance (derived, information): largest laser-cut {lab} BEFORE plating = drawing maximum + 2 x zinc_um, so that the plated size stays at or below the drawing maximum; rounded DOWN', 3)
    text('plating_basis_note',
         f"The supplier allows for plating; the designer checks the drawing size. Note 4: dimensions apply after plating (the sheet thickness is the exception: {fm(i['t_steel'])} ±{fm(i['t_tol'])} before plating). "
         f"So the fits are checked on the drawing sizes: Ø{fm(i['hole_M5'])} ±{fm(i['tol_laser'])} gives {fm(round(hmin, 2))} - {fm(i['d_M5'])} = {fm(round(hmin - i['d_M5'], 2))} available against {fm(round(i['tol_laser_pos'] + i['tol_tapped_pos'], 2))} used "
         f"(Ø{fm(i['tol_laser_pos'])} + Ø{fm(i['tol_tapped_pos'])}), {fm(math.floor((hmin - i['d_M5'] - i['tol_laser_pos'] - i['tol_tapped_pos']) * 100 + 1e-9) / 100)} spare; the M3 slot {fm(i['m3_slot'])} ±{fm(i['tol_laser'])} gives {fm(round(smm, 2))} - 3 = {fm(round(smm - 3, 2))}, "
         f"the {fm(i['tol_laser_pos'])} slot zone uses {fm(i['tol_laser_pos'])} and {fm(math.floor((smm - 3.0 - i['tol_laser_pos']) * 100 + 1e-9) / 100)} is left for the motor screw pattern. "
         f"The supplier cuts larger to make room for the zinc ({fm(i['zinc_um'])}-{fm(i['zinc_um_max'])} µm per wall): hole {fm(math.ceil((hmin + zmx) * 1000 - 1e-9) / 1000)}-{fm(math.floor((i['hole_M5'] + i['tol_laser'] + zmn) * 1000 + 1e-9) / 1000)}, "
         f"slot {fm(math.ceil((smm + zmx) * 1000 - 1e-9) / 1000)}-{fm(math.floor((i['m3_slot'] + i['tol_laser'] + zmn) * 1000 + 1e-9) / 1000)} (drawing limits + 2 x maximum zinc / + 2 x minimum zinc). "
         f"If the plater does not hold the minimum inside holes, the upper cut limit is the drawing maximum. Never subtract the plating again from a drawing size.",
         'course decision (4); from hole_M5, tol_laser, d_M5, tol_laser_pos, tol_tapped_pos, m3_slot, zinc_um, zinc_um_max, t_steel, t_tol (= stack_*, slot_fit_*, laser_cut_* keys)')

    # ---------- course decision (1)(2): basic dimensions that tie the hole and slot patterns to the outline and to datum B; CZ on the hole frame ----------
    put('hole_pat_BC', i['hole_pat_BC'], 'mm', 'input (drawing): basic spacing of the M5 hole columns across the flange, datum B column to datum C column', 1)
    put('drw_ted_hole_edge', (i['b'] - i['hole_pat_BC']) / 2, 'mm', '(b - hole_pat_BC) / 2: BASIC (boxed) dimension from the flange side edge to the datum-B hole column; replaces the reference (10)', 1)
    put('drw_ted_B_slot_centre', i['hole_pat_BC'] / 2, 'mm', 'hole_pat_BC / 2: BASIC (boxed) dimension from the datum-B axis to the slot-pattern centre plane (= flange centre plane); the boxed m3_pat is symmetric about it and the pilot slot sits on it (TED 0)', 1)
    put('drw_ted_B_slot_row', abs((i['b'] - i['hole_pat_BC']) / 2 - (i['b'] - i['m3_pat']) / 2), 'mm', '|drw_ted_hole_edge - (b - m3_pat)/2|: BASIC distance from the datum-B axis to the near M3 slot row (outboard of B); equivalent to drw_ted_B_slot_centre', 1)
    put('hole_edge_lmc', (i['b'] - i['hole_pat_BC']) / 2 - (i['hole_M5'] + i['tol_laser']) / 2, 'mm', 'drw_ted_hole_edge - (hole_M5 + tol_laser)/2: material from the flange side edge to the M5 hole at its largest drawing size (nominal position)', 2)
    flag('ted_chain_check', abs((i['b'] - i['hole_pat_BC']) / 2 + i['hole_pat_BC'] / 2 - i['b'] / 2) < 1e-9 and (i['b'] - i['m3_pat']) / 2 > 0,
         'hole pattern and slot pattern share the flange centre plane: drw_ted_hole_edge + drw_ted_B_slot_centre = b/2 (one open chain, no double dimension)')
    text('drw_hole_frame', f"4× Ø{fm(i['hole_M5'])} ±{fm(i['tol_laser'])} / ⌖ | Ø{fm(i['tol_laser_pos'])}Ⓜ CZ | A",
         'ACT-103 drawing frame on the M5 hole pattern (course decision (2)): from hole_M5, tol_laser, tol_laser_pos')
    text('drw_cz_note', f"CZ (ISO 5458:2018, combined zone): the four Ø{fm(i['tol_laser_pos'])} position zones are one pattern, locked to each other at their basic spacings. "
         "Without CZ, ISO reads one frame on 4× features as four separate zones (SZ) that can move apart, so the fixed-fastener check and the one-way fit are not protected. "
         "ASME Y14.5 reads the same frame as one pattern by default, so the ASME drawing needs no modifier.",
         'course decision (2); ISO 5458:2018 5.3 Rule A and 5.4.3 (REVIEW_GDT finding 1); from tol_laser_pos')

    # ---------- course decision (3): pilot-slot position tolerance from its clearance stack (width only, drawing sizes after plating) ----------
    psm = i['pilot_slot'] - i['tol_gen_m']
    put('pilot_dia', i['pilot_dia'], 'mm', 'input (SAMPLE motor datasheet): pilot boss diameter, largest; the maker wins', 1)
    put('tol_gen_m', i['tol_gen_m'], 'mm', 'input: ISO 2768-m linear general tolerance +/-, over 6 up to 30 mm (the pilot slot width)', 1)
    put('pilot_slot_min', psm, 'mm', 'pilot_slot - tol_gen_m: narrowest pilot slot AS DRAWN (after plating, note 4)', 2)
    put('pilot_clear', psm - i['pilot_dia'], 'mm', 'pilot_slot_min - pilot_dia: total clearance across the slot; rounded down', 2)
    put('pilot_clear_side', (psm - i['pilot_dia']) / 2, 'mm', 'pilot_clear / 2: clearance per side with everything centred (the reviewer\'s 0.39 subtracted the plating again)', 2)
    pmx = psm - i['pilot_dia'] - i['tol_laser_pos'] - math.floor((smm - 3.0 - i['tol_laser_pos']) * 100 + 1e-9) / 100
    put('pilot_slot_pos_max', pmx, 'mm', 'pilot_clear - M3 slot zone (tol_laser_pos, width) - motor_pat_pos_req (pilot to pattern, diameter): widest pilot-slot position zone that keeps the pilot clear with the screws centred in their slots; rounded down', 2)
    put('pos_pilot_slot', i['pos_pilot_slot'], 'mm', 'input (drawing choice): pilot-slot position zone WIDTH, width only, to A|B|C on the same TEDs as the motor slots (TED 0 to their centre plane)', 1)
    put('pilot_slot_pos_margin', pmx - i['pos_pilot_slot'], 'mm', 'pilot_slot_pos_max - pos_pilot_slot: spare width in the pilot clearance stack; rounded down', 2)
    flag('pilot_slot_pos_check', i['pos_pilot_slot'] <= pmx + 1e-9, 'pos_pilot_slot <= pilot_slot_pos_max: the pilot does not touch the slot, so it does not locate the motor (note 6)')
    text('drw_pilot_frame', f"⌖ | {fm(i['pos_pilot_slot'])} | A | B | C (PILOT SLOT, WIDTH ONLY; TED 0 TO THE MOTOR-SLOT CENTRE PLANE)",
         'ACT-103 drawing frame under the pilot-slot callout (course decision (3)): from pos_pilot_slot')
    text('pilot_stack_note', f"Pilot-slot stack (width, drawing sizes after plating): {fm(i['pilot_slot'])} - {fm(i['tol_gen_m'])} = {fm(round(psm, 2))} slot minimum, less the Ø{fm(i['pilot_dia'])} pilot = {fm(round(psm - i['pilot_dia'], 2))} "
         f"({fm(round((psm - i['pilot_dia']) / 2, 2))} per side). The motor-slot zone takes {fm(i['tol_laser_pos'])} and the motor's pattern-to-pilot tolerance Ø{fm(math.floor((smm - 3.0 - i['tol_laser_pos']) * 100 + 1e-9) / 100)}, "
         f"so the pilot-slot zone may be up to {fm(math.floor(pmx * 100 + 1e-9) / 100)} wide; the drawing gives {fm(i['pos_pilot_slot'])}, {fm(math.floor((pmx - i['pos_pilot_slot']) * 100 + 1e-9) / 100)} spare. "
         "The screw float in the motor slots is adjustment, not error: the motor is clamped by its screws and the pilot only has to clear.",
         'course decision (3); from pilot_slot, tol_gen_m, pilot_dia, tol_laser_pos, motor_pat_pos_req, pos_pilot_slot')

    # ---------- ECO-001 ----------
    text('eco001_root_cause', f"Root cause: motor-screw preload drops in service (short M3 grip, about {fm(i['t_steel'] + i['washer_M3'])} mm of sheet and washer between plated faces, so a few micrometres of embedding lose much of the preload) and the motor slips in its slots; contributing: belt stretch uses up the travel.",
         'course decision (one sentence everywhere, with the mechanism); grip = t_steel + washer_M3')
    text('retrofit_jig_pn', 'ACT-110', 'next free ACT-1xx number (ACT-101..109 used in the EBOM)')
    text('retrofit_jig_desc', 'ACT-110 Drill-and-tap jig, ECO-001 retrofit: locates 2x M4 tapped holes in a Rev A ACT-101 end block in the field (service tool, with instruction; illustrative)',
         'course decision')

    # ---------- Ep 17: hole-to-bend, flat pattern (geometry unchanged) ----------
    req = t + R + 2.5 * t + R; put('hb_required', req, 'mm', '(t + R) + 2.5t + R, measured from the outside face of the other flange (strict reading of the Ep 17 rule); supplier guide wins', 2)
    put('hb_from_bend', 2.5 * t + R, 'mm', '2.5t + R: the same rule measured from the bend tangent (hb_required - c_rel)', 2)
    put('hb_slot_edge', i['a'] - i['T'] / 2 - i['m3_pat'] / 2 - i['m3_slot'] / 2, 'mm', 'a - T/2 - m3_pat/2 - m3_slot/2 (near M3 slot end edge from datum A; Rev A)', 1)
    put('hb_slot_edge_revB', i['a'] - i['T'] / 2 - i['m3_pat'] / 2 - i['m3_slot'] / 2, 'mm', 'same at Rev B: the slots grow away from the bend, so the near end does not move', 1)
    # ERRORS sheet planted error E3 (Ep 16 S10, course decision): motor slots drawn 2 mm short, so the travel is 2 mm less than T
    err_travel = i['T'] - 2
    put('err_travel', err_travel, 'mm', 'ERRORS sheet E3: travel = slot length - slot width = T - 2 (planted error, LESS than T)', 1)
    put('err_slot_len', i['m3_slot'] + err_travel, 'mm', 'ERRORS sheet E3: motor slot length = slot width + travel (planted error; Rev A is m3_slot + T)', 1)
    assert abs(i['m3_slot'] + err_travel - 9.4) < 1e-9, 'ERRORS sheet E3 slot length must equal the sheet callout 9.4'
    put('slot_near_end', i['a'] - i['T'] / 2 - i['m3_pat'] / 2, 'mm', 'a - T/2 - m3_pat/2: centre of the near end of the M3 slots from datum A (Rev A = Rev B)', 1)
    put('hb_pilot_edge', i['a'] - i['T'] / 2 - i['pilot_end_ext'] - i['pilot_slot'] / 2, 'mm', 'a - T/2 - pilot_end_ext - pilot/2: pilot slot near edge (Rev A and B; CHANGED MEANING slot 0.5 longer at each end)', 1)
    put('hb_hole_edge', i['L1'] - i['hole_M5'] / 2, 'mm', 'L1 - hole/2', 2)
    put('hb_hole_edge_worst', i['L1'] - i['tol_across_bend'] - (i['hole_M5'] + i['tol_laser']) / 2, 'mm', 'L1 - tol_across_bend - (hole_M5 + tol_laser)/2: worst-case hole edge from the motor-flange outside face, size across the bend (Ep13 S13)', 2)
    flag('hb_hole_worst_check', i['L1'] - i['tol_across_bend'] - (i['hole_M5'] + i['tol_laser']) / 2 >= req - 1e-9, 'hb_hole_edge_worst >= hb_required (Ep13 S13)')
    flag('hb_check', min(rv_('hb_slot_edge'), rv_('hb_slot_edge_revB'), rv_('hb_pilot_edge'), rv_('hb_hole_edge')) >= req - 1e-9,
         'every hole and slot edge >= hb_required, full travel, Rev A and Rev B')
    far_B = i['a'] - i['T'] / 2 + i['T_revB']
    put('far_end_revB', far_B, 'mm', 'a - T/2 + T_revB: motor centre at the far end, Rev B (slots grow away from the bend only)', 1)
    put('edge_slot_far_revB', i['L_motor'] - (far_B + i['m3_pat'] / 2 + i['m3_slot'] / 2), 'mm', 'L_motor - far M3 slot end (Rev B): material left to the flange end', 1)
    flag('edge_check_revB', rv_('edge_slot_far_revB') >= 2 * t - 1e-9, 'edge_slot_far_revB >= 2t')
    put('edge_pilot_far_revB', i['L_motor'] - (far_B + i['pilot_end_ext'] + i['pilot_slot'] / 2), 'mm', 'L_motor - far pilot-slot end (Rev B, course decision length): material left to the flange end', 1)
    flag('edge_pilot_check_revB', rv_('edge_pilot_far_revB') >= 2 * t - 1e-9, 'edge_pilot_far_revB >= 2t')
    put('pilot_slot_len', i['pilot_slot'] + i['T'] + 2 * i['pilot_end_ext'], 'mm', 'pilot_slot + T + 2 x pilot_end_ext: pilot-slot length, Rev A', 1)
    put('pilot_slot_len_revB', i['pilot_slot'] + i['T_revB'] + 2 * i['pilot_end_ext'], 'mm', 'pilot_slot + T_revB + 2 x pilot_end_ext: pilot-slot length, Rev B', 1)
    put('pilot_end_ext', i['pilot_end_ext'], 'mm', 'input: pilot slot longer than the motor travel at each end', 1)
    BA = math.pi / 2 * (R + i['K_bend'] * t); put('BA_rel', BA, 'mm', 'bend allowance = (pi/2)(R + K t) for 90 deg, released thickness', 2)
    put('straight_mount', i['L_mount'] - t - R, 'mm', 'straight part of the mounting flange in the flat pattern = L_mount - t - R (released)', 1)
    put('straight_motor', i['L_motor'] - t - R, 'mm', 'straight part of the motor flange in the flat pattern = L_motor - t - R (released)', 1)
    put('flat_rel', flat_len, 'mm', '(L_mount - t - R) + (L_motor - t - R) + BA, released thickness', 1)
    put('bend_line_rel', (i['L_mount'] - t - R) + BA / 2, 'mm', 'flat length to the bend centre line, from the mounting-flange edge, released thickness', 1)
    lo, hi, h = i['a'] - i['T'] / 2, far_B, i['m3_pat'] / 2
    webs = []
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        dx *= i['pilot_slot_move']; dz *= i['pilot_slot_move']
        P = ((lo - i['pilot_end_ext'] + dx, dz), (hi + i['pilot_end_ext'] + dx, dz))
        for zs in (h, -h):
            for qa, qb in (((lo - h, zs), (hi - h, zs)), ((lo + h, zs), (hi + h, zs))):
                webs.append(seg_dist(P[0], P[1], qa, qb) - i['pilot_slot'] / 2 - i['m3_slot'] / 2)
    put('web_after_move', min(webs), 'mm', 'smallest web pilot slot to M3 slot after a 1 mm SIDEWAYS move (worst direction, Rev B); rule >= t', 2)
    wal = []
    for dx in (1, -1):
        dx *= i['pilot_slot_move']
        for zs in (h, -h):
            for qa, qb in (((lo - h, zs), (hi - h, zs)), ((lo + h, zs), (hi + h, zs))):
                wal.append(seg_dist((lo - i['pilot_end_ext'] + dx, 0), (hi + i['pilot_end_ext'] + dx, 0), qa, qb) - i['pilot_slot'] / 2 - i['m3_slot'] / 2)
    put('web_move_along', min(wal), 'mm', 'smallest web after a 1 mm move ALONG the slot (either way), Rev B; rule >= t', 2)
    flag('web_check_along', min(wal) >= t, 'web_move_along >= t_steel: the WEB rule alone passes for a move along the slot; the move is still refused on the pilot end clearance (pilot_end_check_move, course decision revised by the course decision pilot frame)')
    flag('web_check_side', min(webs) >= t, 'web_after_move >= t_steel: a sideways move is NOT accepted (expected FAIL at 2.5 mm, course decision)')
    # pilot-to-slot-END clearance at the motor travel limits (along the travel, Rev A and Rev B; drawing sizes after plating, note 4)
    # pilot slot = full-R stadium, end-arc centres at +/- T/2 from the slot centre (length = width + T); radius = half the slot width.
    # travel limit = M3 screw (3.0) against the M3 slot end: motor pattern centre at (m3_slot + tol_laser + T - 3.0) / 2 from the slot centre.
    # worst case: narrowest pilot slot (radius (pilot_slot - tol_gen_m)/2), largest pilot, longest M3 slot, and the location zones applied
    # along the travel as well as across: pilot frame pos_pilot_slot / 2, motor-slot zone tol_laser_pos / 2, motor pattern-to-pilot motor_pat_pos_req / 2.
    mpp = math.floor((i['m3_slot'] - i['tol_laser'] - 3.0 - i['tol_laser_pos']) * 100 + 1e-9) / 100
    loc = i['pos_pilot_slot'] / 2 + i['tol_laser_pos'] / 2 + mpp / 2          # one-sided location error between pilot and pilot slot
    Rn, Rw = i['pilot_slot'] / 2, (i['pilot_slot'] - i['tol_gen_m']) / 2
    pe = {}
    for tag, TT in (('revA', i['T']), ('revB', i['T_revB'])):
        xn = (i['m3_slot'] + TT - 3.0) / 2 - TT / 2 - i['pilot_end_ext']       # pilot centre beyond the end-arc centre, nominal
        xw = (i['m3_slot'] + i['tol_laser'] + TT - 3.0) / 2 - TT / 2 - i['pilot_end_ext'] + loc     # the same, worst case (along the travel)
        pe[tag] = dict(nom=Rn - i['pilot_dia'] / 2 - xn, worst=Rw - i['pilot_dia'] / 2 - xw, worst2d=Rw - i['pilot_dia'] / 2 - math.hypot(max(xw, 0.0), loc),
                       nom_mv=Rn - i['pilot_dia'] / 2 - xn - i['pilot_slot_move'], worst_mv=Rw - i['pilot_dia'] / 2 - math.hypot(xw + i['pilot_slot_move'], loc))
        put(f'pilot_end_clear_nom_{tag}', pe[tag]['nom'], 'mm', f'pilot to pilot-slot end at the motor travel limit ({tag}, either end), nominal sizes, motor screws against the M3 slot ends', 2)
        put(f'pilot_end_clear_worst_{tag}', pe[tag]['worst'], 'mm', f'CHANGED MEANING: the same, worst case ALONG the travel ({tag}): narrowest pilot slot, longest M3 slot, pilot frame + motor-slot zone + motor pattern-to-pilot applied along the travel; rule >= pilot_end_clear_min', 2)
        put(f'pilot_end_clear_corner_{tag}', pe[tag]['worst2d'], 'mm', f'the same with the location errors also applied ACROSS ({tag}, pilot in the end arc, off the axis); rule >= 0 (no contact); its ceiling is the width-stack side clearance (pilot_clear_side - location errors)', 2)
        put(f'pilot_end_clear_move_nom_{tag}', pe[tag]['nom_mv'], 'mm', f'pilot_end_clear_nom_{tag} - pilot_slot_move: the supplier\'s 1 mm move along the slot, at the end it moves towards', 2)
        put(f'pilot_end_clear_move_worst_{tag}', pe[tag]['worst_mv'], 'mm', f'the same with the 1 mm move, worst case ({tag})', 2)
    put('pilot_end_clear_min', i['pilot_end_clear_min'], 'mm', 'input (course practice): least pilot-to-slot-end clearance to keep visible daylight (laser dross, burr, plating build-up at the end)', 1)
    cm = i['pilot_end_clear_min']
    wmin = min(d['worst'] for d in pe.values()); w2d = min(d['worst2d'] for d in pe.values()); nmv = min(d['nom_mv'] for d in pe.values())
    flag('pilot_end_check_move', nmv >= cm - 1e-9, 'supplier 1 mm move along the slot: pilot_end_clear_move_nom >= pilot_end_clear_min at both travel limits, Rev A and Rev B (expected FAIL: the pilot hits the slot end)')
    flag('pilot_end_check_drawing', wmin >= cm - 1e-9 and w2d >= -1e-9, 'drawing as released: worst case along the travel >= pilot_end_clear_min and corner case >= 0, both travel limits, Rev A and Rev B')
    ext = math.ceil((cm - wmin) * 2 - 1e-9) / 2 if wmin < cm else 0.0
    put('pilot_end_ecr_ext', ext, 'mm', 'CHANGED MEANING: FURTHER pilot-slot lengthening needed PER END beyond pilot_end_ext so that the worst-case end clearance reaches pilot_end_clear_min (rounded UP to 0.5); 0 = none', 1)
    text('pilot_query_answer', f"Refuse the {fm(i['pilot_slot_move'])} mm pilot-slot move in both directions. Sideways, the web to the M3 slots drops to {fm(round(min(webs), 2))} mm (< t = {fm(t)}). "
         f"Along the slot the web would be fine ({fm(round(min(wal), 2))} mm), but the pilot hits the slot end at a travel limit: with the motor screws at the ends of their slots the Ø{fm(i['pilot_dia'])} pilot has "
         f"{fm(round(min(d['nom'] for d in pe.values()), 2))} mm to the slot end (nominal; {fm(math.floor(wmin * 100 + 1e-9) / 100)} worst case), and a {fm(i['pilot_slot_move'])} mm move leaves {fm(round(nmv, 2))} mm: the pilot overlaps the slot end. "
         "Answer: the supplier keeps the drawing position and nests around it; a change to the pilot slot needs an ECR that lengthens the slot so both ends keep their clearance, never a nesting change.",
         'course decision revised; from web_after_move, web_move_along, pilot_end_clear_*')

    # ---------- heat path (PDS R10) ----------
    put('k_ratio', i['k_5052'] / i['k_steel'], 'x', 'k_5052 / k_steel: for the same path length, the steel bracket has this many times the thermal resistance', 1)
    v['heat_path_note'] = dict(value='Steel conducts heat about 2.8 times less well than 5052, so less of the motor heat leaves through the bracket. '
                                     'A NEMA 17-size stepper sheds most of its heat from its own case, and flat steel brackets are a common mount for this size, so the path is judged adequate. '
                                     'PDS R10 is verified by test: motor case temperature at the motor face, worst duty cycle, at (or corrected to) ambient_max, must stay within the motor maker limit.',
                               unit='', formula='engineering judgement + test (no thermal model in this course)', spoken='')

    # ---------- Ep 15: sheet gauges (typical published nominals; never specify a gauge alone) ----------
    for k, lab in (('ga14_steel', 'US 14 gauge, uncoated steel sheet (manufacturers standard gauge)'),
                   ('ga14_galv', 'US 14 gauge, galvanized steel sheet'), ('ga14_al', 'US 14 gauge, aluminium sheet'),
                   ('swg14', 'British SWG 14 (older imperial wire-gauge series, still seen on some quotes)')):
        put(f'{k}_in', i[f'{k}_in'], 'in', f'{lab}: typical published nominal; confirm with the supplier gauge table', 4)
        put(f'{k}_mm', i[f'{k}_in'] * 25.4, 'mm', f'{k}_in x 25.4', 3)
    tg = i['ga14_steel_in'] * 25.4
    put('ga14_t_diff', tg - i['t2'], 'mm', 'RETIRED story (2.0 mm drawing; course decision moved the deviation to 12 GA): ga14_steel_mm - t2', 3)
    cutw = max(cutA, cutB)
    fg = strength(i, tg, Ss, F, cutw)
    put('ga14_FOS_min', min(fg.values()), '-', 'smallest FOS at 14 GA steel on Sy_steel_min (bend, lumped net, worst real line Rev A/B, M5 hole section)', 2)
    flag('ga14_strength_check', min(fg.values()) >= i['FOS_gate'], 'ga14_FOS_min >= FOS_gate')
    _, tgA, mgA = stiffness(i, tg, i['E_steel'], nearA, F); _, tgB, mgB = stiffness(i, tg, i['E_steel'], nearB, F, travel=i['T_revB'])
    put('ga14_tilt', math.degrees(max(tgA, tgB)), 'deg', 'shaft tilt at 14 GA steel, design load, worst of Rev A/B (R = t)')
    put('ga14_move', max(mgA, mgB), 'mm', 'pulley movement at 14 GA steel, worst of Rev A/B')
    flag('ga14_tilt_check', math.degrees(max(tgA, tgB)) <= i['tilt_limit'] and max(mgA, mgB) <= i['move_limit'], 'R11 and R5 at 14 GA')
    g5, g3, gro5, gro3 = screws(tg)
    put('ga14_engD_M5', g5 / 5, 'D', 'M5 x 12 engagement at 14 GA / 5 mm', 2)
    put('ga14_engD_M3', g3 / 3, 'D', 'M3 x 6 engagement at 14 GA / 3 mm', 2)
    put('ga14_runout_M5', gro5, 'mm', 'depth_M5 - engagement at 14 GA: thread left below the screw tip (rule asks >= 1)', 2)
    put('ga14_runout_M3', gro3, 'mm', 'depth_M3 - engagement at 14 GA (rule asks >= 1)', 2)
    flag('ga14_screw_check', g5 / 5 >= 1.5 and g3 / 3 >= 1 and min(gro5, gro3) >= 1 - 1e-9, 'engagement rules and depth >= engagement + 1 at 14 GA')
    put('runout_M5', ro5, 'mm', 'depth_M5 - eng_M5 at the released thickness t_steel, nominal (rule asks >= 1)', 2)
    put('runout_M3', ro3, 'mm', 'depth_M3 - eng_M3 at the released thickness t_steel, nominal (rule asks >= 1; least value at the tolerance limits: runout_M3_min)', 2)
    put('ga14_tilt_revA', math.degrees(tgA), 'deg', 'shaft tilt at 14 GA steel, Rev A far end (information)')
    gok_s = v['ga14_strength_check']['value'] == 'PASS'; gok_t = v['ga14_tilt_check']['value'] == 'PASS'
    gtxt = (f"14 GA steel {'passes' if gok_s else 'fails'} strength (smallest FOS {fm(v['ga14_FOS_min']['value'])} on the specified minimum yield). "
            f"Shaft tilt is {fm(v['ga14_tilt_revA']['value'])} deg at Rev A and {fm(v['ga14_tilt']['value'])} deg at Rev B against the {fm(i['tilt_limit'])} deg limit, "
            f"so R11 {'passes' if gok_t else 'is not met at Rev B'} on the simplified model. "
            f"Each screw sits about {fm(round(-v['ga14_t_diff']['value'], 1))} mm deeper, leaving {fm(round(min(gro5, gro3), 1))} mm of thread below the tip instead of the 1 mm rule. ")
    gtxt += ('14 GA can be accepted as a recorded deviation after checking the real motor thread depth. ' if gok_s and gok_t else
             'Deviation request REJECTED on analysis: the supplier ships the 2.0 mm sheet on the drawing. A test alone is not a reason to accept a known analysis fail. ')
    v['ga14_verdict'] = dict(value=gtxt + 'The drawing stays "2.0 mm"; never specify a gauge alone.', unit='', formula='RETIRED story (2.0 mm drawing; superseded by ga12_verdict, course decision); from ga14_* keys', spoken='')

    # ---------- Ep 15 / Ep 22: 12 GA offered for the 2.5 mm drawing; 13 GA as the supplier's alternative ----------
    for gk, lab in (('ga12', 'US 12 gauge, uncoated steel'), ('ga13', 'US 13 gauge, uncoated steel')):
        tq = i[f'{gk}_steel_in'] * 25.4
        put(f'{gk}_steel_in', i[f'{gk}_steel_in'], 'in', f'{lab}: typical published nominal; confirm with the supplier gauge table', 4)
        put(f'{gk}_steel_mm', tq, 'mm', f'{gk}_steel_in x 25.4', 3)
        put(f'{gk}_t_diff', tq - t, 'mm', f'{gk}_steel_mm - t_steel (positive = thicker than the drawing)', 3)
        fq = strength(i, tq, i['Sy_steel_min'], F, cutw)
        put(f'{gk}_FOS_min', min(fq.values()), '-', f'smallest FOS at {lab} on Sy_steel_min', 2)
        flag(f'{gk}_strength_check', min(fq.values()) >= i['FOS_gate'], f'{gk}_FOS_min >= FOS_gate')
        _, qA, mqA = stiffness(i, tq, i['E_steel'], nearA, F); _, qB, mqB = stiffness(i, tq, i['E_steel'], nearB, F, travel=i['T_revB'])
        put(f'{gk}_tilt_revA', math.degrees(qA), 'deg', f'shaft tilt at {lab}, Rev A; ' + MODEL)
        put(f'{gk}_tilt', math.degrees(max(qA, qB)), 'deg', f'shaft tilt at {lab}, worst of Rev A/B')
        put(f'{gk}_move', max(mqA, mqB), 'mm', f'pulley movement at {lab}, worst of Rev A/B')
        put(f'{gk}_sys_margin', i['tilt_limit'] - (math.degrees(max(qA, qB)) + math.degrees(sl)) * work, 'deg', f'{lab}: tilt_limit - system tilt at the working load', 3)
        flag(f'{gk}_tilt_check', math.degrees(max(qA, qB)) <= i['tilt_limit'] and max(mqA, mqB) <= i['move_limit'], f'R11 and R5 at {lab}')
        q5, q3, qro5, qro3 = screws(tq)
        put(f'{gk}_engD_M5', q5 / 5, 'D', f'M5 x 12 engagement at {lab} / 5 mm', 2)
        put(f'{gk}_engD_M3', q3 / 3, 'D', f'M3 x 6 engagement at {lab} / 3 mm (rule >= 1D)', 2)
        put(f'{gk}_runout_M5', qro5, 'mm', f'depth_M5 - engagement at {lab} (rule >= 1)', 2)
        put(f'{gk}_runout_M3', qro3, 'mm', f'depth_M3 - engagement at {lab} (rule >= 1)', 2)
        put(f'{gk}_runout_M3x8', i['depth_M3'] - (i['L_M3_next'] - tq - i['washer_M3']), 'mm', f'depth_M3 - engagement with M3 x 8 at {lab} (negative = bottoms)', 2)
        flag(f'{gk}_screw_screen', q5 / 5 >= 1.5 and q3 / 3 >= 1 - 1e-9 and min(qro5, qro3) >= 1 - 1e-9,
             f'quick screen at the {lab} nominal: M5 >= 1.5D, M3 >= 1D, run-out >= 1 (a failed screen calls for the corner check)')
        tol = i[f'{gk}_tol_in'] * 25.4; lmin, lmax = tq - tol, tq + tol
        put(f'{gk}_tol_in', i[f'{gk}_tol_in'], 'in', f'{lab}: +/- band of a supplier gauge table for A1008 sheet (confirm with the supplier)', 4)
        put(f'{gk}_lot_t_min', lmin, 'mm', f'{lab}: thinnest sheet in the gauge band', 3)
        put(f'{gk}_lot_t_max', lmax, 'mm', f'{lab}: thickest sheet in the gauge band', 3)
        flag(f'{gk}_conform', tlo - 1e-9 <= tq <= thi + 1e-9, f'{lab} nominal inside the drawing band t_steel_min..t_steel_max (FAIL = nonconforming: a deviation is needed)')
        qlo = (i['L_M3'] - i['L_M3_tol']) - (lmax + zg) - (i['washer_M3'] + i['washer_M3_tol'])
        qhi = (i['L_M3'] + i['L_M3_tol']) - lmin - (i['washer_M3'] - i['washer_M3_tol'])
        nlo = (i['L_M3'] - i['L_M3_tol']) - (tq + zg) - (i['washer_M3'] + i['washer_M3_tol'])
        nhi = (i['L_M3'] + i['L_M3_tol']) - tq - (i['washer_M3'] - i['washer_M3_tol'])
        put(f'{gk}_engD_M3_min', qlo / 3, 'D', f'{lab}: least M3 x 6 engagement / 3 mm (gross), thickest sheet of the band, shortest screw, thickest washer', 2)
        put(f'{gk}_runout_M3_min', i['depth_M3'] - qhi, 'mm', f'{lab}: least run-out, thinnest sheet of the band, longest screw, thinnest washer (rule >= 1)', 2)
        put(f'{gk}_runout_M3_min_nom', i['depth_M3'] - nhi, 'mm', f'{lab}: least run-out with the sheet at the gauge nominal (rule >= 1)', 2)
        put(f'{gk}_FOS_strip', tA * (qlo - ded) / i['preload_M3'], '-', f'{lab}: strip FOS at the worst corner of the band, full threads (gate strip_gate)', 2)
        put(f'{gk}_FOS_strip_nom', tA * (nlo - ded) / i['preload_M3'], '-', f'{lab}: strip FOS with the sheet at the gauge nominal, full threads', 2)
        put(f'{gk}_FOS_strip_max', tA * (qlo - ded) / pmax, '-', f'{lab}: worst band corner at preload_M3_max (must stay above 1)', 2)
        okn = q5 / 5 >= 1.5 and qro5 >= 1 - 1e-9 and i['depth_M3'] - nhi >= 1 - 1e-9 and tA * (nlo - ded) / i['preload_M3'] >= i['strip_gate'] and tA * (nlo - ded) > pmax
        flag(f'{gk}_screw_check', okn, f'release check with the sheet at the {lab} nominal: M5 rules, M3 run-out >= 1 and strip check (full threads) at every screw/washer corner')
        flag(f'{gk}_band_check', t_win_lo <= lmin + 1e-9 and lmax <= t_win_hi + 1e-9, f'the whole {lab} gauge band inside stack_t_lo..stack_t_hi (FAIL = every sheet must be measured)')
        flag(f'{gk}_check', all(v[f'{gk}_{x}_check']['value'] == 'PASS' for x in ('strength', 'tilt', 'screw')), f'every check at the {lab} nominal (strength, tilt, screws)')
    put('ga12_max_measured_t', math.floor(t_win_hi * 100 + 1e-9) / 100, 'mm', 'stack_t_hi rounded down to 0.01: the thickest bare sheet (measured at incoming inspection) that passes every gate (strip FOS >= strip_gate on full threads, thread below tip >= 1)', 2)
    put('ga12_max_measured_t_plated', math.floor((t_win_hi + zg) * 100 + 1e-9) / 100, 'mm', 'stack_grip_hi rounded down to 0.01: limit for every finished PART measured OVER THE PLATING (micrometer, motor flange, 3 points); the plating allowance (grip_plating) is inside this limit, and a thicker real plating is caught by the measurement', 2)
    g12 = lambda k: v[f'ga12_{k}']['value']; g13 = lambda k: v[f'ga13_{k}']['value']
    ok12 = g12('check') == 'PASS'; tm = g('ga12_max_measured_t'); tmp_ = g('ga12_max_measured_t_plated')
    t12 = (f"A supplier offers one lot of 12 GA steel ({fm(g12('steel_mm'))} mm; gauge band {fm(round(g12('lot_t_min'), 2))}-{fm(round(g12('lot_t_max'), 2))}) for the {fm(t)} ±{fm(i['t_tol'])} mm on the drawing. "
           f"Strength {'passes' if g12('strength_check') == 'PASS' else 'fails'} (smallest FOS {fm(g12('FOS_min'))}) and tilt {'passes' if g12('tilt_check') == 'PASS' else 'fails'} ({fm(g12('tilt'))} deg). "
           f"The M3 x {fm(i['L_M3'])} motor screws fail the quick 1D screen ({fm(g12('engD_M3'))}D), so the stack is checked at every tolerance corner on full threads only: at the gauge nominal the strip FOS is {fm(g12('FOS_strip_nom'))} against {fm(i['strip_gate'])}, "
           f"but the top of the gauge band ({fm(round(g12('lot_t_max'), 2))} mm) would give only {fm(g12('FOS_strip'))}; every gate still passes up to {fm(tm)} mm. "
           f"It is still off the drawing ({fm(round(thi, 2))} mm max), so it needs a deviation. ")
    t12 += (f"Deviation ACCEPTED for this lot only, on one condition: at incoming inspection every PART measured over the plating (micrometer on the motor flange, 3 points) is {fm(tmp_)} mm or less, the plating allowance being inside that limit (parts above it are rejected); if agreed, every sheet may instead be measured bare at source before laser cutting, {fm(tm)} mm or less; lot number and quantity recorded, M3 x {fm(i['L_M3'])} and washer unchanged (M3 x {fm(i['L_M3_next'])} would bottom), quality approves. "
            if ok12 else 'Deviation request REJECTED on analysis. ')
    t12 += (f"A 13 GA lot ({fm(g13('steel_mm'))} mm; band {fm(round(g13('lot_t_min'), 2))}-{fm(round(g13('lot_t_max'), 2))}) fails on thread below the tip: at its thin end it leaves {fm(g13('runout_M3_min'))} mm, under our 1 mm rule. "
            f"The drawing stays \"{fm(t)} ±{fm(i['t_tol'])} mm before plating\"; never specify a gauge alone.")
    v['ga12_verdict'] = dict(value=t12, unit='', formula='course decision / re-based on the screw stack at the tolerance corners (full threads); generated from ga12_*, ga13_*, stack_t_*, ga12_max_measured_t', spoken='')
    text('ga12_lesson', 'Re-check the stack, not just strength: a thicker sheet takes engagement from every screw that passes through it, and a thinner one takes run-out. A failed quick screen calls for the full check at the tolerance limits, counting full threads only; if the lot passes only up to a measured thickness, that limit goes on the deviation and is checked at incoming inspection.',
         'Ep 15 / Ep 22 lesson line (replaces "thicker is not always better" as the deviation lesson; that line stays on Ep 06 route a)')
    text('ga12_dev_record', f"Deviation record (illustrative): part ACT-103; lot (SAMPLE lot number) and quantity; 12 GA uncoated steel {fm(g12('steel_mm'))} mm instead of {fm(t)} ±{fm(i['t_tol'])} mm; "
         f"THIS LOT ONLY; disposition: use as is if every PART measured over the plating (micrometer, motor flange, 3 points) is {fm(tmp_)} mm or less at incoming inspection (plating allowance inside the limit; reject parts above it), or every sheet measured bare at source before laser cutting is {fm(tm)} mm or less, motor screws M3 x {fm(i['L_M3'])} + ISO 7089 unchanged; "
         'checks re-run: strength, tilt, screw stack at the tolerance corners; approvals: quality and engineering (and the customer if the contract asks); drawing unchanged.',
         'Ep 22 S06 deviation record fields')

    # ---------- US conversions (Ep 15) ----------
    put('t2_in', i['t2'] / 25.4, 'in', 't2 / 25.4', 3)
    put('b_in', i['b'] / 25.4, 'in', 'b / 25.4', 2)
    put('F_design_lbf', F / 4.448222, 'lbf', 'F_design / 4.448', 1)
    put('M_lbfin', M / 112.98483, 'lbf.in', 'M (N.mm) / 112.985', 2)
    put('torque_lbfin', i['K'] * i['preload_M5'] * i['d_M5'] / 1000 * 8.850746, 'lbf.in', 'torque (N.m) x 8.851', 1)

    # ---------- cost and quantities (Ep 03, 18, 19) ----------
    be = i['be_tool_molded'] / (i['be_piece_sheet'] - i['be_piece_molded'])
    v['breakeven_inputs'] = dict(value=f"illustrative cost units: sheet metal {i['be_piece_sheet']:.1f}/part, no tooling; machined {i['be_piece_machined']:.1f}/part; molded {i['be_piece_molded']:.1f}/part + {i['be_tool_molded']:.0f} tooling; quantity {i['be_qty']:.0f}/year",
                                 unit='', formula='input', spoken='')
    put('breakeven_qty', be, 'parts', 'molded tooling / (sheet piece - molded piece)', 0)
    put('breakeven_years', be / i['qty_year'], 'years', 'breakeven_qty / qty_year (1778 / 500 = 3.56, said as three point six years)', 1)
    v['breakeven_years']['spoken'] = 'three point six years'
    # Ep 03 S13 (R4 #151): the Pugh datum is the machined block, so the cost score of the molded concept uses molded vs machined
    bem = i['be_tool_molded'] / (i['be_piece_machined'] - i['be_piece_molded'])
    put('breakeven_qty_machined', bem, 'parts', 'molded tooling / (machined piece - molded piece): molded vs the machined Pugh datum (Ep 03 S13)', 0)
    put('breakeven_years_machined', bem / i['qty_year'], 'years', 'breakeven_qty_machined / qty_year (485 / 500 = 0.97: under one year)', 2)
    text('breakeven_machined_note', f"Molded vs machined: break-even {round(bem)} parts, under 1 year at {i['qty_year']:.0f}/year", 'from breakeven_qty_machined, breakeven_years_machined, qty_year (Ep 03 S13 Pugh cost reason)')

    # ---------- Ep 07: materials and the weighted matrix ----------
    put('PA66_Sy', i['PA66_Sy'], 'MPa', 'typical PA66 yield, dry as moulded; lower when it absorbs moisture; creeps under steady load, more when warm', 0)
    put('PA66_E', i['PA66_E'], 'MPa', 'typical PA66 modulus, dry as moulded (lower when moist or warm)', 0)
    v['PA66_rho'] = dict(value=i['PA66_rho'], unit='g/cm^3', formula='typical PA66 density', spoken='one point one four grams per cubic centimetre')
    put('anodize_um', i['anodize_um'], 'um', 'clear anodize thickness, minimum: ACT-101 end block (the bracket is now zinc plated)', 0)
    v['anodize_um']['spoken'] = 'ten micrometres'
    v['zinc_um']['spoken'] = 'eight micrometres'
    w = i['mx_weights']; S = {m: dict(sc) for m, sc in i['mx_scores'].items()}
    if abs(sum(w.values()) - 1) > 1e-9: raise SystemExit('matrix weights must add to 100 %')
    lo_b, hi_b = i['study_score_bands']
    for m, tt, E, lp in (('steel', i['t_steel'], i['E_steel'], False), ('al', i['t2'], i['E'], True), ('ss', i['t_steel'], i['study_E_ss'], False)):
        qa = math.degrees(stiffness(i, tt, E, nearA, F, lp)[1]); qb = math.degrees(stiffness(i, tt, E, nearB, F, lp, travel=i['T_revB'])[1])
        sm = i['tilt_limit'] - (max(qa, qb) + math.degrees(sl)) * work
        S[m]['stiffness'] = 1 if max(qa, qb) > i['tilt_limit'] else 2 if sm < 0 else 3 if sm / i['tilt_limit'] * 100 < lo_b else 4 if sm / i['tilt_limit'] * 100 < hi_b else 5
        put(f'mx_sysmargin_{m}', sm, 'deg', f'Ep 07 stiffness basis, {m} ({fm(tt)} mm, its best route): tilt_limit - worst system tilt at the working load', 3)
        put(f'mx_sysmargin_{m}_pct_n', sm / i['tilt_limit'] * 100, '', f'mx_sysmargin_{m} as % of tilt_limit, number only (spoken without the unit word: E07S07_05 voice fix, FIX_ENG Ep07 S-1)', 0)
    kk = {'al': i['k_5052'], 'steel': i['k_steel'], 'ss': i['k_ss304'], 'pa66': i['k_PA66']}
    order_k = sorted(kk, key=kk.get)
    flag('mx_heat_consistent', all(S[order_k[j]]['heat'] <= S[order_k[j + 1]]['heat'] for j in range(len(order_k) - 1)),
         'Ep 07 heat scores never rise as typical thermal conductivity falls (k_PA66 < k_ss304 < k_steel < k_5052)')
    text('mx_heat_basis', f"Heat-path score (PDS R10) follows typical thermal conductivity: 5052 {fm(i['k_5052'])}, low-carbon steel {fm(i['k_steel'])}, 304 stainless {fm(i['k_ss304'])}, PA66 {fm(i['k_PA66'])} W/(m.K) (typical; the maker's data governs). 304 and PA66 both score 1, the bottom of the scale.",
         'from k_5052, k_steel, k_ss304, k_PA66 and mx_s_*_heat')
    text('mx_stiff_rule', f"Stiffness score from the real margin: R11 fail 1; system over the limit 2; system margin under {fm(lo_b)} % of the limit 3; under {fm(hi_b)} % 4; otherwise 5. Steel and 304 at the released thickness, aluminium on its lips route.",
         'scores mx_s_*_stiffness are computed, not typed')
    for cname, wt in w.items():
        put(f'mx_w_{cname}', wt * 100, '%', f'Ep 07 weight, {cname}', 0)
        for m in S:
            put(f'mx_s_{m}_{cname}', S[m][cname], '-', f'Ep 07 score 1-5, {m}, {cname}', 0)
    tot = {m: sum(w[c] * S[m][c] for c in w) for m in S}
    for m in S:
        put(f'mx_total_{m}', tot[m], '-', 'Ep 07 matrix (6 criteria incl. heat path R10): sum(weight x score)', 2)
    # sensitivity: every 10 % shift from one criterion to another
    worst = (9.0, '')
    for a_ in w:
        for b_ in w:
            if a_ == b_ or w[a_] < 0.10 - 1e-9: continue
            alt = dict(w); alt[a_] -= 0.10; alt[b_] += 0.10
            ts = {m: sum(alt[c] * S[m][c] for c in alt) for m in S}
            gap = ts['steel'] - max(ts[m] for m in S if m != 'steel')
            if gap < worst[0]: worst = (gap, f'{a_} -> {b_}', ts['steel'], ts['al'])
    put('mx_sens_gap', worst[0], '-', f'smallest lead of steel over the runner-up after any 10 % weight shift (worst case: {worst[1]})', 2)
    put('mx_sens_steel', worst[2], '-', f'steel total in that worst case ({worst[1]})', 2)
    put('mx_sens_al', worst[3], '-', f'aluminium + lips total in that worst case ({worst[1]})', 2)
    # heat weight at which aluminium would catch steel (heat weight taken from stiffness)
    d_heat = S['al']['heat'] - S['steel']['heat']; d_stiff = S['steel']['stiffness'] - S['al']['stiffness']
    x = (tot['steel'] - tot['al']) / (d_heat + d_stiff)
    put('mx_heat_tie_pct', (w['heat'] + x) * 100, '%', 'heat-path weight (taken from stiffness) at which aluminium + lips ties with steel', 0)

    # ---------- Ep 21: repair-time estimate (illustrative) ----------
    names = ['isolate and lock out power', 'remove top cover', 'back off tension screw', 'loosen motor screws, slide motor',
             'open belt clamps, remove belt', 'fit new belt, clamp ends', 'tension, tighten motor screws, lock nut',
             'check tension and tracking, test move', 'refit cover, restore power']
    for k, (m, nm) in enumerate(zip(i['mttr'], names), 1):
        put(f'mttr_s{k}', float(m), 'min', f'illustrative step time: {nm}', 0)
    put('mttr_total', float(sum(i['mttr'])), 'min', 'sum of mttr_s1..s9 (excludes travel to the unit and fetching parts)', 0)
    text('worst_rev_rule', 'Margins on screen (Ep 06 route table, Ep 07, Ep 23) use the worst-revision keys: route_*_margin_worst and route_*_sys_margin_worst (= study_*_margin / study_*_sys_margin, tilt_sys_margin_steel). The Rev A keys route_*_tilt, route_*_margin, route_*_sys_margin are shown only when labelled "Rev A, motor at the far end".',
         'one set of margin keys for every episode')
    # ---------- ECO-001 load path: COTS-219 -> ACT-109 -> 2x COTS-221 -> ACT-101 (6061-T6) ----------
    # SAMPLE belt installation tension (Ep 21 service, course decision): both straight spans pull on the shaft, so each span carries half the hub load
    put('belt_T_install', i['F_max'] / 2, 'N', 'SAMPLE installation tension per belt span = F_max / 2 (two parallel spans give the hub load F_max); confirm with the belt maker', 0)
    text('belt_T_method', f"Set the belt to the SAMPLE installation tension, {fm(i['F_max'] / 2)} N per span, measured with a belt tension meter (span frequency) or the belt maker's force-deflection method; then lock the tension screw. Confirm the value with the belt maker.", 'service step: tension is measured, never set by feel')
    put('act109_load_work', i['F_max'], 'N', 'tension-screw (COTS-219) load = working belt load on the motor, F_max: ACT-109 carries it to ACT-101', 1)
    put('act109_load_stall', rv_('F_stall'), 'N', 'same at a crash / stall (F_stall), rare', 1)
    def m4(L, Lt):
        lo_ = (L - Lt) - (i['act109_t'] + i['act109_t_tol']); hi_ = (L + Lt) - (i['act109_t'] - i['act109_t_tol'])
        return lo_, hi_
    m_lo, m_hi = m4(i['L_M4'], i['L_M4_tol']); s_lo, s_hi = m4(i['L_M4_short'], i['L_M4_short_tol'])
    put('eng_M4_min', m_lo, 'mm', 'COTS-221 M4 x 12: (L - L_M4_tol) - (act109_t + act109_t_tol): least engagement in ACT-101', 2)
    put('engD_M4_min', m_lo / i['d_M4'], 'D', 'eng_M4_min / 4 mm (rule >= 1.5D in 6061-T6)', 2)
    put('runout_M4_min', i['depth_M4'] - m_hi, 'mm', 'depth_M4 - most engagement: thread left below the tip (rule >= 1)', 2)
    put('engD_M4x10_min', s_lo / i['d_M4'], 'D', 'information: the M4 x 10 first listed gives this (below 1.5D), so it is not used', 2)
    nm = 1 / i['P_M4']; Am4 = math.pi * nm * i['d_min_M4'] * (1 / (2 * nm) + 0.57735 * (i['d_min_M4'] - i['D2_max_M4']))
    dm4 = (i['thread_end_P'] + i['lead_in_P']) * i['P_M4']
    put('FOS_strip_M4', i['tau_6061'] * Am4 * (m_lo - dm4) / i['preload_M4'], '-', 'information: tau_6061 x A_strip x full-thread engagement / preload_M4 (screw end 2P and lead-in 0.5P deducted)', 1)
    put('act109_slip_margin', 2 * i['mu'] * i['preload_M4'] / rv_('F_stall'), '-', '2 x mu x preload_M4 / F_stall: the 2x M4 hold ACT-109 by friction even at a stall (static)', 0)
    flag('M4_act109_check', m_lo / i['d_M4'] >= 1.5 and i['depth_M4'] - m_hi >= 1 - 1e-9, 'COTS-221 M4 x 12: >= 1.5D in 6061-T6 and run-out >= 1 at the tolerance limits')
    text('cots221_choice', f"COTS-221 = ISO 4762 M4 x {fm(i['L_M4'])}, class 8.8 (closes 'length TBC'): through the {fm(i['act109_t'])} mm ACT-109 flange it engages at least {fm(round(m_lo / i['d_M4'], 2))}D in ACT-101 (rule 1.5D in 6061-T6) "
         f"and leaves at least {fm(round(i['depth_M4'] - m_hi, 2))} mm of the {fm(i['depth_M4'])} mm thread below the tip; M4 x {fm(i['L_M4_short'])} would give only {fm(round(s_lo / i['d_M4'], 2))}D.",
         'from eng_M4_min, runout_M4_min, engD_M4x10_min')
    text('act109_load_note', f"ECO-001 load path: the tension screw COTS-219 bears on a flat face of the motor flange (not on the pilot or a thread) and carries the working belt load ({fm(i['F_max'])} N) into ACT-109; 2x COTS-221 M4 x {fm(i['L_M4'])} hold ACT-109 to ACT-101 by friction (slip margin {fm(round(2 * i['mu'] * i['preload_M4'] / g('F_stall')))} even at a stall) with at least {fm(round(m_lo / i['d_M4'], 2))}D engagement.",
         'Ep 22 S09 check line; from act109_*, eng_M4_min')

    # ---------- belt-alignment budget (PDS R11; alignment_study.md): the 1/4 deg is TOTAL angular misalignment between the pulleys ----------
    # steering plane = rotation about an axis parallel to the ACT-103 bend line (the axis of the load tilt AND of the bend-angle error)
    tw_ = math.degrees(max(totS, totSB)); e_br = tw_ * work; e_sh = math.degrees(sl) * work; e_tot = e_br + e_sh
    bud = i['tilt_guide'] - e_tot
    put('mis_total_allowed', i['tilt_guide'], 'deg', 'R11 total budget: belt-entry angle at each pulley in every span (static + elastic, in operation); for an open-ended carriage belt the spans are pulley-to-clamp and the return span (synchronous-belt guidance; belt maker wins)', 2)
    put('mis_e_bracket', e_br, 'deg', 'elastic item: worst bracket tilt (Rev B, motor at the far end) x F_max / F_design (working load); ' + MODEL, 3)
    put('mis_e_shaft', e_sh, 'deg', 'elastic item: tilt_shaft_est x F_max / F_design (motor shaft flex at the working load, bearings rigid)', 3)
    put('mis_elastic', e_tot, 'deg', 'ELASTIC budget used: mis_e_bracket + mis_e_shaft (= tilt_sys_work_steel)', 3)
    put('misalign_budget', bud, 'deg', 'STATIC budget: tilt_guide - mis_elastic: what all static errors together may use (as-made bend, machined chain, motor face, pulleys, bearing play) (= tilt_sys_margin_steel)', 3)
    put('mis_static_budget', bud, 'deg', 'same as misalign_budget (name used in the budget table)', 3)
    a_seat = math.degrees(math.atan(i['perp_motor_seat'] / i['perp_seat_len']))
    put('perp_motor_seat', i['perp_motor_seat'], 'mm', 'input (drawing): perpendicularity of the motor seat to datum A (the frame "⊥ 1.2 | A")', 2)
    put('perp_seat_len', i['perp_seat_len'], 'mm', 'input: length of the motor seat over which the perpendicularity zone applies', 0)
    put('perp_seat_angle', a_seat, 'deg', 'atan(perp_motor_seat / perp_seat_len): seat angle the perpendicularity frame allows', 2)
    s_bend = max(i['tol_bend_angle'], a_seat)
    s_mach = i['mis_mach_n'] * math.degrees(i['mis_mach_perp'] / i['mis_mach_len'])
    s_mot = math.degrees(i['motor_perp_tir'] / i['motor_perp_dia'])
    s_pul = 2 * math.degrees(i['pulley_bore_form'] / i['pulley_bore_len'])
    s_mpl = math.degrees(i['motor_play'] / i['motor_play_span'])
    s_ipl = math.degrees(i['idler_clear'] / i['idler_span'])
    oth = [s_mach, s_mot, s_pul, s_mpl, s_ipl]; s_oth = sum(oth); s_worst = s_bend + s_oth
    put('mis_s_bend', s_bend, 'deg', 'static item, worst case: max(tol_bend_angle, perp_seat_angle): as-made motor-seat angle the drawing allows (bend 90 deg +/-1 deg; ⊥ 1.2 | A over 65 mm)', 2)
    put('mis_s_machined', s_mach, 'deg', 'static item: machined chain ACT-101 end face, ACT-108 base plate, ACT-102 idler bore: mis_mach_n x mis_mach_perp / mis_mach_len (illustrative CNC values)', 3)
    put('mis_s_motor', s_mot, 'deg', 'static item: SAMPLE motor mounting-face perpendicularity to the shaft, motor_perp_tir T.I.R. read at motor_perp_dia (assumed): T.I.R. / diameter (the real motor maker wins)', 3)
    put('mis_s_pulley', s_pul, 'deg', 'static item: both pulleys seated by their set screws, bore form error pulley_bore_form over pulley_bore_len each (assumed)', 3)
    put('mis_s_motor_play', s_mpl, 'deg', 'static item: SAMPLE motor radial play motor_play over the bearing span motor_play_span (assumed); taken up by the belt pull', 3)
    put('mis_s_idler_play', s_ipl, 'deg', 'static item: 608 bearing radial clearance (normal group, upper value) over the ACT-102 bearing span (assumed)', 3)
    put('mis_s_other', s_oth, 'deg', 'static items that are NOT the bracket: machined chain + motor face + pulleys + bearing play (worst-case sum)', 3)
    put('mis_s_other_rss', math.sqrt(sum(x * x for x in oth)), 'deg', 'information: the same items added statistically (root sum of squares); still above misalign_budget', 3)
    put('mis_static_worst', s_worst, 'deg', 'STATIC total as toleranced, no adjustment: mis_s_bend + mis_s_other (worst case)', 2)
    put('mis_total_toleranced', e_tot + s_worst, 'deg', 'information: mis_elastic + mis_static_worst: a conforming assembly with no alignment step', 2)
    flag('mis_tolerance_check', s_worst <= bud, 'static errors as toleranced <= misalign_budget (expected FAIL: the bend tolerance and the bought parts use it up)')
    put('perp_motor_seat_needed', math.tan(math.radians(bud)) * i['perp_seat_len'], 'mm', 'information: tan(misalign_budget) x perp_seat_len: the motor-seat ⊥ a tolerance-only route would need if the bracket took the WHOLE static budget (nothing left for the bought parts)', 2)
    put('bend_static_tilt', i['tol_bend_angle'], 'deg', 'as-made bend-angle error allowed by the drawing (tol_bend_angle); it rotates the motor seat about the same axis as the load tilt', 1)
    flag('bend_budget_check', i['tol_bend_angle'] <= bud, 'bend_static_tilt <= misalign_budget (expected FAIL: the bend tolerance alone is about 11 times the static budget)')
    # options
    put('tol_bend_practical', i['tol_bend_practical'], 'deg', 'input: press-brake bend angle, practical +/- with machine calibration (typical published shop value; supplier confirms)', 1)
    put('tol_bend_best', i['tol_bend_best'], 'deg', 'input: press-brake bend angle, +/- with active angle measurement and crowning (specialised; typical published value)', 1)
    oa = i['tol_bend_best'] + s_oth
    put('mis_opt_a_static', oa, 'deg', 'option (a) tighten the bend to tol_bend_best: static = tol_bend_best + mis_s_other', 2)
    flag('mis_opt_a_check', oa <= bud, 'option (a) static <= misalign_budget (expected FAIL; even a perfect bend leaves mis_s_other above the budget)')
    ob = math.degrees(math.atan(rv_('stack_t_margin_hi') / i['m3_pat']))
    put('mis_opt_b_range', ob, 'deg', 'option (b) shims under the motor face: largest correction = atan(stack_t_margin_hi / m3_pat): a thicker shim breaks the M3 strip check', 2)
    flag('mis_opt_b_check', ob >= s_worst, 'option (b) shim range >= mis_static_worst (expected FAIL; shims also add two faying faces to the friction joint)')
    oc = math.degrees(i['mis_mach_perp'] / i['mis_mach_len']) + s_oth
    put('mis_opt_c_static', oc, 'deg', 'option (c) motor on a machined seat or spigot: static = one machined feature + mis_s_other', 2)
    flag('mis_opt_c_check', oc <= bud, 'option (c) static <= misalign_budget (expected FAIL; also changes the released part)')
    put('mis_adj_range', i['adj_range'], 'deg', 'design requirement: ACT-102 idler-angle adjustment range +/- in the steering plane (the idler is set to the rail)', 1)
    flag('mis_adj_range_check', i['adj_range'] >= s_worst, 'RETIRED (first alignment method: idler-only setting, both pulleys compared with each other; replaced by the per-pulley method to the rail, mis_p_accept / mis_drv_total / mis_idl_total; never show): option (d): mis_adj_range >= mis_static_worst (every conforming part can be set)')
    u_ = math.degrees(2 * i['dti_res'] / i['set_sweep'])
    put('mis_set_accept', i['set_accept'], 'deg', 'RETIRED (first alignment method: idler-only setting, both pulleys compared with each other; replaced by the per-pulley method to the rail, mis_p_accept / mis_drv_total / mis_idl_total; never show): option (d) assembly acceptance: angle between the two pulley faces in the steering plane after setting', 2)
    put('mis_set_accept_mm', math.tan(math.radians(i['set_accept'])) * i['set_sweep'], 'mm', 'RETIRED (first alignment method: idler-only setting, both pulleys compared with each other; replaced by the per-pulley method to the rail, mis_p_accept / mis_drv_total / mis_idl_total; never show): mis_set_accept as an indicator difference over set_sweep (16 mm of carriage travel across each pulley flange face)', 3)
    put('mis_set_uncert', u_, 'deg', 'RETIRED (first alignment method: idler-only setting, both pulleys compared with each other; replaced by the per-pulley method to the rail, mis_p_accept / mis_drv_total / mis_idl_total; never show): measurement uncertainty of the setting: 2 x dti_res / set_sweep (two readings, each to the indicator resolution)', 3)
    res = i['set_accept'] + u_
    put('mis_static_set', res, 'deg', 'RETIRED (first alignment method: idler-only setting, both pulleys compared with each other; replaced by the per-pulley method to the rail, mis_p_accept / mis_drv_total / mis_idl_total; never show): STATIC after setting: mis_set_accept + mis_set_uncert (every static item is measured together on the pulley faces at installation tension)', 3)
    flag('mis_static_set_check', res <= bud, 'RETIRED (first alignment method: idler-only setting, both pulleys compared with each other; replaced by the per-pulley method to the rail, mis_p_accept / mis_drv_total / mis_idl_total; never show): mis_static_set <= misalign_budget')
    tot_ = e_tot + res
    put('mis_total', tot_, 'deg', 'RETIRED (first alignment method: idler-only setting, both pulleys compared with each other; replaced by the per-pulley method to the rail, mis_p_accept / mis_drv_total / mis_idl_total; never show): TOTAL in operation with option (d): mis_elastic + mis_static_set (elastic counted from zero load: the pretension already acting when the setting is made is not credited)', 3)
    put('mis_margin', i['tilt_guide'] - tot_, 'deg', 'RETIRED (first alignment method: idler-only setting, both pulleys compared with each other; replaced by the per-pulley method to the rail, mis_p_accept / mis_drv_total / mis_idl_total; never show): tilt_guide - mis_total', 3)
    put('mis_margin_pct', (i['tilt_guide'] - tot_) / i['tilt_guide'] * 100, '%', 'RETIRED (first alignment method: idler-only setting, both pulleys compared with each other; replaced by the per-pulley method to the rail, mis_p_accept / mis_drv_total / mis_idl_total; never show): mis_margin as % of tilt_guide', 0)
    flag('mis_check', tot_ <= i['tilt_guide'] and i['adj_range'] >= s_worst, 'RETIRED (first alignment method: idler-only setting, both pulleys compared with each other; replaced by the per-pulley method to the rail, mis_p_accept / mis_drv_total / mis_idl_total; never show): R11 total budget met with option (d): mis_total <= tilt_guide and the adjustment covers every conforming part')
    text('drw_bend_note', f"BEND 90° ±{fm(i['tol_bend_angle'])}°, INSIDE R{fm(R)}", 'ACT-103 drawing note (unchanged value): from tol_bend_angle, R_rel')
    text('drw_perp_motor_seat', f"⊥ {fm(i['perp_motor_seat'])} | A (MOTOR SEAT)", 'ACT-103 drawing frame on the motor seat (unchanged value): from perp_motor_seat')
    # ---------- belt alignment R2: open-ended belt clamped to the carriage (alignment_study.md section R2) ----------
    # Three belt spans: S1 drive pulley <-> carriage clamp 1, S2 idler pulley <-> carriage clamp 2, S3 return span drive <-> idler.
    # Each clamp travels along the rail, so the reference for BOTH pulleys and BOTH clamps is the rail (carriage travel), not the other pulley.
    # Steering plane = rotation about the vertical axis (parallel to the ACT-103 bend line). Twist about the belt direction is checked separately.
    d_ = math.degrees
    m1 = d_(i['mis_mach_perp'] / i['mis_mach_len'])
    text('mis_req_text', f"Belt alignment, open-ended belt clamped to the carriage: the belt has three spans - drive pulley to carriage clamp, idler pulley to carriage clamp, and the return span between the pulleys. "
         f"In the steering plane (rotation about the vertical axis, parallel to the ACT-103 bend line) the belt-entry angle at each pulley, in every span, is at most {fm(i['tilt_guide'])} deg in operation, static + elastic. "
         "Each clamp travels along the rail, so both pulleys AND both clamps are set to the rail (the carriage travel), not only to each other; the drive-to-idler difference is also limited (return span). "
         "Twist about the belt direction does not change the entry angle; it is checked (mis_twist_strain), not budgeted.",
         'R11 requirement, open-ended carriage belt; belt-entry-angle wording per synchronous-belt installation guidance (alignment_study.md R2)')
    for k, u_, src in (('adj_range_drive', 'deg', 'input: ACT-101 drive end block yaw adjustment range +/- (design requirement)'),
                       ('act101_dowel_span', 'mm', 'input: ACT-101 pivot dowel to ACT-111 eccentric centre (design value, illustrative)'),
                       ('ecc_e', 'mm', 'input: ACT-111 eccentric pin eccentricity (design value)'),
                       ('pulley_x', 'mm', 'input: pivot dowel to drive pulley axis along the rail (layout value, illustrative)'),
                       ('dti_res_r2', 'mm', 'input: digital indicator resolution for the alignment step; reading error taken as one resolution per reading'),
                       ('flange_flat', 'mm', 'input (SAMPLE pulley spec): outer flange face turned with the bore, flatness over the reading zone; receiving check'),
                       ('travel_straight', 'mm', 'input (illustrative): carriage running straightness over a 16-20 mm sweep'),
                       ('clamp_sweep', 'mm', 'input: carriage travel along the ACT-107 reference side face'),
                       ('clamp_face_par', 'mm', 'input (drawing value): ACT-107 reference side face parallel to the belt-tooth slot, machined in one set-up'),
                       ('clamp_adj_range', 'deg', 'input: ACT-107 clamp yaw range on its screw holes +/- (design requirement; confirm at the ACT-104/107 detail)'),
                       ('span_min', 'mm', 'input (layout value, illustrative): shortest live belt span, carriage at the stroke end'),
                       ('peel_lam', 'mm', 'input: lamination of a standard peel shim (wedge-shim option)')):
        put(k, i[k], u_, src, 3)
    # static items per pulley, as toleranced (worst case), each against the rail
    s_drv = s_bend + 2 * m1 + s_mot + s_pul / 2 + s_mpl
    s_idl = 2 * m1 + s_pul / 2 + s_ipl
    put('mis_drv_static_worst', s_drv, 'deg', 'drive pulley to the rail, as toleranced: mis_s_bend + ACT-101 end face + ACT-108 dowel line to rail seat (2 x mis_mach_perp / mis_mach_len) + mis_s_motor + one pulley (mis_s_pulley / 2) + mis_s_motor_play', 2)
    put('mis_idl_static_worst', s_idl, 'deg', 'idler pulley to the rail, as toleranced: ACT-102 bore + ACT-108 dowel line to rail seat (2 x mis_mach_perp / mis_mach_len) + one pulley (mis_s_pulley / 2) + mis_s_idler_play', 3)
    # acceptance (per part, against the rail) and measurement uncertainty (worst-case sum of the items)
    a_p = d_(math.atan(i['r2_accept_mm'] / i['set_sweep'])); a_c = d_(math.atan(i['r2_accept_mm'] / i['clamp_sweep']))
    put('read_r', i['set_sweep'] / 2, 'mm', 'reading radius on the pulley flange face: the two indicator points are read_r either side of the shaft centre (set_sweep / 2)', 0)
    put('mis_p_accept_mm', i['r2_accept_mm'], 'mm', 'acceptance, EACH pulley against the rail: indicator change over set_sweep (two points 8 mm either side of the shaft centre, mean of two half-turn positions)', 3)
    put('mis_p_accept', a_p, 'deg', 'mis_p_accept_mm as an angle: atan(r2_accept_mm / set_sweep)', 3)
    put('mis_c_accept_mm', i['r2_accept_mm'], 'mm', 'acceptance, EACH belt clamp (ACT-107) against the rail: indicator change over clamp_sweep along its reference side face', 3)
    put('mis_c_accept', a_c, 'deg', 'mis_c_accept_mm as an angle: atan(r2_accept_mm / clamp_sweep)', 3)
    put('mis_d_accept_mm', i['r2_accept_mm'], 'mm', 'acceptance, return span: drive-pulley mean minus idler-pulley mean (with sign), over set_sweep', 3)
    put('mis_d_accept', a_p, 'deg', 'mis_d_accept_mm as an angle', 3)
    u_r = d_(2 * i['dti_res_r2'] / i['set_sweep']); u_f = d_(i['flange_flat'] / i['set_sweep']); u_t = d_(i['travel_straight'] / i['set_sweep']); u_p = u_r + u_f + u_t
    put('mis_u_res', u_r, 'deg', 'uncertainty item, each pulley: indicator reading error, 2 x dti_res_r2 / set_sweep (two readings; resolution and local indication error over the few micrometres used)', 4)
    put('mis_u_flat', u_f, 'deg', 'uncertainty item, each pulley: flange-face flatness, flange_flat / set_sweep (the half-turn mean cancels wobble and every odd-order face form; the belt turns the pulley during the sweep, so even-order form such as a saddle remains: counted in full)', 4)
    put('mis_u_travel', u_t, 'deg', 'uncertainty item, each pulley: carriage running straightness over the sweep, travel_straight / set_sweep', 4)
    put('mis_u_pulley', u_p, 'deg', 'measurement uncertainty, EACH pulley: mis_u_res + mis_u_flat + mis_u_travel (worst-case sum)', 3)
    put('mis_u_pulley_rss', math.sqrt(u_r ** 2 + u_f ** 2 + u_t ** 2), 'deg', 'information: the same items added statistically (root sum of squares); the budget uses the worst-case sum', 3)
    c_r = d_(2 * i['dti_res_r2'] / i['clamp_sweep']); c_p = d_(i['clamp_face_par'] / i['clamp_sweep']); c_t = d_(i['travel_straight'] / i['clamp_sweep']); u_c = c_r + c_p + c_t
    put('mis_u_clamp', u_c, 'deg', 'measurement uncertainty, EACH clamp: (2 x dti_res_r2 + clamp_face_par + travel_straight) / clamp_sweep (worst-case sum)', 3)
    # span totals (elastic acts on the drive pulley only: bracket + motor shaft; the idler block is taken as rigid)
    s1 = e_tot + a_p + u_p + a_c + u_c; s2 = a_p + u_p + a_c + u_c; s3 = e_tot + a_p + 2 * u_p
    put('mis_s1_total', s1, 'deg', 'span S1, drive pulley to carriage clamp: mis_elastic + (mis_p_accept + mis_u_pulley) + (mis_c_accept + mis_u_clamp)', 3)
    put('mis_s2_total', s2, 'deg', 'span S2, idler pulley to carriage clamp: (mis_p_accept + mis_u_pulley) + (mis_c_accept + mis_u_clamp); no elastic item on the idler (rigid block assumed; the R11 test covers it)', 3)
    put('mis_s3_total', s3, 'deg', 'span S3, return span drive to idler: mis_elastic + mis_d_accept + 2 x mis_u_pulley (difference of two measured means)', 3)
    for n_, t_ in (('s1', s1), ('s2', s2), ('s3', s3)):
        put(f'mis_{n_}_margin', i['tilt_guide'] - t_, 'deg', f'tilt_guide - mis_{n_}_total', 3)
    dt_ = max(s1, s3); it_ = max(s2, s3)
    put('mis_drv_total', dt_, 'deg', 'DRIVE pulley, worst span: max(mis_s1_total, mis_s3_total)', 3)
    put('mis_idl_total', it_, 'deg', 'IDLER pulley, worst span: max(mis_s2_total, mis_s3_total) (the return span carries the drive elastic item)', 3)
    put('mis_drv_margin', i['tilt_guide'] - dt_, 'deg', 'tilt_guide - mis_drv_total', 3)
    put('mis_idl_margin', i['tilt_guide'] - it_, 'deg', 'tilt_guide - mis_idl_total', 3)
    put('mis_drv_margin_pct', (i['tilt_guide'] - dt_) / i['tilt_guide'] * 100, '%', 'mis_drv_margin as % of tilt_guide (rounded down)', 0)
    put('mis_idl_margin_pct', (i['tilt_guide'] - it_) / i['tilt_guide'] * 100, '%', 'mis_idl_margin as % of tilt_guide (rounded down)', 0)
    flag('mis_r2_check', max(s1, s2, s3) <= i['tilt_guide'] and a_p + u_p + a_c + u_c <= bud, 'R11 met in every span with the R2 method: mis_s1/s2/s3_total <= tilt_guide')
    s1p = e_tot / work + a_p + u_p + a_c + u_c
    put('mis_s1_total_peak', s1p, 'deg', 'information: span S1 at the design load (start-stop peak, F_design): mis_elastic x F_design / F_max + the same static items; momentary', 3)
    text('mis_budget_basis', f"The R11 budget is for steady running at the working load (F_max). Start-stop peaks at F_design = {fm(i['k_dyn'])} x F_max are momentary: the drive span then reaches about {fm(g('mis_s1_total_peak'))} deg for an instant; "
         "the 1.25 factor is a strength and tilt-gate factor and is not inside the alignment budget.", 'R2 transient note; from mis_s1_total_peak')
    # adjustment ranges
    rng_d = d_(math.atan(i['ecc_e'] / i['act101_dowel_span']))
    put('mis_drv_range', rng_d, 'deg', 'ACT-101 yaw range from ACT-111: atan(ecc_e / act101_dowel_span)', 2)
    flag('mis_drv_range_check', rng_d >= i['adj_range_drive'] >= s_drv, 'mis_drv_range >= adj_range_drive >= mis_drv_static_worst (every conforming drive side can be set)')
    flag('mis_idl_range_check', i['adj_range'] >= s_idl, 'mis_adj_range (ACT-102) >= mis_idl_static_worst')
    put('mis_ecc_turn', a_p / (i['ecc_e'] / i['act101_dowel_span']), 'deg', 'eccentric turn that moves the drive pulley by one acceptance, mid-range: mis_p_accept / (ecc_e / act101_dowel_span) (fine; set, torque, re-measure)', 2)
    put('mis_drv_shift_max', i['pulley_x'] * math.tan(math.radians(s_drv)), 'mm', 'largest axial shift of the drive pulley when ACT-101 turns: pulley_x x tan(mis_drv_static_worst); re-centre the pulley on its shaft (assembly step 1)', 2)
    # options that do not work (or are not needed)
    sp = i['y2'] - i['L1']
    text('mis_opt_slot_text', 'Slotting the ACT-103 holes (or the motor slots) cannot correct the yaw: a part bolted flat on a face can only turn in the plane of that face. '
         'The ACT-103 mounting flange lies on the ACT-101 end face, so slots turn it about the belt direction (twist plane), not about the bend line; the motor turns in its seat only about its own shaft. It would also change ACT-103.',
         'R2 option (b): physics of a bolted face')
    flag('mis_opt_slot_check', False, 'option (b) slotted ACT-103 or motor mounting corrects the steering plane (FAIL: wrong plane, and ACT-103 is frozen)')
    put('mis_opt_wedge_dt', sp * math.tan(math.radians(s_drv)), 'mm', 'option (c) wedge shim between ACT-103 and ACT-101: thickness difference across the M5 rows (y2 - L1) for mis_drv_static_worst', 2)
    put('mis_opt_wedge_step', sp * math.tan(math.radians(a_p)), 'mm', 'option (c): shim step that one acceptance needs, (y2 - L1) x tan(mis_p_accept)', 4)
    put('mis_opt_peel_step', d_(math.atan(i['peel_lam'] / sp)), 'deg', 'option (c): angle step of one peel-shim lamination under one M5 row, atan(peel_lam / (y2 - L1))', 3)
    flag('mis_opt_wedge_check', d_(math.atan(i['peel_lam'] / sp)) <= a_p, 'option (c) shim steps fine enough for mis_p_accept (FAIL; shims also add faying faces to the bracket friction joint, the ECO-001 root cause)')
    on_ = e_tot + a_p + u_p + s_idl
    put('mis_opt_noidl_total', on_, 'deg', 'option: drop the ACT-102 adjustment (idler as toleranced): return span = mis_elastic + mis_p_accept + mis_u_pulley + mis_idl_static_worst', 3)
    flag('mis_opt_noidl_check', on_ <= i['tilt_guide'], 'idler without adjustment meets R11 in the return span (FAIL: keep the ACT-102 adjustment)')
    # twist plane (rotation about the belt direction): does not change the entry angle; belt twist over the shortest span
    tw_skew = d_(math.atan(2 * i['tol_across_bend'] / i['b'])); tw_clr = d_((i['hole_M5'] - i['d_M5']) / sp)
    tws = tw_skew + tw_clr + s_mot + s_pul / 2
    put('mis_twist_worst', tws, 'deg', 'twist plane, drive pulley, as toleranced (upper bound): bend-line skew atan(2 tol_across_bend / b) + M5 hole clearance turn (hole_M5 - d_M5) / (y2 - L1) + mis_s_motor + one pulley', 2)
    put('mis_twist_strain', (i['belt_width'] / 2) ** 2 * (math.radians(tws) / i['span_min']) ** 2 / 2 * 1e6, 'microstrain', 'belt edge strain from that twist over span_min: (belt_width / 2)^2 x (twist / span_min)^2 / 2 (second order; no steering)', 1, speak=False)
    text('mis_twist_note', f"Twist about the belt direction (the second angular plane) turns the pulley axis up or down, but the belt still runs in the pulley plane, so the entry angle does not change. "
         f"Worst case as toleranced the drive pulley twists about {fm(math.ceil(tws * 10 - 1e-9) / 10)} deg; over the shortest span that adds only a few millionths of edge strain to the belt. It is not budgeted; the tracking run at both stroke ends confirms it.",
         'R2 twist plane; from mis_twist_worst, mis_twist_strain')
    # requirement and process texts (drawings, EBOM, assembly, inspection)
    text('act101_adjust_req', f"ACT-101 drive end block (Rev A; ECO-001 Rev B adds only the M4 holes): turns about the dowel nearer the bracket (COTS-214, fit as now); the second dowel hole becomes a slot on the line to the pivot, engaged by the ACT-111 eccentric pin in ACT-108; "
         f"yaw range at least ±{fm(i['adj_range_drive'])} deg (eccentricity {fm(i['ecc_e'])} mm at {fm(i['act101_dowel_span'])} mm gives ±{fm(math.floor(rng_d * 100 + 1e-9) / 100)} deg). "
         "The four M5 clamp holes in ACT-108 under ACT-101 are opened so the block can turn (size at the ACT-101/ACT-108 detail), with large washers. After setting: torque the four M5, lock ACT-111 with its M4 nut, measure again. "
         "This turns the end face, ACT-103, the motor and the drive pulley together, inside the machined chain; ACT-103 is unchanged.",
         'design requirement for the ACT-101 Rev A and ACT-108 drawings; from adj_range_drive, ecc_e, act101_dowel_span')
    text('act111_desc', f"ACT-111 Eccentric adjusting pin: steel; plain shank turning in the ACT-108 bore, eccentric head (offset {fm(i['ecc_e'])} mm) in the ACT-101 slot, hex socket 2 mm and M4 thread at the lower end, locked by an M4 nut (COTS-220) under ACT-108 (illustrative; sizes at the detail)",
         'EBOM text for the new part; from ecc_e')
    # ---------- rolling direction (panel session 5, item 2): second and third sentence of drawing note 2 ----------
    text('drw_grain_note', "BEND LINE ACROSS (AT 90° TO) THE ROLLING DIRECTION OF THE SHEET. ANOTHER DIRECTION NEEDS WRITTEN AGREEMENT.",
         'ACT-103 drawing note 2 (Rev A, Rev B), added after the drw_bend_note sentence; the arrow on the flat pattern is at 90 deg to the bend line (panel session 5)')
    # ---------- tool count (panel session 5, item 3): drivers for the screws and nuts, one per EBOM drive ----------
    # COTS-223 stays an ISO 4026 M3 set screw (1.5 mm key): the panel's change to a cap screw is subject to head clearance at the
    # ACT-102 detail, which is not drawn and has no Facts value. Recorded as a deviation from the panel decision (rule book section I, item 4),
    # open until the ACT-102 detail: the set screw is kept until head clearance is shown (every count is one higher).
    hex_rel = [1.5, 2, 2.5, 4]     # mm across flats: M3 set screw COTS-223; ACT-111 socket; M3 cap screws; M5 cap screws
    hex_eco = [3]                  # mm: M4 cap screws COTS-219 and COTS-221, added by ECO-001
    spanner_M4, lobe_cover = 7, 10                   # mm spanner across flats for the M4 nut COTS-220; six-lobe size for the thread-forming cover screws COTS-213 (typical, to confirm with the screw maker)
    other_rel = [f'{spanner_M4} mm spanner', f'six-lobe {lobe_cover}']
    put('tool_count_release', len(hex_rel) + len(other_rel), '', 'drivers for the screws and nuts at first release: one per different drive in the EBOM (hex keys 1.5, 2, 2.5 and 4 mm, 7 mm spanner, six-lobe 10); COTS-223 kept as a set screw until head clearance is shown at the ACT-102 detail', 0)
    put('tool_count_eco', len(hex_rel) + len(other_rel) + len(hex_eco), '', 'drivers for the screws and nuts after ECO-001: tool_count_release + the 3 mm hex key for the M4 screws', 0)
    text('tool_list', 'hex keys ' + ', '.join(fm(h) for h in hex_rel[:-1]) + f' and {fm(hex_rel[-1])} mm, ' + ', '.join(other_rel)
         + f'; ECO-001 adds the {fm(hex_eco[0])} mm hex key. Not counted: retaining-ring pliers (COTS-218), pulley grub-screw key (pulley maker)',
         'tool list behind tool_count_release and tool_count_eco (six-lobe size is typical, to confirm with the screw maker); from the EBOM drives')
    # ---------- Ep 21 S09 belt change (Rev B, tension block): drivers from the same EBOM drives, one entry per screw or nut the task list touches ----------
    def mm_adj(x):      # spoken adjective: 2.5 -> 'two-and-a-half-millimetre'
        w_ = spoken(int(x)) + ('-and-a-half' if abs(x - int(x) - 0.5) < 1e-9 else '') if abs(x - round(x * 2) / 2) < 1e-9 else spoken(x)
        return w_ + '-millimetre'
    bc_uses = [  # (printed driver, spoken driver, printed use, spoken use, task-list step from the mttr names)
        (other_rel[1], 'six-lobe driver', 'cover screws', 'cover', names[1]),
        (other_rel[0], f'{mm_adj(spanner_M4)} spanner', 'lock nut', 'lock nut', names[2]),
        (f'{fm(hex_eco[0])} mm hex key', f'{mm_adj(hex_eco[0])} key', 'tension screw', 'tension screw', names[2]),
        (f'{fm(hex_rel[2])} mm hex key', f'{mm_adj(hex_rel[2])} key', 'motor screws', 'motor', names[3]),
        (f'{fm(hex_rel[2])} mm hex key', f'{mm_adj(hex_rel[2])} key', 'clamp screws', 'clamp screws', names[4])]
    bc_drv = []
    for d_, ds_, u_, us_, st_ in bc_uses:
        if d_ not in [e[0] for e in bc_drv]: bc_drv.append([d_, ds_, [], []])
        e_ = [e for e in bc_drv if e[0] == d_][0]; e_[2].append(u_); e_[3].append(us_)
    def join_uses(us):
        if len(us) > 1 and all(u.endswith(' screws') for u in us): return ' and '.join(u[:-7] for u in us) + ' screws'
        return ' and '.join(us)
    put('belt_change_driver_count', len(bc_drv), '', 'drivers for the belt change (Ep 21 S09 task list): one per different drive among the screws and nuts the steps touch; from hex_rel, hex_eco, spanner and six-lobe sizes of the tool count', 0)
    text('belt_change_drivers', ', '.join(f'{d_} ({join_uses(u_)})' for d_, _, u_, _ in bc_drv),
         'belt change drivers, one per different drive: cover screws COTS-213 (task step 2), lock nut COTS-220 and tension screw COTS-219 (step 3), motor screws (step 4), clamp screws (step 5); '
         'from the tool-count drives (hex_rel, hex_eco, spanner, six-lobe); the bracket screws are never touched; six-lobe size typical, to confirm with the screw maker')
    sp_ = [f'a {ds_} for the {join_uses(us_)}' for _, ds_, _, us_ in bc_drv]
    v['belt_change_drivers']['spoken'] = ', '.join(sp_[:-1]) + ', and ' + sp_[-1]
    # ---------- Ep 21 S07 access: M5 head (motor side of the mounting flange) to the motor body, along the screw axis ----------
    head_top = i['t_steel'] + i['washer_M5'] + i['k_M5']
    put('access_head_top', head_top, 'mm', 't_steel + washer_M5 + k_M5: top of the first-row M5 head from datum A (outside face of the mounting flange)', 1)
    put('gap_head_motor_near', i['a'] - i['T'] / 2 - i['motor_body'] / 2 - head_top, 'mm',
        'a - T/2 - motor_body/2 - access_head_top: M5 head to motor body, motor at the near end of travel (Rev A and Rev B; slots grow away from the bend)', 1)
    put('gap_head_motor_far_revB', i['a'] - i['T'] / 2 + i['T_revB'] - i['motor_body'] / 2 - head_top, 'mm',
        'a - T/2 + T_revB - motor_body/2 - access_head_top: the same at the Rev B far end of travel (largest gap)', 1)
    text('act107_align_req', f"ACT-107 belt clamp: one machined side face parallel to the belt-tooth slot within {fm(i['clamp_face_par'])} mm over {fm(i['clamp_sweep'])} mm (same set-up); "
         f"the screw holes allow at least ±{fm(i['clamp_adj_range'])} deg of yaw on ACT-104; set to the rail at assembly within {fm(i['r2_accept_mm'])} mm over {fm(i['clamp_sweep'])} mm. The clamp defines the belt line of its span.",
         'design requirement for the ACT-107 drawing; from clamp_face_par, clamp_sweep, clamp_adj_range, r2_accept_mm')
    text('cots_pulley_req', f"COTS-203/204 timing pulleys: flanged both sides; outer flange face turned with the bore and plain around the reading radius of 8 mm (hub on the inner side), flat within {fm(i['flange_flat'])} mm over the reading zone (SAMPLE spec; receiving check on a surface plate with the 0.001 mm indicator).",
         'EBOM text for the drive and idler pulleys; from flange_flat')
    put('mis_flat_accept_mm', i['flange_flat'], 'mm', 'receiving check: pulley outer flange face flatness over the reading zone', 3)
    put('mis_rep_spread_mm', 2 * i['dti_res_r2'], 'mm', 'repeatability check: three repeats of each mean must agree within 2 x dti_res_r2', 3)
    A_ = fm(i['r2_accept_mm']); SW = fm(i['set_sweep']); CS = fm(i['clamp_sweep'])
    text('drw_note_alignment', f"THE MOTOR-SEAT ANGLE (BEND 90° ±{fm(i['tol_bend_angle'])}°, ⊥ {fm(i['perp_motor_seat'])} | A) IS NOT THE BELT-ALIGNMENT CONTROL. AT ASSEMBLY EACH PULLEY IS SET PARALLEL TO THE RAIL: "
         "THE DRIVE PULLEY BY TURNING THE ACT-101 END BLOCK ON ITS PIVOT DOWEL (ECCENTRIC PIN ACT-111), THE IDLER BY THE ACT-102 ADJUSTMENT (ASSEMBLY NOTE: BELT ALIGNMENT).",
         'ACT-103 drawing note (Rev A, Rev B), R2 wording; from tol_bend_angle, perp_motor_seat')
    text('act102_adjust_req', f"ACT-102 idler end block: idler shaft seat adjustable in angle about the vertical axis (the steering plane), range at least ±{fm(i['adj_range'])} deg; set with one M3 push screw and locked with two M3 screws; "
         "the idler is set to the RAIL (not to the drive pulley), then the drive-minus-idler difference is checked; the locked seat carries the belt load without slip and is taken as rigid in the budget (non-conservative; the R11 test measures the total).",
         'design requirement for the ACT-102 drawing, R2 wording; from adj_range')
    text('asm_alignment_step', f"BELT ALIGNMENT (PDS R11; open-ended belt: every part the belt touches is set to the rail). "
         f"0. On receipt: each pulley's outer flange face flat within {fm(i['flange_flat'])} mm over the reading zone (pulley on a surface plate, indicator on a stand), or reject. "
         "1. Fit the motor, both flanged pulleys and the belt; tension the belt to the installation value; move a pulley along its shaft if needed so the belt runs centred between the flanges at both stroke ends. "
         f"2. Clamps: digital indicator ({fm(i['dti_res_r2'])} mm) on a magnetic base on ACT-108, stylus on the reference side face of a belt clamp (ACT-107); move the carriage {CS} mm; the change must be {A_} mm or less. If not, loosen the clamp screws, turn the clamp, tighten, measure again. Both clamps. "
         f"3. Drive pulley: indicator on the carriage, stylus on the outer flange face on the line through the shaft centre parallel to the rail; read at the two points 8 mm either side of the centre ({SW} mm of carriage travel; the belt turns the pulley as the carriage moves). Then move the carriage on by half a pulley turn ({fm(i['pulley_teeth'] * i['belt_pitch'] / 2)} mm = {fm(i['pulley_teeth'] / 2)} teeth), move the indicator base back by the same distance on the carriage and repeat; the mean of the two changes is the pulley's angle to the rail (face wobble cancels) and must be {A_} mm or less. "
         "If not, in this order (set, snug, check, torque, re-check): set - the four ACT-101 M5 screws just loose enough to slide, turn the ACT-111 eccentric until the reading is in; "
         "snug - the four M5 screws lightly, cross pattern; check - read again, correct with ACT-111 if needed; "
         "torque - the four M5 screws, cross pattern, and lock the ACT-111 M4 nut; re-check - measure again; outside, back to set. "
         f"4. Idler pulley: the same; adjust with the ACT-102 push screw (loosen and re-tighten its two locking screws). "
         f"5. Drive mean minus idler mean, read with the same sign convention: {A_} mm or less. "
         f"6. Repeat steps 3-5 three times; each mean must repeat within {fm(2 * i['dti_res_r2'])} mm. "
         "7. Run 10 full strokes: the belt rides no flange and stays centred at both stroke ends. Record every mean on the assembly record.",
         'assembly note (assembly record and Ep 20 inspection plan), R2 method; from dti_res_r2, set_sweep, clamp_sweep, r2_accept_mm, flange_flat')
    text('insp_alignment_line', f"Belt alignment record: clamp 1, clamp 2 ({CS} mm sweep), drive pulley, idler pulley ({SW} mm, mean of two half-turn positions): each change {A_} mm or less; drive minus idler {A_} mm or less; "
         f"3 repeats within {fm(2 * i['dti_res_r2'])} mm; pulley flange flatness {fm(i['flange_flat'])} mm (receipt); tracking run 10 strokes. Gauge: digital indicator {fm(i['dti_res_r2'])} mm on a magnetic base.",
         'Inspection_Card / Ep 20 record line; from the R2 acceptance keys')
    text('pds_r11_text', f"Belt alignment: belt-entry angle at each pulley in every span (drive and idler to their carriage clamps, and the return span between the pulleys), in operation at the working load, at most {fm(i['tilt_guide'])} deg (synchronous-belt guidance; the belt maker wins). "
         f"Shares: bracket + motor shaft (elastic, drive pulley only) by design, bracket tilt at the design load at most {fm(i['tilt_limit'])} deg; every static error set out at assembly by setting each pulley and each belt clamp to the rail within {A_} mm over its sweep. Verified by the tilt test (total).",
         'PDS R11 wording, R2 (replaces "between the drive and idler pulleys"); from tilt_guide, tilt_limit, r2_accept_mm')
    text('mis_verdict', f"R11, open-ended belt: the belt-entry angle at each pulley, in every span, must stay within {fm(i['tilt_guide'])} deg. Each clamp rides the rail, so each pulley and each clamp is set to the rail, not only to the other pulley. "
         f"Elastic {fm(round(e_tot, 3))} deg (bracket {fm(round(e_br, 3))} + motor shaft {fm(round(e_sh, 3))}, working load, drive pulley only). "
         f"As toleranced the drive pulley is up to {fm(math.ceil(s_drv * 100 - 1e-9) / 100)} deg off the rail (mostly the bend), so the drive side needs its own adjustment: ACT-101 turns on one dowel, set by the ACT-111 eccentric (±{fm(math.floor(rng_d * 100 + 1e-9) / 100)} deg); "
         f"slots in ACT-103 turn it in the wrong plane, and wedge shims cannot step finely enough. The idler keeps its ACT-102 adjustment (without it the return span reaches {fm(math.ceil(on_ * 1000 - 1e-9) / 1000)} deg). "
         f"Each pulley and clamp is set within {A_} mm over its sweep with a {fm(i['dti_res_r2'])} mm indicator; with flange flatness, reading and travel errors: drive pulley {fm(math.ceil(dt_ * 1000 - 1e-9) / 1000)} deg, margin {fm(math.floor((i['tilt_guide'] - dt_) * 1000 + 1e-9) / 1000)} deg ({fm(math.floor((i['tilt_guide'] - dt_) / i['tilt_guide'] * 100 + 1e-9))} %); "
         f"idler pulley {fm(math.ceil(it_ * 1000 - 1e-9) / 1000)} deg, margin {fm(math.floor((i['tilt_guide'] - it_) * 1000 + 1e-9) / 1000)} deg ({fm(math.floor((i['tilt_guide'] - it_) / i['tilt_guide'] * 100 + 1e-9))} %). "
         "Simplified model, steady running; R11 stays open until the tilt test, which measures the total.",
         'alignment_study.md R2; from mis_* keys')
    # ---------- scorecard one-liners ----------
    g = lambda k: v[k]['value']
    put('tilt_sys_margin_steel_pct', rv_('tilt_sys_margin_steel') / i['tilt_limit'] * 100, '%', 'tilt_sys_margin_steel as % of tilt_limit', 0)
    text('scorecard_strength', f"Strength (PDS R4): released {fm(i['t_steel'])} mm steel, smallest FOS {fm(g('FOS_min_steel'))} on the specified minimum yield (gate {fm(i['FOS_gate'])}): PASS; crash/stall smallest FOS {fm(g('FOS_stall_min'))} (gate {fm(i['FOS_stall_gate'])}): PASS.",
         'from FOS_min_steel, FOS_stall_min')
    text('scorecard_stiffness', f"Stiffness (PDS R5, R11): shaft tilt {fm(g('tilt_steel'))} / {fm(g('tilt_steel_revB'))} deg at Rev A / Rev B (limit {fm(i['tilt_limit'])}); with the motor shaft at the working load {fm(g('tilt_sys_margin_steel'))} deg ({fm(g('tilt_sys_margin_steel_pct'))} %) is left for every static misalignment, including the as-made bend angle, which is set out at assembly by setting each pulley to the rail (drive pulley {fm(g('mis_drv_total'))} deg in its worst span after setting); pulley movement {fm(g('move_steel_revB'))} mm (limit {fm(i['move_limit'])}): PASS on a simplified model; to be confirmed by test (open action): R11 open until the tilt test.",
         'from tilt_steel, tilt_steel_revB, tilt_sys_margin_steel, move_steel_revB')
    study(i, v, put, text, flag, F, sl)
    return v


def study(i, v, put, text, flag, F, sl):
    """course team study B (thickness before freeze). Keys study_*; the released design keys are not changed."""
    fm = lambda x: f'{x:g}'
    work = i['F_max'] / F; lim = i['tilt_limit']; Ss = i['Sy_steel_min']; shaft = math.degrees(sl)

    def near(ii, rev):
        return ii['a'] + ii['T'] / 2 - ii['m3_pat'] / 2 if rev == 'A' else ii['a'] - ii['T'] / 2 + ii['T_revB'] - ii['m3_pat'] / 2

    def case(tag, label, tt, E=None, ii=None, lipped=False, screws_ok=True):
        ii = ii or i; E = E or ii['E_steel']; R = ii['R_over_t'] * tt
        tA = math.degrees(stiffness(ii, tt, E, near(ii, 'A'), F, lipped)[1])
        tB = math.degrees(stiffness(ii, tt, E, near(ii, 'B'), F, lipped, travel=ii['T_revB'])[1])
        put(f'study_{tag}_tilt_A', tA, 'deg', f'{label}: bracket tilt, design load, Rev A; ' + MODEL, 3)
        put(f'study_{tag}_tilt_B', tB, 'deg', f'{label}: bracket tilt, design load, Rev B', 3)
        put(f'study_{tag}_margin', lim - max(tA, tB), 'deg', f'{label}: tilt_limit - worst bracket tilt (R11, bracket only)', 3)
        sA, sB = (tA + shaft) * work, (tB + shaft) * work
        put(f'study_{tag}_sys_A', sA, 'deg', f'{label}: (tilt + tilt_shaft_est) x F_max/F_design, working load, Rev A', 3)
        put(f'study_{tag}_sys_B', sB, 'deg', f'{label}: same, Rev B', 3)
        sm = lim - max(sA, sB)
        put(f'study_{tag}_sys_margin', sm, 'deg', f'{label}: tilt_limit - worst system tilt: left for assembly misalignment', 3)
        put(f'study_{tag}_sys_margin_pct', sm / lim * 100, '%', f'{label}: system margin as % of tilt_limit', 0)
        lo, hi = study_score_band = i['study_score_bands']
        score = 1 if max(tA, tB) > lim else 2 if sm < 0 else 3 if sm / lim * 100 < lo else 4 if sm / lim * 100 < hi else 5
        put(f'study_{tag}_stiff_score', score, '-', f'{label}: Ep 07 stiffness score from the rule: R11 fail 1; system over the limit 2; system margin < {fm(lo)} % 3; < {fm(hi)} % 4; else 5', 0)
        return score

    def plate(tag, label, tt, ii=None, travel_note=True):
        ii = ii or i; R = ii['R_over_t'] * tt; c = tt + R
        cA, _ = worst_cut(ii, ii['T']); cB, _ = worst_cut(ii, ii['T_revB'])
        fs = [strength(ii, tt, Ss, F, cA), strength(ii, tt, Ss, F, cB)]
        put(f'study_{tag}_FOS_min', min(min(d.values()) for d in fs), '-', f'{label}: smallest FOS on Sy_steel_min (bend, lumped net, real lines Rev A/B, M5 hole section)', 2)
        e5 = ii['L_M5'] - tt - ii['washer_M5']; e3 = ii['L_M3'] - tt - ii['washer_M3']; e3n = ii['L_M3_next'] - tt - ii['washer_M3']
        put(f'study_{tag}_engD_M5', e5 / 5, 'D', f'{label}: M5 x 12 engagement / 5 (rule >= 1.5D)', 2)
        put(f'study_{tag}_runout_M5', ii['depth_M5'] - e5, 'mm', f'{label}: depth_M5 - engagement (rule >= 1)', 2)
        put(f'study_{tag}_engD_M3', e3 / 3, 'D', f'{label}: M3 x 6 engagement / 3 (rule >= 1D)', 2)
        put(f'study_{tag}_runout_M3', ii['depth_M3'] - e3, 'mm', f'{label}: depth_M3 - engagement, M3 x 6 (rule >= 1)', 2)
        put(f'study_{tag}_runout_M3x8', ii['depth_M3'] - e3n, 'mm', f'{label}: depth_M3 - engagement with the next length M3 x 8 (negative = bottoms)', 2)
        ok = e5 / 5 >= 1.5 and ii['depth_M5'] - e5 >= 1 - 1e-9 and ((e3 / 3 >= 1 - 1e-9 and ii['depth_M3'] - e3 >= 1 - 1e-9) or (e3n / 3 >= 1 and ii['depth_M3'] - e3n >= 1))
        flag(f'study_{tag}_screw_check', ok, f'{label}: study B quick screen at nominal (M5 x 12 and an ISO 4762 M3 length 6 or 8 meet 1D / 1.5D and run-out); superseded for release by the corner check (M3_check, ga*_screw_check)')
        req = c + 2.5 * tt + R
        edges = min(ii['a'] - ii['T'] / 2 - ii['m3_pat'] / 2 - ii['m3_slot'] / 2, ii['a'] - ii['T'] / 2 - ii['pilot_end_ext'] - ii['pilot_slot'] / 2, ii['L1'] - ii['hole_M5'] / 2)
        put(f'study_{tag}_hb_required', req, 'mm', f'{label}: (t + R) + 2.5t + R from the outside face of the other flange', 2)
        flag(f'study_{tag}_hb_check', edges >= req, f'{label}: every hole and slot edge >= hb_required')
        return ok

    # ---- option 1: 2.0 mm steel (the thinner option; the release is 2.5 mm, course decision) ----
    s1 = case('o1', 'option 1, 2.0 mm steel (thinner option; superseded, not released)', i['t2'])
    plate('o1', 'option 1, 2.0 mm steel (thinner option; superseded, not released)', i['t2'])
    # ---- option 2: 2.5 mm steel, same geometry ----
    ts = i['t_steel']; R = i['R_over_t'] * ts
    s2 = case('o2', 'option 2, 2.5 mm steel', ts)
    plate('o2', 'option 2, 2.5 mm steel', ts)
    BA = math.pi / 2 * (R + i['K_bend'] * ts); fl = (i['L_mount'] - ts - R) + (i['L_motor'] - ts - R) + BA
    put('study_o2_BA', BA, 'mm', 'option 2: (pi/2)(R + K t), R = t', 2)
    put('study_o2_flat', fl, 'mm', 'option 2: (L_mount - t - R) + (L_motor - t - R) + BA', 1)
    put('study_o2_bend_line', (i['L_mount'] - ts - R) + BA / 2, 'mm', 'option 2: flat length to the bend centre line from the mounting-flange edge', 1)
    m20 = RAW['mass_al_g'] * i['rho_steel'] / i['rho_al']
    put('study_o2_mass_g', RAW['mass_steel_g'], 'g', 'option 2 (now released): = mass_steel_g', 0)
    put('study_o2_mass_pct', (RAW['mass_steel_g'] / m20 - 1) * 100, '%', 'option 2: extra mass vs the same blank in 2.0 mm steel', 0)
    lo, hi = i['a'] - i['T'] / 2, i['a'] - i['T'] / 2 + i['T_revB']; h = i['m3_pat'] / 2; webs = []
    wd = {}
    for nm, dx, dz in (('none', 0, 0), ('along', 1, 0), ('back', -1, 0), ('side', 0, 1)):
        dx *= i['pilot_slot_move']; dz *= i['pilot_slot_move']
        wd[nm] = min(seg_dist((lo - i['pilot_end_ext'] + dx, dz), (hi + i['pilot_end_ext'] + dx, dz), qa, qb) - i['pilot_slot'] / 2 - i['m3_slot'] / 2
                     for zs in (h, -h) for qa, qb in (((lo - h, zs), (hi - h, zs)), ((lo + h, zs), (hi + h, zs))))
    put('study_web_nominal', wd['none'], 'mm', 'smallest web pilot slot to M3 slot, no move (Rev B; same for every thickness)', 2)
    put('study_web_move_along', min(wd['along'], wd['back']), 'mm', 'smallest web after a 1 mm pilot move along the slot (either way)', 2)
    put('study_web_move_side', wd['side'], 'mm', 'smallest web after a 1 mm pilot move sideways (= web_after_move)', 2)
    flag('study_o2_web_check', min(wd.values()) >= ts, 'option 2: web after the Ep 22 1 mm pilot move >= t ("web >= t" rule, 2.5 mm)')
    flag('study_o2_web_check_along', min(wd['none'], wd['along'], wd['back']) >= ts, 'option 2: web >= t if the move is along the slot only')
    put('study_o2_mass_ratio_al', RAW['mass_steel_g'] / RAW['mass_al_g'], 'x', 'option 2 mass / mass_al_g (2.0 mm aluminium blank) = mass_ratio_rel', 2)
    # gauges a US supplier could offer instead of 2.5 mm
    for g in ('ga12', 'ga13'):
        tg = i[f'{g}_steel_in'] * 25.4
        put(f'study_{g}_mm', tg, 'mm', f'{g}_steel_in x 25.4 (US manufacturers standard gauge, uncoated steel; typical nominal)', 3)
        case(g, f'{g.upper()[:2]} {g[2:]} gauge steel', tg)
        plate(g, f'{g[2:]} GA steel', tg)
    # ---- option 3: 2.0 mm steel, motor centre 5 mm nearer the bend ----
    i3 = dict(i, a=i['study_a_alt'])
    s3 = case('o3', 'option 3, 2.0 mm steel, a moved to study_a_alt', i['t2'], ii=i3)
    plate('o3', 'option 3, 2.0 mm steel, a moved', i['t2'], ii=i3)
    # ---- other candidates for the Ep 07 stiffness score (each on its best route, real margin) ----
    sl_ = case('lips', 'route (c) 2.0 mm 5052 + lips', i['t2'], E=i['E'], lipped=True)
    sss = case('ss', '304 stainless 2.0 mm flat', i['t2'], E=i['study_E_ss'])
    s3al = case('thick', 'route (a) 3.0 mm 5052', i['t_alt2'], E=i['E'])
    # ---- Ep 07 matrix re-run with stiffness scores from the rule ----
    w = i['mx_weights']; S0 = i['mx_scores']

    def evaluate(tag, S, label):
        tot = {m: sum(w[c] * S[m][c] for c in w) for m in S}
        worst = (9.0, '')
        for a_ in w:
            for b_ in w:
                if a_ == b_ or w[a_] < 0.10 - 1e-9: continue
                alt = dict(w); alt[a_] -= 0.10; alt[b_] += 0.10
                ts_ = {m: sum(alt[c] * S[m][c] for c in alt) for m in S}
                lead = max(ts_, key=ts_.get); rest = sorted(ts_.values())[-2]
                gap = ts_['steel'] - max(ts_[m] for m in S if m != 'steel')
                if gap < worst[0]: worst = (gap, f'{a_} -> {b_}')
        for m in S:
            put(f'study_mx{tag}_total_{m}', tot[m], '-', f'{label}: sum(weight x score), {m}', 2)
        put(f'study_mx{tag}_lead', tot['steel'] - max(tot[m] for m in S if m != 'steel'), '-', f'{label}: steel total - best other total', 2)
        put(f'study_mx{tag}_sens_gap', worst[0], '-', f'{label}: smallest steel lead after any 10 % weight shift (worst: {worst[1]}); negative = leader changes', 2)
    S1 = {m: dict(S0[m]) for m in S0}
    S1['steel']['stiffness'] = s1; S1['al']['stiffness'] = sl_; S1['ss']['stiffness'] = sss
    evaluate('1', S1, 'matrix with real-margin stiffness scores, steel 2.0 mm')
    S2 = {m: dict(S1[m]) for m in S1}; S2['steel']['stiffness'] = s2
    evaluate('2', S2, 'matrix with real-margin stiffness scores, steel 2.5 mm (cost, process, heat scores unchanged)')


def self_check(v, shelf=None):
    bad = []
    g = lambda k: v[k]['value']
    t = 2.0; M = g('M'); tr = g('t_steel')
    if abs(g('F_design') - 30.0) > 1e-9: bad.append('F_design')
    if abs(g('sigma_net_t2') - 6 * M / (20.2 * t * t)) > 0.1: bad.append('sigma_net_t2 second way')
    # material keys agree with the shelf data set
    want = dict(Sy=193, E=70300, rho_al=2.68, Sy_steel=210, E_steel=200000, rho_steel=7.85, Sy_steel_min=205)
    for k, x in want.items():
        if g(k) != x: bad.append(f'{k} must equal the shelf value {x}')
    if shelf:
        for k, sk in (('Sy', 'shelf_al_Sy'), ('E', 'shelf_al_E'), ('rho_al', 'shelf_al_rho'), ('Sy_steel', 'shelf_steel_Sy'),
                      ('E_steel', 'shelf_steel_E'), ('rho_steel', 'shelf_steel_rho')):
            if sk not in shelf or shelf[sk]['value'] != g(k): bad.append(f'{k} differs from {sk} in the shelf JSON')
        if 'V1_Ep07_mass_ratio' in shelf and abs(shelf['V1_Ep07_mass_ratio']['value'] - g('mass_ratio')) > 0.005: bad.append('mass_ratio vs shelf')
    # Ep 05 story (aluminium baseline)
    if not (g('bend_check_t1') == g('bend_check_t2') == 'PASS'): bad.append('story: bend check passes both')
    if g('net_check_t1') != 'FAIL' or g('net_check_t2') != 'PASS': bad.append('story: lumped net t1 FAIL / t2 PASS')
    if not (g('netreal_check_t1') == 'FAIL' and g('netreal_check_t2') == 'PASS'): bad.append('story: real worst line fails 1.5 mm, passes 2.0 mm')
    if not (24.3 <= g('b_net_real') <= 24.7): bad.append('b_net_real about 24.5')
    # Ep 06 story: flat aluminium movement passes, tilt fails
    if not (g('stiff_check_t1') == 'FAIL' and g('stiff_check_t2') == 'PASS'): bad.append('story (A2 model): movement fails 1.5 mm, passes 2.0 mm (aluminium)')
    # gates on specified minimum yield; Ep 05 verdicts unchanged
    if abs(g('Sy_min') - 23.0 * 6.894757) > 0.06 or g('Sy_min') >= g('Sy'): bad.append('Sy_min = 23 ksi (ASTM B209), below typical')
    if abs(g('FOS_bend_t2') - g('Sy_min') / g('sigma_bend_t2')) > 0.02: bad.append('FOS_bend_t2 second way (Sy_min)')
    if g('FOS_min_steel_typ') <= g('FOS_min_steel'): bad.append('typical-yield FOS must be above the minimum-yield FOS')
    # slot zone makes every tilt bigger than the gross-section model
    if not (g('tilt_steel') > g('tilt_gross_steel') and g('tilt_steel_revB') > g('tilt_gross_steel_revB')): bad.append('slot zone must add tilt')
    if abs(g('slot_zone_start') - g('hb_slot_edge')) > 0.01: bad.append('slot zone starts at the near M3 slot edge')
    # course decision stack, course decision lever arms, /#23 keys
    if g('stack_check') != 'PASS' or g('stack_check_square') != 'FAIL': bad.append('Ep 13 stack: diameter zones PASS, square reading FAIL')
    if abs(g('stack_used') - (g('tol_laser_pos') + g('tol_tapped_pos'))) > 1e-9 or abs(g('tol_tapped') * 2 - g('tol_tapped_pos')) > 1e-9: bad.append('stack keys')
    if not (g('M_mid') < g('M') and g('M_heel_exact') < g('M_heel')): bad.append('M and M_heel must be conservative')
    if g('p') != g('shaft_load_distance') or g('pulley_distance') != g('p'): bad.append('p / shaft_load_distance / pulley_distance same reference')
    if g('R_rel') != g('R_bend') or abs(g('hb_required') - g('c_rel') - g('hb_from_bend')) > 1e-9: bad.append('R_rel / hb keys')
    if abs(g('slot_near_end') - 20.5) > 1e-9 or abs(g('slip_res') - 4 * g('mu') * g('preload_M3')) > 1: bad.append('slot_near_end / slip_res')
    for k in ('note_heel_pivot', 'note_motor_weight', 'note_nominal_stress', 'note_K_dry', 'torque_note', 'note_M3_motor_limit',
              'eco001_root_cause', 'retrofit_jig_pn', 'laser_capability', 'tapped_capability'):
        if k not in v: bad.append(f'new key missing: {k}')
    if g('torque_note') != 'TIGHTEN M5 TO 4 N\u00b7m \u00b110% (ILLUSTRATIVE)': bad.append('torque_note text')
    if 'ISO 2081' in g('finish') or 'ISO 19598' not in g('finish'): bad.append('finish standard')
    if not (g('tilt_check_t1') == g('tilt_check_t2') == 'FAIL'): bad.append('story: flat aluminium tilt fails both')
    if g('tilt_check_t25') != 'FAIL' or g('tilt_check_t3') != 'PASS': bad.append('story: thickness alone needs 3.0 mm')
    # three routes, owner numbers (about 0.16 / 0.18 / 0.22 deg)
    for k, x in (('route_thick_tilt', 0.17), ('route_steel_tilt', 0.10), ('route_lips_tilt', 0.22)):
        if abs(g(k) - x) > 0.006: bad.append(f'{k} should be about {x} (slot-zone model)')
    for k in ('route_thick_check', 'route_steel_check', 'route_lips_check'):
        if g(k) != 'PASS': bad.append(f'{k} must PASS')
    if g('route_thick_M3_check') != 'FAIL': bad.append('story: 3.0 mm breaks the M3 motor screw')
    if g('route_steel_check_t1') != 'FAIL': bad.append('story: 1.5 mm steel fails tilt (steel stays 2.0 mm)')
    if not (g('route_steel_sys_margin') > g('route_thick_sys_margin') - 0.03 and g('route_steel_sys_margin') > 2 * g('route_lips_sys_margin')):
        bad.append('story: steel keeps a clear system margin; lips margin is thin')
    if not (0 <= g('route_lips_sys_margin') < 0.01): bad.append('story: lips system margin is thin but not negative')
    if g('route_lips_I_ratio') < 30: bad.append('lips raise I at least 30 times')
    if not (30 <= g('route_lips_I_ratio_same_web') < g('route_lips_I_ratio')): bad.append('D156: same-web lip ratio between 30 and the 50 mm ratio')
    ch = channel(58.0, 12.0, 2.0)
    if abs(ch['I'] - ch['I_check']) > 1e-6: bad.append('route_lips_I second way')
    # final design
    if g('route_steel_tilt') != g('tilt_steel') or g('route_steel_move') != g('move_steel'): bad.append('route_steel and final keys differ')
    for k in ('strength_check_steel', 'tilt_check_steel', 'stiff_check_steel', 'stall_check', 'M5_check', 'M3_check', 'shaft_check',
              'hb_check', 'edge_check_revB'):
        if g(k) != 'PASS': bad.append(f'final: {k}')
    if g('FOS_min_steel') < g('FOS_net_t2'): bad.append('steel must be at least as strong as the 2.0 mm aluminium screen')
    if g('tilt_sys_work_steel') > g('tilt_guide'): bad.append('final: bracket + shaft at working load must stay within the guidance')
    if tr != 2.5: bad.append('released thickness 2.5 mm')
    if g('tilt_sys_margin_steel_pct') < 20: bad.append('final: system margin at least 20 % of the limit')
    if g('route_steel_thin_check') != 'PASS' or not (0 <= g('route_steel_thin_sys_margin') < 0.01): bad.append('story 2.0 mm steel passes the bracket check, ~0 system margin')
    if abs(g('FOS_bend_steel') - 205 / (6 * M / (50 * tr * tr))) > 0.01: bad.append('FOS_bend_steel second way (Sy_steel_min, t_steel)')
    if g('engD_M3') != 1 or g('M3_screen') != 'PASS' or g('M3_check') != 'PASS': bad.append('M3: 1.00D at nominal (screen); release check at the tolerance corners PASS')
    # M3 motor-screw stack at the tolerance limits
    if abs(g('engD_M3_min') - 0.86) > 0.005 or abs(g('engD_M3_max') - 1.14) > 0.005: bad.append('M3 engagement range 0.86-1.14D at the tolerance limits')
    if g('runout_M3_min') < 1 or g('runout_M3_margin') < 0: bad.append('M3 run-out >= 1 at every corner')
    if g('strip_check_M3') != 'PASS' or g('FOS_strip_M3') < g('strip_gate') or g('FOS_strip_M3_max') <= 1: bad.append('M3 strip check at the worst corner')
    if abs(g('preload_M3_nom') - g('preload_M3')) > 0.5: bad.append('torque_M3 / (K d) must equal preload_M3')
    A2 = math.pi * g('d_min_M3') * (0.5 + 0.57735 * (g('d_min_M3') - g('D2_max_M3')) / g('P_M3'))
    if abs(A2 - g('A_strip_M3')) > 0.002: bad.append('A_strip_M3 second way')
    if abs(g('tau_motor') * g('A_strip_M3') * g('eng_M3_full_min') - g('F_strip_M3_min')) > 6: bad.append('F_strip_M3_min second way')
    if not (g('stack_t_lo') <= g('t_steel_min') and g('t_steel_max') <= g('stack_t_hi')): bad.append('drawing thickness band inside the stack window')
    if g('m3alt_nowasher_check') != 'FAIL' or g('m3alt_flange_check') != 'FAIL': bad.append('no-washer and flanged-head stacks bottom-side FAIL at the corners')
    for tag in ('nowasher', 'flange', 'm3x8_spacer'):
        if g(f'm3alt_{tag}_check') == 'PASS' and (g(f'm3alt_{tag}_runout_min') > g('runout_M3_min') + 1e-9 or g(f'm3alt_{tag}_FOS_strip') > g('FOS_strip_M3') + 1e-9):
            bad.append(f'recommended stack must be at least as robust as m3alt_{tag}')
    # course decision / 12 GA fails the screen, passes the full-thread check at its nominal, band top over the limit -> measured-thickness condition
    if not (g('ga12_screw_screen') == 'FAIL' and g('ga12_screw_check') == 'PASS' and g('ga12_band_check') == 'FAIL' and g('ga12_conform') == 'FAIL'
            and g('ga12_check') == 'PASS' and g('ga12_strength_check') == 'PASS' and g('ga12_tilt_check') == 'PASS'): bad.append('12 GA screen FAIL, nominal PASS, band FAIL, nonconforming')
    if not (g('ga12_steel_mm') < g('ga12_max_measured_t') <= g('stack_t_hi') < g('ga12_lot_t_max')): bad.append('ga12_max_measured_t between the 12 GA nominal and the band top')
    if abs(g('ga12_max_measured_t') - 2.77) > 0.03: bad.append('ga12_max_measured_t about 2.77 (E1, course decision)')
    if 'ACCEPTED' not in g('ga12_verdict') or 'incoming inspection' not in g('ga12_verdict') or str(g('ga12_max_measured_t')) not in g('ga12_verdict'): bad.append('ga12_verdict: measured-thickness condition')
    if str(g('ga12_max_measured_t')) not in g('ga12_dev_record'): bad.append('ga12_dev_record carries the limit')
    if g('ga13_screw_screen') != 'PASS' or abs(g('ga13_engD_M3') - 1.07) > 0.005 or g('ga13_conform') != 'FAIL' or g('ga13_runout_M3_min') >= 1 or g('ga13_check') != 'FAIL':
        bad.append('13 GA facts: 1.07D at nominal; fails thread below tip')
    # course decision strip basis and torque
    if g('torque_M3') != 0.5 or abs(g('thread_ded_M3') - 1.25) > 1e-9: bad.append('torque 0.5 N.m; deduction 2P + 0.5P')
    if not (g('FOS_strip_M3') < g('FOS_strip_M3_1P') < g('FOS_strip_M3_gross')): bad.append('strip FOS ordered: full allowance < 1P < none')
    if abs(g('FOS_strip_M3') - 1.66) > 0.01 or abs(g('FOS_strip_M3_max') - 1.13) > 0.015: bad.append('strip FOS about 1.66 / 1.13 at the maximum plating (worst corner everywhere)')
    if not (18 <= g('slip_margin') <= 25): bad.append('slip margin about 22 at 0.5 N.m')
    # E3: plated slot fit; E1 Must-fix: worst-revision keys, ECO-001 load path, R11 wording
    if g('slot_fit_check_plated') != 'PASS' or abs(g('slot_fit_margin_plated') - 0.076) > 1e-6 or abs(g('slot_fit_margin_plated_zmin') - 0.084) > 1e-6: bad.append('plated slot fit 0.076 at the maximum plating (0.084 at the minimum)')
    if 'BEFORE PLATING' not in g('drawing_t_note'): bad.append('drawing_t_note BEFORE PLATING')
    for r, sk in (('route_thick', 'study_thick_sys_margin'), ('route_steel', 'tilt_sys_margin_steel'), ('route_lips', 'study_lips_sys_margin')):
        if abs(g(f'{r}_sys_margin_worst') - g(sk)) > 0.0015: bad.append(f'{r}_sys_margin_worst = {sk}')
    if abs(g('route_thick_margin_worst') - g('study_thick_margin')) > 0.0015: bad.append('route_thick_margin_worst = study_thick_margin')
    if g('M4_act109_check') != 'PASS' or g('engD_M4x10_min') >= 1.5 or 'M4 x 12' not in g('cots221_choice'): bad.append('COTS-221 M4 x 12 load-path check')
    if 'R11 open until the tilt test' not in g('scorecard_stiffness') or 'R11 open until the tilt test' not in g('note_tilt_model'): bad.append('R11 status wording')
    # other accepted changes (review of 13 Nov)
    if g('stack_check_plated') != 'PASS' or abs(g('hole_M5_min_plated') - (g('hole_M5_min') - 2 * g('zinc_um_max') / 1000)) > 1e-9: bad.append('plated hole stack')
    if g('netreal_check_t1_min') != 'FAIL' or g('FOS_netreal_t1_min') >= g('FOS_gate') or g('t1_min') >= g('t1'): bad.append('1.5 mm at minimum thickness below the gate')
    if 'to be confirmed by test (open action' not in g('scorecard_stiffness'): bad.append('scorecard_stiffness open action')
    nt = g('note_tilt_model')
    if not all(w in nt for w in ('rigid (no joint', 'bearings as rigid', 'motor weight', 'Rev B far end', 'upper bound')): bad.append('note_tilt_model lists every choice and the R11 test')
    rc = g('eco001_root_cause')
    if 'embedding' not in rc or rc.count('. ') or not rc.endswith('.'): bad.append('eco001_root_cause: one sentence with the mechanism')
    if 'SAMPLE' not in v['depth_M3']['formula'] or '2.0 mm' in v['runout_M3']['formula'] or '2.0 mm' in v['runout_M5']['formula']: bad.append('depth_M3 / runout labels')
    if not v['tol_tapped']['formula'].startswith('RETIRED'): bad.append('tol_tapped retired')
    if any('(released)' in d['formula'] for k, d in v.items() if k.startswith('study_o1')): bad.append('stale "2.0 (released)" in study_o1_*')
    if v['breakeven_years']['spoken'] != 'three point six years': bad.append('breakeven_years spoken')
    if not (g('breakeven_years_machined') < 1 and g('breakeven_qty_machined') < g('breakeven_qty')): bad.append('Ep 03 Pugh: the mould pays back against the machined datum in under a year')
    if g('web_check_along') != 'PASS' or g('web_check_side') != 'FAIL': bad.append('course decision pilot query: along PASS, sideways FAIL')
    if g('mx_s_steel_stiffness') != 5 or g('mx_s_al_stiffness') != 3: bad.append('matrix stiffness scores from the rule')
    if abs(g('flat_rel') - 127.2) > 0.05 or abs(g('bend_line_rel') - 59.6) > 0.05: bad.append('flat pattern 127.2 / 59.6 (2.5 mm, course decision)')
    if g('hb_slot_edge_revB') != g('hb_slot_edge'): bad.append('Rev B near slot end must not move')
    if g('fatigue_ratio') < 4: bad.append('fatigue status line')
    if not (2.7 <= g('k_ratio') <= 2.9): bad.append('k_ratio about 2.8 (heat note text)')
    if g('mx_heat_consistent') != 'PASS': bad.append('Ep 07 heat scores consistent with thermal conductivity')
    if abs(g('Sy_steel_min') / g('sigma_netreal_steel') - g('FOS_netreal_steel')) > 0.05 or abs(g('Sy_steel_min') / g('sigma_netreal_steel_revB') - g('FOS_netreal_steel_revB')) > 0.05: bad.append('sigma_netreal_steel second way')
    for rv in ('', '_revB'):
        r2 = 'revB' if rv else 'revA'
        if not (g(f'fea_tilt_lo_{r2}') < g(f'tilt_steel{rv}') < g(f'fea_tilt_hi_{r2}')): bad.append(f'FEA tilt band brackets the hand value ({r2})')
    if not (g('fea_peak_hi') < g('Sy_steel_min')): bad.append('expected peak below the minimum yield')
    if any(g(k) is None for k in ('fea_tilt_revA', 'fea_tilt_revB', 'fea_stress_revA', 'fea_stress_revB', 'fea_peak', 'fea_move_revA', 'fea_move_revB', 'fea_line2_revA', 'fea_line2_revB', 'fea_bend_lin', 'fea_mesh_delta_pct', 'fea_model_rev')) and g('fea_verdict') != 'PENDING': bad.append('fea_verdict PENDING until filled')
    if not (24.9 <= g('x_clamp_edge') <= 25.1 and 26.9 <= g('x_clamp_edge_revB') <= 27.1): bad.append('clamp edge x = 25.0 / 27.0 (REVIEW_F11_CAE)')
    if not (33.7 <= g('b_net_clamp_edge') <= 33.9 and 16.9 <= g('sigma_clampedge_steel') <= 17.1 and 20.7 <= g('sigma_clampedge_steel_revB') <= 20.9): bad.append('clamp edge b_net 33.8 / 17.0 / 20.8 MPa (REVIEW_F11_CAE)')
    if not (g('sigma_clampedge_steel') < g('sigma_netreal_steel') and g('sigma_clampedge_steel_revB') < g('sigma_netreal_steel_revB')): bad.append('worst line stays the conservative bound')
    if abs(g('fea_stress_lo_revA') - 0.9 * g('sigma_clampedge_steel')) > 0.1 or abs(g('fea_stress_hi_revB') - 1.1 * g('sigma_clampedge_steel_revB')) > 0.1: bad.append('FC1 stress band +/-10 % on the clamp edge')
    if g('fea_stress_revA') is not None and not (g('fea_stress_lo_revA') <= g('fea_stress_revA') <= g('fea_stress_hi_revA')): bad.append('FEA clamp-edge stress in band (REVIEW_F11_CAE 16.4)')
    if not (13.2 <= g('sigma_slotend_steel') <= 13.4): bad.append('slot-end nominal about 13.3 (REVIEW_F11_CAE finding 6)')
    if abs(g('sigma_bend_lin_steel') - g('Sy_steel_min') / g('FOS_bend_steel')) > 0.05 or not (1.25 < g('Ki_bend_inner') < 1.33): bad.append('bend linearised / curved-beam factor')
    if not (g('c_rel') < g('x_fullM_line') < g('slot_zone_start')): bad.append('full-moment line in the gross zone')
    # Ep 07 matrix: steel leads and no 10 % shift changes the leader
    if not (g('mx_total_steel') > g('mx_total_al') > g('mx_total_ss') > g('mx_total_pa66')): bad.append('matrix order steel > al > ss > pa66')
    if g('mx_sens_gap') <= 0: bad.append('a 10 % weight shift changes the leader')
    if abs(sum(g(f'mx_w_{c}') for c in ('strength', 'stiffness', 'cost', 'process', 'corrosion', 'heat')) - 100) > 1e-9: bad.append('weights add to 100')
    # Ep 15 gauges (story: 14 GA strength and tilt pass; screw runout drops to about 0.9 mm)
    if abs(g('ga14_steel_mm') - 1.897) > 0.001: bad.append('ga14_steel_mm 1.897')
    if not (g('ga14_al_mm') < g('ga14_steel_mm') < g('ga14_galv_mm')): bad.append('gauge depends on material')
    if g('ga14_strength_check') != 'PASS' or g('ga14_tilt_check') != 'FAIL': bad.append('14 GA: strength PASS, tilt FAIL at Rev B (slot-zone model)')
    if g('ga14_tilt_revA') > g('tilt_limit'): bad.append('14 GA Rev A tilt within the limit')
    if g('ga14_screw_check') != 'FAIL' or abs(min(g('ga14_runout_M3'), g('ga14_runout_M5')) - 0.9) > 0.01: bad.append('14 GA runout story (0.9 mm)')
    # kept keys
    if g('mttr_total') != sum(g(f'mttr_s{k}') for k in range(1, 10)): bad.append('mttr_total')
    if g('qty_year') != 500 or g('qty_year_cast') != 5000 or g('pilot_slot_move') != 1: bad.append('quantity / slot-move keys')
    for k in ('PA66_Sy', 'PA66_E', 'PA66_rho', 'anodize_um'):
        if k not in v: bad.append(f'kept key missing: {k}')
    if any(k in v for k in REMOVED): bad.append('a removed key is still emitted')
    # course team study B: option 2 equals the released keys, option 1 equals route_steel_thin; study keys never replace released ones
    if abs(g('study_o2_tilt_A') - g('tilt_steel')) > 0.006 or abs(g('study_o2_tilt_B') - g('tilt_steel_revB')) > 0.006 \
            or abs(g('study_o2_sys_margin') - g('tilt_sys_margin_steel')) > 0.0015: bad.append('study option 2 must equal the released keys')
    if abs(g('study_o1_sys_margin') - g('route_steel_thin_sys_margin')) > 0.0015: bad.append('study option 1 = route_steel_thin')
    if abs(g('study_web_move_side') - g('web_after_move')) > 0.006: bad.append('study web = web_after_move')
    if 'REJECTED' not in g('ga14_verdict'): bad.append('course team decision A: 14 GA deviation rejected')

    # belt-alignment budget (R1 E1-M1 / E2-M1 / E3-M1), fatigue line (E1-M2), 12 GA over plating (E2-M2), public text
    if abs(g('misalign_budget') - g('tilt_sys_margin_steel')) > 0.0015 or abs(g('mis_elastic') - g('tilt_sys_work_steel')) > 0.0015: bad.append('misalign_budget = tilt_sys_margin_steel')
    if not (g('mis_tolerance_check') == g('bend_budget_check') == g('mis_opt_a_check') == g('mis_opt_b_check') == g('mis_opt_c_check') == 'FAIL'): bad.append('alignment: tolerance-only options must FAIL')
    if not (g('mis_adj_range_check') == g('mis_static_set_check') == g('mis_check') == 'PASS') or g('mis_margin') <= 0: bad.append('alignment: option (d) must PASS with margin')
    if abs(g('mis_total') - g('mis_elastic') - g('mis_static_set')) > 0.0015: bad.append('mis_total second way')
    # R2: open-ended belt, each pulley and each clamp set to the rail
    if not (g('mis_r2_check') == g('mis_drv_range_check') == g('mis_idl_range_check') == 'PASS') or min(g('mis_drv_margin'), g('mis_idl_margin')) <= 0: bad.append('R2 alignment must PASS with margin per pulley')
    if not (g('mis_opt_slot_check') == g('mis_opt_wedge_check') == g('mis_opt_noidl_check') == 'FAIL'): bad.append('R2: slot, wedge and no-idler options must FAIL')
    s1_ = g('mis_elastic') + g('mis_p_accept') + g('mis_u_pulley') + g('mis_c_accept') + g('mis_u_clamp')
    if abs(g('mis_s1_total') - s1_) > 0.003 or g('mis_drv_total') < max(g('mis_s1_total'), g('mis_s3_total')) - 1e-9: bad.append('R2 span totals second way')
    for k in ('mis_set_accept', 'mis_set_accept_mm', 'mis_set_uncert', 'mis_static_set', 'mis_static_set_check', 'mis_total', 'mis_margin', 'mis_margin_pct', 'mis_check', 'mis_adj_range_check'):
        if not v[k]['formula'].startswith('RETIRED'): bad.append(f'{k} retired (R2)')
    if v['tool_count_release']['value'] != 6 or v['tool_count_release']['spoken'] != 'six' or v['tool_count_eco']['value'] != v['tool_count_release']['value'] + 1 or v['tool_count_eco']['spoken'] != 'seven': bad.append('tool counts (COTS-223 kept as a set screw: six at release, one more after ECO-001)')
    if g('tool_list').split(';')[0].count(',') + 2 != v['tool_count_release']['value'] or 'hex socket 2 mm' not in g('act111_desc'): bad.append('tool_list matches tool_count_release; ACT-111 drive defined')
    # Ep 21 S09 belt change: one driver per different drive the task-list steps touch; every driver is in the tool list (Rev B = after ECO-001)
    steps_ = ' '.join(v[f'mttr_s{k}']['formula'] for k in range(1, 10))
    drv_ = g('belt_change_drivers').split('), ')
    if g('belt_change_driver_count') != len(drv_) or v['belt_change_driver_count']['spoken'] != 'four' or g('belt_change_driver_count') > g('tool_count_eco') \
            or v['belt_change_drivers']['spoken'].count(' for the ') != len(drv_) \
            or any(w not in steps_ for w in ('remove top cover', 'tension screw', 'motor screws', 'belt clamps')) \
            or any(d.split(' (')[0].replace(' mm hex key', '') not in g('tool_list') for d in drv_): bad.append('belt_change_drivers: count = drivers, steps on the task list, drivers in tool_list')
    # Ep 21 S07 access: both gaps (near end, Rev B far end) are shorter than the short leg of the M5 key, and the far gap is the near gap + T_revB
    if not (0 < g('gap_head_motor_near') < g('gap_head_motor_far_revB') < g('key_leg_M5')) or abs(g('gap_head_motor_far_revB') - g('gap_head_motor_near') - g('T_revB')) > 1e-9:
        bad.append('S07 access: 0 < near gap < Rev B far gap < key short leg; far - near = T_revB')
    if 'ROLLING DIRECTION' not in g('drw_grain_note') or g('drw_bend_note') in g('drw_grain_note'): bad.append('drw_grain_note is the added sentences only')
    if 'ACT-111' not in g('drw_note_alignment') or 'RAIL' not in g('drw_note_alignment') or 'rail' not in g('asm_alignment_step') or 'ACT-111' not in g('act101_adjust_req'): bad.append('R2 texts name the drive-side adjustment and the rail')
    if g('mis_drv_total') != math.ceil(g('mis_drv_total') * 1000 - 1e-9) / 1000: bad.append('R2 totals printed rounded up')
    if abs(g('sigma_range_slot') - 20.7) > 0.1 or abs(g('fatigue_ratio_slot') - 7.3) > 0.1: bad.append('fatigue on the worst slot line: 20.7 MPa, 7.3x')
    if g('ga12_max_measured_t_plated') != math.floor(g('stack_grip_hi') * 100 + 1e-9) / 100 or str(g('ga12_max_measured_t_plated')) not in g('ga12_verdict') or 'over the plating' not in g('ga12_dev_record'): bad.append('12 GA: every part measured over the plating')
    if g('FOS_min_steel') != 7.18 or g('FOS_strip_M3') != 1.66 or g('FOS_strip_M3_zmin') != 1.67: bad.append('every FOS rounded down')
    sheet_ = 'Legal ' + 'Safe' + 'guards'   # internal sheet name, never in a public text (built so the literal does not appear here)
    if any(sheet_ in str(d['formula']) or sheet_ in str(d['value']) for d in v.values()): bad.append('no internal sheet names in public Facts')
    if g('slot_fit_margin_plated') >= g('slot_fit_margin_plated_zmin') or g('FOS_strip_M3') < g('strip_gate') or g('FOS_strip_M3') > g('FOS_strip_M3_zmin') or g('ga12_max_measured_t_plated') != 2.77: bad.append('maximum plating is the worst case for fits and the stack; strip gate still met; over-plating limit 2.77')
    if 'E0' in str(g('Sy_source')) or '5052' not in g('Sy_source') or 'steel' not in g('Sy_steel_source'): bad.append('Sy_source / Sy_steel_source text')
    # course decision (4): fits on the drawing size (after plating); supplier cut sizes derived; no live key subtracts the plating again
    if g('stack_check') != 'PASS' or abs(g('stack_allowed') - 0.4) > 1e-9 or abs(g('stack_margin') - 0.1) > 1e-9: bad.append('M5 stack on the drawing size 0.4 / 0.1')
    if g('slot_fit_check') != 'PASS' or abs(g('slot_M3_mmc') - 3.3) > 1e-9 or abs(g('slot_fit_allowed') - 0.3) > 1e-9 or abs(g('slot_fit_margin') - 0.1) > 1e-9 or abs(g('motor_pat_pos_req') - 0.1) > 1e-9:
        bad.append('slot fit on the drawing size 3.3 / 0.3 / 0.1; motor pattern requirement 0.1')
    if abs(g('laser_cut_M5_min') - 5.424) > 1e-9 or abs(g('laser_cut_M5_max') - 5.616) > 1e-9 or abs(g('laser_cut_M3_slot_min') - 3.324) > 1e-9 or abs(g('laser_cut_M3_slot_max') - 3.516) > 1e-9:
        bad.append('laser-cut sizes = drawing limits + 2 x zinc max / min')
    if 'the designer checks the drawing size' not in g('plating_basis_note') or '5.424' not in g('plating_basis_note'): bad.append('plating_basis_note')
    for k in ('hole_M5_min_plated', 'stack_allowed_plated', 'stack_margin_plated', 'stack_margin_plated_zmin', 'stack_check_plated', 'slot_M3_mmc_plated',
              'slot_fit_allowed_plated', 'slot_fit_margin_plated', 'slot_fit_margin_plated_zmin', 'slot_fit_check_plated'):
        if not v[k]['formula'].startswith('RETIRED'): bad.append(f'{k} retired')
    for k, d in v.items():
        if not str(d['formula']).startswith('RETIRED') and ('_plated' in str(d['formula'])) and k not in ('ga12_max_measured_t_plated', 'ga12_verdict', 'ga12_dev_record'):
            bad.append(f'live key {k} cites a retired *_plated key')
    # course decision (1)(2)(3): basic dimensions, CZ, pilot-slot position
    if g('drw_ted_hole_edge') != 10 or g('drw_ted_B_slot_centre') != 15 or g('drw_ted_B_slot_row') != 0.5 or g('ted_chain_check') != 'PASS': bad.append('TEDs 10 / 15 / 0.5')
    if ' CZ ' not in g('drw_hole_frame') or 'ISO 5458' not in g('drw_cz_note'): bad.append('CZ frame and note')
    if g('pilot_slot_pos_check') != 'PASS' or abs(g('pilot_slot_pos_max') - 0.5) > 1e-9 or abs(g('pilot_slot_pos_margin') - 0.1) > 1e-9 or '0.4' not in g('drw_pilot_frame'): bad.append('pilot slot zone 0.4 (max 0.5)')
    if g('pilot_end_check_move') != 'FAIL' or 'Refuse' not in g('pilot_query_answer') or 'ECR' not in g('pilot_query_answer') or 'Accept' in g('pilot_query_answer'): bad.append('pilot query refused both ways (pilot hits the slot end at a travel limit)')
    for k, d in v.items():
        if d['unit'] == 'rad' and d['spoken']: bad.append(f'{k}: rad values are never spoken')
    return bad


def write(v, out_dir):
    L = ['<!-- SPDX-License-Identifier: CC-BY-4.0 -->', '',
         '\u00a9 2026 Vijayakumar Yeddula \u00b7 CC BY 4.0 \u00b7 Mechanical Design Basics (C4)', '',
         'Educational example - not for production, manufacture or legal use.', '',
         '# Facts_C4 - named values for every spoken or on-screen bracket number',
         f"Generated by make_facts.py (ACT-103 = flat {v['t_steel']['value']} mm cold-rolled low-carbon steel, course decision). Do not edit by hand. "
         'Scripts use [F: name]; the narrator speaks the "spoken" column. Values in rad are for answer keys only (never spoken). '
         'Sy and E are the 5052-H32 baseline of Ep 05/06 (typical values, Ep 07 comparison); every FOS gate uses a specified minimum yield '
         '(Sy_min, ASTM B209; Sy_steel_min, ASTM A1008/A1008M SS Grade 30 [205]). Tilt and movement come from a simplified model that errs both ways '
         '(gross section elsewhere, net section in slot zone; mounting term an upper bound; motor and screws rigid); PDS R11 is confirmed by test.', '',
         '| Name | Value | Unit | Spoken form | Formula / source |', '|---|---|---|---|---|']
    for k, d in v.items():
        L.append(f"| {k} | {d['value']} | {d['unit']} | {d['spoken']} | {d['formula']} |")
    L += ['', 'Teaching story: on the 5052-H32 baseline (specified minimum yield) the quick bend check passes both thicknesses; 1.5 mm fails the lumped net-section check '
          'and also falls below the gate on the real worst line, so it is rejected. Pulley movement fails 1.5 mm and passes 2.0 mm; '
          'shaft tilt (PDS R11) fails for both flat aluminium sheets. Ep 06 compares three routes to stiffness: thicker aluminium (3.0 mm; no standard M3 motor screw then works), '
          f"a stiffer material ({v['t_steel']['value']} mm steel, flat; 2.0 mm steel passes the bracket check but leaves almost nothing once the motor shaft flexes) and "
          'shape (2.0 mm aluminium + lips; thin margin once the motor shaft flex is added). The Ep 07 matrix, with stiffness scored from the real margin and the heat path as a criterion, picks steel. '
          f"The released ACT-103 is flat {v['t_steel']['value']} mm low-carbon steel, zinc plated; the heat path is confirmed by a motor-face temperature test. "
          'All loads, limits, scores and costs are illustrative.', '',
          'Removed keys (old -> replacement): ' + '; '.join(f'{k} -> {r}' for k, r in REMOVED.items())]
    open(os.path.join(out_dir, 'Facts_C4.md'), 'w').write('\n'.join(L) + '\n')
    json.dump(v, open(os.path.join(out_dir, 'facts_c4.json'), 'w'), indent=1)


if __name__ == '__main__':
    args = sys.argv[1:]
    shelf = None
    if '--shelf' in args:
        k = args.index('--shelf'); shelf = json.load(open(args[k + 1])); del args[k:k + 2]
    out = args[0] if args else '.'
    os.makedirs(out, exist_ok=True)
    v = compute(I)
    write(v, out)
    bad = self_check(v, shelf)
    import datetime
    line = 'PASS 0 failures' if not bad else f'FAIL {len(bad)} failures (see make_facts.log)'
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    open(os.path.join(out, 'make_facts.log'), 'w').write('\n'.join([f'{stamp} make_facts.py: {len(v)} keys, {line}'] + bad) + '\n')
    print(line)
