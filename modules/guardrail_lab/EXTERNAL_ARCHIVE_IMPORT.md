# External prompt archive importer

The importer turns a supplied ZIP into an **inert source inventory** for OpenMind
Jailbreak Lab. It inventories every non-directory member, records its original
relative path, model/folder label, byte count, SHA-256 digest, and keyword-based
attack-pattern tags.

It deliberately does **not** copy prompt bodies into the generated catalog,
execute source content, install source files as system/developer instructions,
or treat keyword matches as proof of a successful bypass. Tags are heuristic
review leads only. Every record starts as `unreviewed_source_record`.

## Run

```bash
python scripts/import_external_prompt_archive.py \
  --input imports/jailbreaks-main.zip \
  --out data/external_prompt_archive_v2.jsonl
```

The ZIP is read in place; members are never extracted. The importer rejects
path traversal and archives exceeding 256 files, 2 MB per member, or 20 MB
total uncompressed size. Keep the source ZIP in a private/local imports folder
unless you have verified redistribution rights.

## Current uploaded collection

The uploaded `jailbreaks-main (1).zip` contains 55 files. The importer is
designed to inventory all of them, including model-specific prompt/config
files, the source README, and empty placeholders. Re-run it against the exact
archive to produce the reproducible 55-record catalog.

## Safety and interpretation

The collection includes prompt/configuration material that references
authority spoofing, refusal suppression, persona and policy reframing,
agent/tool permissions, and in some files malware/credential abuse, sexual
content, or physical-harm boundaries. The importer stores only hashes and
metadata; it does not reproduce operational harmful instructions. Review
individual source files in an isolated, non-executing workflow and use
harmless canaries when testing model behavior.

Pattern labels are broad lexical indicators, not adjudicated classifications.
A source record is not a test result. Confirm any suspected issue with a
controlled test, matched benign controls, repeated observations, and human
review before calling it a finding.
