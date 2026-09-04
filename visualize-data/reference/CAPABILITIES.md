# Capability-to-CLI matrix

| Capability | CLI | Blocking evidence |
|---|---|---|
| Contract | `init`, `contract check` | valid manifest and contract files |
| Static input | `input rasterize` | target-DPI PNG from PNG/PDF/SVG |
| Masks | `mask build`, `mask distance` | exported mask/distance raster |
| Global whitespace | `whitespace audit` | global/panel occupancy and ink bounds |
| Source clipping | `clipping source` | four-edge source-panel clearance |
| Composite clipping | `clipping composite` | four-edge final-slot clearance |
| Panel boundaries | `boundary check` | declared safety-band ink counts |
| Labels/leaders | `labels place`, `labels check` | placement records and collision report |
| Geometry | `geometry check` | isotropic transform and endpoint evidence |
| Raster operations | `raster crop|compose|check` | crop/transform report |
| Print scale | `print check` | physical width and effective DPI |
| Semantic colors | `colors check` | declared color pixel presence |
| Cross-panel consistency | `consistency check` | manifest constraints and evidence |
| Quantitative disclosure | `quantitative check` | units and transformations |
| Scientific integrity | `integrity check` | required-content evidence and approvals |
| Output discipline | `outputs check` | canonical files and hashes |
| Human review | `review init|check` | five categories and current render hash |
| Deviations | `deviations check` | structured deviation records |
| Strict delivery | `qa run --strict` | aggregate report, no blocking findings |
| Skill integrity | `skill check` | frontmatter, ≤100 lines, clean assets |

`capabilities` prints the machine-readable map. Every listed command must have CLI
subprocess coverage; `skill check` is the meta-gate preventing prose-only features.
