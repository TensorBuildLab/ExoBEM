"""Earth / Moon / Mars factors that matter for building energy simulation, and how each tool treats them.

One list feeds the factor tables of both manuscripts and docs/planetary_factors.md, so the papers and the
documentation cannot drift apart.

Each entry: (category, factor, earth, moon, mars, exobem, core) where exobem / core describe the treatment
in ExoBEM (Python) and ExoBEM-Core (C++).  Status words used in the tables:
  modelled   - physics implemented and verified
  input      - a user parameter with a documented default
  enforced   - checked; a contradicting input stops the run
  neglected  - deliberately left out, with the reason given
"""

FACTORS = [
    # ------------------------------------------------------------------------------------------- time and Sun
    ("Time and Sun", "Length of the solar day", "24 h", "29.53 d (708.7 h): 354 h of light, 354 h of night", "1 sol = 24.66 h (88,775 s)",
     "modelled: any day length; time step independent of the day", "modelled: Sun moves at the body's hour-angle rate on an Earth clock"),
    ("Time and Sun", "Seasons and orbit", "365.25 d; obliquity 23.4°; e = 0.017",
     "Spin axis 1.5° from the ecliptic: almost no seasons; Sun grazes the horizon at the poles", "668.6 sols; obliquity 25.2°; e = 0.093",
     "modelled: Mars24 ephemeris; lunar subsolar point", "modelled: same ephemerides, daily fit"),
    ("Time and Sun", "Solar irradiance at the top of the atmosphere", "1361 W/m² (±3.4 %)", "1361 W/m² (±3.4 %), no atmosphere",
     "490–714 W/m² (1.38–1.67 AU)", "modelled: 1361/r²", "modelled"),
    ("Time and Sun", "Clock for crew schedules", "Local civil time", "Earth (UTC) mission time; the lunar day cannot set crew rhythms",
     "Local mean solar time (sol)", "modelled: UTC on the Moon, LMST on Mars", "Earth clock on both (Mars sol clock planned)"),
    ("Time and Sun", "Terrain horizon and eclipses", "Usually ignored", "Polar ridges: Sun circles the horizon; multi-day eclipses",
     "Crater rims", "modelled: horizon profile with finite solar disk", "input: uniform horizon ≥ 0°"),
    ("Time and Sun", "Earthshine and Earth's shadow", "–", "Earthshine < 0.2 W/m²; lunar eclipses of up to a few hours, 0–3 per year", "–",
     "neglected: < 0.02 % of sunlight; eclipse hours are within normal night", "neglected"),
    # ------------------------------------------------------------------------------------------- atmosphere and sky
    ("Atmosphere and sky", "Ambient gas and pressure", "Air, 101 kPa", "Vacuum (~10⁻¹² kPa)", "95 % CO2, 0.6–0.8 kPa, ±12 % seasonal cycle",
     "modelled: vacuum or CO2 with seasonal pressure", "modelled: separate ambient pressure"),
    ("Atmosphere and sky", "Diffuse sunlight", "Clouds and aerosols (Perez model)", "None", "Dust scattering; τ = 0.3 to > 6 in global storms",
     "modelled: delta-Eddington two-stream, τ(Ls), storm scenario", "modelled: same model or read from the weather file"),
    ("Atmosphere and sky", "Sky long-wave radiation", "Effective sky 230–290 K", "2.7 K cosmic background", "CO2 and dust emission, sky ≈ 150–200 K",
     "modelled", "modelled; all sky view to the sky"),
    ("Atmosphere and sky", "Near-surface air temperature", "From weather file", "No air", "Large diurnal swing, follows the ground",
     "modelled: lagged ground surrogate calibrated to MEDA", "modelled (Moon: carries the ground temperature, unused)"),
    ("Atmosphere and sky", "Wind", "Main driver of exterior convection", "None", "2–10 m/s, but ~1 % of Earth's dynamic pressure",
     "modelled: diurnal wind for convection", "modelled"),
    ("Atmosphere and sky", "Humidity, rain, snow, clouds", "Important for loads and envelopes", "None", "Trace water; seasonal CO2 frost at high latitude",
     "neglected (none present; frost sites excluded)", "neglected; outdoor moisture exchange switched off"),
    # ------------------------------------------------------------------------------------------- ground
    ("Ground", "Ground thermal model", "Monthly ground temperatures", "Regolith k ≈ 1–10 mW/(m·K), surface 95–390 K",
     "Regolith with CO2 in pores, thermal inertia ≈ 350 SI", "modelled: 1-D regolith column (Hayne et al. 2017; thermal inertia)",
     "modelled: same column, or from the weather file"),
    ("Ground", "Geothermal heat flux", "60–90 mW/m²", "18 mW/m² (Apollo heat flow)", "~20 mW/m² (estimated)", "modelled on the Moon; neglected on Mars (< 0.1 % of loads)",
     "same"),
    ("Ground", "Ground reflectance", "0.2, snow up to 0.7", "0.12, rising at grazing incidence", "0.14 (Jezero)", "modelled", "modelled"),
    # ------------------------------------------------------------------------------------------- envelope
    ("Envelope", "Exterior convection", "Correlations for air at 1 atm (TARP, DOE-2)", "None", "Mixed convection in thin CO2 at 3.72 m/s², 20–70× weaker",
     "modelled: physical correlation for any gas, pressure, gravity", "modelled; Earth floor on h bypassed"),
    ("Envelope", "Exterior long-wave exchange", "Ground at air temperature; part of the sky view to air", "Sky 2.7 K; hot or cold regolith",
     "Sky and regolith", "modelled: sky and regolith only", "modelled"),
    ("Envelope", "Thermal extremes and materials", "−30 to +40 °C", "−180 to +120 °C at the surface", "−90 to +20 °C",
     "modelled: k(T), cp(T) for regolith; no lower temperature limit", "modelled: CondFD limit −270 °C; k(T), cp(T) tables"),
    ("Envelope", "Radiation shield as thermal mass", "–", "≥ 0.5–1 m regolith cover: time constant of years", "Time constant of months",
     "modelled: stretched grid; steady start-up solve", "modelled: steady start-up profile + correction"),
    ("Envelope", "Multi-layer insulation", "–", "Effective in vacuum", "Degraded by gas conduction at 0.6–0.8 kPa (use aerogel)",
     "input: separate vacuum and Mars insulation materials", "input"),
    ("Envelope", "Windows and solar gains", "Major load component", "Small ports at most", "Small ports at most",
     "neglected: windowless reference habitats", "not yet supported (windows refused)"),
    ("Envelope", "Dust on exterior surfaces", "–", "Raises solar absorptance (0.1 → 0.35 on radiators)", "Dust settling",
     "input: absorptance scenarios", "input"),
    # ------------------------------------------------------------------------------------------- cabin
    ("Cabin", "Outdoor air: infiltration, ventilation, economizers", "Major load component", "None: sealed pressure vessel", "None: sealed pressure vessel",
     "enforced: infiltration must be 0", "enforced: all outdoor-air objects refused"),
    ("Cabin", "Cabin gas lost overboard", "–", "Leakage ~0.1–0.2 kg/d; airlock venting per EVA", "Same",
     "modelled: leakage + airlock losses, make-up gas energy and mass", "neglected (energy < 1 W); reported by ExoBEM"),
    ("Cabin", "Cabin pressure and composition", "101 kPa, 21 % O2", "70.3 kPa / 26.5 % O2 or 56.5 kPa / 34 % O2", "Same",
     "modelled: density, cp, conductivity, psychrometrics of the cabin gas", "modelled: cabin pressure for all zone and HVAC air"),
    ("Cabin", "Oxygen limits", "–", "Hypoxia below ~16 kPa O2; flammability above 34 % O2", "Same", "enforced: input checks", "input"),
    ("Cabin", "Humidity and condensate", "Outdoor-air humidity dominates", "Only crew and plants add water; condensing heat exchanger removes it",
     "Same", "modelled: vapour balance, RH 25–60 %, condensate reported", "modelled: EnergyPlus moisture balance at cabin pressure"),
    ("Cabin", "Natural convection inside", "1 g, 101 kPa", "1.62 m/s², 56.5 kPa: ~2.5× weaker", "3.72 m/s², 56.5 kPa: ~1.9× weaker",
     "modelled: physical mixed convection with forced cabin flow 0.15 m/s", "modelled"),
    ("Cabin", "Life support (CO2 removal, O2 generation, water processing)", "–", "Kilowatts of electric power, released as cabin heat",
     "Same", "modelled: electric internal gains", "modelled: electric equipment"),
    ("Cabin", "Crew metabolism and schedules", "Occupant densities", "BVAD: 85 W sensible + 54 W latent per person (mean)", "Same",
     "modelled: BVAD values, sleep/work schedule", "modelled: People/equipment schedules"),
    ("Cabin", "Interior thermal mass (racks, stowage)", "Furniture", "Racks and stowage", "Same", "modelled: internal mass", "modelled: InternalMass"),
    # ------------------------------------------------------------------------------------------- systems
    ("Systems", "Heat rejection", "Outdoor air, cooling towers", "Radiators only; hot regolith can force heat-pump lift", "Radiators (thin-gas convection secondary)",
     "modelled: radiator sink, heat-pump COP, pump power", "refused air/evaporative equipment; space radiator planned"),
    ("Systems", "Electric power generation", "Grid", "PV with lunar-night storage, or fission", "PV with dust losses, or fission",
     "modelled: PV (cell temperature in vacuum), batteries, RFC, fission, dispatch", "modelled: PV one-diode with vacuum cell temperature, batteries in a zone"),
    ("Systems", "Energy storage", "Optional", "354 h night at the equator; multi-day polar eclipses", "Night and global dust storms (weeks)",
     "modelled: battery and RFC state of charge", "modelled: EnergyPlus storage objects"),
    ("Systems", "Gravity in fluids and equipment", "9.81 m/s²", "1.62 m/s²", "3.72 m/s²", "modelled in convection; pumps/fans as electric loads",
     "modelled in convection; other buoyancy models refused"),
]

STATUS_WORDS = ("modelled", "input", "enforced", "neglected")


def markdown():
    rows = ["| Category | Factor | Earth | Moon | Mars | ExoBEM | ExoBEM-Core |", "|---|---|---|---|---|---|---|"]
    rows += ["| " + " | ".join(f) + " |" for f in FACTORS]
    return "\n".join(rows)


if __name__ == "__main__":
    print(markdown())
