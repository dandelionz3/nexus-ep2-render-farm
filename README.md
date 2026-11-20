# nexus-ep2-render-farm

Render farm NEXUS ZERO Episode 2 "THE FIRST DOUBT" (60 dtk, 24 fps, 1440 frame).
Eevee via GitHub Actions (setting B7, samples 6). JANGAN dipakai untuk Ep 1
(repo Ep 1: `nexus-render-farm`).

- `pipeline-nexus/` — build_scene / plan / animate / plan.json (md5 identik
  dengan `~/workspace/shorts/nexus-zero-ep2/pipeline/`).
- `.github/workflows/render-nexus-ep2-test.yml` — tes 120 frame
  (S1 hook + S2 gagap + S4 ECU luka + S8 hero).
- `.github/workflows/render-nexus-ep2-full.yml` — full run 40 job × 72 frame
  (2880 frame 9:16+16:9), Release baru.
