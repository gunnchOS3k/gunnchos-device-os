# Third-Party Service Dependencies

| Service | Integration | Data leaves device | Certification |
|---------|-------------|-------------------|---------------|
| Google Workspace | External browser tab | Yes (Google) | Not certified |
| Netflix / Hulu / Disney+ | External browser tab | Yes | **Not certified** — see PR #45 tracker |
| YouTube | Browser route | Yes | Not certified |
| GitHub / VS Code web | External tab | Yes | Not certified |
| Local HTML5 media | File picker | No (local file) | N/A |

GunnchOS prototype does not embed licensed CDM components.

See [STREAMING_SERVICE_CLAIM_BOUNDARY.md](STREAMING_SERVICE_CLAIM_BOUNDARY.md).
