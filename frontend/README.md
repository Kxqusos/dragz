## MVP Setup

Required environment variables:

- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL`
- `GEOAPIFY_API_KEY`

Current MVP flow:

1. User allows geolocation in the UI.
2. Symptom queries go through the internal `/api/search` pipeline.
3. Exact drug titles go to the pharmacy search branch.
4. Two or more selected pharmacies unlock fastest route building through `/api/route`.

The current implementation keeps demo-safe fallbacks in place so the UI still works when `ref003` or OpenRouter is unstable.
