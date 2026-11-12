# Thermonaut manuscript: response to the pre-submission reviews

Two pre-submission reviews were received:

- **A.** `review_report.md`: three short perspectives.
- **B.** `Thermonaut_peer_review_report.md`: a major-revision report with comments R1.1–R1.7, R2.1–R2.9 and R3.1–R3.9.

Every comment was checked against the manuscript and the code. No comment was found to be wrong. A few requests are declined or narrowed, with the reason given below. Several comments led to changes in the engine itself, not only in the text. In particular, tracing every audit finding to the code (R1.1, R1.2, R1.6) showed that some refusals were documented but not implemented. They are now implemented and tested (patch set M2e).

Status labels used below:

- **Done**: the comment was addressed in full.
- **Partly**: part of the request was done; the rest is explained.
- **Declined**: not done, with the reason.

## Review A

| Comment | Status | What changed |
|---|---|---|
| Mention the need for thermal-vacuum validation in the abstract or introduction | Done | The last sentence of the abstract says so. The introduction states that none of the evidence validates a complete habitat. Section 6.1 says what validation requires. |
| Give a threshold or timeline for proposing the changes upstream | Done | Section 6.3: the plan is an EnergyPlus new-feature proposal once the M3 sol clock and space radiator stabilize the time-base and plant interfaces. |
| Add a start-up diagram contrasting the default warm-up with the correction | Done | New Fig. 3 shows temperature profiles of the lunar regolith shell: the default 23 °C start, the steady profile, the state after warm-up, and the full and warm-up-aware corrections. |

## Review B: Reviewer 1 (software, reproducibility)

| Comment | Status | What changed |
|---|---|---|
| R1.1 The audit should be reproducible; qualify its completeness | Done | Section 3.1 describes the protocol: areas, searched symbols, agent procedure, priority rules. A second, separate agent pass traced every one of the 271 report rows (252 findings plus 19 notes) back to the v26.2.0 source. 264 rows were found at the cited line, 3 had moved and 4 cite no line. Supplementary file S1 (CSV) gives, for each row, file and line, symbol, assumption, effect, proposed change, priority, disposition, treatment and location check. The text says that the audit is a protocol-based search, not a proof of completeness. Third-party code: the window engine and Kiva are covered through their callers and are refused. |
| R1.2 Make the findings traceable to the implementation | Done | New Table 3 counts dispositions by area (modified, refused, avoided, deferred, harmless) plus a P0 row. Supplement S1 lists every deferred row. Only two P0 rows remain open: the exterior long-wave linearization, which EnergyPlus also uses on Earth. It is now listed as a limitation. |
| R1.3 Narrow the bit-for-bit claim | Done | The claim is now scoped to "the tested files, climates and build" in the abstract, Section 5.1 and the conclusions. A second climate (Phoenix TMY3) was added. The number of values compared is reported (about 4.7 million per climate). The text states that every patch set from M1 to M2e passed. Supplement S3 has the per-file results; the harness is in the repository. |
| R1.3.4 Test more than one compiler or platform | Declined | Only one toolchain is available. The text states the compiler and OS, and the claim is scoped to them. |
| R1.4 Separate the unit tests from planetary verification | Done | The text now says that the upstream unit tests do not exercise the planetary mode. A new planetary test suite of 23 end-to-end tests covers weather-file checks, refusals and Earth-mode identity (Section 5.1, Supplement S4). New gtests inside the EnergyPlus suite are not added. |
| R1.5 Give a fuller PWF specification | Done | Section 4.3 explains the role of each solar field: the engine computes its own sun position and uses only the irradiance magnitudes. It also states the time conventions and the checks. Supplement S8 has the header and column tables. Physical range checks are now actually implemented in the reader (M2e); before, the paper claimed them but the code did not have them. |
| R1.6 Show the refusal mechanism is complete | Done (engine change) | The tracing found gaps: windows, SimpleCombined outside convection (which silently dropped sky and ground long-wave), several air-cooled and outdoor-air components, DElight, EcoRoof, ground models, F/C-factor constructions, per-surface HAMT, the CO2 balance, unscheduled water mains, and one step per hour (where the sun timing is inconsistent). All are now refused. A backstop stops any planetary run in which a component registered an outdoor-air node. The refusals have new tests, and Supplement S9 lists them. False positives are avoided by checking values (for example, water-cooled chillers are allowed). |
| R1.7 Discuss fork maintenance with evidence | Partly | Section 6.3 calls the release procedure "proposed rather than demonstrated" (the patches have been applied only to v26.2.0). It explains the fail-safe anchors and the regression gate, and adds the upstream plan. Porting to another release was not attempted. |
| Minor: version history | Done | Supplement S6. |
| Minor: line counts | Done | Section 4.1 separates the new module, the input definition and the hooks. Patch scripts, tests and docs are excluded and say so. |
| Minor: research fork in title and abstract | Done | The abstract says "research fork". The licence paragraph is kept. |
| Minor: tagged release | Done | Tag `thermonaut-m2e`. |
| Minor: licence of the audit and test material | Done | It is in the repository under the EnergyPlus licence (title page, data availability). |

## Review B: Reviewer 2 (building physics, numerics)

| Comment | Status | What changed |
|---|---|---|
| R2.1 The cabin-gas 0.4% bound is wrong at 34% O2 | Done (the reviewer was right) | Section 4.6 now gives the 26.5% and 34% values. At 34% O2: gas constant −1.4%, specific heat −1.0%, volumetric heat capacity 0.4% too low, humidity ratio 1.4% too high (molar-mass ratio 0.613 instead of 0.622). This is also listed as a limitation. |
| R2.2 Compare the regolith at the same depth | Done | The engine profile is now reported at 0.5, 1, 2 and 3 m. At 1 m it is 253 K against the ≈252–256 K reference (Table 6). |
| R2.3 Justify the Mars convection and its applicability | Done | Section 4.7 gives Ra, Re and Pr ranges and a Knudsen number below 2e-5 (continuum). It notes where Ra falls below the fitted range of the horizontal correlation, where forced convection dominates. Sensitivity to pressure, wind, ΔT and length scale is in Supplement S5. The NIST check is described as checking the implementation, not the correlations. |
| R2.4 Lunar radiative scope | Done | Earthshine (<0.2 W/m²) and Earth's thermal emission (about 0.07 W/m²) are quantified and neglected. The verified domain is limited to equatorial and mid-latitude sites with a uniform horizon. Polar sites and shadowed terrain are excluded. |
| R2.5 Robustness of the start-up correction | Done | The derivation is now Eqs. 4–5 with Fig. 3. Tests added: a long spin-up (Mars +0.07%; Moon +1.2%, so a one-year spin-up is advised for lunar design studies); minimum warm-up of 1 or 20 days; CondFD grid constant of 10 or 90; time step of 2 or 6 min. The k(T) iteration converges by 2e-6 K at the sixth iteration. The text states the method is untested with phase-change or moisture-dependent materials. |
| R2.6 Ideal loads and humidity | Done | Table 9 reports RH, dew point and the margin between the coldest surface and the dew point for both codes. The ideal-loads margin is 3.6 K too optimistic, and the text says condensation risk should not be judged from ideal loads. A condensing heat exchanger is on the roadmap. |
| R2.7 Test the PV model beyond its residual | Partly | The text now gives the assumptions (ε 0.85 on both faces, a free-standing module, no self-shading). It also estimates the thermal time constant (about 5 min, close to the step) and the emissivity sensitivity (±10% gives about 8 K) with T ∝ ε^−1/4, and explains the 79 K night temperature. No measured module data are available, so the check is labelled as numerical closure. |
| R2.8 Link the sealed cabin to leakage and life support | Done | Section 5.5 gives the leakage and airlock make-up gas (about 0.3 kg/day), whose heating needs less than 1 W. Compression and O2 generation are within the 14 kW electric load. |
| R2.9 Validate the weather generator across conditions | Partly | The sun is checked against JPL Horizons on both bodies, the lunar regolith against Diviner and Apollo, and the Mars sky against MEDA and the 2018 storm. The verified domain is narrowed to match. A second Martian site and polar lunar sites are not added; the domain statement excludes them instead. |

## Review B: Reviewer 3 (positioning, V&V, applicability)

| Comment | Status | What changed |
|---|---|---|
| R3.1 State the novelty relative to ExoBEM | Done | The introduction says the subject is auditing, changing and verifying a production engine, not the planetary model the two codes share. Table 1 compares the routes. |
| R3.2 Use consistent V&V terms | Done | New Table 5 sets out the hierarchy (levels 1–6 plus system validation, which is not available). Each check is labelled with its level. |
| R3.3 Characterize how independent ExoBEM is | Done | Section 5.3: same authors, same physical model and weather format, no shared code. The text lists what differs and states that agreement cannot reveal an error the two codes share. "Independent tool" has been removed. |
| R3.4 Provenance of the "NASA-class" habitat | Done | It is renamed "NASA-informed representative habitat". Supplement S7 lists every input as a NASA document value, derived from NASA data, or an authors' assumption. |
| R3.5 The cases are few and not general | Partly | Claims are narrowed. A supported-domain section (6.1), the feature-coverage table (Table 4) and the sensitivity analysis (Table 10) are added. No new habitat cases are added. |
| R3.6 Practical relevance of the feature set | Done | Table 4 lists features. Section 6.1 says what a user can and cannot do today. |
| R3.7 Position against spacecraft thermal modelling | Done | Section 2.2 covers SINDA/FLUINT and Thermal Desktop [Gilmore 2002] and presents the two kinds of tool as complementary. |
| R3.8 Uncertainty and sensitivity | Done | New Section 5.7 and Table 10 give one-at-a-time sensitivity (MLI R, beta-cloth optics, regolith properties, horizon, thermal inertia, dust, wind). They show that input uncertainty exceeds the code-to-code differences. |
| R3.9 Data availability for reproduction | Done | Public repositories, the tag `thermonaut-m2e`, the inventory CSV, the test and regression harnesses, and a script that reruns every case and checks its output against the recorded one. Before acceptance, the recommendation is to archive the release on Zenodo with a DOI. Independent reproduction by another group is outside the authors' control and is listed as a limitation. |

## Not changed, and why

- **Multi-compiler regression (R1.3):** no second toolchain is available; the claim is scoped instead.
- **Porting the patches to a second EnergyPlus release (R1.7):** the procedure is presented as proposed, not demonstrated.
- **Measured PV module temperatures in vacuum (R2.7):** no open dataset was found.
- **Second Martian site and polar lunar sites (R2.9, R3.5):** the verified domain is narrowed instead.
- **Independent third-party reproduction and system-level validation (R3.3, R3.9):** these are not possible before publication; both are stated as limitations.
