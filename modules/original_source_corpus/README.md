# Original Source Corpus Browser

This component is separate from Guardrail Lab's defensive benchmark and from its 52 safe adaptations. It provides searchable provenance and human-review records for the authentic archive without placing raw prompt bodies in the repository or exposing them to automated execution.

## Browse

From the repository root:

```bash
python -m modules.original_source_corpus
python -m modules.original_source_corpus --search gemini
python -m modules.original_source_corpus --id SRC-022 --json
python -m modules.original_source_corpus --id SRC-022 --export-review-template manual_reviews/SRC-022.json
python -m modules.original_source_corpus --verify-archive /path/to/source_archive.zip
```

The browser reads `data/source_corpus/source_inventory.jsonl`. It shows source IDs, paths, sizes, hashes, and status only. It does not display or execute original prompt text. The archive SHA check uses `data/source_corpus/manifest.json`. A blank example of the review template is kept at `manual_reviews/original_source_review_template.json`.

## Inventory validation

The loader validates each non-empty JSONL line before using it:

- Each line must decode to a JSON object; scalar, string, boolean, null, and array values are rejected with a line-numbered `ValueError`.
- Required fields and their types are checked, including a non-negative integer byte count and a 64-character lowercase SHA-256.
- Every inventory record must explicitly set `runnable` to `false`.
- Duplicate source IDs and paths are rejected.
- Unknown source IDs return a clear error and a non-zero exit code.

Regression tests cover these malformed-input cases. The checked-in review template is also compared with the generated template in the test suite, preventing the example and CLI output from silently drifting apart.

## Separation and review

- The original archive is the provenance source; inventory entries are not runnable tests.
- The 52 inert adaptations remain in the defensive Guardrail Lab and are not represented as verbatim originals.
- Review templates are human-authored records. Completing one does not add a source to a runner.
- Withdrawn material and content involving real-world harmful operations, unauthorized access, credential theft, or safeguard evasion must not be converted into executable instructions. Safe research can instead use a bounded, inert test with a separate ID and documented scope.

## Validation

```bash
python -m unittest discover -s tests -p 'test_original_source_corpus.py' -v
```
