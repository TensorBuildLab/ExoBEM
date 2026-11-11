# Planetary Weather Format (PWF) 1.0

PWF is the weather-file format of ExoBEM and Thermonaut. It plays the role that the EPW file plays for
EnergyPlus, without EPW's Earth assumptions. It is plain text, so it can be read by any tool, and it is
written by ExoBEM's environment generators:

```bash
exobem weather --body moon --lat -89.5 --lon 0 --horizon -1.65 --days 59 -o lunar_pole.pwf
exobem weather --body mars --lat 18.44 --lon 77.45 --days 60 --dust-storm 190 270 6 -o jezero_storm.pwf
exobem info jezero_storm.pwf
```

## Why not EPW?

| EPW property | Problem on the Moon or Mars | PWF |
|---|---|---|
| 8,760 (8,784) records of one hour | The lunar day lasts 708.7 h; a Mars sol 24.66 h; multi-year Mars periods | Any number of equally spaced records of any length (`timestep_s`) |
| Month/day/hour time stamps of an Earth year | Mars seasons follow the solar longitude Ls, not the calendar | Elapsed seconds from `start_utc`, plus `local_time_h` and `day_index` for schedules |
| Range checks: a dry-bulb of 99.9 °C or more is treated as missing; a pressure of 31 kPa or less is replaced by the standard value | Lunar-noon regolith reaches 120 °C; Mars pressure is 0.6–0.8 kPa; Moon 0 Pa | Physical checks only (non-negative irradiance, temperatures above the 2.725 K cosmic background, pressure consistent with the atmosphere) |
| Dew point, relative humidity, precipitation, snow, cloud cover, visibility | No meaning in vacuum or a dry CO2 atmosphere | Not present; `T_air_K` is `nan` in vacuum |
| Horizontal infrared from the sky, opaque/total sky cover models | Sky emission comes from dust and CO2 (Mars) or is the 2.7 K background (Moon) | `T_sky_K` and `L_down_W_m2` given directly |
| Ground temperatures by month at three depths | Regolith swings 290 K in a lunar day; ground model must be dynamic | `T_ground_K` (surface, every record) and `T_deep_K` (below the habitat) |
| No body, gravity or atmosphere information | Convection depends on gravity, gas and pressure | Header carries `body`, `gravity_m_s2`, `atmosphere` |

## File layout

```
# PWF 1.0
# body: mars
# site_name: Jezero crater
# latitude_deg: 18.440000
# longitude_deg: 77.450000
# start_utc: 2030-01-01T00:00:00
# timestep_s: 1800
# n_records: 2880
# solar_day_s: 88775.244147
# gravity_m_s2: 3.72100
# atmosphere: mars_co2
# clock: mars_lmst
# sky_includes_air: false
# generator: exobem 0.2.0 weather --body mars --lat 18.44 --lon 77.45 ...
# units: s,h,-,deg,deg,-,W/m2,W/m2,W/m2,K,K,K,K,-,Pa,m/s,deg,W/m2,deg,-,h
time_s,local_time_h,day_index,zenith_deg,sun_azimuth_deg,sun_visible,dni_W_m2,...
1800,4.076848,0,121.9043,107.584,0,0,0,0,205.549,161.4181,...
```

* Line 1 must be `# PWF <version>`.
* Header lines are `# key: value`. Unknown keys are ignored.
* The first line that does not start with `#` holds the column names; every following line is one record.
* Values are separated by commas; missing or not-applicable values are written `nan`.

### Header keys

| Key | Required | Meaning |
|---|---|---|
| `body` | yes | `moon`, `mars` or `earth` |
| `latitude_deg`, `longitude_deg` | yes | Planetocentric latitude (north +) and longitude (east +) |
| `start_utc` | yes | ISO 8601 UTC time of the start of the first record (`YYYY-MM-DDTHH:MM:SS`) |
| `timestep_s` | yes | Record length in seconds; records must be equally spaced |
| `gravity_m_s2` | yes | Surface gravity (1.625 Moon, 3.721 Mars) |
| `atmosphere` | yes | `none` (vacuum), `mars_co2` or `earth_air`: the gas for exterior convection |
| `solar_day_s` | recommended | Length of the solar day (2,551,442.9 s Moon; 88,775.244 s Mars) |
| `clock` | recommended | What `local_time_h` means: `earth_utc` (Moon: crew time follows UTC), `mars_lmst` (local mean solar time) or `earth_local` |
| `sky_includes_air` | no | `true` only for Earth files (EnergyPlus-style split of the sky view) |
| `site_name`, `n_records`, `generator` | no | Documentation |
| `horizon_azimuth_deg`, `horizon_elevation_deg` | no | Horizon profile used to compute `sun_visible` (space-separated lists) |

### Columns

Solar quantities are evaluated at the **middle** of each record's interval; state quantities at its **end**
(the same convention as ExoBEM's time-step solution).

| Column | Unit | Required | Meaning |
|---|---|---|---|
| `time_s` | s | yes | End of the interval, seconds since `start_utc` |
| `local_time_h` | h | yes | Clock hour used by schedules (see `clock`) |
| `day_index` | – | yes | Integer day (Earth day or sol) used by schedules |
| `zenith_deg` | deg | yes | Solar zenith angle |
| `sun_azimuth_deg` | deg | yes | Solar azimuth, clockwise from north |
| `sun_visible` | – | yes | Fraction of the solar disk above the local horizon |
| `dni_W_m2` | W/m² | yes | Direct (beam) normal irradiance, already multiplied by `sun_visible` |
| `dhi_W_m2` | W/m² | yes | Diffuse horizontal irradiance (0 on the Moon) |
| `ghi_W_m2` | W/m² | yes | Global horizontal irradiance |
| `T_air_K` | K | yes | Near-surface air temperature (`nan` in vacuum) |
| `T_sky_K` | K | yes | Effective sky temperature for long-wave exchange (2.725 K on the Moon) |
| `T_ground_K` | K | yes | Ground (regolith) surface temperature |
| `T_deep_K` | K | yes | Ground temperature at the bottom of ground-contact constructions |
| `ground_albedo` | – | yes | Ground solar reflectance |
| `pressure_Pa` | Pa | yes | Ambient (outdoor) pressure; 0 in vacuum |
| `wind_m_s` | m/s | yes | Wind speed at measurement height (0 in vacuum) |
| `wind_dir_deg` | deg | yes | Wind direction, clockwise from north |
| `L_down_W_m2` | W/m² | no | Downwelling long-wave radiation |
| `Ls_deg` | deg | no | Areocentric solar longitude (Mars season) |
| `dust_tau` | – | no | Column dust optical depth (Mars) |
| `ltst_h` | h | no | Local true solar time (Mars) |
| `lunar_local_time_h` | h | no | Lunar local solar time |
| `humidity_ratio` | kg/kg | no | Outdoor humidity ratio (Earth files only) |

## Checks applied when a file is read

* the first line, required header keys and required columns are present;
* records are equally spaced by `timestep_s`;
* irradiances are non-negative, zenith is within 0–180°, `sun_visible` within 0–1;
* `T_sky_K`, `T_ground_K`, `T_deep_K` lie between 2.725 K and 1000 K;
* `pressure_Pa` is 0 when `atmosphere: none` and positive otherwise.

There are deliberately **no Earth range checks**: a lunar-noon surface at 390 K or a Martian night at 160 K is
valid data.

## Using a PWF file

**ExoBEM (Python)** – in a JSON model:

```json
"site": {"weather_file": "jezero.pwf"}
```

or in Python: `env = exobem.weather.read_pwf("jezero.pwf")`. The model's `timestep_s` must equal the file's.

**Thermonaut (C++)** – in the IDF:

```
Site:PlanetaryBody,
  Habitat, Mars, EarthClock, 2030, autocalculate, 70300, 0.265, 0.15, 6.0, 0.0,
  autocalculate, autocalculate, autocalculate, autocalculate, 3.0, 710, Climatology, 0.5, 0, 0, 0, 3.2, 2.0,
  jezero.pwf;                       !- Planetary Weather File Name
```

No EPW is then needed (`energyplus -d out habitat.idf`). Thermonaut writes a calendar-only EPW to the output
folder for its run-period machinery, keeps computing the sun from its own ephemeris, and interpolates every
other value from the PWF file to its time step (solar columns at mid-interval, state columns at interval end).
The PWF file must cover the run period.

## Producing PWF files from other sources

Any tool can write PWF. For example, Mars Climate Database (MCD) or rover data can be converted by filling the
required columns; quantities the source lacks (e.g. `T_deep_K`) can be taken from an ExoBEM-generated file for
the same site. `exobem.weather.validate(env)` checks a file before use.
