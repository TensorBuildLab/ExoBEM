# Can we build an extraterrestrial BEM tool from EnergyPlus? — License analysis

*Prepared 2026-11-08 from the license file shipped with EnergyPlus 23.2
(`C:\EnergyPlusV23-2-0\LICENSE.txt`, identical in substance to `LICENSE.txt` in
github.com/NREL/EnergyPlus). This is a practical reading for a research project, not legal advice.*

## Short answer

**Yes.** EnergyPlus is open-source software released under a permissive, BSD-3-Clause-style
license with one extra clause about the name. You may use, study, modify, and redistribute it
(in source or binary form), and build derived tools from it, for research or even commercial purposes.
No fee or permission is needed. You must respect four conditions.

## The four conditions

| Clause | What it requires | How ExoBEM complies |
|---|---|---|
| (1) Source redistribution | Keep the EnergyPlus copyright notice, conditions and disclaimer in redistributed source code. | ExoBEM contains **no EnergyPlus source code**: it is a fresh Python implementation of algorithms documented in the EnergyPlus Engineering Reference. We still credit EnergyPlus and reproduce its license in `NOTICE` and `third_party/EnergyPlus-LICENSE.txt`, so any future EnergyPlus-derived C++ code (roadmap Phase 3) is already covered. |
| (2) Binary redistribution | Reproduce the notice in documentation of binaries. | Same `NOTICE` file; it ships with every distribution. |
| (3) No endorsement | The names of the University of California, LBNL, University of Illinois, U.S. DOE or contributors cannot be used to endorse or promote the derived product without written permission. | The README and paper state that ExoBEM is *not* endorsed by these organizations. |
| (4) Use of the EnergyPlus™ name | A modified product **may not** be called "EnergyPlus", "E+", "e+" or anything confusingly similar in a product name, company name or promotion without DOE's prior written consent. Unmodified redistributions must be called "EnergyPlus version X". | The tool is named **ExoBEM**. It is described factually as "re-implementing the EnergyPlus heat-balance method" (an allowed factual reference, not a product name). |

## Action item: the repository name

The GitHub repository is currently `TensorBuildLab/EnergyPlus-extraterrestrial`. A repository
name works like a product name in practice. To stay clearly within clause (4), we recommend renaming the
repository to `TensorBuildLab/ExoBEM` (GitHub automatically redirects the old URL). The code and
paper never use "EnergyPlus" as the product name.

## Other notes

* The U.S. Government retains a paid-up license to EnergyPlus; this does not restrict you.
* The **weather files** (TMY3 EPW) distributed with EnergyPlus are used only to verify ExoBEM
  against EnergyPlus; they are not redistributed in this repository.
* EnergyPlus bundles third-party components under their own licenses (e.g., Python, `Licenses/`).
  ExoBEM does not redistribute any of them.
* ExoBEM itself is released under the BSD 3-Clause license, which is compatible with the EnergyPlus license.
