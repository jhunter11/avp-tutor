# Public teaching and learner-modeling research collection

These sources extend the project's research material. **They are not automatically used by the live tutor, added to approved AVP training examples, or evidence that personalization improves learning.** Raw files stay in ignored `artifacts/public-datasets/`; the repository publishes the pinned URLs, revisions, SHA-256 checksums, acquisition tooling, and intended-use notes.

## Sources and acquisition scope

| ID | Source | Download scope | Intended use / limits |
|---|---|---|---|
| mathdial | [MathDial](https://github.com/eth-nlped/mathdial) | Full published train/test JSONL + source README | Teaching moves and misconception handling. Human teachers interact with simulated students; not a real-student learning-outcome dataset. CC BY-SA 4.0. |
| oatutor | [OATutor Content](https://github.com/CAHLR/OATutor-Content) | Initial 25 lexicographically selected problem bundles; all JSON within those bundles, plus README | Inspect hints, scaffolds, skill structure and per-item attribution. This is a bounded convenience sample, not the full corpus or a representative evaluation sample. CC BY 4.0. |
| mrbench | [MRBench](https://github.com/kaushal0494/UnifyingAITutorEvaluation) | V2 JSON, pedagogical annotation guideline PDF, README | Evaluation of guidance and mistake handling. Contains responses of varying quality, not uniformly positive training targets. CC BY-SA 4.0. |
| csedm | [CSEDM 2019](https://github.com/thomaswp/CSEDM2019-Data-Challenge) | Source documentation only | Programming attempts and correctness for learner modeling. Actual interaction archive requires DataShop account access at dataset 2865; not downloaded. Review dataset-specific terms after access. |
| ednet | [EdNet](https://github.com/riiid/ednet) | Source documentation only | Offline knowledge-tracing/event-model research. Full KT archives not downloaded; acquisition is a separate large-data step. CC BY-NC 4.0, research use; do not silently mix into a general commercial training corpus. |

For MathDial, credit Macina et al. (2023), “MathDial: A Dialogue Tutoring Dataset with Rich Pedagogical Properties Grounded in Math Reasoning Problems.” OATutor content attribution is retained in each original JSON and its README. MRBench and EdNet bibliographic citations are preserved in their downloaded source READMEs. Use the exact source revision and per-item notices when producing derived artifacts. This file is a source inventory, not a blanket grant for every downstream use.

## Fetch and verify

```sh
uv run python -m scripts.fetch_teaching_data
# Or one source:
uv run python -m scripts.fetch_teaching_data --source mathdial
```

The default collection is bounded by `sources.lock.json`; it does not follow links to multi-gigabyte archives or create accounts. Each file must match its published lock checksum before installation. Reruns reuse verified files, replace a corrupt file only after verification, and write a local receipt. Upstream changes do not silently alter an experiment: refresh the lock intentionally and record why. Source documentation for CSEDM and EdNet is not their interaction data.

`inventory.json` records counts and bytes observed during initial acquisition. Counts mean records/files, not approved examples or verified teaching quality. Raw originals remain unchanged. The local download command makes no model requests and uses no model API keys.

## How these enter development

1. Inspect source schemas and pedagogical annotations; retain original records, splits and provenance.
2. Extract teaching patterns into reviewed skill designs or a separate pedagogy index. Do not add raw mathematical dialogue to `knowledge/` as AVP factual evidence.
3. Create instructor-reviewed examples using this project's AVP code and interpreter traces. Keep public-source derivatives labeled with source/license and synthetic versus human provenance.
4. Keep MRBench evaluation separate from positive SFT targets. Audit overlap with MathDial/Bridge before choosing evaluation partitions; merely choosing two different dataset names does not prevent leakage.
5. Use CSEDM/EdNet only in explicit learner-model experiments once their actual data has been acquired. Their students and tasks do not establish which strategy helps an AVP user.
6. Keep local student profiles and consented sessions separate from public datasets. No student identifiers or raw feedback are added to this repository.

The next work is normalization, review and AVP-specific assessment design in phases 1–3 of [the Waterfall plan](../docs/planning/WATERFALL.md). No automatic conversion into the existing approved-training format is provided because source labels, tutoring quality and domain semantics differ.
