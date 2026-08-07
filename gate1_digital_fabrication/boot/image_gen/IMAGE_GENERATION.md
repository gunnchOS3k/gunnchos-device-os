# Image Generation (development)

Source: `os_build/image_prototype/`
Output class: **development OS image prototype** (not production signed).
Steps: Dockerfile builds launcher + policy bundle; export tarball/OCI as development artifact.
Physical flash blocked by freeze + `REQUIRES_LOCAL_HARDWARE`.
