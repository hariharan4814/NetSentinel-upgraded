# AI Lab source release

Release scope: the local SIMULATION prototype, separate from the public utility
and the unsigned Windows companion preview. This is source distribution, not a
signed executable or production intrusion-detection product. See `plan.md` for
current validation and unresolved gates; `AI_LAB_SETUP.md` provides startup and
demonstration steps.

## Reproduce the source artifact

After reviewing and committing the dedicated branch:

```powershell
New-Item -ItemType Directory -Force artifacts/release
git archive --format=zip --prefix=NetSentinel-AI-Lab/ --output=artifacts/release/NetSentinel-AI-Lab-source.zip HEAD
Get-FileHash artifacts/release/NetSentinel-AI-Lab-source.zip -Algorithm SHA256
```

`git archive` contains committed source only. Virtual environments, `.env`,
captures, databases, downloaded resources, trained models, test reports and build
outputs must remain excluded. Inspect the archive's entry list before sharing.
Install dependencies from the preserved lockfiles; no dependency binaries,
driver or model weights are bundled. Generated labelled demonstration reports
may be shared separately after inspecting their content.

Keep this release on `codex/ai-lab-prototype` for review. Do not merge the default
branch automatically. To update an installation, stop it, preserve its ignored
lab data directory, review changes and locks, rebuild the frontend, then restart.
The launcher applies committed lab migrations to its own database. Back up that
database while stopped before an upgrade that changes its schema. Original
PostgreSQL migrations/data and companion state are separate.

## Third-party attribution

- scikit-learn 1.9.0 provides Isolation Forest, Random Forest, dummy models and
  evaluation primitives. BSD-3-Clause; retained notice:
  `resources/ai-lab/licenses/scikit-learn-1.9.0.txt`.
- SHAP 0.51.0 provides explanation algorithms. MIT; retained notice:
  `resources/ai-lab/licenses/shap-0.51.0.txt`.
- NumPy, SciPy, pandas and other transitive packages remain pinned in
  `requirements-lab.lock`. Their own distribution metadata/licenses remain in
  installed wheels. Repackaging binaries requires retaining all their notices,
  including bundled numerical-library notices; this source release does not
  redistribute those wheels.
- Existing Django/DRF, Next.js/React and jsPDF/AutoTable dependencies retain their
  existing manifests/locks and notices. No upstream project is rebranded as an
  original algorithm. Papers in the ignored cache are research references and
  are not republished in this artifact.

Resource selection, pinned versions, official URLs, hashes and license evidence
are in `resources/ai-lab/manifest.json`. Optional Qwen weights and CICIDS datasets
are not included. No new project-wide license grant is inferred for the owner's
existing code.

The public website continues to use only `frontend/scripts/build-public.mjs`'s
static allowlist. Never deploy the full source ZIP, lab runtime or model/data
directories to the public host. The optional public recorded AI showcase is
deferred; a successful local demonstration is not a public deployment.
