# Parameter and Literature Dossier: Lunar and Martian Habitat Building Energy Simulation

Compiled 2026-11-08. This dossier supports the planetary extensions of the Python re-implementation of the EnergyPlus heat-balance engine, and the accompanying journal paper.

## Verification legend

Every number has a source. The "Verified?" column says how the value was checked.

| Code | Meaning |
|---|---|
| **V-text** | Read directly in the primary source: the full-text PDF, an official web page, or a published table. |
| **V-abs** | Read in the primary source's abstract or landing page only. |
| **V-fig** | Read off a figure in the primary full text. Treat as approximately ±10 %. |
| **V-sec** | Confirmed in a secondary source that quotes the primary, such as a later paper or a reference implementation's code. |
| **Derived** | Calculated here from verified inputs. The formula is shown. |
| **Unverified** | From memory or a search snippet only. Check before using in code or the paper. |

Corrections to the original brief, and other inconsistencies found in the sources, are marked **⚠**.

---

## 1. Mars solar geometry (Allison & McEwen 2000; NASA GISS Mars24)

Primary references:
- Allison & McEwen (2000), *Planet. Space Sci.* 48, 215–235, doi:10.1016/S0032-0633(99)00092-6. Citation confirmed via Crossref.
- The algorithm and coefficients below are from the NASA GISS Mars24 "Technical Notes on Mars Solar Time" page, https://www.giss.nasa.gov/tools/mars24/help/algorithm.html. **V-text**, fetched 2026-11-08.

### 1.1 Algorithm steps

Δt is in days since J2000 on the TT scale. All angles are in degrees.

| Step | Quantity | Equation (Mars24 / AM2000) |
|---|---|---|
| A-1/A-2 | Julian Date (UT) | JD_UT = 2440587.5 + millis/(8.64×10⁷) |
| A-4 | TT − UTC | After 1972: leap seconds (TAI−UTC) + 32.184 s. Mars24 includes leap seconds through 2016-12-31, giving 69.184 s. Before 1972: 64.184 + 59T − 51.2T² − 67.1T³ − 16.4T⁴, with T = (JD_UT − 2451545.0)/36525. |
| A-5/A-6 | Δt_J2000 | JD_TT = JD_UT + (TT−UTC)/86400; Δt = JD_TT − 2451545.0 |
| B-1 | Mean anomaly | M = 19.3871 + 0.52402073 Δt |
| B-2 | Fictitious Mean Sun angle | α_FMS = 270.3871 + 0.524038496 Δt |
| B-3 | Perturbers | PBS = Σᵢ₌₁⁷ Aᵢ cos[(0.985626 Δt/τᵢ) + φᵢ]. Here 0.985626° = 360°/365.25. |
| B-4 | Equation of center | ν − M = (10.691 + 3.0×10⁻⁷ Δt) sin M + 0.623 sin 2M + 0.050 sin 3M + 0.005 sin 4M + 0.0005 sin 5M + PBS |
| B-5 | Areocentric solar longitude | Ls = α_FMS + (ν − M) |
| C-1 | Equation of time (degrees; ÷15 for hours) | EOT = 2.861 sin 2Ls − 0.071 sin 4Ls + 0.002 sin 6Ls − (ν − M) |
| C-2 | Mars Coordinated Time / Airy Mean Time | MST = mod₂₄{24 h × [(JD_TT − 2451549.5)/1.0274912517 + 44796.0 − 0.0009626]} |
| C-3 | Local mean solar time | LMST = mod₂₄{MST − Λ/15}, where Λ is **west** longitude in degrees |
| C-4 | Local true solar time | LTST = LMST + EOT/15 |
| C-5 | Subsolar longitude | Λs = 15·MST + EOT + 180 |
| D-1 | Solar declination (planetographic) | δs = arcsin(0.42565 sin Ls) + 0.25 sin Ls |
| D-2 | Heliocentric distance (AU) | r = 1.52367934 × (1.00436 − 0.09309 cos M − 0.004336 cos 2M − 0.00031 cos 3M − 0.00003 cos 4M) |
| D-3 | Heliocentric longitude | l = Ls + 85.061 − 0.015 sin(71 + 2Ls) − 5.5×10⁻⁶ Δt |
| D-4 | Heliocentric latitude | b = −(1.8497 − 2.23×10⁻⁵ Δt) sin(Ls − 144.50 + 2.57×10⁻⁶ Δt) |
| D-5 | Solar zenith angle | Z = arccos(sin δs sin φ + cos δs cos φ cos H), with H = Λ − Λs (hour angle, west longitudes) |
| D-6 | Solar azimuth | A = atan2(sin H, cos φ tan δs − sin φ cos H) |

### 1.2 Perturbation terms (Mars24 page)

| i | Aᵢ (deg) | τᵢ (Julian years) | φᵢ (deg) |
|---|---|---|---|
| 1 | 0.0071 | 2.2353 | 49.409 |
| 2 | 0.0057 | 2.7543 | 168.173 |
| 3 | 0.0039 | 1.1177 | 191.837 |
| 4 | 0.0037 | 15.7866 | 21.736 |
| 5 | 0.0021 | 2.1354 | 15.704 |
| 6 | 0.0020 | 2.4694 | 95.528 |
| 7 | 0.0018 | 32.8493 | 49.095 |

All values are **V-text**, from the Mars24 page.

⚠ Some implementations round Aᵢ to 0.007, 0.006, 0.004, 0.004, 0.002, 0.002, 0.002 (Schorghofer, Planetary-Code-Collection `Mars/marsorbit.f90`, which cites AM2000). Use the 4-decimal Mars24 values above. The difference is ≤ 0.0005° in Ls.

### 1.3 Mars24 worked examples (unit-test reference values; V-text)

| Quantity | Example 1: 2000-01-06 00:00 UTC, 0°W 0°N | Example 2: MER-A Spirit, 2004-01-04 13:46:31 UTC, 184.702°W 14.640°N |
|---|---|---|
| millis | 947116800000 | 1073137591000 |
| JD_TT | 2451549.50074 | 2453008.07471 |
| Δt_J2000 | 4.50074 | 1463.07471 |
| M | 21.74558 | 66.06858 |
| α_FMS | 272.74566 | 317.09457 |
| PBS | 0.00142 | 0.01614 |
| ν − M | 4.44193 | 10.22959 |
| Ls | 277.18758 | 327.32416 |
| EOT (deg) | −5.18774 | −12.77553 |
| MST (h) | 23.99425 | 13.16537 |
| LMST (h) | 23.99425 | 0.85190 |
| LTST (h) | 23.64840 | 0.00025 |
| Subsolar longitude Λs | 174.72600 | 4.70500 |
| δs | −25.22825 | −13.42065 |
| r (AU) | 1.39358 | 1.47767 |
| l, b | 2.26352, −1.35957 | 52.37564, 0.08965 |
| Z, A | 154.26182, 191.03905 | 151.93895, 179.99383 |

Both examples use TT − UTC = 64.184 s.

### 1.4 Mars constants

| Quantity | Value | Source | Verified? |
|---|---|---|---|
| Mean solar day (sol) | 1.0274912517 d = **88775.244 s** (24 h 39 m 35.244 s) | Mars24 C-2 divisor × 86400 | V-text / Derived |
| Length of day | 24.6597 h | NSSDC Mars Fact Sheet, https://nssdc.gsfc.nasa.gov/planetary/factsheet/marsfact.html | V-text |
| Sidereal rotation period | 24.6229 h | NSSDC | V-text |
| Obliquity | **25.19°** (arcsin 0.42565 = 25.1918°) | NSSDC; AM2000 D-1 | V-text / Derived |
| Sidereal orbital period | 686.980 d | NSSDC | V-text |
| Semimajor axis | 227.956×10⁶ km = 1.52367934 AU (AM2000 D-2) | NSSDC; Mars24 | V-text |
| Eccentricity | 0.0935 (NSSDC); 0.093377 (Appelbaum) | NSSDC; Appelbaum & Landis 1991 | V-text |
| Solar irradiance at mean distance | **586.2 W/m²**. Check: 1361/1.52368² = 586.2. | NSSDC; Derived | V-text |
| Range over orbit | ≈ 492 W/m² (aphelion, 1.666 AU) to ≈ 717 W/m² (perihelion, 1.381 AU) | Derived from a(1±e), S = 1361 | Derived |
| Surface gravity | NSSDC: 3.73 m/s². Commonly cited mean: 3.721 m/s². GM/R² = 42828.37 km³s⁻²/(3389.5 km)² = 3.728 m/s² without rotation; centrifugal correction at the equator is ≈ 0.017 m/s². | NSSDC; Derived | 3.73 V-text; **3.721 Unverified** (no primary source located) |

**Recommendation:** use g = 3.71 m/s² as the equatorial value, or 3.72–3.73 m/s² as the mean, and cite NSSDC.

⚠ Older Appelbaum papers use S = 1371 W/m², a mean distance of 1.5236915 AU giving a mean beam of 590 W/m², obliquity δ₀ = 24.936°, and sin δ = sin δ₀ sin Ls (TM-105216 Eqs. 5–13; V-text). For geometry, use AM2000. If you want to reproduce Appelbaum's published figures, use 590 W/m² only for that.

---

## 2. Moon solar geometry and global constants

| Quantity | Value | Source | Verified? |
|---|---|---|---|
| Synodic month (mean) | **29.530589 d** (Espenak: 29.53059 d = 29 d 12 h 44 m 03 s) | NASA GSFC eclipse site, https://eclipse.gsfc.nasa.gov/help/moonorbit.html | V-text (to 5 decimals) |
| Synodic day used in Hayne thermal model | P = 2.55024×10⁶ s (= 29.5306 d) | Hayne et al. 2017, Table A1 | V-text |
| Sidereal month | 27.32166 d | NASA eclipse site | V-text |
| Draconic month | 27.21222 d | NASA eclipse site | V-text |
| Nodal regression period | 18.6 yr (6793.48 d) | NASA eclipse site | V-text |
| Orbit inclination to ecliptic | 5.145° | NASA eclipse site; NSSDC Moon fact sheet | V-text |
| Lunar mean equator inclination to ecliptic | **I = 1.54242°** (1°32′32.7″). Meeus constant 0.0269203 rad = 1.54242°. | Meeus (1998) *Astronomical Algorithms*, 2nd ed., ch. 53, p. 372, as coded in libTheSky (`moon_routines.f90`) | V-sec |
| ⚠ Variant used by heat1d | 0.026878 rad (= 1.540°) | phayne/heat1d `planets.py` | V-text (code) |
| Eclipse (draconic) year | **346.620 d**. Sun's return to the lunar node: 1/(1/365.25636 + 1/6793.48) = 346.620 d. | Derived from the NASA regression period | Derived |
| Subsolar (selenographic) latitude | Varies between about ±1.54° with the eclipse-year period of 346.62 d. By Cassini's laws the lunar equator's descending node coincides with the orbit's ascending node, so the Sun's selenographic latitude ≈ I·sin(λ☉ − Ω) (sign set by convention), plus small libration terms. | Cassini's laws; Meeus ch. 53 | Derived (approximate form) |
| Bond albedo (global) | 0.11 | NSSDC Moon fact sheet, https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html | V-text |
| Geometric albedo | 0.12 | NSSDC | V-text |
| Normal-incidence bolometric Bond albedo used in thermal models | A₀ = 0.12 (lunar average) | Hayne et al. 2017, Table A1, citing Vasavada et al. 2012 | V-text |
| Total solar irradiance at 1 AU | **1361 W/m²**. Kopp & Lean (2011) give 1360.8 ± 0.5 W/m². | Kopp & Lean 2011, GRL 38, L01706, doi:10.1029/2010GL045777; NSSDC uses 1361.0 | Citation V (Crossref); 1361 V-text (NSSDC, Hayne); 1360.8 ± 0.5 V-sec |
| Surface gravity | 1.62 m/s² | NSSDC | V-text |
| Equatorial surface temperature range | 95 K to 390 K | NSSDC | V-text |

---

## 3. Mars atmospheric radiative transfer at the surface

### 3.1 Appelbaum model equations

Sources:
- Appelbaum & Landis, NASA TM-105216 (1991), https://ntrs.nasa.gov/citations/19910023732. Full scanned PDF read: **V-text**.
- Journal version: Appelbaum, Landis & Sherman (1993), *Solar Energy* 50(1), 35–51, doi:10.1016/0038-092X(93)90006-A.
- Original model: Appelbaum & Flood (1990), *Solar Energy* 45(6), 353–363, doi:10.1016/0038-092X(90)90156-7.

| Eq. (TM-105216) | Relation |
|---|---|
| (5)–(8) | Top-of-atmosphere beam: G_ob = S/r². With S = 1371 W/m² and a mean distance of 1.5236915 AU, G_ob = 590 [1 + e cos(Ls − 248°)]² / (1 − e²)², with e = 0.093377. Perihelion is at Ls = 248°. |
| (10)–(11) | Beer–Lambert direct beam at normal incidence: G_b = G_ob exp[−τ m(z)], with m(z) ≈ 1/cos z. Valid up to z ≈ 80°. |
| (19) | Global irradiance on a horizontal surface: **G_h = G_ob cos z · f(z,τ,al)/(1 − al)** |
| (21) | Beam irradiance on a horizontal surface: **G_bh = G_ob cos z · exp(−τ/cos z)** |
| — | Diffuse irradiance: **G_dh = G_h − G_bh** |
| (3) | Albedo during dust storms: al = max{al_T, min(0.18τ, 0.4)}. Mean Mars albedo is 0.27 and the maximum is 0.4. |
| (20) | Polynomial fit to f: f(z,τ,al) = [Σᵢ₌₀⁵ Σⱼ₌₀⁵ Σₖ₌₀¹ p(i,j,k) τⁱ (z/100)ʲ alᵏ](1 − al). Mean error 0.7 %, maximum about 7 % (at z ≥ 80° and τ > 5). The p coefficients are in TM-105216 Table V, not transcribed here. |
| Note | For albedo between 0.1 and 0.4, interpolate f linearly between Tables III and IV. |

The diffuse fraction is G_dh/G_h = 1 − exp(−τ/cos z)(1 − al)/f(z,τ,al).
- At VL1 the diffuse fraction is about 50 % of daily insolation in low-τ spring and summer, and about 90 % in high-τ autumn and winter (TM-105216 p. 15; V-text).
- Worked example (Derived): z = 0°, τ = 0.5, al = 0.1. f = 0.813 gives G_h/G_ob = 0.903 and G_bh/G_ob = 0.607, so the diffuse fraction is 0.33.

### 3.2 Normalized net flux function f(z, τ, al): selected values

Source: TM-105216 Tables III(a,b) (al = 0.1) and IV(a,b) (al = 0.4), read from the scanned pages. These are **V-text**.

The full grid also exists as a machine-readable transcription in the marsrad R package (github.com/georgeslabreche/marsrad, `data-raw/csv/netflux_al_0-1_table_iii_1991_update.csv` and `netflux_al_0-4_table_iii_1991_update.csv`). It covers τ = 0.1–6 in steps of 0.05–0.5 and z = 0–85° in 5° steps. The values were cross-checked against the scan.

**al = 0.1 (Table III)**

| τ \ z | 0° | 30° | 60° | 80° |
|---|---|---|---|---|
| 0.1 | 0.883 | 0.879 | 0.855 | 0.757 |
| 0.5 | 0.813 | 0.793 | 0.701 | 0.462 |
| 1.0 | 0.728 | 0.694 | 0.557 | 0.324 |
| 2.0 | 0.578 | 0.532 | 0.413 | 0.217 |
| 3.0 | 0.457 | 0.411 | 0.301 | 0.162 |
| 5.0 | 0.289 | 0.253 | 0.162 | 0.101 |
| 6.0 | 0.229 | 0.200 | 0.128 | 0.081 |

**al = 0.4 (Table IV)**

| τ \ z | 0° | 30° | 60° | 80° |
|---|---|---|---|---|
| 0.1 | 0.596 | 0.590 | 0.575 | 0.509 |
| 0.5 | 0.560 | 0.546 | 0.483 | 0.318 |
| 1.0 | 0.511 | 0.488 | 0.392 | 0.228 |
| 2.0 | 0.417 | 0.384 | 0.273 | 0.158 |
| 3.0 | 0.336 | 0.303 | 0.202 | 0.121 |

⚠ **Data-quality notes for the code**
1. The marsrad CSV has a transcription error at τ = 2.2, z = 10°: it gives 0.549, but the scan shows 0.545.
2. The original Table III(b) prints 0.339 at τ = 2.10, z = 55°. That is non-monotonic; the neighbours are 0.431 at 50° and 0.364 at 60°. It is almost certainly a typo for about 0.389. Interpolate rather than use it.
3. The older v1 table (marsrad "lookup_v1", attributed to TM-102299 / Appelbaum & Flood 1990) differs by up to about 0.01. Examples: τ = 1, z = 0 gives 0.732 vs 0.728; τ = 0.5, z = 80 gives 0.452 vs 0.462. Use the 1991 update.

### 3.3 Dust optical depth (visible, approximately 880 nm)

| Site / season | τ | Source | Verified? |
|---|---|---|---|
| Viking Landers, non-storm | ≈ 0.5 typical | TM-105216 §2 | V-text |
| Jezero, aphelion season (Ls 6–150°, MY36) | ≈ 0.3–0.6, mostly 0.35–0.5 | Martínez et al. 2023, Fig. 3a, doi:10.1029/2022JE007537 | V-fig |
| Jezero, Ls 150–241° (dusty season onset) | ≈ 0.7–1.3 | Sánchez-Lavega et al. 2023, Fig. 8, doi:10.1029/2022JE007480 | V-fig |
| Jezero regional storm, Jan 2022 (Ls 153–156°) | peak **≈ 2**; winds up to 20 m/s | Lemmon et al. 2022, GRL 49, e2022GL100126, doi:10.1029/2022GL100126 | V-abs |
| Gale, aphelion minimum | ≈ 0.35–0.5 (minimum ≈ 0.35 near Ls 120–135°) | Lemmon et al. 2024, Icarus 408, 115821, doi:10.1016/j.icarus.2023.115821 | V-text + V-fig |
| Gale, perihelion season | ≈ 0.8–1.5 typical; regional-storm peaks ≈ 1.7–2.2 (Ls ≈ 235°, 320°) | Lemmon et al. 2024, Fig. 4 | V-fig |
| Gale, 2018 / MY34 global dust storm | **τ(880 nm) = 8.5** (peak). UV −97 %. Diurnal air-temperature range reduced by 30 K. | Guzewich et al. 2019, GRL 46, 71–79, doi:10.1029/2018GL080839 | V-abs |
| Opportunity (Perseverance Valley), MY34 storm | **τ ≈ 10.8** (10 June 2018, sol 5111) | NASA/JPL PIA22930, https://www.jpl.nasa.gov/images/pia22930-last-images-opportunity-took/ | V-text |
| MER early mission | τ ≈ 0.9 at both sites | Lemmon et al. 2004, Science 306, 1753, doi:10.1126/science.1104474 | V-abs |

⚠ Lemmon et al. 2015 (Icarus 251, 96–111, doi:10.1016/j.icarus.2014.03.029) is the **MER** (Spirit and Opportunity) record, not Gale. The Gale/MSL record is Lemmon et al. 2024.

**Design-τ scenarios (suggested)**

| Scenario | τ |
|---|---|
| Clear | 0.4 |
| Typical dusty season | 1.0 |
| Regional storm | 2 |
| Global storm (Gale-type) | 5–8.5 |
| Extreme (Opportunity-type) | 10.8 |

### 3.4 Dust optical properties (visible)

| Quantity | Value | Source | Verified? |
|---|---|---|---|
| Single-scattering albedo ω₀ (~650 nm), representative of Wolff et al. 2009 | 0.975 | Chen-Chen et al. 2019, Icarus 330, 16–29, doi:10.1016/j.icarus.2019.04.004 | V-sec |
| ω₀ range at 880 nm from CRISM, as given in the brief | 0.93–0.97, or ≈ 0.97–0.98 | Wolff et al. 2009, JGR 114, E00D04, doi:10.1029/2009JE003350 | **Unverified** (paper not accessible) |
| ω₀, alternative (Pathfinder) | 0.94 | Tomasko et al. 1999, as used in Chen-Chen 2019 | V-sec |
| Asymmetry parameter g (650 nm) | 0.673 ± 0.081 (published); 0.687 in the arXiv version. Consistent with Wolff 2009. | Chen-Chen et al. 2019 | V-abs / V-text (preprint) |
| g, 0.63–0.68 range from the brief | — | Wolff et al. 2009 | **Unverified** |
| Effective radius r_eff | ≈ 1.5 µm (MER); 1.8 µm (CRISM, 2007 storm); 1.4 µm (diffuse dust) | Lemmon et al. 2004 (V-abs); Wolff 2009 abstract (V-sec, snippet) | as noted |
| Visible extinction / 9 µm opacity ratio | ≈ 2 (MER); 1.8 (Jezero, used to scale TIRS τ); 2.6 (τ_ext,vis/τ_abs,9.3µm; TES climatology) | Lemmon 2004 (V-abs); Martínez 2023 (V-text); Montabone et al. 2015, Icarus 251, 65–95, doi:10.1016/j.icarus.2014.12.034 (**Unverified**) | as noted |

---

## 4. Mars near-surface meteorology (MEDA at Jezero; REMS at Gale)

### 4.1 Jezero (Perseverance / MEDA, MY36)

| Quantity | Value | Source | Verified? |
|---|---|---|---|
| Daily-mean surface pressure | 735 Pa (Ls 13–16°) → max **761 Pa** (Ls ≈ 55°) → min **≈ 625 Pa** (Ls ≈ 150°) → ≈ 790 Pa (Ls 241°) | Sánchez-Lavega et al. 2023, JGR Planets 128, e2022JE007480, doi:10.1029/2022JE007480 | V-text |
| Diurnal pressure peak-to-peak | ≈ 20 Pa (aphelion), rising to ≈ 50 Pa in the dusty season. Maximum at 07–08 LMST, minimum at 12–16 LMST. | Sánchez-Lavega et al. 2023 | V-text |
| Ground temperature, daily max / min | ≈ 265–290 K / ≈ 183–205 K (Ls 6–174°) | Martínez et al. 2023, Fig. 3c, doi:10.1029/2022JE007537 | V-fig |
| Ground diurnal amplitude | ≈ 87 K (TI 230); ≈ 56 K (TI 525) | Martínez et al. 2023 §4.1 | V-text |
| Air temperature at 1.45 m, daily max / min | ≈ 240–262 K / ≈ 188–197 K, giving a diurnal range of ≈ 45–65 K | Martínez et al. 2023, Fig. 3e | V-fig |
| Air density at 1.45 m | ≈ 0.012–0.021 kg/m³ | Martínez et al. 2023, Fig. 3f | V-fig |
| Wind speed | Mean 3.2 ± 2.3 m/s at 1.5 m. Afternoon peak 6.1 ± 2.2 m/s. 99 % of samples < 10 m/s. Up to 20 m/s in the Jan 2022 storm. | Viúdez-Moreiras et al. 2022, JGR Planets 127, e2022JE007522, doi:10.1029/2022JE007522 (summary values via Jackson et al. 2024, arXiv:2410.19132); Lemmon 2022 | V-sec |
| Daily max relative humidity at 1.45 m | ≈ 5–43 % | Martínez et al. 2023, Fig. 3g | V-fig |
| Overview | — | Rodríguez-Manfredi et al. 2023, Nat. Geosci. 16, 19–28, doi:10.1038/s41561-022-01084-0 | V-abs |

### 4.2 Gale (Curiosity / REMS)

| Quantity | Value | Source | Verified? |
|---|---|---|---|
| Daily-mean pressure | ≈ 700 to ≈ 925 Pa. Absolute max at Ls 240–270°, minimum at Ls ≈ 150°. MY31–37. | Ruíz et al. 2025, Remote Sens. 17, 368, doi:10.3390/rs17030368 | V-text |
| Diurnal pressure | ±60 Pa about the mean. Early-mission drop of 85 Pa between 08:00 and 16:00 (11 % of 775 Pa). | Ruíz 2025 (V-text); Haberle et al. 2014, JGR Planets 119, 440–453, doi:10.1002/2013JE004488 (V-sec) | as noted |
| Daily temperature extremes | Max ≈ 275 K (Ls 180–210°); min ≈ 185 K (Ls ≈ 90°) | Ruíz et al. 2025 | V-text |
| Air temperature diurnal swing | > 55 K typical. Reduced by 30 K in the MY34 storm. | NASA PIA20600; Guzewich 2019 | V-text / V-abs |
| Winds | Not obtained. The REMS boom was damaged at landing. | — | — |
| Planet-wide context | Pressure 6.36 mb at mean radius (4.0–8.7 mb seasonal). Surface density ≈ 0.016 ± 0.006 kg/m³. Viking winds 2–7 m/s (summer), 5–10 m/s (fall), 17–30 m/s (storm). | NSSDC Mars fact sheet | V-text |

### 4.3 Downwelling longwave (IR) flux at the surface

| Quantity | Value | Source | Verified? |
|---|---|---|---|
| MEDA/TIRS instrument | IR1 channel 6.5–30 µm, extended to 5–80 µm; accuracy < 6.9 W/m² | Martínez et al. 2023, Table 1 | V-text |
| LW↓ daily mean, Jezero | **≈ 30 W/m²** (Ls 20–150°), rising to **≈ 40 W/m²** (Ls 150–180°) | Martínez et al. 2023 | V-text |
| LW↓ diurnal range, aphelion | Min ≈ 20–25 W/m² (04–06 LMST); max ≈ 35–45 W/m² (13–16 LMST) | Martínez et al. 2023, Fig. 8c | V-fig |
| LW↓ during the Jan 2022 storm | Max ≈ 70 W/m² | Martínez et al. 2023 | V-fig |
| LW↓ vs opacity | τ(9 µm) 0.3–0.6 gives 35–52 W/m²; τ(9 µm) 0.1–0.3 gives 27–42 W/m² (same air temperature) | Martínez et al. 2023, Fig. 11 | V-fig |
| LW↓ daily mean, Gale (REMS-derived) | 20–40 W/m² (Ls 20–150°); 40–60 W/m² (Ls 150–180°) | Martínez et al. 2021, JGR Planets 126, e2020JE006804, doi:10.1029/2020JE006804, as quoted in Martínez 2023 | V-sec |
| Other Jezero energy-budget terms | SW↓ daily max ≈ 440–545 W/m². LW↑ max ≈ 290–390 W/m², min ≈ 75–95 W/m². Sensible heat flux daily max ≈ 5–28 W/m². Latent heat flux ≲ a few tenths of a W/m². | Martínez et al. 2023, Fig. 8 | V-fig / V-text |
| Constants used by Martínez 2023 | cp = 736 J kg⁻¹K⁻¹; R = 191 J kg⁻¹K⁻¹; z₀ = 1 cm; regolith ρc = 1.2×10⁶ J m⁻³K⁻¹ | Martínez et al. 2023 | V-text |

**Parameterizations of LW↓**

| Approach | Form | Source | Verified? |
|---|---|---|---|
| Fraction of noon insolation (Viking-era) | LW↓ = 0.02 × noon insolation, constant over the sol. Schorghofer's code: `Qlw = fracIR*max(Qo*sinbetaNoon, σ·150⁴)`. | Kieffer et al. 1977, JGR 82, 4249–4291, doi:10.1029/JS082i028p04249 (V-sec via Hayashi et al. 1994, NTRS 19940031630); Schorghofer `flux_mars.f90` (V-text, code) | V-sec |
| ⚠ KRC (Kieffer 2013) | **Not** a fixed 2 %. Uses a one-layer atmosphere, grey in both solar and IR, with a Delta-Eddington solar treatment. Inputs: TAUD, TAURAT (thermal/visible opacity), CABR (IR opacity of the dust-free atmosphere), DUSTA (single-scattering albedo), ARC2 (Henyey–Greenstein g). Output: DOWNIR. | Kieffer 2013, JGR Planets 118, 451–470, doi:10.1029/2012JE004164; KRC helplist (V-text) | V-text (helplist) |
| Effective sky emissivity (this work) | ε_sky = LW↓/(σT_a⁴) ≈ 0.15–0.30 in clear aphelion conditions (LW↓ 20–45 W/m², T_a 190–250 K). Increases with dust; LW↓ roughly doubles from τ_vis ≈ 0.4 to ≈ 2. | Derived from the Martínez 2023 values | Derived |

**Model recommendation:** for an engineering-grade engine, use LW↓ = ε_sky(τ)·σT_a⁴ with ε_sky ≈ 0.2 at τ = 0.4, scaling to ≈ 0.4 at τ ≈ 2. Calibrate against the MEDA daily-mean values of 30–40 W/m². Keep the Kieffer 2 %-of-noon option for comparison.

---

## 5. Mars regolith thermophysics and CO₂ gas properties

### 5.1 Regolith

| Quantity | Value | Source | Verified? |
|---|---|---|---|
| Thermal inertia, Jezero traverse | **180 (sand) to 605 (bedrock)** J m⁻²K⁻¹s⁻¹ᐟ². Mean 350 (THEMIS gives 330). About 10 % uncertainty. | Martínez et al. 2023, doi:10.1029/2022JE007537 | V-text |
| Thermal inertia, Gale (REMS) | 170–610 | Martínez et al. 2023 (comparison section) | V-text |
| Thermal inertia, global Mars maps | 5–5000 tiu lookup range. Low-TI unit < 175 poleward of 65°S. | Putzig & Mellon 2007, Icarus 191, 68–94, doi:10.1016/j.icarus.2007.05.013 | V-abs |
| **Default for code** | TI ≈ 250–350 (typical); 200–400 sensitivity range | Martínez 2023; Putzig & Mellon 2007 | Derived recommendation |
| Volumetric heat capacity ρc | **1.2×10⁶ J m⁻³K⁻¹** | Martínez et al. 2023 | V-text |
| Thermal conductivity, InSight soil (0.03–0.37 m) | **0.039 ± 0.002 W m⁻¹K⁻¹**. Porosity ≈ 60 %; grains mostly < 100–170 µm. | Grott et al. 2021, JGR Planets 126, e2021JE006861, doi:10.1029/2021JE006861 | V-sec (search abstract) |
| Bulk density | ≈ 1200–1600 kg/m³ typical; InSight ≈ 1211 kg/m³ | Various | **Unverified** (1211 not confirmed) |
| Specific heat | ≈ 630–840 J kg⁻¹K⁻¹. For basalt it rises about 75 % between 150 K and 315 K. Approximation: use ρc = 1.2×10⁶ with ρ ≈ 1500 kg/m³, giving c ≈ 800 J kg⁻¹K⁻¹. | Piqueux & Christensen 2011, JGR 116, E07004, doi:10.1029/2011JE003805 (V-abs for the 75 % trend) | Range **Unverified**; trend V-abs |
| Broadband albedo, Jezero | **0.14** (traverse mean at ~14:00; range 0.093–0.18). TES gives 0.147. Non-Lambertian: higher at low sun. | Martínez et al. 2023 | V-text |
| Albedo, other sites | Gale 0.06–0.28; InSight 0.16; MER 0.11–0.24. Planet: Bond 0.250, geometric 0.170 (NSSDC). Appelbaum mean 0.27. | Martínez 2023; NSSDC; TM-105216 | V-text |
| IR emissivity | ≈ 0.95–1.0. heat1d uses 0.95 for Mars; KRC uses a user-set EMIS. | heat1d `planets.py` (V-text, code) | Typical value **Unverified** for Jezero |

### 5.2 CO₂ gas properties at 600 Pa

Source: NIST WebBook (Span–Wagner EOS), https://webbook.nist.gov/cgi/fluid.cgi?ID=C124389&Type=IsoBar&P=0.0006. All rows **V-text**.

| T (K) | ρ (kg/m³) | cp (J kg⁻¹K⁻¹) | μ (Pa·s) | k (W m⁻¹K⁻¹) | Pr |
|---|---|---|---|---|---|
| 216.59 | 0.014664 | 754.0 | 1.0951×10⁻⁵ | 0.010665 | 0.774 |
| 220 | 0.014437 | 757.8 | 1.1118×10⁻⁵ | 0.010894 | 0.773 |
| 230 | 0.013809 | 769.1 | 1.1606×10⁻⁵ | 0.011577 | 0.771 |
| 240 | 0.013234 | 780.4 | 1.2094×10⁻⁵ | 0.012276 | 0.769 |
| 250 | 0.012704 | 791.7 | 1.2581×10⁻⁵ | 0.012989 | 0.767 |
| 260 | 0.012215 | 802.8 | 1.3067×10⁻⁵ | 0.013714 | — |
| 280 | 0.011343 | 824.7 | 1.4034×10⁻⁵ | 0.015198 | — |
| 300 | 0.010587 | 845.9 | 1.4994×10⁻⁵ | 0.016720 | — |

Notes:
- NIST gives no data below the triple-point temperature of 216.59 K. Extrapolate μ and k roughly linearly in T, and use the ideal gas law for ρ.
- The Mars atmosphere is 95.1 % CO₂, 2.59 % N₂, 1.94 % Ar, mean molar mass 43.49 g/mol, scale height 11.0 km (NSSDC; V-text).
- Gas constant R = 191 J kg⁻¹K⁻¹ (Martínez 2023).
- Mars gravity: see §1.4.

---

## 6. Lunar regolith thermophysical model (Hayne et al. 2017) and polar illumination

Source: Hayne et al. 2017, JGR Planets 122(12), 2371–2400, doi:10.1002/2017JE005387 (arXiv:1711.00977). Appendix A and Tables A1/A2 were read from the full text: **V-text**. The same values are coded in the reference implementation github.com/phayne/heat1d (`python/heat1d/planets.py`).

### 6.1 Model equations

| Eq. | Relation |
|---|---|
| Density | ρ(z) = ρ_d − (ρ_d − ρ_s) exp(−z/H) |
| (A5) Contact conductivity | K_c(ρ) = K_d − (K_d − K_s)(ρ_d − ρ)/(ρ_d − ρ_s). Equivalent to the same exponential form in z. |
| (A4) Total conductivity | K = K_c [1 + χ (T/350)³] |
| (A6) Specific heat | c_p(T) = c₀ + c₁T + c₂T² + c₃T³ + c₄T⁴. Valid from < 90 K to > 400 K; negative below 1.3 K. |
| (A7) Surface boundary condition | K ∂T/∂z\|₀ + Q_s = εσT_s⁴, with Q_s = (1 − A)F |
| (A8) Albedo | A(θ) = A₀ + a(θ/(π/4))³ + b(θ/(π/2))⁸ |
| (A12) Lower boundary | ∂T/∂z = Q_b/K |

### 6.2 Parameters (Table A1)

| Parameter | Value | Verified? |
|---|---|---|
| Solar constant S | 1361 W/m² (Kopp & Lean 2011) | V-text |
| Synodic period P | 2.55024×10⁶ s | V-text |
| IR emissivity ε | **0.95** | V-text |
| Normal-incidence Bond albedo A₀ | **0.12** (lunar average) | V-text |
| Albedo coefficients a, b | **a = 0.06, b = 0.25** | V-text |
| Surface contact conductivity K_s | **7.4×10⁻⁴ W m⁻¹K⁻¹** | V-text |
| Deep contact conductivity K_d | **3.4×10⁻³ W m⁻¹K⁻¹** | V-text |
| Radiative conductivity parameter χ | **2.7** | V-text |
| Surface density ρ_s | **1100 kg/m³** | V-text |
| Deep density ρ_d | **1800 kg/m³** | V-text |
| H-parameter | **0 to > 0.2 m, global average 0.06 m**. ⚠ heat1d's default is 0.07 m. | V-text |
| c₀ | −3.6125 J kg⁻¹K⁻¹ | V-text |
| c₁ | +2.7431 J kg⁻¹K⁻² | V-text |
| c₂ | +2.3616×10⁻³ J kg⁻¹K⁻³ | V-text |
| c₃ | −1.2340×10⁻⁵ J kg⁻¹K⁻⁴ | V-text |
| c₄ | +8.9093×10⁻⁹ J kg⁻¹K⁻⁵ | V-text |
| Polynomial data sources | Hemingway et al. 1981; Ledlow et al. 1992 | V-text |
| Interior (geothermal) heat flow Q_b | **0.018 W/m²** (Langseth et al. 1976) | V-text |
| Thermal inertia, global average | **55 ± 2 J m⁻²K⁻¹s⁻¹ᐟ²** at 273 K (upper 4–7 cm). At the equator: 35 at midnight, 70 at noon. | V-text |
| Diurnal skin depth | ≈ 4.4 cm (large H) to ≈ 7 cm (H = 0) | V-text |

Check value (Derived): c_p(250 K) ≈ 672 J kg⁻¹K⁻¹.

### 6.3 Model constraints (Table A2) and observed temperatures

| Quantity | Value | Source | Verified? |
|---|---|---|---|
| Equatorial peak noon T_s | **385 K** (A₀ = 0.12) | Hayne Table A2, citing Vasavada et al. 2012, doi:10.1029/2011JE003987 | V-text |
| Equatorial midnight T_s | 101 K | Hayne Table A2 | V-text |
| Equatorial minimum (pre-dawn) T_s | **95 K** | Hayne Table A2 | V-text |
| Equatorial range (fact sheet) | 95–390 K | NSSDC | V-text |
| Diurnal-mean T, Apollo 15 (26°N) | Surface 211 K; **252 K at 83 cm** | Hayne Table A2, citing Keihm/Langseth | V-text |
| Diurnal-mean T, Apollo 17 (20°N) | Surface 216 K; **256 K at 130 cm** | Hayne Table A2 | V-text |
| **Equatorial T at ~1 m** | ≈ 250–260 K. Use 250–255 K at the equator; Apollo sites at 20–26° latitude show 252–256 K. | Hayne Table A2 (Apollo); heat1d `Moon.Tsavg = 250` | V-text (Apollo) / Derived (equator) |
| Measured conductivity at ~1 m | 7.0×10⁻³ (equatorial) and 0.9–1.3×10⁻² W m⁻¹K⁻¹ (> 50 cm) | Hayne Table A2 | V-text |
| Density at 0–30 cm | 1800–1900 kg/m³ (Apollo) | Hayne Table A2 | V-text |

### 6.4 South-pole illumination

| Quantity | Value | Source | Verified? |
|---|---|---|---|
| Shackleton rim (best point, LOLA 240 m DEM) | Continuously sunlit for **240 days each year**. Longest continuous darkness ≈ **1.5 days**. Small height gains (~10 m) improve illumination substantially. | Mazarico et al. 2011, Icarus 211(2), 1066–1081, doi:10.1016/j.icarus.2010.10.030 (NTRS 20120010094) | V-abs |
| PSR areas | 12,866 km² (north); 16,055 km² (south) | Mazarico et al. 2011 | V-abs |
| Best Connecting Ridge site (Shackleton–de Gerlache), 20 m/pixel DTM, 19-yr simulation | **92.27 %** of time sunlit at 2 m above ground; **95.65 %** at 10 m. Longest darkness typically **3–5 days**. | Gläser et al. 2014, Icarus 243, 78–90, doi:10.1016/j.icarus.2014.08.013 | V-sec (DLR repository abstract) |
| Mean-annual sunlit fraction at the Shackleton rim | ≈ 80–90 % is often quoted | — | **Unverified** (no primary figure located). Mazarico 2011 gives days, not a percentage. |
| NASA lunar surface habitat design eclipse | Up to ≈ 100 h of darkness | Schunk et al. 2021 TFAWS, https://ntrs.nasa.gov/citations/20210020015 | V-text |

---

## 7. Habitat and human loads (NASA BVAD; NASA-STD-3001)

Source: Anderson, Ewert & Keener (2018), *Life Support Baseline Values and Assumptions Document*, NASA/TP-2015-218570/REV1, https://ntrs.nasa.gov/citations/20180001338.

"Y (layout)" means the value was read in the source, but the PDF table layout was scrambled. Watts are derived as MJ/d ÷ 86400.

### 7.1 Crew metabolic loads (nominal crew member: 82 kg, RQ 0.92, includes exercise)

| Quantity | Value | Source | Verified? |
|---|---|---|---|
| Total metabolic heat | 12.00 MJ/CM-d = **138.9 W** | BVAD Table 3-33 | Y (layout); W Derived |
| Sensible | 7.35 MJ/CM-d = **85.1 W** | BVAD Table 3-33 | Y (layout) |
| Latent | 4.65 MJ/CM-d = **53.8 W** (h_fg = 2420 kJ/kg) | BVAD Table 3-33 | Y (layout) |
| Water vapour (respiration + perspiration) | **1.9 kg/CM-d**. Table 3-22 gives 1.85 kg vapour + 0.08 kg sweat. | BVAD Tables 3-33, 3-22 | Y |
| O₂ consumed / CO₂ produced | 0.816 / 1.04 kg/CM-d | BVAD Table 3-33 | Y (layout) |
| Hourly schedule (Table 3-22) | Sleep: 88 W total (62 sensible / 26 latent), 8 h. Awake nominal: 139 W (91 / 47), 14.5 h. Exercise at 75 % VO₂max: 1206–2974 kJ/h in 15-min steps. | BVAD Table 3-22 (HIDH 2014) | Y |
| Basis of Table 3-22 | Cabin 294.3 K, dew point 283.2 K, 0.152 m/s air speed, 70.3 kPa | BVAD p. 44 | Y |
| EVA average metabolic rate | 1055 kJ/h (293 W) | BVAD §4.6 | Y |

### 7.2 Cabin setpoints

| Quantity | Value | Source | Verified? |
|---|---|---|---|
| Air temperature | 291.15–300.15 K (**18–27 °C**); nominal 296 K. The brief's "18.3–26.7 °C" (65–80 °F) was not found in BVAD REV1. | BVAD Tables 4-78, 4-1 | Y |
| Relative humidity | **25–75 %**, nominal 40 % | BVAD Table 4-78 | Y |
| Dew point | 271–295 K | BVAD Table 4-78 | Y |
| Ventilation velocity | 0.076–0.61 m/s | BVAD Table 4-78 | Y |
| NASA-STD-3001 Vol 2 Rev C | Comfort envelope anchored at 18 °C / 75 % RH and 27 °C / 25 % RH. Performance zone 20–25 °C, 30–60 % RH. ppCO₂ ≤ 3 mmHg (1-h average). | NASA-STD-3001 Vol 2 Rev C (2022), [V2 6012/6013/6004] | Y |

### 7.3 Cabin pressure options

| Option | Total pressure | O₂ fraction | Source | Verified? |
|---|---|---|---|---|
| Earth-normal (ISS, transit) | 101.3 kPa (14.7 psia) | 21 % | BVAD p. 64 | Y |
| Intermediate | **70.3 kPa** (10.2 psia) | **26.5 %** | BVAD p. 64 | Y |
| EVA-intensive surface habitat | **56.5 kPa** (8.2 psia; BVAD prints "57 kPa") | **34 %** | BVAD p. 64; Norcross et al. 2013, NASA/TM-2013-217377 | Y |
| Original EAWG proposal | 55.2 kPa (8.0 psia) | 32 % | Norcross et al. 2013 | Y (abstract) |
| ISS operating band | 96.5–102.7 kPa | — | Schaezler et al. 2011, NTRS 20110012997 | Y |

### 7.4 Leakage

| Quantity | Value | Source | Verified? |
|---|---|---|---|
| Design leakage (BVAD) | 0 / **0.05** / 0.14 % of mass per day (low / nominal / high) | BVAD Table 4-1 | Y |
| Mars DRM module leakage | 0.15 kg/d per module | BVAD Table 4-91 | Y |
| ISS whole-station measured leak | ≈ 0.064 kg/d (2004) → ≈ 0.227 kg/d (2011). Planning value 0.227 kg/d. | Schaezler et al. 2011 | Y |
| Airlock gas loss | 10 % of N₂ mass per cycle (≈ 1 kg/cycle) | BVAD Tables 4-90/4-91 | Y |

### 7.5 Equipment loads

| Quantity | Value | Source | Verified? |
|---|---|---|---|
| ISS average system power | e.g. ECLSS 5.31 kW; TCS 8.72 kW; C&DH 4.08 kW | BVAD Table 3-2 | Y |
| NASA lunar surface habitat reference | 2–4 crew; 15 kW power and 15 kWt heat rejection; 2 kW at night; 70.3 kPa (10.2 psia); 175 m³ | Schunk et al. 2021 TFAWS | Y |
| Survive-the-night heat leak | ≈ 1.55 kW | Schunk et al. 2021 TFAWS | Y |

⚠ BVAD Table 4-1's "low" O₂ value (0.518 kg/CM-d) and CO₂ value (0.622 kg/CM-d) are inconsistent with RQ = 0.92. They are reported here as printed.

---

## 8. Heat rejection on the Moon; MLI and insulation in the Mars atmosphere

### 8.1 Lunar radiator environment

| Quantity | Value | Source | Verified? |
|---|---|---|---|
| Subsolar lunar surface IR | 1314 W/m² at perihelion. Night surface ≈ 100 K, emitting ≈ 5.2 W/m². Solar 1414 ± 7 W/m² (perihelion). | Garrison & Nguyen 2007, AIP Conf. Proc. 880, 35–42, doi:10.1063/1.2437438 (citing Gilmore 2002) | Y |
| Equivalent sink, horizontal radiator (sun overhead) | ≈ 278 K (500 °R). A horizontal radiator does not view the lunar surface. | Bien & Guentert 1969, NASA TM X-1729, NTRS 19690007893 | Y |
| Equivalent sink, vertical radiator (equator, noon) | **≈ 333–334 K** | Bien & Guentert 1969 | Y |
| Vertical sink with aluminized ground cover | ≈ 222 K | Bien & Guentert 1969 | Y |
| Parabolic shade | Sink lowered > 100 K (model) and 70 K (thermal-vacuum test) | Ewert, Graf & Keller 1995, SAE 951524, doi:10.4271/951524 | Y (abstract) |
| Vertical-panel fluid temperature needed at noon | ≈ 325 K for positive rejection | Ochoa 2013, NTRS 20130013573 | Y (abstract) |
| View factor, vertical plate to an infinite plane | 0.5 to ground, 0.5 to sky | Geometric identity | Derived |
| South-pole habitat radiator | 283 K fluid; worst-case lunar ground 217 K; 48 m² double-sided panels for 15 kWt | Schunk et al. 2021 TFAWS | Y |
| Horizontal OSR radiator capacity | 245 W/m² (subsolar) to 312 W/m² (dark side) | Garrison & Nguyen 2007 | Y |

### 8.2 Coatings

| Coating | α_s (beginning → end of life) | ε | Source | Verified? |
|---|---|---|---|---|
| Silver-Teflon | **0.07 → 0.14** | **0.80** | BVAD Table 4-77 (Conger & Clark 1997) | Y |
| Silver-Teflon, design value for a south-pole radiator | 0.10 | 0.85 | NTRS 20080014322 | Unverified |
| Aluminized Teflon | 0.12 → 0.20 | 0.80 | BVAD Table 4-77 | Y |
| A276 white paint | 0.28 → 0.36 | 0.87 → 0.90 | BVAD Table 4-77 | Y |
| Z-93 (LDEF/MISSE) | 0.14 → 0.13–0.15 | Unchanged | Finckenor, Pippin & Frey, NTRS 20080031037 | Y |
| Beta cloth | 0.26 (new); 0.4 (design assumption) | 0.90 | BVAD; Schunk 2021 | Y |
| OSR (quartz mirror) | ≈ 0.05 | 0.8 | Garrison & Nguyen 2007 | Y |
| Lunar dust effect | A monolayer raises α/ε by **3–4×**. Brushing recovers ≥ 80–90 %. | Gaier et al. 2008, NASA/TM-2008-215492; Gaier 2009, NASA/TM-2009-215647; Gaier et al. 2011, NASA/TM-2011-217231 | Y (abstracts) |

### 8.3 MLI and insulation

| Quantity | Value | Source | Verified? |
|---|---|---|---|
| MLI pressure requirement | < 10⁻⁵ torr. Above that, conductivity "quickly reverts" toward that of the gas. | Finckenor & Dooling 1999, NASA/TP-1999-209263, NTRS 19990047691 | Y |
| ε* used in thermal models | 0.007–0.015 (300 K zone); 0.03–0.06 (180 K); 0.05–0.10 (100 K) | Bae & Rodriguez-Ruiz 2019, TFAWS, NTRS 20190030285 | Y (layout) |
| ε*, ideal discrete-spacer MLI | 0.0077 (5 layers), 0.0038 (10), 0.0019 (20) | Bae & Rodriguez-Ruiz 2019 | Y (layout) |
| ε* ≈ 0.005–0.05, as given in the brief (Gilmore 2002) | — | Gilmore 2002 handbook | **Unverified** (not read) |
| MLI on Mars | "Almost useless in the cold environments of Mars" (at 6.4–7.5 torr) | Trevino & Orndoff 2000, 30th ICES, NTRS 20100042640 | Y |
| Fibrous insulation at Mars pressure | 10–15 mW m⁻¹K⁻¹. Best high-loft fibre 18 mW m⁻¹K⁻¹. Aerogel ≈ 8 mW m⁻¹K⁻¹ at ~50 torr. Shuttle EMU MLI in vacuum ≈ 1.6 mW m⁻¹K⁻¹. | Trevino & Orndoff 2000 | Y |
| Aerogel-insulated rover WEB structure in 10 torr CO₂ | 0.0163 (24 °C), 0.0126 (−27 °C), 0.0089 W m⁻¹K⁻¹ (−80 °C) | Hickey et al. 1995, SAE 951523, doi:10.4271/951523 | Y (abstract) |
| MSL CO₂-gap insulation | The ~8 torr CO₂ atmosphere is used as the insulator in engineered gaps, sized below the onset of convection | Bhandari et al. 2011, ICES, NTRS 20120013533 | Y (abstract) |
| Aerogel blanket in N₂ (293 / 78 K) | 1.5 mW m⁻¹K⁻¹ (high vacuum) → 12.3 mW m⁻¹K⁻¹ (760 torr) | Fesmire et al. 2017, IOP Conf. Ser. MSE 278, 012198, doi:10.1088/1757-899X/278/1/012198 | Y |
| MLI vs aerogel in simulated Mars CO₂ (10–10⁴ Pa) | Aerogel conductivity is lower than MLI's above 100 Pa | Scaccabarozzi et al. 2014, https://re.public.polimi.it/handle/11311/764520 | **Unverified** |

**Model recommendation:**
- **Moon:** model MLI with an effective emittance ε* of 0.005–0.03.
- **Mars:** do not model MLI as radiative. Treat it as a porous layer with k_eff ≈ 10–20 mW m⁻¹K⁻¹. The CO₂ gas conductivity limit is 0.011–0.013 W m⁻¹K⁻¹ at 220–250 K. Alternatively, model aerogel with k ≈ 9–16 mW m⁻¹K⁻¹.

---

## 9. Prior work on thermal and energy simulation of space habitats

Search coverage: WebSearch, Crossref and NTRS. Scopus and Web of Science were not used, so phrase novelty claims as "to the authors' knowledge".

| # | Reference | Method / tool | Summary |
|---|---|---|---|
| 1 | Simonsen, DeBarro & Farmer 1992. Lunar base thermal control system (NTRS 19930004815) | Conceptual trade study | Adapts Space Station thermal control (pumped water loop inside, two-phase NH₃ loop outside) to a lunar base. Compares heat pumps, shading, regolith and radiator orientation for the hot lunar day. |
| 2 | Gadkari, Goyal & Vanniasinkam 1991. NASA-CR-192014 | Conceptual TCS | Inflatable lunar module. Selects a water loop, a vapour-compression heat pump and reflux-boiler radiators. |
| 3 | Malla & Brown 2015. Acta Astronautica 107, 196–207, doi:10.1016/j.actaastro.2014.10.038 | Analytical/numerical regolith heat transfer | Lunar surface 102–387 K. A 1 m regolith cover damps the cycle; adjacent-surface albedo raises the structure's daytime peak. |
| 4 | Tripathi, Steiner & Malla 2023. Acta Astronautica 204, 263–280, doi:10.1016/j.actaastro.2022.12.040 | 3-D transient FE | Temperature field in a dome-shaped lunar habitat shell. |
| 5 | Steiner, Tripathi & Malla 2023. Earth & Space 2022, ASCE, 946–955, doi:10.1061/9780784484470.079 | Zonal air model | Interior air pressure, temperature and mass flow in a lunar dome. The closest lunar analogue to building-simulation zonal methods. |
| 6 | Tripathi, Steiner & Malla 2023. Earth & Space 2022, 966–975, doi:10.1061/9780784484470.081 | 3-D finite differences | Intact vs damaged lunar dome. Crown reaches ≈ 365 K at noon. |
| 7 | Steiner & Malla 2021. Earth & Space 2021, 1285–1296, doi:10.1061/9780784483374.119 | 1-D nonlinear heat equation | Layered ISRU / Earth-material shielding walls for thermal and impact protection. |
| 8 | Schunk, Babiak & Evans 2022. IEEE Aerospace Conf. (NTRS 20210026557) | Analytical TCS / radiator | South-pole surface habitat. Rejects more than 15 kW. Eclipses up to 100 h, mitigated with thermal storage and coatings. |
| 9 | von Einem, Groll & Heinicke 2022. J. Space Safety Eng. 9(2), 145–153, doi:10.1016/j.jsse.2022.02.005 | OpenFOAM CFD | Ventilation and thermal comfort in the MaMBA lunar/Mars lab module. A rack-ventilation loop is needed. |
| 10 | Borshchak Kachalov et al. 2025. Microgravity Sci. Technol. 37(4), 38, doi:10.1007/s12217-025-10194-4 | Numerical heat transfer | 3D-printed regolith walls with a PCM core. Outer optical properties set the mean interior temperature. |
| 11 | Liu et al. 2024. J. Asian Archit. Build. Eng. 24(3), 1454–1474, doi:10.1080/13467581.2024.2357195 | Simulation + Delphi/TOPSIS | Performance evaluation of four lunar habitat profiles. Tools not named in the abstract. |
| 12 | Azimi et al. 2025. AIAA Journal 63(2), 376–388, doi:10.2514/1.J063845 | Coupled virtual testbed (HabSim) | Purdue RETH system-of-systems habitat simulator, including thermal and interior environment. |
| 13 | Jadeja, Jaiswal, Ghosh & Sanghavi 2016. Intelligent Buildings International 8(4), 215–233, doi:10.1080/17508975.2015.1120185 | PlanetWRF + Ecotect + CFD | Building-physics thermal-comfort design study of a Mars module. Uses BPS tools, but not EnergyPlus. |
| 14 | Li, Bai, Bi & Beer 2025. Adv. Space Res. 76(6), 3700–3716, doi:10.1016/j.asr.2025.06.069 | FE thermo-mechanical | Steel habitat structures under Martian diurnal cycling. A 3 m regolith cover damps it. |
| 15 | Charoenboonvivat & de Weck 2026. AIAA SciTech 2026, AIAA 2026-1922, doi:10.2514/6.2026-1922 | MATLAB HabNet thermal-power module | Hourly heating and cooling demand for a hemispherical Mars habitat. Peak ≈ 90 kW (figure from a press source). |
| 16 | Ross 2022. IAC-22-A5.IP.4 (x68257) | Open-source semi-empirical heat balance | Fast Mars habitat thermal balance covering insolation, radiation, CO₂ convection and regolith conduction. |
| 17 | Perumal, Mukherjee & Gahlot 2022. IAC-22-A3.IPB.10 (x74243) | COMSOL conjugate heat transfer | Moon Village module at Shackleton. A regolith coating stabilises the interior. |
| 18 | Lagarde 2021. IAC-21-B3.7.10, https://spacearchitect.org/pubs/IAC-21-B3.7.10.pdf | Grasshopper/Ladybug with a hand-built Mars EPW | Builds a Gale-crater EPW for solar and orientation studies only. Heating and cooling loads left as future work. |
| 19 | Aydemir 2026. PhD dissertation, METU, https://hdl.handle.net/11511/118421 | Mars Climate Database → EPW; ClimateStudio (EnergyPlus-based) | "M-BPS" framework. The abstract describes adapting the weather file and inputs only. |
| 20 | Engler, Binsted & Leung 2019. Acta Astronautica 162, 50–55, doi:10.1016/j.actaastro.2019.05.049 | Data-driven forecasting | HI-SEAS analog habitat energy demand forecasting. |

Also found (lower tier):
- Brnčić 2020/21, BSc thesis, Univ. Zagreb: TRNSYS heating demand for NASA 3D-printed Mars habitats. Year and details partly unverified.
- Keller et al. 2026, arXiv:2607.23685 (preprint): Thermal Desktop/COMSOL study of variable-emissivity lunar domes.
- Manikkan et al. 2026, arXiv:2609.04614 (preprint): RC thermal digital twin of a habitat.

### 9.1 Novelty assessment: EnergyPlus for the Moon or Mars

Prior use of EnergyPlus-family tools for Mars is limited to two things:
- Building Mars-like EPW weather files (Lagarde 2021; Aydemir 2026).
- Running **unmodified** engines or front-ends (Ladybug, ClimateStudio).

EnergyPlus practitioners and developers have stated publicly that changing the EPW alone is insufficient. They say it needs physics changes to the solar calculations, the definition of a "day", and so on (Unmet Hours Q#59215, 2021; Q#67099, 2022 — grey literature).

No prior work was found that re-implements or modifies the EnergyPlus heat-balance algorithms themselves. That includes vacuum or low-pressure CO₂ convection, regolith ground coupling, AM2000 solar geometry and the sol, dust-scattering sky radiation, or lunar day/night cycles. No lunar application of any EnergyPlus-family tool was found.

**Suggested claim:** "To the authors' knowledge, this is the first open-source re-implementation of the EnergyPlus heat-balance method with physics modifications for planetary surface environments."

### 9.2 EnergyPlus license, clause (4)

Source: `LICENSE.txt` on the `develop` branch, https://raw.githubusercontent.com/NREL/EnergyPlus/develop/LICENSE.txt, fetched 2026-11-08. **V-text**.

> "(4) Use of EnergyPlus(TM) Name. If Licensee (i) distributes the software in stand-alone form without changes from the version obtained under this License, or (ii) Licensee makes a reference solely to the software portion of its product, Licensee must refer to the software as "EnergyPlus version X" software, where "X" is the version number Licensee obtained under this License and may not use a different name for the software. Except as specifically required in this Section (4), Licensee shall not use in a company name, a product name, in advertising, publicity, or other promotional activities any name, trade name, trademark, logo, or other designation of "EnergyPlus", "E+", "e+" or confusingly similar designation, without the U.S. Department of Energy's prior written consent."

What the rest of the license says:
- It is BSD-3-Clause-like. Clauses (1)–(2) require keeping the copyright notice and disclaimer. Clause (3) forbids endorsement using the names of the institutions or contributors.
- ⚠ There is **no** "Based on EnergyPlus" wording in the current text.

Implication for this project:
- A derivative or re-implemented engine must not carry "EnergyPlus", "E+" or "e+" in its product name or in promotion without DOE consent.
- Factual attribution of algorithm provenance in the paper and documentation is fine.
- Keep the copyright notice and license text, for example in `NOTICE` or `third_party/`.

---

## 10. Low-pressure natural convection and Mars external heat transfer

### 10.1 Scaling with gravity and gas density

- Gr = gβΔT L³ ρ²/μ² and Ra = Gr·Pr. With Nu = C·Raⁿ, **h = (k/L)·C·Raⁿ ∝ k (g ρ²)ⁿ**.
- n = 1/4 for laminar flow and 1/3 for turbulent flow.
- For an ideal gas, ρ = pM/(RT), so at fixed T, h ∝ (g p²)ⁿ.
- Standard correlation: Churchill & Chu (1975), Int. J. Heat Mass Transfer 18, 1323–1329, doi:10.1016/0017-9310(75)90243-4. For all Ra: Nu = {0.825 + 0.387 Ra^(1/6)/[1 + (0.492/Pr)^(9/16)]^(8/27)}². The citation was verified via Crossref; the formula is the standard textbook form.
- Forced convection: Churchill & Bernstein (1977), J. Heat Transfer 99, 300–306, doi:10.1115/1.3450685.

| Case | Factor on h vs Earth sea-level air (same ΔT and L) | Verified? |
|---|---|---|
| Moon habitat interior, same gas (g = 1.62) | × 0.637 (laminar) or × 0.548 (turbulent) | Derived |
| 56.5 kPa cabin vs 101.3 kPa, same gas, 1 g | × 0.747 (laminar) or × 0.678 (turbulent) | Derived |
| Mars exterior (600 Pa CO₂, 240 K, g = 3.71) vs 1 atm air at 293 K | Gr ratio ≈ 1.3×10⁻⁴, so Ra^(1/4) ratio ≈ 0.11. With k ratio ≈ 0.48, h ratio ≈ **0.05** (laminar asymptote). Churchill–Chu's constant term raises this at low Ra. | Derived |
| Moon exterior | No convection (vacuum, ~3×10⁻¹⁰ Pa per heat1d). Radiation and conduction only. | — |

### 10.2 Mars external convection: correlations and published values

| Item | Value | Source | Verified? |
|---|---|---|---|
| Churchill–Chu, 600 Pa CO₂ at 240 K, g = 3.71 m/s² | 1 m plate, ΔT 50 K: Ra ≈ 7×10⁵, **h ≈ 0.19 W m⁻²K⁻¹**. ΔT 20 K: h ≈ 0.15. 3 m plate, ΔT 50 K: h ≈ 0.16. | Derived (NIST properties) | Derived |
| Laminar forced flow, flat plate, L = 1 m | h ≈ 0.25 / 0.55 / 0.78 / 1.1 W m⁻²K⁻¹ at 1 / 5 / 10 / 20 m/s | Derived | Derived |
| Mars surface-layer bulk formula | Sensible flux H = ρ c_p C_h U ΔT, taking C_h ≈ C_d (neutral). The drag coefficient is C_d = [0.4/ln(z₁/z₀)]², with z₀ = 1 cm and z₁ = 2 m, giving C_d ≈ 0.0057. Effective h = ρ c_p C_d U ≈ 0.13 / 0.33 / 0.65 W m⁻²K⁻¹ at 2 / 5 / 10 m/s (ρ = 0.015 kg/m³, c_p = 760 J kg⁻¹K⁻¹). | Spiga et al. 2010, QJRMS 136(647), 414–428, doi:10.1002/qj.563 (C_d form V-text via subagent; DOI V via Crossref); h values Derived | V-text / Derived |
| CO₂ enclosure on Mars (CFD; 1000 Pa, g = 3.62) | Critical Gr: 2625 (horizontal), 6006 (vertical). Nu = 0.01775 Gr^0.535 AR^−0.0369. | Sun et al. 2018, Energies 11, 756, doi:10.3390/en11040756 | V-text (horizontal/vertical correlations print identically; check) |
| Published Mars h values | h ≈ 1–2 W m⁻²K⁻¹ (Pathfinder-era tests, 0–5 m/s); 0.2–1.5 W m⁻²K⁻¹ (Chinese study); 0.1–1.68 W m⁻²K⁻¹ (JAXA hot / cold cases) | Secondary or grey sources | **Unverified** |
| Measured Mars daytime surface sensible heat flux | 15–20 W/m² (Viking 1, summer); ≈ 5–28 W/m² (Jezero MEDA) | Sutton, Leovy & Tillman 1978 via Michaels & Rafkin 2004 (V-sec); Martínez 2023 (V-fig) | as noted |
| Mars boundary-layer models | — | Haberle et al. 1993, J. Atmos. Sci. 50, 1544–1559; Martínez, Valero & Vázquez 2009, J. Atmos. Sci. 66, 187–198 | Citation only |

**Recommendation:** for exterior Mars surfaces, use h = max(h_natural, h_forced). Compute h_natural from Churchill–Chu with NIST CO₂ properties and local g. Compute h_forced from a flat-plate correlation, or from the bulk formula with the MEDA wind distribution (mean 3.2 m/s). Expect h ≈ 0.2–1 W m⁻²K⁻¹, and run sensitivity cases up to 2 W m⁻²K⁻¹.

---

## Items not verified (check before publication)

1. Wolff et al. 2009 ω₀ (0.93–0.97, or 0.97–0.98) and g (0.63–0.68) at 880 nm. Only the secondary value ω₀ = 0.975 and Chen-Chen's g = 0.673 were confirmed.
2. Mars g = 3.721 m/s² has no primary source located. NSSDC gives 3.73.
3. Montabone 2015 conversion factor of 2.6.
4. InSight bulk density of 1211 kg/m³; Mars regolith cp range; Mars surface emissivity at Jezero.
5. The mean-annual illumination percentage at the Shackleton rim. Only Mazarico's "240 continuous days" and Gläser's Connecting Ridge 92.27 % / 95.65 % were confirmed.
6. Gilmore (2002) MLI ε* range and coating tables.
7. Published Mars external h values (0.2–2 W m⁻²K⁻¹ range).
8. Scaccabarozzi 2014 aerogel vs MLI; NTRS 20080014322 silver-Teflon 0.10/0.85.
9. The "18.3–26.7 °C" setpoint (65–80 °F) does not appear in BVAD REV1, which gives 18–27 °C.

---

## References

Allison, M., McEwen, M., 2000. A post-Pathfinder evaluation of areocentric solar coordinates with improved timing recipes for Mars seasonal/diurnal climate studies. Planetary and Space Science 48(2–3), 215–235. https://doi.org/10.1016/S0032-0633(99)00092-6

Anderson, M.S., Ewert, M.K., Keener, J.F., 2018. Life Support Baseline Values and Assumptions Document. NASA/TP-2015-218570/REV1. NASA Johnson Space Center. https://ntrs.nasa.gov/citations/20180001338

Appelbaum, J., Flood, D.J., 1990. Solar radiation on Mars. Solar Energy 45(6), 353–363. https://doi.org/10.1016/0038-092X(90)90156-7

Appelbaum, J., Landis, G.A., 1991. Solar Radiation on Mars—Update 1991. NASA TM-105216. https://ntrs.nasa.gov/citations/19910023732

Appelbaum, J., Landis, G.A., Sherman, I., 1993. Solar radiation on Mars—Update 1991. Solar Energy 50(1), 35–51. https://doi.org/10.1016/0038-092X(93)90006-A

Aydemir, G.N., 2026. An Integrated Framework for Mars-Based Building Performance Simulations (M-BPS): From Site Selection to Habitat Assessment. PhD Dissertation, Middle East Technical University. https://hdl.handle.net/11511/118421

Azimi, M., et al., 2025. HabSim: A modular-coupled virtual testbed for simulating extraterrestrial habitat systems. AIAA Journal 63(2), 376–388. https://doi.org/10.2514/1.J063845

Bae, D., Rodriguez-Ruiz, J., 2019. Review of MLI behavior at low temperatures and application to L'Ralph thermal modeling. Thermal & Fluids Analysis Workshop (TFAWS). https://ntrs.nasa.gov/citations/20190030285

Bhandari, P., Karlmann, P., Anderson, K., Novak, K., 2011. CO2 insulation for thermal control of the Mars Science Laboratory. 41st International Conference on Environmental Systems. https://ntrs.nasa.gov/citations/20120013533

Bien, D.D., Guentert, D.C., 1969. A method for reducing the equivalent sink temperature of a vertically oriented radiator on the lunar surface. NASA TM X-1729. https://ntrs.nasa.gov/citations/19690007893

Borshchak Kachalov, A., Salgado Sánchez, P., Mollah, M.T., Ezquerro, J.M., Spangenberg, J., Šeta, B., 2025. Numerical analysis of coaxially 3D printed lunar habitats: Integrating regolith and PCM for passive temperature control. Microgravity Science and Technology 37(4), 38. https://doi.org/10.1007/s12217-025-10194-4

Charoenboonvivat, Y., de Weck, O., 2026. Surface power demand modeling for human Martian and lunar missions. AIAA SciTech 2026 Forum, AIAA 2026-1922. https://doi.org/10.2514/6.2026-1922

Chen-Chen, H., Pérez-Hoyos, S., Sánchez-Lavega, A., 2019. Characterisation of Martian dust aerosol phase function from sky radiance measurements by MSL engineering cameras. Icarus 330, 16–29. https://doi.org/10.1016/j.icarus.2019.04.004

Churchill, S.W., Bernstein, M., 1977. A correlating equation for forced convection from gases and liquids to a circular cylinder in crossflow. Journal of Heat Transfer 99(2), 300–306. https://doi.org/10.1115/1.3450685

Churchill, S.W., Chu, H.H.S., 1975. Correlating equations for laminar and turbulent free convection from a vertical plate. International Journal of Heat and Mass Transfer 18(11), 1323–1329. https://doi.org/10.1016/0017-9310(75)90243-4

Engler, S.T., Binsted, K., Leung, H., 2019. HI-SEAS habitat energy requirements and forecasting. Acta Astronautica 162, 50–55. https://doi.org/10.1016/j.actaastro.2019.05.049

Espenak, F. Eclipses and the Moon's orbit. NASA GSFC Eclipse Web Site. https://eclipse.gsfc.nasa.gov/help/moonorbit.html

Ewert, M.K., Graf, J.P., Keller, J.R., 1995. Development of a lunar radiator parabolic shading system. SAE Technical Paper 951524. https://doi.org/10.4271/951524

Fesmire, J.E., Ancipink, J.B., Swanger, A.M., White, S., Yarbrough, D.W., 2017. Thermal conductivity of aerogel blanket insulation under cryogenic-vacuum conditions in different gas environments. IOP Conference Series: Materials Science and Engineering 278, 012198. https://doi.org/10.1088/1757-899X/278/1/012198

Finckenor, M.M., Dooling, D., 1999. Multilayer Insulation Material Guidelines. NASA/TP-1999-209263. https://ntrs.nasa.gov/citations/19990047691

Gadkari, K., Goyal, S.K., Vanniasinkam, J., 1991. Conceptual design of a thermal control system for an inflatable lunar habitat module. NASA-CR-192014. https://ntrs.nasa.gov/citations/19930008924

Gaier, J.R., Siamidis, J., Panko, S.R., Rogers, K.J., Larkin, E.M.G., 2008. The effect of simulated lunar dust on the absorptivity, emissivity, and operating temperature of AZ-93 and Ag/FEP thermal control surfaces. NASA/TM-2008-215492. https://ntrs.nasa.gov/citations/20090005996

Gaier, J.R., Journey, K., Christopher, S., Davis, S., 2011. Evaluation of brushing as a lunar dust mitigation strategy for thermal control surfaces. NASA/TM-2011-217231. https://ntrs.nasa.gov/citations/20120000070

Garrison, M.B., Nguyen, D.H., 2007. Thermal considerations for designing the next lunar lander. AIP Conference Proceedings 880, 35–42. https://doi.org/10.1063/1.2437438

Gläser, P., Scholten, F., De Rosa, D., Marco Figuera, R., Oberst, J., Mazarico, E., Neumann, G.A., Robinson, M.S., 2014. Illumination conditions at the lunar south pole using high resolution Digital Terrain Models from LOLA. Icarus 243, 78–90. https://doi.org/10.1016/j.icarus.2014.08.013

Grott, M., Spohn, T., Knollenberg, J., Krause, C., Hudson, T.L., Piqueux, S., Müller, N., Golombek, M., Vrettos, C., Marteau, E., et al., 2021. Thermal conductivity of the Martian soil at the InSight landing site from HP3 active heating experiments. Journal of Geophysical Research: Planets 126(7), e2021JE006861. https://doi.org/10.1029/2021JE006861

Guzewich, S.D., Lemmon, M., Smith, C.L., Martínez, G., et al., 2019. Mars Science Laboratory observations of the 2018/Mars Year 34 global dust storm. Geophysical Research Letters 46(1), 71–79. https://doi.org/10.1029/2018GL080839

Haberle, R.M., Houben, H.C., Hertenstein, R., Herdtle, T., 1993. A boundary-layer model for Mars: Comparison with Viking lander and entry data. Journal of the Atmospheric Sciences 50(11), 1544–1559. https://doi.org/10.1175/1520-0469(1993)050<1544:ABLMFM>2.0.CO;2

Haberle, R.M., et al., 2014. Preliminary interpretation of the REMS pressure data from the first 100 sols of the MSL mission. Journal of Geophysical Research: Planets 119, 440–453. https://doi.org/10.1002/2013JE004488

Hayne, P.O., Bandfield, J.L., Siegler, M.A., Vasavada, A.R., Ghent, R.R., Williams, J.-P., Greenhagen, B.T., Aharonson, O., Elder, C.M., Lucey, P.G., Paige, D.A., 2017. Global regolith thermophysical properties of the Moon from the Diviner Lunar Radiometer Experiment. Journal of Geophysical Research: Planets 122(12), 2371–2400. https://doi.org/10.1002/2017JE005387

Hickey, G.S., Braun, D., Wen, L.-C., Eisen, H.J., 1995. Integrated lightweight structure and thermal insulation for Mars rover. SAE Technical Paper 951523. https://doi.org/10.4271/951523

Jadeja, A., Jaiswal, M.M., Ghosh, S., Sanghavi, P., 2016. Thermal comfort analysis of a proposed design for a sustainable living space on Mars. Intelligent Buildings International 8(4), 215–233. https://doi.org/10.1080/17508975.2015.1120185

Kieffer, H.H., 2013. Thermal model for analysis of Mars infrared mapping. Journal of Geophysical Research: Planets 118(3), 451–470. https://doi.org/10.1029/2012JE004164

Kieffer, H.H., Martin, T.Z., Peterfreund, A.R., Jakosky, B.M., Miner, E.D., Palluconi, F.D., 1977. Thermal and albedo mapping of Mars during the Viking primary mission. Journal of Geophysical Research 82(28), 4249–4291. https://doi.org/10.1029/JS082i028p04249

Kopp, G., Lean, J.L., 2011. A new, lower value of total solar irradiance: Evidence and climate significance. Geophysical Research Letters 38(1), L01706. https://doi.org/10.1029/2010GL045777

Lagarde, T.J.-R., 2021. Using computational techniques for the optimal design of evolving habitats. 72nd International Astronautical Congress, IAC-21-B3.7.10. https://spacearchitect.org/pubs/IAC-21-B3.7.10.pdf

Lemmon, M.T., et al., 2004. Atmospheric imaging results from the Mars Exploration Rovers: Spirit and Opportunity. Science 306(5702), 1753–1756. https://doi.org/10.1126/science.1104474

Lemmon, M.T., et al., 2015. Dust aerosol, clouds, and the atmospheric optical depth record over 5 Mars years of the Mars Exploration Rover mission. Icarus 251, 96–111. https://doi.org/10.1016/j.icarus.2014.03.029

Lemmon, M.T., Smith, M.D., Viúdez-Moreiras, D., et al., 2022. Dust, sand, and winds within an active Martian storm in Jezero crater. Geophysical Research Letters 49(17), e2022GL100126. https://doi.org/10.1029/2022GL100126

Lemmon, M.T., Guzewich, S.D., Battalio, J.M., Malin, M.C., Vicente-Retortillo, A., Zorzano, M.-P., Martín-Torres, J., Sullivan, R., Maki, J.N., Smith, M.D., Bell, J.F. III, 2024. The Mars Science Laboratory record of optical depth measurements via solar imaging. Icarus 408, 115821. https://doi.org/10.1016/j.icarus.2023.115821

Li, J., Bai, Y., Bi, S., Beer, M., 2025. Thermomechanical behavior of steel structural configurations subjected to cyclic cryogenic conditions in Martian environment. Advances in Space Research 76(6), 3700–3716. https://doi.org/10.1016/j.asr.2025.06.069

Liu, Y., Mei, H., Pan, W., Wang, J., Tan, X., Wang, Y., 2024. Comprehensive performance evaluation of basic type of lunar habitat. Journal of Asian Architecture and Building Engineering 24(3), 1454–1474. https://doi.org/10.1080/13467581.2024.2357195

Malla, R.B., Brown, K.M., 2015. Determination of temperature variation on lunar surface and subsurface for habitat analysis and design. Acta Astronautica 107, 196–207. https://doi.org/10.1016/j.actaastro.2014.10.038

Martínez, G.M., Valero, F., Vázquez, L., 2009. Characterization of the Martian surface layer. Journal of the Atmospheric Sciences 66(1), 187–198. https://doi.org/10.1175/2008JAS2765.1

Martínez, G.M., et al., 2017. The modern near-surface Martian climate: A review of in-situ meteorological data from Viking to Curiosity. Space Science Reviews 212, 295–338. https://doi.org/10.1007/s11214-017-0360-x

Martínez, G.M., Vicente-Retortillo, A., Vasavada, A.R., et al., 2021. The surface energy budget at Gale crater during the first 2500 sols of the Mars Science Laboratory mission. Journal of Geophysical Research: Planets 126(9), e2020JE006804. https://doi.org/10.1029/2020JE006804

Martínez, G.M., Sebastián, E., Vicente-Retortillo, A., Smith, M.D., Johnson, J.R., Fischer, E., Savijärvi, H., et al., 2023. Surface energy budget, albedo, and thermal inertia at Jezero crater, Mars, as observed from the Mars 2020 MEDA instrument. Journal of Geophysical Research: Planets 128(2), e2022JE007537. https://doi.org/10.1029/2022JE007537

Mazarico, E., Neumann, G.A., Smith, D.E., Zuber, M.T., Torrence, M.H., 2011. Illumination conditions of the lunar polar regions using LOLA topography. Icarus 211(2), 1066–1081. https://doi.org/10.1016/j.icarus.2010.10.030

Meeus, J., 1998. Astronomical Algorithms, 2nd ed. Willmann-Bell, Richmond, VA.

Montabone, L., et al., 2015. Eight-year climatology of dust optical depth on Mars. Icarus 251, 65–95. https://doi.org/10.1016/j.icarus.2014.12.034

NASA, 2022. NASA-STD-3001, NASA Space Flight Human-System Standard, Volume 2, Revision C. https://www.nasa.gov/wp-content/uploads/2020/10/2022-04-08_nasa-std-3001_vol_2_rev_c_final.pdf

NASA GISS. Mars24 Sunclock — Algorithm and worked examples (Technical Notes on Mars Solar Time). https://www.giss.nasa.gov/tools/mars24/help/algorithm.html

NASA NSSDC. Mars Fact Sheet; Moon Fact Sheet. https://nssdc.gsfc.nasa.gov/planetary/factsheet/marsfact.html ; https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html

NIST Chemistry WebBook, SRD 69. Thermophysical properties of fluid systems: carbon dioxide (Span–Wagner EOS). https://webbook.nist.gov/chemistry/fluid/

Norcross, J., Norsk, P., Law, J., et al., 2013. Effects of the 8 psia / 32% O2 atmosphere on the human in the spaceflight environment. NASA/TM-2013-217377. https://ntrs.nasa.gov/citations/20130013505

NREL/EnergyPlus, LICENSE.txt (develop branch), retrieved 2026-11-08. https://github.com/NREL/EnergyPlus/blob/develop/LICENSE.txt

Perumal, K.R., Mukherjee, C.S., Gahlot, A., 2022. Thermal analysis of an Moon Village concept. 73rd International Astronautical Congress, IAC-22-A3.IPB.10.x74243.

Piqueux, S., Christensen, P.R., 2011. Temperature-dependent thermal inertia of homogeneous Martian regolith. Journal of Geophysical Research 116, E07004. https://doi.org/10.1029/2011JE003805

Putzig, N.E., Mellon, M.T., 2007. Apparent thermal inertia and the surface heterogeneity of Mars. Icarus 191(1), 68–94. https://doi.org/10.1016/j.icarus.2007.05.013

Rodríguez-Manfredi, J.A., de la Torre Juárez, M., Sánchez-Lavega, A., Hueso, R., Martínez, G.M., et al., 2023. The diverse meteorology of Jezero crater over the first 250 sols of Perseverance on Mars. Nature Geoscience 16, 19–28. https://doi.org/10.1038/s41561-022-01084-0

Ross, S., 2022. Development of an open source modelling package for thermal balance of crewed Mars habitats. 73rd International Astronautical Congress, IAC-22-A5.IP.4.x68257.

Ruíz, M., Sebastián-Martínez, E., Rodríguez-Manfredi, J.A., Pla-García, J., de la Torre-Juárez, M., Rafkin, S.C.R., 2025. Meteorological changes across Curiosity rover's traverse using REMS measurements and comparisons with measurements and MRAMS model results. Remote Sensing 17(3), 368. https://doi.org/10.3390/rs17030368

Sánchez-Lavega, A., del Río-Gaztelurrutia, T., Hueso, R., et al., 2023. Mars 2020 Perseverance rover studies of the Martian atmosphere over Jezero from pressure measurements. Journal of Geophysical Research: Planets 128, e2022JE007480. https://doi.org/10.1029/2022JE007480

Schaezler, R.N., Cook, A.J., Leonard, D.J., Ghariani, A., 2011. Trending of overboard leakage of ISS cabin atmosphere. 41st International Conference on Environmental Systems. https://ntrs.nasa.gov/citations/20110012997

Schunk, G., Babiak, S., Naville, D., Evans, B., 2021. Conceptual thermal control system design for a lunar surface habitat. Thermal & Fluids Analysis Workshop (TFAWS). https://ntrs.nasa.gov/citations/20210020015

Schunk, R.G., Babiak, S.D., Evans, B.W., 2022. Thermal control system architecture and technology challenges for a lunar surface habitat. IEEE Aerospace Conference. https://ntrs.nasa.gov/citations/20210026557

Simonsen, L.C., DeBarro, M.J., Farmer, J.T., 1992. Conceptual design of a lunar base thermal control system. In: The Second Conference on Lunar Bases and Space Activities of the 21st Century. https://ntrs.nasa.gov/citations/19930004815

Spiga, A., Forget, F., Lewis, S.R., Hinson, D.P., 2010. Structure and dynamics of the convective boundary layer on Mars as inferred from large-eddy simulations and remote-sensing measurements. Quarterly Journal of the Royal Meteorological Society 136(647), 414–428. https://doi.org/10.1002/qj.563

Steiner, J.T., Malla, R.B., 2021. A study of layered structural configurations as thermal and impact shielding of lunar habitats. In: Earth and Space 2021, ASCE, pp. 1285–1296. https://doi.org/10.1061/9780784483374.119

Steiner, J.T., Tripathi, S., Malla, R.B., 2023. Air pressure and temperature distribution within a dome habitat structure on the lunar surface. In: Earth and Space 2022, ASCE, pp. 946–955. https://doi.org/10.1061/9780784484470.079

Sun, Y., Lin, G., Bu, X., Bai, L., Xiao, C., Wen, D., 2018. A numerical study of fluid flow and heat transfer in carbon dioxide enclosures on Mars. Energies 11(4), 756. https://doi.org/10.3390/en11040756

Sutton, J.L., Leovy, C.B., Tillman, J.E., 1978. Diurnal variations of the Martian surface layer meteorological parameters during the first 45 sols at two Viking lander sites. Journal of the Atmospheric Sciences 35, 2346–2355. https://doi.org/10.1175/1520-0469(1978)035<2346:DVOTMS>2.0.CO;2

Trevino, L.A., Orndoff, E.S., 2000. Advanced space suit insulation feasibility study. 30th International Conference on Environmental Systems. https://ntrs.nasa.gov/citations/20100042640

Tripathi, S., Steiner, J.T., Malla, R.B., 2023a. Three-dimensional temperature profile in a dome-shaped habitat structure on the moon. Acta Astronautica 204, 263–280. https://doi.org/10.1016/j.actaastro.2022.12.040

Tripathi, S., Steiner, J.T., Malla, R.B., 2023b. Diurnal temperature variation on an intact and damaged lunar habitat structure. In: Earth and Space 2022, ASCE, pp. 966–975. https://doi.org/10.1061/9780784484470.081

Vasavada, A.R., Bandfield, J.L., Greenhagen, B.T., Hayne, P.O., Siegler, M.A., Williams, J.-P., Paige, D.A., 2012. Lunar equatorial surface temperatures and regolith properties from the Diviner Lunar Radiometer Experiment. Journal of Geophysical Research: Planets 117(E12), E00H18. https://doi.org/10.1029/2011JE003987

Viúdez-Moreiras, D., Lemmon, M., Newman, C.E., et al., 2022. Winds at the Mars 2020 landing site: 1. Near-surface wind patterns at Jezero crater. Journal of Geophysical Research: Planets 127(12), e2022JE007522. https://doi.org/10.1029/2022JE007522

von Einem, M., Groll, R., Heinicke, C., 2022. Computational modeling of a ventilation concept for a lunar habitat laboratory. Journal of Space Safety Engineering 9(2), 145–153. https://doi.org/10.1016/j.jsse.2022.02.005

Wolff, M.J., Smith, M.D., Clancy, R.T., Arvidson, R., Kahre, M., Seelos, F., Murchie, S., Savijärvi, H., 2009. Wavelength dependence of dust aerosol single scattering albedo as observed by the Compact Reconnaissance Imaging Spectrometer. Journal of Geophysical Research 114, E00D04. https://doi.org/10.1029/2009JE003350

**Reference implementations consulted (code, not cited as literature):**
- phayne/heat1d. https://github.com/phayne/heat1d
- georgeslabreche/marsrad. https://github.com/georgeslabreche/marsrad
- nschorgh/Planetary-Code-Collection. https://github.com/nschorgh/Planetary-Code-Collection
