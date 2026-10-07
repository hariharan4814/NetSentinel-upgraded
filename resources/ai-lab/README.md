# AI Lab external resource cache

Acquired **2026-10-04**, following the user's instruction to download external
resources before application coding. No downloaded package was installed and
no downloaded source, notebook or model code was executed.

## Implementation update — 2026-10-05

The acquisition record below is historical. The 20 pinned wheels have since been
installed offline into the separate `.venv-lab` environment and exercised by real
training and SHAP tests. `requirements-lab.lock` is the application runtime lock.
Optional dataset CSV and LLM weights remain unavailable/deferred as listed.

## What was acquired

| Resource | Saved content | Purpose / status |
| --- | --- | --- |
| scikit-learn 1.9.0 | Official source archive, Windows CPython 3.11 wheel, license, release metadata and API/splitting references | Existing version preserved; resource integrity VERIFIED |
| SHAP 0.51.0 | Official source archive, Windows CPython 3.11 wheel, MIT license and explanation/release references | Python 3.11 candidate; runtime integration NOT_STARTED |
| ML dependency cache | 20 wheels total, including the existing eight pinned ML requirements and SHAP's resolved dependencies | Publisher hashes and offline dependency resolution VERIFIED; packages not installed |
| Research papers | Isolation Forest (2008), Random Forests (2001), original SHAP paper (2017, v2) | PDFs from author universities/arXiv; signature/trailer checks passed |
| CICIDS2017 | Official dataset description, citation terms and registration page | Documentation saved; actual CSV dataset BLOCKED by registration step |
| Optional Qwen assistant | Official model metadata, model card, configuration and Apache-2.0 license | Revision pinned; model weights/runtime DEFERRED |

**40 inventoried artifacts**, approximately **129 MB**, plus small verification
and publisher-metadata files. Papers were downloaded as research references;
they were not visually reviewed or reproduced in a project report.

## Inventory and layout

- [manifest.json](manifest.json): exact original URLs, versions/revisions, paths,
  sizes, SHA-256, verification scope, licenses, checks and pending items.
- [wheels-win-py311.lock](wheels-win-py311.lock): exact 20-package candidate set
  with hashes for Windows x64 / Python 3.11. This is an acquisition lock,
  **not a replacement for the application's requirements or lockfiles**.
- `downloads/sources/`: two untouched upstream source distributions.
- `downloads/wheels/`: binary wheels; no source compilation/setup execution.
- `downloads/licenses/`, `references/`, `papers/`, `metadata/`,
  `model-reference/`: original reference resources.
- `downloads/evidence/`: integrity checks, offline resolver report, public
  advisory response and installed-package snapshots before/after acquisition.

The entire `downloads/` directory is excluded from Git. Do not force-add it or
copy it into the public static build. A new checkout needs these files restored
or re-fetched from manifest URLs and checked against expected hashes; the
inventory does not itself contain the binary resources.

## Selection and licensing

- [scikit-learn](https://github.com/scikit-learn/scikit-learn) supplies estimators,
  grouped validation and metrics under BSD-3-Clause. Version 1.9.0 preserves the
  existing pin, avoiding an unrelated upgrade.
- [SHAP 0.51.0](https://pypi.org/project/shap/0.51.0/) supports this Python 3.11
  download target; [0.52.0](https://pypi.org/project/shap/0.52.0/) requires Python
  3.12 or newer. Saved stable SHAP docs can describe newer APIs; inspect the
  cached 0.51.0 source during integration. Its license is MIT.
- Every wheel contains bundled license/notice files; archive paths are recorded
  in the inventory. Binary dependencies can have multiple notices, including
  NumPy's bundled components, LLVM exceptions and tqdm's MPL-2.0/MIT terms.
  Review these before distribution; do not describe every dependency as MIT.
- Paper PDFs remain copyrighted research references, not open-source code.
  Attribute and link to originals in the dissertation; do not automatically
  bundle them into a public software release.
- [CICIDS2017's official page](https://www.unb.ca/cic/datasets/ids-2017.html)
  supplies research/citation terms. Its download link opens a registration form.
  No identity details were guessed/submitted or unverified mirror substituted.
- The optional [Qwen3-4B-Instruct-2507 model](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507)
  reference is pinned to `cdbee75f17c01a7cc42f958dc650907174af0554`, with its
  Apache-2.0 license. There are **no weights**, tokenizer bundle or inference
  runtime in this cache; hardware/quantization selection remains future work.

Paper originals: [Isolation Forest](https://cs.nju.edu.cn/zhouzh/zhouzh.files/publication/icdm08b.pdf),
[Random Forests](https://www.stat.berkeley.edu/~breiman/randomforest2001.pdf),
[SHAP](https://arxiv.org/abs/1705.07874v2).

## Verification performed

1. All 20 wheels and both source archives match official PyPI size/SHA-256
   values; selected distributions were not marked yanked by that metadata.
2. Wheel ZIP CRCs, name/version metadata and safe member paths passed. Bundled
   license files were found in every wheel. Source archive structure/member
   bounds and licenses passed; archives were not extracted.
3. JSON parsed; HTML contained expected identifiers; PDFs had PDF header/end
   markers. References without publisher digests have local hashes only, which
   are not authenticity signatures or audits of upstream code.
4. Offline hash-required resolution succeeded using `--dry-run --ignore-installed
   --no-index`. This proves resolver consistency, **not runtime imports or SHAP
   explanation correctness**.
5. Before/after installed-package inventories were identical. Existing
   application requirements/lockfiles and the frontend user edit were preserved.
6. OSV's public version lookup returned no advisory IDs for the 20 queried
   versions at acquisition time. Raw query/response are saved. This is a limited
   lookup, not a security guarantee; repeat before installation/release.

The existing Python 3.11 interpreter/pip 22.3 worked with scoped execution
permission outside the sandbox. Earlier startup/socket errors under restrictions
did not require rebuilding the environment.

Repeat offline resolution from the repository root (no installation):

```powershell
.\.venv-ml\Scripts\python.exe -m pip --isolated --disable-pip-version-check install --dry-run --ignore-installed --no-index --no-cache-dir --find-links resources/ai-lab/downloads/wheels --require-hashes -r resources/ai-lab/wheels-win-py311.lock
```

## Remaining acquisition and integration

- **CICIDS2017 CSV — BLOCKED:** complete the
  [official registration](https://cicresearch.ca/CICDataset/CIC-IDS-2017/) and
  supply the authorized link. Then obtain a bounded labelled flow CSV resource,
  record its terms/hashes and inspect the schema. No raw PCAP/payload archives.
  Core simulator work does not require this optional benchmark.
- **LLM weights/runtime — DEFERRED:** choose a tested runtime/quantization that
  fits the laptop before downloading gigabytes. Core models need no LLM/GPU.
- **Integration — NOT_STARTED:** no model import/training, feature generation,
  migration, UI change or application test was performed. Install into an
  isolated lab environment only during the later coding phase; preserve the
  original research environment. Test sklearn/NumPy/Numba/SHAP interaction,
  prediction parity and explanation additivity before adopting dependencies.

Continue A1 in [plan.md](../../plan.md) when coding resumes. Downloads do not
satisfy model accuracy, application or LIVE verification gates. Consult hashes
before repeating downloads.
