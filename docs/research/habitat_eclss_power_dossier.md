# Habitat, ECLSS and Power Dossier: Reference Values for Lunar and Martian Habitat Energy Simulation

Compiled 2026-11-09. This dossier supports the building-energy simulation (BES) of crewed surface habitats on the Moon and Mars in the journal paper. It covers three areas: (A) habitat sizing, (B) cabin environment and life support, and (C) power generation and storage. It closes with two recommended parameter sets and a reference list in Elsevier numbered style.

It is a companion to `parameter_dossier.md`, which covers solar geometry, regolith and atmosphere.

## Verification legend

This dossier uses the same codes as `parameter_dossier.md`.

| Code | Meaning |
|---|---|
| **V-text** | Read directly in the primary source: the full-text PDF, an official web page, or a published table. All V-text entries below were read from PDFs downloaded during this session and converted to text with `pdftotext`. |
| **V-abs** | Read in the primary source's abstract or landing page only. |
| **V-sec** | Confirmed in a secondary source that quotes the primary. |
| **Derived** | Calculated here from verified inputs. The formula is shown. |
| **Assumption** | An engineering choice made for this paper, with its rationale. No source states it. |
| **Not found** | Searched for but not located in a citable primary source. Do not cite a number. |

Corrections to the original brief, and inconsistencies between sources, are marked **⚠**.

Unit conversions: 1 psi = 6.894757 kPa, so 8.2 psia = 56.5 kPa, 10.2 psia = 70.3 kPa and 14.7 psia = 101.3 kPa. Also 1 kJ/h = 0.2778 W and 1 kJ/d = 0.011574 W.

---

## A. Habitat sizing for the first crews

### A.1 NASA Artemis Base Camp lunar Surface Habitat (SH, also called the Foundation Surface Habitat)

**Context.** The SH is a NASA reference concept, not a flight design. Burke et al. [Burke2022] say it "is instead a proof of concept, derived from a set of Ground Rules and Assumptions". The numbers below have changed between papers, so always cite the specific paper.

| Quantity | Value | Unit | Source | Verified | Notes |
|---|---|---|---|---|---|
| Nominal crew | 2 | crew | [Burke2022] §II, GR&A 1; [Kessler2022] §3 | V-text | "The Surface Habitat is required to accommodate a nominal crew of two." |
| Crew during swap-out or contingency | 4 for a short period; 4 for up to 7 days as a contingency safe haven | crew | [Burke2022]; [Kessler2022] | V-text | Four crew are present only briefly, when the Pressurized Rover crew swaps with the SH crew. |
| Evolved or expanded crew | 4 crew for ~30 days and 4 crew for ~60 days | crew, d | [Burke2022] GR&A "Expansion"; [Kessler2022] ("capability to evolve to support up to four crew for up to 60-days"); [Schunk2022] ("up to 60-day habitability for a crew of four") | V-text | **⚠ The brief's "crew size (4)" is the evolved capability, not the baseline.** |
| Nominal surface mission | ~30 | days | [Burke2022]; [Kessler2022] | V-text | The mission happens once a year, and the crew is present "only during mostly illuminated periods" (GR&A). |
| Mission duration range | 30–60 | days | [Schunk2021] (reference table); [Schunk2022] | V-text | |
| Design life | 15 years, with 10 years of total operation | yr | [Kessler2022]; [Schunk2021] | V-text | |
| Structure | Vertical hybrid inflatable: a lower aluminium deck plus two inflatable upper decks around a metallic core | – | [Burke2022] §II; [Kessler2022] | V-text | |
| Inflatable section dimensions | ~6.5 m outer diameter × 5.2 m height, with a 3.3 m diameter inner core | m | [Burke2022] §II | V-text | |
| Metallic (lower) section dimensions | 4.4 m diameter × 2.6 m height | m | [Burke2022] §II | V-text | |
| Overall height | 7.8 m (excluding solar arrays and lander); inflated diameter 6.5 m; launched in a 5 m fairing | m | [Kessler2022] §3 | V-text | |
| Habitable (enclosure) volume | ≈127 m³, i.e. ≈64 m³ per crewmember for 2 crew | m³ | [Burke2022] §V | V-text | This value comes from the CAD layout. |
| "Habitable volume" (reference table) | 175 m³ | m³ | [Schunk2021] slide "Lunar Surface Habitat Architecture Reference" | V-text | **⚠** This disagrees with the 127 m³ above. It most likely means the pressurized volume; see the next row. |
| Pressurized volume | 174 m³ | m³ | [Stromgren2023] slides (NTRS 20230002484), Airsave slide: "With 174 m3 Pressurized SH volume" | V-text | **Recommended value for the BES air volume.** It is consistent with the 175 m³ above. |
| Net habitable volume (NHV) required by the functional study | 14.6 m³ total (7.3 m³ per crewmember) for the crew-function volumes, plus a 5.0 m³ airlock | m³ | [Burke2022] Table 2 | V-text | These are minimum functional volumes only, not the total NHV. |
| EVA airlock | Two-chamber airlock with suitports. Stromgren's design: floor ≈4.7 m², volume 12.0 m³ | m², m³ | [Kessler2022]; [Stromgren2023] slide 6 | V-text | |
| Landed mass limit | 12 t (ground rule); the May 2022 master equipment list (MEL) predicted 12,517 kg | t | [Burke2022] §III and §VI; [Schunk2022] | V-text | |
| Cabin atmosphere (nominal) | 10.2 psia (70.3 kPa) and 26.5 % O₂, with capability to run at 8.2 psia (56.5 kPa) and 34 % O₂ | psia, % | [Kessler2022] §3; [Schunk2022] | V-text | Kessler: "On-going trade analyses are currently assessing ... transitioning the SH to a nominal operating pressure of 8.2 psia." |
| Cabin atmosphere (EVA study baseline) | 8.2 psia | psia | [Stromgren2023] | V-text | 10.2 psia is analysed as an alternative. |
| Electrical power (day) | 15 kW (reference table); "deployable solar array (10–15 kW)" | kW | [Schunk2021]; [Schunk2022] | V-text | |
| Night power | 2 kW (reference table); "Regenerative fuel cells will provide up to 3 kW of power during eclipse periods lasting up to 100 hours" | kW | [Schunk2021]; [Schunk2022] | V-text | |
| PV technology | Solar array wing with GaAs cells, 15-year life | – | [Kessler2022] | V-text | |
| Energy storage | Regenerative fuel cell (RFC). Its waste heat "provides supplemental heat during those [dark] periods" | – | [Kessler2022] | V-text | |
| EVA limits | Total EVA time ≤24 h per crewmember per week. Maximum surge rate is one 2-person, 8-hour EVA per 24 h. | h | [Burke2022] GR&A 4 | V-text | |

**Thermal-control data useful for BES verification.** All values below are V-text from [Schunk2022] (IEEE Aerospace 2022) and [Schunk2021] (TFAWS 2021).

| Quantity | Value | Notes |
|---|---|---|
| TCS heat rejection requirement | >15 kW under peak summer conditions at the south pole. The baseline (8 double-sided panels) gives 17 kW, and 12 panels give 27 kW. | Radiators: 48 m² double-sided total, 3 m × 2 m panels, 14 kg/m² areal density. |
| Coolants | Internal loop: 60/40 water/propylene glycol, split into a low-temperature loop (condensing heat exchanger) and a moderate-temperature loop. External loop: NOVEC 7200 (HFE 7200). | |
| Envelope insulation | 10-layer MLI. Its performance is treated as degraded on the inflatable because of creases from packing. | |
| Outer covering optical properties | Beta cloth: infrared emittance ε = 0.9, solar absorptance α = 0.4. A lower-emittance option of ε = 0.70 saves about 50 kWh per night. | |
| Habitat heat leak during survive-the-night | ≈1550 W to hold the habitable volume at 293 K. [Schunk2022] gives this as the heat leak "to maintain the SH at a minimum temperature of 283K" in one place and as the make-up heat for "above (293 K) 68°F" in another. **⚠ The 283 K vs 293 K wording is inconsistent in the source.** | A key **validation target** for an envelope model under a 100 h eclipse. |
| Net envelope heat loss during daylight operations | ≈850 W | A second validation target. |
| Radiator freeze protection during the night | ≥3840 W to stay above the NOVEC 7200 working limit (173 K), or ≥1353 W to stay above its freezing point (136 K). Retracting the radiators cuts the loss from ≈3400 W to ≈700 W. | |
| Unmitigated survive-the-night energy (100 h) | 540 kWh. Pre-heating (the "nominal" mitigation case) reduces it to 155 kWh. | |
| Survive-the-night heat load simulated | 3.7 kWt. The fuel cell is sized for 2.5 kWe, which gives 1.2 kWt of waste heat. | [Schunk2021]. |
| Fuel cell figure | "400 kWe/kg with 243 kWt/kg of waste heat at 62.2 % efficiency", attributed to Jakupca (2020) | **⚠ These units cannot be correct as printed; they are probably W/kg or kWh-type ratios. Do not use them.** |

### A.2 NASA Mars Design Reference Architecture 5.0 (DRA 5.0)

| Quantity | Value | Unit | Source | Verified | Notes |
|---|---|---|---|---|---|
| Crew per mission | 6 | crew | [Drake2009] §3 ("a crew of six would be sent on each of these missions") | V-text | |
| Surface stay | ~500 days (abstract). The example 2037 all-propulsive trajectory gives 539 days on Mars, 914 days total, with 174 d outbound and 201 d inbound. | d | [Cataldo2009] abstract; [Drake2009] §4.1 | V-text | Cataldo: "the crew will be on the surface for the duration of 500–550 days." **⚠** These are Earth days, not sols. 539 d ≈ 525 sols, using 1 sol = 1.0275 d. |
| Surface habitat concept | The reference "Commuter" option: a habitat on its lander plus two small pressurized rovers | – | [Drake2009] §5.1 | V-text | Drake: "a detailed assessment of Mars habitats was not conducted." The MEL was scaled from lunar habitat studies. |
| Commuter habitat mass and power | ≈21.5 t, using 12.1 kWe | t, kWe | [Drake2009] §5.1 | V-text | |
| Habitat pressurized volume | 154–198 m³ (single monolithic habitat, ≈23,000 kg) | m³ | [Rucker2018] §II, summarising DRA 5.0 | V-sec | This is the only volume found. The DRA 5.0 Addendum (NASA-SP-2009-566-ADD) was over 10 MB and was not read. **⚠** [Rucker2018] also gives the "six-crew DRA 5.0 monolithic habitat" as 16.5 t in a later section, which is inconsistent with its own 23 t. |
| Volume per crewmember | 25.7–33.0 m³ pressurized per person | m³ | Derived: 154/6 and 198/6 | Derived | The NHV would be smaller than this, so the DRA 5.0 habitat sits at or below the 25 m³ NHV guideline in A.3. |
| Habitat power design load | "Power systems were sized for a 12-kWe day/night load for the habitat when using the ISRU-produced O₂ supply. Additional habitat power would be required for closed-loop air revitalization." | kWe | [Drake2009] §5.4.1; [Cataldo2009] | V-text | Use 12 kWe as the habitat electrical load **excluding** O₂ generation (see B.6). |
| Crew-phase total surface load | ≈20 kWe day and night (photovoltaic case) | kWe | [Cataldo2009] §IV | V-text | Covers the habitat, rovers, logistics and ascent-vehicle keep-alive. With ascent-propellant ISRU, the daytime average is ≈96 kWe; ascent ISRU alone is 66 kWe over 8 h/day (22 kWe continuous). |
| Fission power | A 30-kWe version of the 40-kWe lunar design. The reactor is ≈1 km from the habitat, with a shaped shield giving 5 rem/yr at 1 km toward the habitat. | kWe | [Drake2009] §5.4.1; [Cataldo2009] §VI | V-text | **⚠ The brief's "30–40 kWe" range is correct: 30 kWe for DRA 5.0 and 40 kWe for the lunar design and later Mars studies [Rucker2018].** |
| Reactor mass (20 kWe, non-propellant ISRU) | 6,800 kg, including 20 % contingency | kg | [Drake2009] §6 | V-text | The 30 kWe mass is also given in §6 but was not extracted. |
| PV/RFC alternative | 5 modules, each 5 kWe RFC plus 290 m² of PV at 29 % cell efficiency. Total: 25 kWe night and 25 kWe day to loads, plus recharge. A dust-storm roll-out array adds 4,300 m² (5,800 m² total, +8,000 kg). | – | [Cataldo2009] §V | V-text | The solar case is sized for 30°N or the equator. |
| Later Mars surface habitat (EMC) | 7.2 m diameter, 172 m³ pressurized volume, monolithic, 4 crew, up to 550-day stays | m, m³ | [Rucker2018] §II | V-sec | EMC is the 2014–2016 Evolvable Mars Campaign. Its wet mass was 29,479 kg. |
| 2023 Mars Surface Habitat (MSH) concept | 2 crew, 30 sols, ~11,338 kg landed. It is derived from the lunar SH. | – | [Hughes2023] | V-text | **Not** a 500-sol concept. Cite only as the current NASA lineage. |

### A.3 Habitable volume per crewmember

| Quantity | Value | Unit | Source | Verified | Notes |
|---|---|---|---|---|---|
| Minimum acceptable NHV, long-duration exploration | **25 m³ (883 ft³) per person** | m³/person | [Whitmire2014] | V-text | Based on Mars DRM 5.0 mission parameters (6 crew, up to 912 days). The panel advised against reducing it for shorter missions: "reducing the volume to accommodate a shorter mission is not recommended." |
| Individual crew quarters within that NHV | 5.4 m³ (ISS crew quarters are 2.1 m³) | m³ | [Whitmire2014] | V-text | |
| Historical habitable volume per person | Skylab 120.3, ISS 85.2, Salyut 33.5, Mir 45 | m³/person | [Whitmire2014] Table 1 | V-text | |
| NASA-STD-3001 requirement | The standard sets no single m³ value. It requires the NHV to accommodate mission functions and points to SA-16-156, NASA/TP-2014-218556, HIDH §8.2 and JSC 63557. | – | [NASA2026STD] §8.1 | V-text | **⚠ Do not attribute "25 m³" to NASA-STD-3001.** Cite [Whitmire2014]. |
| Lunar SH NHV per crew at 4 crew | 127/4 = 31.8 | m³/person | Derived from [Burke2022] | Derived | Above the 25 m³ guideline. |
| Ratio of habitable to pressurized volume (lunar SH) | 127/174 ≈ 0.73 | – | Derived from [Burke2022] and [Stromgren2023] | Derived | Used in §D to size the Mars habitat. |

---

## B. Habitat environment and life support (sealed habitat)

### B.4 Cabin leakage

| Quantity | Value | Unit | Source | Verified | Notes |
|---|---|---|---|---|---|
| ISS overboard leak rate (whole station) | Rose from ≈0.064 kg/day air (0.14 lbm/d) in 2004 to ≈0.227 kg/day air (0.5 lbm/d) in 2011. The 2011 planning number is 0.227 kg/d. | kg/d | [Schaezler2011] §IV and Conclusions | V-text | **⚠** This is for the **whole ISS**, not "0.1–0.2 kg/day per module". |
| ISS free-air volume | 434 m³ (start of 2008) → 899 m³ (March 2011) | m³ | [Schaezler2011] | V-text | |
| ISS leakage as a fraction of air mass | ≈0.021 %/d | %/d | Derived: 0.227 kg/d ÷ (899 m³ × 1.19 kg/m³) | Derived | |
| Module specification leakage (examples) | US Lab 0.109 lbm/d; Node 1 0.117; Node 2 and Node 3 0.117 each; Columbus 0.5; JEM PM 0.3; Russian SM 0.0044 | lbm/d | [Schaezler2011] Table 3 | V-text | Ground-measured leakage is 10–1000× lower than specification. |
| Maximum design leakage rate (spaceflight) | Lower 0, nominal **0.05 %/d**, upper **0.14 %/d** | %/d of cabin gas mass | [Anderson2018] Table 4-1 | V-text | **Recommended design value for surface habitats.** BVAD notes "the actual leakage rate is significantly lower than the specification." |
| Lunar SH (174 m³ at 8.2 psia, 34 % O₂) | Gas mass 117.7 kg, so 0.059 kg/d (nominal) to 0.165 kg/d (upper) | kg/d | Derived: ρ = PM/(RT) = 0.676 kg/m³ at 295 K | Derived | Equivalent to only ~2×10⁻⁵ air changes per hour, which is **thermally negligible** in a BES model. Model leakage as a mass and consumables term, not as infiltration. |

### B.5 Airlock gas loss and EVA frequency

| Quantity | Value | Unit | Source | Verified | Notes |
|---|---|---|---|---|---|
| Two-crew airlock volume | Empty 4.25 m³; free gas 3.7 m³ in use. A single-person airlock is 1.02 m³ empty and ≈0.89 m³ free. | m³ | [Anderson2018] §4.6.2 | V-text | |
| Gas lost per depress cycle | About 10 % of the free airlock gas is lost (not recovered by the pump). This can be cut to 5 % at the cost of more pump time and power. | % | [Anderson2018] §4.6.2 and Table 4-75 (low 5, nominal 10, high 10 %) | V-text | |
| Lunar EVA table | Airlock volume 3.3 m³ and free gas 2.9 m³. Airlock cycles per week: 3.5 / 5 / 7 (low/nominal/high). EVA sorties per week: 7 / 10 / 14. EVA crew-hours per week: 80. EVA metabolic rate: 1.06 MJ/CM-h (300 W). | – | [Anderson2018] Table 4-75 | V-text | Each sortie is two crewmembers. |
| Gas lost per cycle, 2.9 m³ at 8.2 psia/34 % O₂ | 1.96 kg free gas, so ≈0.20 kg at 10 % or ≈0.10 kg at 5 % | kg/cycle | Derived: ρ = 0.676 kg/m³ | Derived | At 14.7 psia, the same airlock holds 3.45 kg (0.35 kg lost at 10 %). |
| SH airlock (12 m³) with 90 % Airsave recovery | 8.1 kg per full depress, so ≈0.81 kg lost per EVA | kg | Derived from [Stromgren2023] (12.0 m³, "90% gas recovery", 35 min pump-down at 8.2 psia) | Derived | |
| Gas loss per 28-day lunar mission, including tankage ("carriers") | Airlock 861 kg; suitlock 510 kg; suitport-airlock 533 kg; airlock with 10 % reduced loss 495 kg | kg/mission | [Stromgren2023] slides 9–10 (8.2 psia, 28 d, 2 × 2-crew EVAs per week) | V-text | The slide's table layout is garbled and one cell reads "861 g". The values include tank mass. Verify against the paper (DOI in the references) before quoting. |
| Suitport per-cycle loss | Not found as a primary per-cycle mass. | – | Boyle & Mitchell (2012) not retrieved | **Not found** | The NASA EVA-access study recommends a suitport-airlock for the SH [Stromgren2023]. |
| Mars EVA cadence | Two 4-hour ("half-day") 2-person sorties per workday at 5 workdays/week gives **520 sorties (airlock cycles) per year**, about 10 per week | cycles/yr | [Anderson2018] §4.6.2 | V-text | |
| Lunar SH EVA cadence | EVA ≤24 h per crewmember per week; surge rate of one 2-person 8-h EVA per day | – | [Burke2022] | V-text | |
| EVA consumables (lunar) | O₂ losses 0.069 / 0.092 / 0.110 kg/CM-h. Cooling water: 0.25 / 0.3375 / 0.5 kg/CM-h at the poles and 0.4625 / 0.625 / 0.7625 at the equator. | kg/CM-h | [Anderson2018] Table 4-75 | V-text | |

### B.6 ECLSS power and heat

| Quantity | Value | Unit | Source | Verified | Notes |
|---|---|---|---|---|---|
| ISS average power by system (one day, beta = 0°, no visiting vehicles) | ECLSS 5.31; TCS 8.72; C&DH 4.08; CTS 2.90; EPS 2.02; Service Module 3.64; JEM 5.35; ESA 2.04; FCES 1.07; FGB 1.80; GN&C 0.62; MSS 1.20; CHeCS 0.11; payload up to 30 | kW | [Anderson2018] Table 3-2 (from Pritchett 2014) | V-text | This was re-extracted in raw mode because the layout text misaligned the columns. It is for the whole ISS with ~6–7 crew. **Do not divide it into a per-crew ECLSS figure without caveats.** |
| ISS OGA production capacity | Up to 9.25 kg/day O₂ at 46.9 A cell-stack current (100 % rate), enough for 10.88 crew at 0.85 kg O₂/crew/day. The process range is 10–46.9 A. | kg/d | [Takada2023] §II | V-text | |
| ISS OGA stack | 28 cells. The power supply module (PSM) can provide "over 3800 Watts of power for electrolysis." | – | [Takada2019] §F | V-text | 3800 W is the PSM capability, not the measured draw. |
| OGA stack power at full rate | ≈2.4–2.6 kW, i.e. ≈256–284 W per kg/day O₂, or **≈210–235 W per crewmember** at 0.82 kg O₂/CM-d | W | Derived: P = I·N·V_cell with V_cell = 1.8–2.0 V (assumed). The Faraday check (I·N/4F) gives 9.4 kg/d, consistent with the stated 9.25. | Derived | Excludes pumps, controller and heaters. The thermodynamic minimum (HHV, 1.48 V) is ≈170 W per crewmember. A measured OGA power draw was **not found** in a primary source. |
| Fraction of OGA electrical power that becomes cabin or coolant heat | ≈18–26 %, i.e. 1 − 1.48/V_cell | – | Derived (thermoneutral-voltage energy balance) | Derived | The remainder leaves as the chemical enthalpy of H₂ (vented, or sent to Sabatier). If a Sabatier reactor is used, its exothermic reaction returns part of this as heat. **This is important for BES:** most ECLSS power is heat, but electrolysis power largely is not. |
| CDRA, 4BCO2, UPA, WPA, TCCS individual power | – | – | – | **Not found** | ICES-2026-160 tabulates CO₂ removal capacity (CDRA 4.2/6.5 kg/d and 4BCO2 4.5/6.9 kg/d at 2/3 mmHg) and ESM, but not power in W. A NASA slide value (CDRA ≈1000 W, 620 W of heat to TCS) was seen only in a search snippet, so do not cite it. |
| Total ECLSS power per crewmember | – | – | – | **Not found** as a single primary value | Use the whole-habitat loads instead: lunar SH 15 kW for 2–4 crew [Schunk2021], or the Mars habitat 12 kWe plus closed-loop air revitalization [Drake2009]. |
| Heat from all other electrical loads | ≈100 % of the electrical power dissipated inside the pressure shell appears as heat in the cabin air or the coolant loops | – | First law | Derived | Consistent with the SH TCS: >15 kW rejected for a 15 kW electrical system [Schunk2022]. |

### B.7 Crew metabolic heat, moisture and gas exchange

All values in this section are V-text from [Anderson2018], which reproduces HIDH (2014) Table 3-22. The model assumptions are a cabin at 294.3 K with a dew point of 283.2 K, air velocity 0.152 m/s, pressure 70.3 kPa, an 82 kg male, VO₂max 45 mL/kg-min, RQ 0.92, and one 30-min exercise session followed by 60 min of recovery.

**Short-duration (HIDH) design loads per crewmember** ([Anderson2018] Table 3-22):

| Activity | Duration (h/d) | Sensible (kJ/h; W) | Latent incl. sweat (kJ/h; W) | Total (kJ/h; W) | Water vapour (kg/min×10⁻⁴) | O₂ (kg/min×10⁻⁴) | CO₂ (kg/min×10⁻⁴) |
|---|---|---|---|---|---|---|---|
| Sleep | 8 | 224; 62.2 | 92; 25.6 | 317; 88.1 | 6.30 | 3.60 | 4.55 |
| Nominal awake | 14.5 | 329; 91.4 | 171; 47.5 | 500; 138.9 | 11.77 | 5.68 | 7.20 |
| Exercise 0–15 min (75 % VO₂max) | 0.25 | 514 | 692 | 1206 | 46.16 | 39.40 | 49.85 |
| Exercise 15–30 min | 0.25 | 624 | 2351 | 2974 | 128.42 | 39.40 | 49.85 |
| Recovery 0–15 / 15–30 / 30–45 / 45–60 min | 0.25 each | 568 / 488 / 466 / 455 | 1437 / 589 / 399 / 296 | 2005 / 1078 / 865 / 751 | 83.83 / 40.29 / 27.44 / 20.40 | 5.68 | 7.02 |
| **Daily total** | 24 | **7351 kJ (85.1 W avg)** | **4649 kJ (53.8 W avg)** | **12000 kJ (138.9 W avg)** | **1.85 kg** (+0.08 kg sweat run-off) | **0.82 kg** | **1.04 kg** |

**Long-duration exploration loads** ([Anderson2018] Tables 3-28 and 3-29, from the 41-Node Man model with long-duration exercise protocols):

| Case | Daily metabolic (kJ) | Sensible (kJ; W avg) | Latent (kJ; W avg) | Water vapour (kg/d) | Sweat (kg/d) | O₂ (kg/d) | CO₂ (kg/d) |
|---|---|---|---|---|---|---|---|
| 5th percentile | 8991 | 5187 | 3714 | 1.41 | 0.08 | 0.62 | 0.79 |
| 50th percentile | 12418 | 6299 | 5975 | 2.26 | 0.29 | 0.86 | 1.09 |
| 95th percentile (design extreme) | 16338 | 7423 | 8687 | 3.29 | 1.73 | 1.13 | 1.43 |
| **Reference crewmember** | **13337 (154.4 W)** | **6608 (76.5 W)** | **6590 (76.3 W)** | **2.50** | 0.38 | **0.92** | **1.17** |

Steady-state values for the reference crewmember ([Anderson2018] Table 3-28):

| State | Metabolic (kJ/h) | Sensible (kJ/h; W) | Latent (kJ/h; W) |
|---|---|---|---|
| Sleep | 317 | 160; 44.4 | 157; 43.6 |
| Awake | 500 | 306; 85.0 | 194; 53.9 |

Other per-crewmember values:

| Quantity | Value | Unit | Source | Verified | Notes |
|---|---|---|---|---|---|
| Nominal metabolic interface | O₂ 0.816 kg/CM-d; CO₂ 1.04 kg/CM-d; total heat 12.00 MJ/CM-d (sensible 7.35, latent 4.65); respiration and perspiration water 1.9 kg/CM-d; metabolic water 0.4 kg/CM-d; RQ 0.9276; body mass 82 kg | – | [Anderson2018] Table 3-33 | V-text | |
| Atmosphere design bounds | O₂ consumed 0.518 / 0.818 / 5.67 kg/CM-d and CO₂ generated 0.622 / 1.037 / 7.178 kg/CM-d (lower/nominal/upper). Respired water vapour 0.803 / 0.885 / 0.975 kg/CM-d; perspired 0.036 / 0.699 / 1.973 kg/CM-d. | – | [Anderson2018] Table 4-1 | V-text | |
| EVA metabolic rate | 293 W (1,055 kJ/CM-h); O₂ 0.075 kg/CM-h; CO₂ 0.093 kg/CM-h | – | [Anderson2018] Table 4-76 | V-text | During EVA, this heat is **not** added to the cabin. |

**⚠ Do not use the "≈120 W per crewmember average" figure found in a non-NASA skills web page.** Use 138.9 W (HIDH) or 154.4 W (long-duration reference crewmember).

### B.8 NASA-STD-3001 Volume 2 cabin environment limits

**⚠ The current revision is Rev F, approved 2026-07-14 (it supersedes Rev E).** The table below was read from Rev F [NASA2026STD]. Rev A (2015) values are given only where they differ.

| Quantity | Value | Requirement ID | Source | Verified | Notes |
|---|---|---|---|---|---|
| Crew health temperature and humidity envelope | Operating limits anchored at 18 °C/75 % RH (upper left) and 27 °C/25 % RH (lower right), based on ASHRAE 55 | [V2 6012] | [NASA2026STD] §6.2.3.1 | V-text | Rev A had separate limits: 18–27 °C [V2 6013] and 24-h average RH 25–75 % [V2 6010]. |
| Crew performance environmental zone | 20–25 °C and 30–60 % RH | [V2 6013] | [OCHMO2023]; [NASA2026STD] Fig. 6.2-3 | V-text (brief) | **Recommended BES control band.** |
| Temperature adjustability | The crew must be able to select set points ([V2 6151]), and the system must adjust temperature at a minimum rate ([V2 6152]). | [V2 6151], [V2 6152] | [NASA2026STD] | V-text | The numeric rate in [V2 6152] was garbled in extraction. Check the PDF if you need it. |
| ppCO₂ | 1-hour average ≤3 mmHg (0.40 kPa) in the habitable volume | [V2 6004] | [NASA2026STD] §6.2.1.3 | V-text | Rev A deferred to the JSC 20584 SMACs. BVAD lists a crew upper bound of 1.01 kPa and a nominal of 0.507 kPa (Table 4-1, older basis). |
| Inspired O₂ partial pressure | Normoxia 145–155 mmHg; indefinite hyperoxia limit 356 mmHg; mild-hypoxia lower limit 127 mmHg (1-h TWA, with monitoring) | [V2 6003] | [NASA2026STD] Table 6.2-1 | V-text | PIO₂ = (P_B − 47 mmHg)·F_IO₂. The table lists the 8.2 psia/34 % "exploration atmosphere" under mild hypoxia. |
| PIO₂ at candidate atmospheres | 8.2 psia/34 % gives 128 mmHg; 10.2 psia/26.5 % gives 127 mmHg; 14.7 psia/21 % gives 150 mmHg | – | Derived | Derived | Both reduced-pressure atmospheres sit at the mild-hypoxia limit. |
| Diluent gas | ≥30 % (assuming the balance is O₂) | [V2 6002] | [NASA2026STD] | V-text | 34 % O₂ leaves 66 % N₂, which complies. |
| Total pressure, indefinite exposure | 34.5 kPa < P ≤ 103 kPa (5.0–15.0 psia) | [V2 6006] | [NASA2026STD] §6.2.2.1 | V-text | Rev A gave 20.7 kPa < P ≤ 103 kPa. |
| Rate of pressure change | ≤13.5 psi/min for changes >1 psi | [V2 6007] | [NASA2026STD] | V-text | |
| Ventilation | "Effective atmosphere velocity range of 4.57–36.58 m/min (15–120 ft/min)", i.e. **0.076–0.61 m/s**, time-averaged in the crew-occupied space | [V2 6107] | [NASA2026STD] §6.2.7.1 rationale | V-text | **⚠ The brief's 0.2 m/s upper value is an older HIDH/Columbus figure. Rev F uses 0.61 m/s.** Rev F also notes that convection from lunar gravity "should be accounted for." |
| Dew point | No explicit dew-point limit in Rev F. The HIDH metabolic tables assume a 283.2 K (10 °C) dew point. | – | [Anderson2018] §3.3.2.1 | V-text | Condensation control follows from the RH limit and from cold-surface design (see the SH night-time condensation risk in [Kessler2022]). |
| Illuminance | General horizontal ambient ≥350 lux; general vertical ≥200 lux; translation and stowage ≥108 lux; medical and maintenance ≥750 lux; crew sleep ≤0.02 lux | [V2 8xxx], Table 8.7-1 | [NASA2026STD] Table 8.7-1 | V-text | |
| Exploration atmosphere recommendations | 57 kPa (8.2 psia)/34 % O₂ for EVA-intensive surface habitats and rovers. 70.3 kPa (10.2 psia)/26.5 % for landers and vehicles with contingency EVA. 101 kPa/21 % for vehicles without EVA. | – | [Anderson2018] §4.1, citing Norcross (2013), which superseded EAWG (2010) | V-text (secondary to Norcross) | NASA/TP-2010-216134 (EAWG final report) was **not retrieved**. Cite Norcross 2013 / BVAD for 8.2/34. |

---

## C. Power generation and storage

### C.9 Fission surface power

| Quantity | Value | Unit | Source | Verified | Notes |
|---|---|---|---|---|---|
| FSP project goal | ≥40 kWe, 10-year life with no maintenance, HALEU fuel, mass <6,000 kg, stowed volume 4 m × 6 m | – | [Kaldon2024] §1 | V-text | Phase 1 contracts ended Sept 2023 with three requirements: 40 kWe for 10 yr, survive launch loads, and ≤5 rem/yr above background at 1 km. **⚠ The RFP was issued in late 2021, not 2022 (news reports); this was not verified against sam.gov.** |
| Deployable 40 kWe concept: reactor thermal power | ~250 kWth | kWt | [Oleson2022] | V-text | |
| Conversion efficiency | Stirling convertor 26.1 %; PMAD 87 %; overall thermal-to-electric (end to end) **18.1 %** | % | [Oleson2022] §III.A.2 | V-text | Eight 6.2 kWe convertors in dual-opposed pairs. The cold end is limited to 420 K. |
| Waste heat and radiators | Reactor 126.4 kW rejected through 133.4 m² (pole) or 216.2 m² (equator) of accordion double-sided radiator. α = 0.14, ε = 0.84, 420 K inlet and 370 K outlet. Electronics 5.1 kW; PMAD 2.0 kW. | – | [Oleson2022] Tables III–IV | V-text | |
| Mass, 40 kWe deployable | Fission power system 3,969 kg basic. Lander-carried element 7,446 kg basic, or 10,046 kg with growth allowance and margin. Mobility system 2,080 kg. | kg | [Oleson2022] MEL | V-text | This exceeds the 6 t goal, so it is delivered in two rover trips. |
| Kilopower range | 1, 3, 5, 7, 10 kWe at reactor thermal power 4.3, 13.0, 21.7, 30.3, 43.3 kWt | – | [Gibson2015] Table I | V-text | |
| Kilopower system mass | 406, 751, 1011, 1246, **1544 kg (10 kWe)**; specific power 2.5 → 6.5 W/kg. Radiator area 3.2 → 20.0 m² (one-sided, 200 K sink). | kg | [Gibson2015] Table I | V-text | |
| Kilopower system efficiency | 10/43.3 = 23.1 % (10 kWe); 1/4.3 = 23.3 % (1 kWe) | % | Derived from [Gibson2015] | Derived | |
| KRUSTY test | 4 kWt steady state at ≈800 °C. The two 80 W-class convertors produced up to 95 and 88 We (183 We combined). Convertor thermal efficiency was 30–34 % (≈50 % of Carnot). | – | [Gibson2018] | V-text | Secondary sources report a ~25 % system efficiency, which was not found in [Gibson2018]. |
| Design life | 10 yr (FSP); Kilopower ≥10–15 yr | yr | [Kaldon2024]; [Gibson2015] | V-text | |

### C.10 Space photovoltaics and dust

| Quantity | Value | Unit | Source | Verified | Notes |
|---|---|---|---|---|---|
| Triple-junction cell efficiency, BOL | **29.5 %** (bare cell) or 29.2 % (CIC), AM0 at 1367 W/m² and 28 °C. AZUR 3G30C-Advanced, InGaP/GaAs/Ge. | % | [Azur2025] | V-text | This is a manufacturer datasheet. |
| After radiation (1 MeV e⁻) | 28.4 % (5×10¹³), 27.8 % (2.5×10¹⁴), 27.3 % (5×10¹⁴), 26.2 % (1×10¹⁵), 18.6 % (1×10¹⁶ e/cm²) | % | [Azur2025] | V-text | The remaining factor at 1×10¹⁵ is 0.89. Surface radiation doses are mission specific; the lunar and Mars surfaces have no trapped belts. |
| Temperature coefficients (BOL) | dVmp/dT = −6.7 mV/K; dImp/dT = +0.24 mA/K; dVoc/dT = −6.2 mV/K; dIsc/dT = +0.36 mA/K (Vmp = 2411 mV, Imp = 504 mA) | – | [Azur2025] | V-text | Valid over 28–140 °C. |
| Power temperature coefficient | **−0.23 %/K** relative to the 28 °C value | %/K | Derived: (Imp·dVmp/dT + Vmp·dImp/dT)/(Vmp·Imp) | Derived | |
| Cell solar absorptivity | 0.91 (with 100 µm AR coverglass) | – | [Azur2025] | V-text | Use for the array energy balance. |
| Array-level and operating-temperature data | – | – | – | **Not found** in a primary source this session | Cataldo assumed 29 % cells for Mars [Cataldo2009]. Packing factor, wiring and mismatch losses must be stated as assumptions. |
| Mars PV dust deposition (Pathfinder MAE) | **≈0.28 % per day** obscuration; the lander array showed ≈0.29 %/day | %/d | [LandisJenkins2000] (V-abs/V-sec); [Cataldo2009] (Sojourner 0.2 %/sol) | V-abs | |
| Mars PV dust, multi-mission review | "~0.2 % per sol is typical", with an observed range of 0.05–2 %/sol. Episodic cleaning occurred on MER; none was seen on InSight. | %/sol | [Lorenz2021] | V-abs | |
| MER Spirit | ≈30 % dust loss by sol 300 and 40 % by sol 400. A clearing event on sol 418 restored output to 90 %. | % | [Cataldo2009] §II | V-text | |
| Dust-storm energy | Opportunity, July 2007 storm: 128 Wh/sol vs ≈900 Wh clear day, i.e. **≈14 %** of clear-day energy | – | [Cataldo2009] | V-text | |
| DRA 5.0 dust management assumption | Robotic cleaning every 40–50 sols keeps the settled-dust loss to ≈10 % | % | [Cataldo2009] | V-text | |
| Lunar dust on PV | Apollo 11/12 Dust Detector Experiments recorded contamination from rocket exhaust and natural dust movement. Adhesion depends on sun elevation. | – | [OBrien2009] | V-abs | **No quantitative natural deposition rate (%/day) suitable for a model was found.** Treat lunar PV dust loss as an event (landing plume or EVA activity) rather than a continuous rate. |

### C.11 Batteries (Li-ion)

| Quantity | Value | Unit | Source | Verified | Notes |
|---|---|---|---|---|---|
| State-of-practice space Li-ion cell | 100–150 Wh/kg and 250–350 Wh/L. Battery level is "20–50 % lower". | Wh/kg | [Surampudi2017] §3 | V-text | |
| Flight battery examples | MER rover 90 Wh/kg (−20 to 30 °C, >4,500 cycles); Juno 110; Phoenix 105; GRAIL 100 Wh/kg | Wh/kg | [Surampudi2017] Table 3-4 | V-text | |
| Packaged Li-ion system | ≈160 Wh/kg (TRL 9) | Wh/kg | [Gilligan2023] slide 6 | V-text | This is a NASA GRC presentation. |
| Cycle life vs depth of discharge (DOD) | >1000 cycles at 100 % DOD; >30,000 cycles at 30 % DOD and ~10 yr calendar life ("only possible at shallow depths of discharge of <30 % and also at benign temperatures of 25 °C") | cycles | [Surampudi2017] §3, §4.2.1 | V-text | |
| Operating temperature | −20 °C to +40 °C (state of practice). MER flight batteries were rated −20 to +30 °C. | °C | [Surampudi2017] | V-text | The battery must sit inside the thermal envelope, which is an internal heat source and sink in BES. |
| Round-trip energy efficiency | – | – | – | **Not found** in a primary space source | **⚠ The brief's "90–95 %" could not be sourced.** [Smith2022] says only that the RFC theoretical maximum (~80 %) is "comparable to batteries". If used, label it an assumption and run a sensitivity case. |

### C.12 Regenerative fuel cells (H₂/O₂ PEM)

| Quantity | Value | Unit | Source | Verified | Notes |
|---|---|---|---|---|---|
| Demonstrated round-trip efficiency (closed-loop PEM RFC, GRC) | Up to **52 %** | % | [Bents2006] | V-text | Fuel cell stack 5.25 kW at 70 % (LHV); electrolyser 15 kW input at 71 % (LHV). Bents also cites a 600 Wh/kg flight-configuration target. |
| NASA GCD RFC project targets (FY23) | Specific energy: threshold 320 Wh/kg, goal 550 Wh/kg. Round-trip efficiency: threshold 50 %, goal 55 %. The goal is 2–3.4× the energy storage of packaged Li-ion. | – | [GilliganJakupca2023] | V-text | |
| Theoretical maximum RTE | ~80 % | % | [Smith2022] §1 | V-text | Smith also finds cryogenic reactant storage pushes RTE below 15 %, and that higher electrolyser pressure lowers RTE. |
| System specific energy range | <100 to >600 Wh/kg, depending on location and energy requirement | Wh/kg | [Gilligan2023] | V-text | |
| DRA 5.0 RFC sizing assumption | 50 % efficiency, 2:1 charge-to-discharge (8 h charge / 16 h discharge) | – | [Cataldo2009] | V-text | |
| Lunar SH use | The RFC supplies 2–3 kWe for up to 100 h; its waste heat offsets heater loads | – | [Kessler2022]; [Schunk2022]; [Schunk2021] | V-text | |

### C.13 Lunar illumination

| Quantity | Value | Unit | Source | Verified | Notes |
|---|---|---|---|---|---|
| Best Shackleton-rim site (LOLA, 240 m DEM, 6 h step, several 18.6-yr cycles) | Sunlit continuously for 240 days each year; longest continuous darkness ≈1.5 days | – | [Mazarico2011] abstract | V-abs | Height gains of about 10 m "can dramatically improve" average illumination. |
| Best sites, 20 m/pixel DEM (Connecting Ridge) | Illuminated 92.27 % of the time at 2 m and 95.65 % at 10 m above ground. "Longest continuous darkness periods ... typically 3–5 days." | – | [Glaser2014] abstract | V-abs | |
| Design eclipse used by NASA SH studies | Up to 100 h (≈4.2 days) | h | [Schunk2022]; [Kessler2022] ("100hr+ eclipse") | V-text | |
| South-pole light/dark cycle (NASA framing) | "Shorter periods of darkness (~4 days) and longer periods of daylight (~200 days)" | d | [Kessler2022] | V-text | This is qualitative and site dependent. |
| Equatorial lunar night | **354.4 h** (14.77 d), i.e. half the synodic month of 29.53 d | h | Derived from [Williams2024] | Derived | |

---

## D. Recommended parameter sets for the paper

Every value here traces to a row above. Values marked *(A)* are assumptions made for this paper and should be stated as such in the manuscript.

### D.1 Four-crew lunar south-pole habitat (30–60 day stay)

| Group | Parameter | Recommended value | Basis |
|---|---|---|---|
| Mission | Crew | 4 (evolved SH capability). Sensitivity case: 2 crew. | [Kessler2022], [Schunk2022] |
| | Stay | 30 d baseline; 60 d extended | [Burke2022] |
| | Site | Connecting Ridge or Shackleton rim. Design eclipse 100 h. Sensitivity: 3–5 day darkness. | [Schunk2022], [Glaser2014] |
| Geometry | Pressurized volume | **174 m³** | [Stromgren2023]; [Schunk2021] (175 m³) |
| | Single-zone equivalent | Vertical cylinder, **D = 6.5 m, H = 5.25 m** (π·3.25²·5.25 = 174 m³) | Derived |
| | Three-zone option | Level 1: metallic cylinder D 4.4 m × H 2.6 m (≈15 m² floor). Levels 2–3: inflatable, OD 6.5 m, total H 5.2 m, around a 3.3 m core (≈24.6 m² annular floor per deck). Airlock: separate 12 m³ zone. | [Burke2022], [Stromgren2023] |
| | Habitable volume (NHV) | 127 m³, i.e. 31.8 m³/crew at 4 crew (≥25 m³ guideline) | [Burke2022], [Whitmire2014] |
| Envelope | Outer surface | Beta cloth, α = 0.4, ε = 0.9. Sensitivity: ε = 0.7. | [Schunk2022] |
| | Insulation | 10-layer MLI, with a degradation factor on the inflatable *(A: choose an effective conductance and calibrate to the 1550 W night heat leak at 293 K)* | [Schunk2022] |
| | Validation targets | Night heat leak ≈1550 W at 293 K; daylight net loss ≈850 W | [Schunk2022] |
| Atmosphere | Total pressure and O₂ | **56.5 kPa (8.2 psia), 34 % O₂**, ρ ≈ 0.676 kg/m³ at 295 K. Alternative: 70.3 kPa/26.5 % (Kessler's nominal). | [Anderson2018], [Stromgren2023], [Kessler2022] |
| | Thermostat | Heating 20 °C / cooling 25 °C (crew performance zone); hard limits 18–27 °C *(A: band choice)* | [V2 6013], [V2 6012] |
| | Humidity | 30–60 % RH control band; 25–75 % hard limits | [V2 6013], [V2 6012] |
| | CO₂ | ≤3 mmHg 1-h average | [V2 6004] |
| | Ventilation | 0.076–0.61 m/s in occupied zones | [V2 6107] |
| | Leakage | 0.05 %/d (0.059 kg/d); upper 0.14 %/d. Not modelled as infiltration. | [Anderson2018] |
| Crew schedule | Daily profile | Sleep 8 h; nominal awake 14.5 h; exercise 0.5 h + recovery 1 h (HIDH). Weekday work ≈8.5 h; weekend recreation 6 h. | [Anderson2018] Tables 3-22 and 3-30 |
| | EVA | 2 × (2-crew, 8-h) EVAs per week. Crew on EVA contribute no cabin load. Surge: one 2-person 8-h EVA per day. | [Stromgren2023], [Burke2022] |
| Internal loads | Crew (per person) | Sleep 62 W sensible + 26 W latent; awake 91 W + 48 W; daily average 85 W + 54 W; water vapour 1.85 kg/d | [Anderson2018] Table 3-22 |
| | Crew (4 persons, average) | ≈340 W sensible + 215 W latent; ≈7.4 kg/d water vapour; 3.3 kg/d O₂ consumed; 4.2 kg/d CO₂ | Derived |
| | Total habitat electrical (day) | **15 kWe**, all treated as internal heat (to air or coolant) except the chemical-energy share of electrolysis | [Schunk2021], [Schunk2022] |
| | ECLSS within that total | OGA ≈0.85–0.93 kW for 4 crew (only ≈18–26 % becomes heat). Remaining ECLSS (CO₂ removal, water recovery, fans, TCCS) is not separately sourced. *(A: allocate as a lumped ECLSS load; see note 1)* | Derived (B.6) |
| | Lighting | ≥350 lux general horizontal; ≤0.02 lux sleep. Lighting power density *(A: ≈7 W/m², i.e. 350 lux ÷ (100 lm/W × 0.5 utilisation); state as an assumption)*. Floor ≈64 m², so ≈0.45 kW when lit. | [NASA2026STD] Table 8.7-1 |
| | Night (quiescent or survive-the-night) | 2–3 kWe; habitat held near 293 K | [Schunk2021], [Schunk2022] |
| Power option 1 (baseline) | PV + RFC | 10–15 kW GaAs/3J array (29.5 % BOL cell, −0.23 %/K, absorptivity 0.91). RFC 2.5–3 kWe × 100 h = 250–300 kWh delivered; RTE 50–55 % gives 500–600 kWh of recharge energy. RFC waste heat goes to the TCS. | [Kessler2022], [Schunk2022], [Azur2025], [GilliganJakupca2023] |
| Power option 2 | PV + Li-ion | 200–300 kWh of storage at ≈160 Wh/kg packaged. At 30 % DOD (for >30,000 cycles) this needs ≈4.2–6.3 t; at 80 % DOD, ≈1.6–2.3 t. *(DOD choice: A)* | [Gilligan2023], [Surampudi2017]; Derived |
| Power option 3 | Fission | 40 kWe FSP at ≥1 km. 18.1 % end-to-end efficiency; ≈126 kW waste heat to 133 m² of radiator at the pole. | [Kaldon2024], [Oleson2022] |

### D.2 Six-crew Mars surface habitat (~500 sols)

| Group | Parameter | Recommended value | Basis |
|---|---|---|---|
| Mission | Crew | 6 | [Drake2009] |
| | Stay | ~500 d. Baseline 539 d (≈525 sols, 2037 example). Sensitivity: 500 sols. | [Drake2009], [Cataldo2009] |
| | Site | 0–30°N for the solar options; fission is latitude independent | [Cataldo2009] |
| Geometry | Pressurized volume | **≈225 m³ baseline**: 6 × 25 m³ NHV = 150 m³, divided by the 0.73 NHV-to-pressurized ratio of the lunar SH, gives ≥205 m³. Sensitivity: 154–198 m³ (DRA 5.0 estimate) and 172 m³ (EMC). | [Whitmire2014], [Rucker2018]; Derived |
| | Shape | Vertical two-deck cylinder, **D = 7.2 m, H = 5.5 m** (π·3.6²·5.5 = 224 m³; ≈40.7 m² per deck, ≈81 m² floor). The 7.2 m diameter is the EMC heritage value. Alternative: horizontal cylinder D 7.2 m × L 5.5 m with the same volume. Airlock: separate 3.3–4.25 m³ zone, or a suitport. | [Rucker2018], [Anderson2018]; *(A: height)* |
| Atmosphere | Total pressure and O₂ | **56.5 kPa / 34 % O₂** (EVA-intensive: about 10 sorties per week) | [Anderson2018] |
| | Setpoints, humidity, CO₂, ventilation | As D.1 | [NASA2026STD] |
| | Leakage | 0.05 %/d (≈0.076 kg/d for 225 m³); upper 0.14 %/d | [Anderson2018] |
| Crew schedule | Daily profile | Long-duration reference crewmember: 8 h sleep, exercise per the long-duration protocol, remainder nominal. Weekday/weekend split as in BVAD Table 3-30. Use a 24.66 h sol *(A: shift the schedule to local solar time)*. | [Anderson2018] Tables 3-28 to 3-30 |
| | EVA | 520 two-person half-day (4 h) sorties per year: 2 per workday, 5 workdays/week. Two crew are absent ≈8 h per workday. | [Anderson2018] §4.6.2 |
| Internal loads | Crew (per person) | Sleep 44 W sensible + 44 W latent; awake 85 W + 54 W; daily average **76.5 W + 76.3 W**; water vapour 2.50 kg/d; O₂ 0.92 kg/d; CO₂ 1.17 kg/d | [Anderson2018] Tables 3-28 and 3-29 |
| | Crew (6 persons, average) | ≈460 W sensible + 458 W latent; ≈15 kg/d water vapour | Derived |
| | Habitat electrical | **12 kWe** day/night (O₂ supplied by ISRU), plus closed-loop air revitalization. Adding OGA electrolysis for 6 crew is ≈1.3–1.4 kW, of which only ≈18–26 % is heat. Baseline total ≈13.5 kWe. | [Drake2009], [Cataldo2009]; Derived |
| | Lighting | As D.1: ≈7 W/m² × 81 m² ≈ 0.57 kW when lit *(A)* | [NASA2026STD] |
| Power option 1 (baseline) | Fission | 30 kWe (DRA 5.0) or 40 kWe (FSP-class, as later Mars studies baseline). Alternative: 3–4 Kilopower 10 kWe units (1,544 kg each, 43.3 kWt, ≈23 % efficient, 20 m² radiator each). | [Drake2009], [Rucker2018], [Gibson2015], [Kaldon2024] |
| Power option 2 | PV + RFC | Five 5 kWe PV/RFC modules: 29 % cells, 290 m² each, 25 kWe day and night to loads. RFC RTE 50 %. Dust: 0.2–0.28 %/sol, capped at 10 % by cleaning every 40–50 sols. Storm: ≈14 % of clear-day energy, with a +4,300 m² roll-out array. | [Cataldo2009], [Lorenz2021], [LandisJenkins2000] |
| Power option 3 | PV + Li-ion | Li-ion at 100–150 Wh/kg cell (state of practice); battery level 20–50 % lower; ≈160 Wh/kg packaged. Must be kept between −20 and +40 °C. RTE not sourced (sensitivity case). | [Surampudi2017], [Gilligan2023] |

**Notes**

1. *ECLSS sub-allocation.* No public primary source was found for the individual power of CDRA/4BCO2, UPA, WPA or TCCS. The paper should therefore treat ECLSS as a lumped share of the whole-habitat electrical load. One option is to scale ECLSS by the ISS ratio ECLSS : (ECLSS + C&DH + CTS + TCS) ≈ 5.31/21.0 ≈ 25 % ([Anderson2018] Table 3-2) and label that as an assumption. Model OGA electrolysis separately, with the 18–26 % heat fraction.
2. *Low-pressure convection.* At 56.5 kPa, air density is 57 % of sea level. Natural and forced convection coefficients drop accordingly. Under 1/6 g and 0.38 g, natural convection weakens further. [NASA2026STD] tells designers to account for gravity-driven convection in [V2 6107].
3. *Night setback.* The SH is designed to drop its internal temperature when uncrewed ([Schunk2022] Fig. 11; "Allowing the un-crewed habitat temperature to sink below respirable atmosphere limits could save on the total energy"). [Kessler2022] notes a condensation risk on cooling. A BES study should report dew-point margin during setback.

---

## E. Items not found or not verified (do not cite numbers)

- Individual ISS ECLSS assembly power for CDRA, UPA, WPA, TCCS and Sabatier, and a single "ECLSS kW per crew" value.
- A measured OGA electrical draw. Only the PSM capability (>3800 W) and the current limit (46.9 A) were verified; the draw in B.6 is derived.
- Li-ion round-trip efficiency in a space-qualified primary source.
- Suitport gas loss per cycle (Boyle & Mitchell 2012, AIAA 2012-3631, was not retrieved).
- DRA 5.0 Addendum (NASA-SP-2009-566-ADD) habitat dimensions; the PDF is over 10 MB and could not be fetched. The 154–198 m³ value is via [Rucker2018].
- EAWG final report NASA/TP-2010-216134 (not retrieved). The 8.2 psia/34 % recommendation is cited via BVAD, which quotes Norcross 2013.
- PV array-level efficiency, packing factor, and in-vacuum operating temperature for lunar or Mars surface arrays.
- A quantitative natural lunar dust deposition rate on PV.
- The lunar "Surface Habitat" pressurized volume in [Schunk2021] is labelled "habitable volume 175 m³". This conflicts with Burke's 127 m³ habitable, and it is treated here as the pressurized volume.

---

## F. Reference list (Elsevier numbered style, Python dict)

```python
REFERENCES_HABITAT_ECLSS_POWER = {
    "Kessler2022": "P. Kessler, T. Prater, T. Nickens, D. Harris, Artemis deep space habitation: Enabling a sustained human presence on the Moon and beyond, in: 2022 IEEE Aerospace Conference (AERO), Big Sky, MT, 2022, pp. 1–12. https://doi.org/10.1109/AERO53065.2022.9843393",
    "Burke2022": "C. Burke, R.L. Howard Jr., P. Kessler, Internal layout of a lunar surface habitat, in: ASCEND 2022, AIAA, Las Vegas, NV, 2022. NASA NTRS 20220013669. https://ntrs.nasa.gov/citations/20220013669",
    "Schunk2022": "R.G. Schunk, S.D. Babiak, B.W. Evans, Thermal control system architecture and technology challenges for a lunar surface habitat, in: 2022 IEEE Aerospace Conference (AERO), Big Sky, MT, 2022. https://doi.org/10.1109/AERO53065.2022.9843698",
    "Schunk2021": "G. Schunk, S. Babiak, D. Naville, B. Evans, Conceptual thermal control system design for a lunar surface habitat, Thermal and Fluids Analysis Workshop (TFAWS 2021), virtual, 24–26 August 2021. NASA NTRS 20210020015. https://ntrs.nasa.gov/citations/20210020015",
    "Stromgren2023": "C. Stromgren, C. Lynch, C. Burke, J. Cho, N. Mary, Evaluating extravehicular activity access options for a lunar surface habitat, in: 2023 IEEE Aerospace Conference (AERO), Big Sky, MT, 2023. https://doi.org/10.1109/AERO55745.2023.10115984 (slides: NASA NTRS 20230002484)",
    "Drake2009": "B.G. Drake (Ed.), Human Exploration of Mars Design Reference Architecture 5.0, NASA/SP-2009-566, NASA Headquarters, Washington, DC, 2009. https://www.nasa.gov/pdf/373665main_NASA-SP-2009-566.pdf",
    "Cataldo2009": "R.L. Cataldo, Power requirements for the NASA Mars Design Reference Architecture (DRA) 5.0, in: Proc. Nuclear and Emerging Technologies for Space (NETS 2009), Atlanta, GA, 14–19 June 2009, Paper 203603. NASA NTRS 20120012929. https://ntrs.nasa.gov/citations/20120012929",
    "Rucker2018": "M.A. Rucker, S.J. Hoffman, A. Andrews, K.D. Watts, Advantages of a modular Mars surface habitat approach, in: 2018 AIAA SPACE and Astronautics Forum and Exposition, Orlando, FL, 2018, AIAA 2018-5102. https://doi.org/10.2514/6.2018-5102",
    "Hughes2023": "R. Hughes, D. McGraw, A. Choate, P. Kessler, Mars Surface Habitat (MSH) concept study, ASCEND 2023 (presentation), 23 October 2023. NASA NTRS 20230014593. https://ntrs.nasa.gov/citations/20230014593",
    "Whitmire2014": "A. Whitmire, L. Leveton, H. Broughton, M. Basner, A. Kearney, Minimum Acceptable Net Habitable Volume for Long-Duration Exploration Missions: Subject Matter Expert Consensus Session Report, NASA Johnson Space Center, JSC-CN-32284, Houston, TX, 2014. NASA NTRS 20140016951. https://ntrs.nasa.gov/citations/20140016951",
    "NASA2026STD": "NASA, NASA Spaceflight Human-System Standard, Volume 2: Human Factors, Habitability, and Environmental Health, NASA-STD-3001 Vol. 2 Rev. F, NASA Office of the Chief Health and Medical Officer, Washington, DC, approved 14 July 2026. https://standards.nasa.gov/system/files/tmp/NASA-STD-3001%20Vol%202%20Rev%20F.pdf",
    "NASA2015STD": "NASA, NASA Space Flight Human-System Standard, Volume 2: Human Factors, Habitability, and Environmental Health, NASA-STD-3001 Vol. 2 Rev. A, NASA, Washington, DC, approved 10 February 2015. https://standards.nasa.gov/sites/default/files/standards/NASA/B/0/Historical/nasa-std-3001_vol_2_rev_a.pdf",
    "OCHMO2023": "NASA Office of the Chief Health and Medical Officer, Environmental Control & Life Support System (ECLSS): Human-Centered Approach, NASA-STD-3001 Technical Brief OCHMO-TB-002, 2023. https://www.nasa.gov/wp-content/uploads/2023/12/ochmo-tb-002-eclss.pdf",
    "Anderson2018": "M.S. Anderson, M.K. Ewert, J.F. Keener, Life Support Baseline Values and Assumptions Document, NASA/TP-2015-218570/REV1, NASA Johnson Space Center, Houston, TX, 2018. https://ntrs.nasa.gov/citations/20180001338",
    "Schaezler2011": "R.N. Schaezler, A.J. Cook, D.J. Leonard, A. Ghariani, Trending of overboard leakage of ISS cabin atmosphere, in: 41st International Conference on Environmental Systems, Portland, OR, 2011, AIAA 2011-5149. https://doi.org/10.2514/6.2011-5149",
    "Takada2019": "K. Takada, Advanced oxygen generation assembly for exploration missions, in: 49th International Conference on Environmental Systems, Boston, MA, 2019, ICES-2019-107. NASA NTRS 20190030425. https://ntrs.nasa.gov/citations/20190030425",
    "Takada2023": "K. Takada, D. Hornyak, et al., Status of the advanced oxygen generation assembly, in: 52nd International Conference on Environmental Systems, Calgary, Canada, 2023, ICES-2023-311. NASA NTRS 20230008013. https://ntrs.nasa.gov/citations/20230008013",
    "Kaldon2024": "L.K. Kaldon, A.L. Presby, L.S. Mason, B.K. Smith, A.S. Weaver, Current status of NASA's Fission Surface Power project, in: 75th International Astronautical Congress, Milan, Italy, 2024, IAC-24-C3.3.4. NASA NTRS 20240011694. https://ntrs.nasa.gov/citations/20240011694",
    "Oleson2022": "S. Oleson, T. Packard, E. Turnbull, M. Gibson, D. Rao, C. Barth, S. Wilson, P. Schmitz, A. Colozza, B. Klefman, L. Tian, L. Mason, A deployable 40 kWe lunar fission surface power concept, in: Nuclear and Emerging Technologies for Space (NETS-2022), American Nuclear Society, Cleveland, OH, 2022. NASA NTRS 20220004670. https://ntrs.nasa.gov/citations/20220004670",
    "Gibson2015": "M.A. Gibson, L.S. Mason, C.L. Bowman, D.I. Poston, P.R. McClure, J. Creasy, C. Robinson, Development of NASA's Small Fission Power System for Science and Human Exploration, NASA/TM-2015-218460, NASA Glenn Research Center, Cleveland, OH, 2015. https://ntrs.nasa.gov/citations/20150011642",
    "Gibson2018": "M.A. Gibson, D.I. Poston, P. McClure, T.J. Godfroy, M.H. Briggs, J.L. Sanzi, The Kilopower Reactor Using Stirling TechnologY (KRUSTY) nuclear ground test results and lessons learned, in: 2018 International Energy Conversion Engineering Conference, Cincinnati, OH, 2018, AIAA 2018-4973. https://doi.org/10.2514/6.2018-4973",
    "Azur2025": "AZUR SPACE Solar Power GmbH, 30% Triple-Junction Bare Solar Cells & Assemblies TJ 3G30-Advanced (4x8), datasheet DB 00010891-01, Heilbronn, 11 April 2025. https://www.azurspace.com/media/uploads/file_links/file/bdb_00010891-01-00_tj3g30-advanced_4x8.pdf",
    "LandisJenkins2000": "G.A. Landis, P.P. Jenkins, Measurement of the settling rate of atmospheric dust on Mars by the MAE instrument on Mars Pathfinder, J. Geophys. Res. Planets 105 (E1) (2000) 1855–1857. https://doi.org/10.1029/1999JE001029",
    "Lorenz2021": "R.D. Lorenz, G.M. Martínez, A. Spiga, A. Vicente-Retortillo, C.E. Newman, N. Murdoch, F. Forget, E. Millour, T. Pierron, Lander and rover histories of dust accumulation on and removal from solar arrays on Mars, Planet. Space Sci. 207 (2021) 105337. https://doi.org/10.1016/j.pss.2021.105337",
    "OBrien2009": "B.J. O'Brien, Direct active measurements of movements of lunar dust: Rocket exhausts and natural effects contaminating and cleansing Apollo hardware on the Moon in 1969, Geophys. Res. Lett. 36 (2009) L09201. https://doi.org/10.1029/2008GL037116",
    "Surampudi2017": "R. Surampudi, J. Blosiu, R. Bugga, E. Brandon, M. Smart, J. Elliott, J. Castillo, et al., Energy Storage Technologies for Future Planetary Science Missions, JPL D-101146, Jet Propulsion Laboratory, Pasadena, CA, 2017. https://solarsystem.nasa.gov/system/downloadable_items/716_Energy_Storage_Tech_Report_FINAL.PDF",
    "Gilligan2023": "R. Gilligan, P.J. Smith, R. Green, Thermal management challenges and technology options for lunar regenerative fuel cells, Thermal and Fluids Analysis Workshop (TFAWS 2023), presentation. https://tfaws.nasa.gov/wp-content/uploads/TFAWS23-ID-11-Presentation.pdf",
    "GilliganJakupca2023": "R. Gilligan, I. Jakupca, FY23 Regenerative Fuel Cell (RFC) annual review, NASA STMD Game Changing Development Program, 20 September 2023. NASA NTRS 20230012948. https://ntrs.nasa.gov/citations/20230012948",
    "Smith2022": "P.J. Smith, K.P. Cain, R.P. Gilligan, I.J. Jakupca, Lunar Equator Regenerative Fuel Cell System Efficiency Analysis, NASA/TM-20210014627, NASA Glenn Research Center, Cleveland, OH, 2022. https://ntrs.nasa.gov/citations/20210014627",
    "Bents2006": "D.J. Bents, V.J. Scullin, B.J. Chang, D.W. Johnson, C.P. Garcia, I.J. Jakupca, Hydrogen-oxygen PEM regenerative fuel cell development at NASA Glenn Research Center, 2006 Fuel Cell Seminar, Honolulu, HI, 13–17 November 2006. NASA NTRS 20070010455. https://ntrs.nasa.gov/citations/20070010455",
    "Mazarico2011": "E. Mazarico, G.A. Neumann, D.E. Smith, M.T. Zuber, M.H. Torrence, Illumination conditions of the lunar polar regions using LOLA topography, Icarus 211 (2011) 1066–1081. https://doi.org/10.1016/j.icarus.2010.10.030",
    "Glaser2014": "P. Gläser, F. Scholten, D. De Rosa, R. Marco Figuera, J. Oberst, E. Mazarico, G.A. Neumann, M.S. Robinson, Illumination conditions at the lunar south pole using high resolution Digital Terrain Models from LOLA, Icarus 243 (2014) 78–90. https://doi.org/10.1016/j.icarus.2014.08.013",
    "Williams2024": "D.R. Williams, Moon Fact Sheet, NASA Space Science Data Coordinated Archive, Goddard Space Flight Center, updated 11 January 2024. https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html",
}
```
