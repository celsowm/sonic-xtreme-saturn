#!/usr/bin/env bash
# Reproducible offline art-authoring pass; leaves the Saturn game build alone.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
python3 -m unittest discover -s tests -p 'test_jade_concept*.py' -v
python3 -m py_compile tools/create_jade_gully_concept.py tools/jade_concept_dressing.py tools/jade_concept_geometry.py tools/jade_concept_presentation.py
python3 tools/validate_jade_concept.py
if ! command -v blender >/dev/null 2>&1; then
  echo '[jade concept] Blender missing. Install Blender 5.2 LTS (4.x also works).' >&2
  exit 1
fi
blender -b --factory-startup --python-exit-code 1 \
  --python tools/create_jade_gully_concept.py -- "$ROOT/build/jade-gully-concept"
printf '%s\n' \
  '[jade concept] Editable: build/jade-gully-concept/jade_gully_act1_concept.blend' \
  '[jade concept] Full: build/jade-gully-concept/jade-gully-concept-{isometric,top}.png' \
  '[jade concept] Regions: jade-gully-concept-{base,ridges,bamboo,current,summit}.png' \
  '[jade concept] No changes to Saturn game build/rom or legacy Adventure layout.'
