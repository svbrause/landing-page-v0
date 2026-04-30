#!/usr/bin/env bash
# Generate design-aligned medspa images via Vertex AI Imagen 3 (requires:
# gcloud auth, Vertex AI API enabled, billing on project).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/assets/generated-landing"
mkdir -p "$OUT"
PROJECT="$(gcloud config get-value project 2>/dev/null)"
LOCATION="${GOOGLE_CLOUD_LOCATION:-us-central1}"
MODEL="imagen-3.0-generate-001"
URL="https://${LOCATION}-aiplatform.googleapis.com/v1/projects/${PROJECT}/locations/${LOCATION}/publishers/google/models/${MODEL}:predict"

gen_one() {
  local slug="$1"
  local prompt="$2"
  local tmp="$ROOT/.tmp-imagen-${slug}.json"
  echo "→ ${slug} ..."
  curl -sS -X POST \
    -H "Authorization: Bearer $(gcloud auth print-access-token)" \
    -H "Content-Type: application/json; charset=utf-8" \
    "$URL" \
    -d "$(python3 -c 'import json,sys; print(json.dumps({"instances":[{"prompt":sys.argv[1]}],"parameters":{"sampleCount":1}}))' "$prompt")" \
    -o "$tmp"
  python3 -c "
import json, base64, sys
p = sys.argv[1]
with open(p) as f:
    d = json.load(f)
if 'error' in d:
    print('API error:', d['error'], file=sys.stderr)
    sys.exit(1)
b64 = d['predictions'][0]['bytesBase64Encoded']
out = sys.argv[2]
with open(out, 'wb') as f:
    f.write(base64.b64decode(b64))
print('  wrote', out)
" "$tmp" "$OUT/${slug}.png"
  rm -f "$tmp"
}

# Prompts tuned to site palette: ink #241c18, espresso #3a2a24, clay #9c6758,
# rose #c88474, blush #f3ddd4, ivory #fffaf5, cream #f8efe8 — warm editorial luxury.

gen_one "proof-patient-warm-01" "Editorial portrait photograph of one woman in her early forties, relaxed genuine smile, soft natural window light from the left, seamless studio background in warm ivory cream and pale blush beige, luxury medspa and wellness brand aesthetic, shallow depth of field, subtle fine grain, color harmony warm browns dusty rose terracotta and deep espresso shadows, high-end beauty campaign, photorealistic, no text, no logos, no watermark, no clinic charts."

gen_one "medspa-lounge-cream-01" "Interior photograph of a serene high-end aesthetic medspa lounge, minimalist architecture, walls in warm ivory and pale blush plaster, light white oak wood accents, linen curtains diffusing sunlight, single sculptural orchid arrangement in muted coral tones, empty inviting seating, editorial architectural digest style, color grade harmonious with cream rose clay and espresso brown, no signage, no logos, no readable text."

gen_one "patient-soft-portrait-02" "Tight beauty portrait of one woman late thirties, calm confident expression, natural skin texture visible, soft golden side light, background smooth gradient from warm ivory to dusty rose, premium skincare brand photography, muted warm palette matching terracotta rose and deep brown, no jewelry logos, no text, no watermark."

gen_one "lifestyle-tablet-warm-01" "Lifestyle photograph over the shoulder of a woman seated in a cream boucle lounge chair, holding a tablet with a blank bright screen, hands relaxed, medspa waiting area softly blurred behind, warm blush ivory and oak color story, soft bokeh, luxury wellness editorial, no readable UI text on screen, no logos."

echo "Done. Files in $OUT"
