# Native physics records, synchronized views and previews

Use when the user wants actual simulation video, collision inspection, repeatable playback or portfolio media. Render solved state records; keep the source solver test distinct from later playback and presentation. Do not substitute generated imagery or prescribed deformation for native physical evidence.

## Record once, render consistently

Record the runtime and solver configuration, input asset hashes, body path/order, native positions/quaternions, deformable node order/topology, simulation sample times, phase/load histories and contacts used. Save native CAD-skin vertices where available, or describe and validate any solver-to-visual mapping. Never infer motion from vertex counts alone.

Keep timestep, recorded sampling interval and presentation fps separate. Store an explicit frame-to-sample map when retiming phases. Use the same map for material view, collision view and all close-ups; verify at least body and release-handle transforms against the source record. Deformation amplification, glyph sizes, geometric thickness added only for display and any scene scale must be declared. A longer video made from a short test is slow-motion presentation, not a real-time performance result.

The optional NumPy helper checks structural integrity of a local, trusted NPZ without loading pickle data:

```sh
python scripts/check_sim_record.py trajectory.npz \
  --time-key telemetry --time-column 0 --pose-key body_q \
  --deform-key shell_q --quaternion-order xyzw \
  --frame-map frame_indices.json --report /project/_conversion_work/reports/record.json
```

Arrays are configured explicitly: poses have shape `(samples, ..., 7)` with xyz first; deformable states have shape `(samples, ..., 3)`. A 1-D time array does not need `--time-column`. Quaternion order is recorded for downstream interpretation; norm checks alone cannot detect swapped components. Frame maps are JSON lists of integer sample indices; holds and reverse playback are allowed. The helper checks shapes, finite values, time order, quaternion norms and map bounds, not mechanical success, contact identity or full topology preservation.

## Build a playback scene without changing the physical source

Work on a copy/session layer. Disable physics for replay deliberately; document that Play advances recorded states rather than recomputing contacts. Do not embed an assumed auto-executing Python controller in a portable USD. State whether users must press Play, run a script or enable a particular runtime feature.

When copying prims, remap internal relationship targets and attribute connections for bodies, joints, attachments, materials and shaders. Flattening a stage can create sibling class/prototype definitions: copying only the default prim can omit them. Inspect all relevant root definitions, including classes, preserve their internal references and compare mesh coverage with instance proxies. `Stage.Export()` flattens composition; use root-layer export when the deliverable should retain composition arcs. Flattening does not embed image assets.

For animated meshes, author compatible points, topology and extents. Use native skinned output where available. Validate source/rest state, a loaded/deformed state, release and final clearance after reopening the exported USD. The material scene and the diagnostic scene should carry the same record hash and frame mapping.

Use `scripts/inspect_usd.py` for portable static checks:

```sh
python scripts/inspect_usd.py /project/final_usd/module.usd \
  --package-root /project/final_usd \
  --report /project/_conversion_work/reports/module-usd.json
```

This requires a Python environment with `pxr`. It inventories authored collision/rigid/deformable APIs, units, references, connections and dependencies. It does not inspect cooked PhysX contact geometry, all variants, unloaded payloads or dynamic behavior. For runtime-specific APIs, raw authored tokens can be visible even when a standalone USD build has no corresponding schema plugin. Dependency containment checks apply to filesystem resources; remote resources need an explicit resolver and separate packaging.

## Material view, collision view and close-ups

- Preserve the source housing and materials in the opaque view. A cabinet can provide visual context without implying a full-rack physics solve; label the actual tested port scope.
- Display collider boundaries, actual convex hulls where available and deformable states in the diagnostic view. An SDF input surface is not a screenshot of the cooked SDF cells. Do not label visual triangles as the exact cooked collision surface.
- Project only recorded contact positions. Declare body/shape identity limits and whether FEM contacts are included. Enlarge glyphs for legibility without implying measured contact-patch size.
- Use synchronized mechanism close-ups when useful. Three stacked panels worked for latch, board contacts and EMI fingers in one example; panel count and layout follow the user's request, not a universal format.

Choose camera framing at outside, seated, unlocked and extracted states so the plug/handle is not clipped. Preview those states before rendering the full sequence. Preserve motion; presentation camera movement is separate from the solver's motion. Keep labels concise and avoid plots or numeric overlays when the user asks for pictures only.

Use a bounded headless process and verify actual device mapping; see [Isaac delivery](isaac-and-delivery.md). Do not reuse a historical GPU index, server address or renderer installation path as a default. Render a few representative frames first, then encode the requested video and fully decode it to detect truncated output.

## GIFs and bilingual portfolio delivery

GitHub READMEs can display a looping GIF linked to a higher-quality MP4. Generate the GIF from the actual rendered video by temporal sampling and palette conversion, without optical-flow motion generation. Keep all requested phases; trade resolution, frame rate and palette size against file weight. GIF frame duration uses centiseconds, so presentation duration may differ slightly from a nominal fps. A cropped preview should retain meaningful geometry and not remove adverse contact behavior.

```sh
python scripts/make_preview_gif.py /project/media/insertion.mp4 \
  /project/media/preview.gif --ffmpeg /path/to/ffmpeg --ffprobe /path/to/ffprobe \
  --width 960 --fps 8 --colors 128 \
  --report /project/_conversion_work/reports/preview.json
```

The helper uses separate palette-generation and conversion passes, selects real decoded frames and verifies all GIF frames decode. It refuses existing outputs/reports and removes incomplete outputs from its own failed run. Reports include source/output hashes, settings, duration, frame count and full-decode status. It neither authenticates the source as physics nor supplies a physics/video renderer. Pair it with the solver record and render provenance.

Keep English `README.md` and Chinese `README.zh-CN.md` synchronized when requested; put language links at the top. Use relative media links and link the preview to the actual MP4. Refresh checksums after Git text normalization; reopen the committed archive if transport/normalization changes could invalidate the manifest. Keep proprietary source assets and large node/skin caches out of a public skill repository. Case-specific datasets and videos belong in the user's authorized portfolio location, with source/license and validation-scope notes.
