# PhD Application Readiness

## Repository role in the PhD portfolio

This repository contains gunnchOS — a service-aware OS/middleware research layer that maps user activity to connectivity, computation, energy, security, and quality-of-experience requirements. It is the decision layer between human activity (WAIKE workloads) and network/compute resources (6G/NTN/local-edge fabric).

gunnchOS is NOT a finished operating system. It is a research middleware concept studied for its service-continuity contributions.

## Current status

**Concept-complete** — Phase 0-1 prototype exists (Docker-based Linux desktop with mode manager, app registry, device profiles). Service profile classification and network selection logic are defined but not fully implemented.

## What is complete

- Mode architecture (Campus Mode, Game Mode, Media Mode)
- Device profiles for all four Device Quartet members
- Privacy/security model documentation
- Fleet management and guardian policy concepts
- Docker-based desktop prototype (launcher mock in React/TypeScript)
- Python mode manager
- App registry framework
- Deploy contracts (DS-XL Coder)
- SBOM and compliance documentation

## What is prototype-pending

- Service profile classifier implementation
- Network selection decision engine
- Compute placement logic
- Graceful degradation automation
- Telemetry collection framework
- Multi-network adaptation
- Real device deployment

## What is simulation-only

- Network selection evaluation (simulated network conditions)
- Compute placement tradeoffs (modeled response times)
- Degradation/recovery behavior (emulated outage scenarios)
- Energy-aware decisions (modeled power consumption)
- Cross-device coordination (emulated device ensemble)

## What is ethics-gated

- Any telemetry from real users
- Guardian/minor policy enforcement with real minors
- Fleet management of devices in schools
- Location-aware mode switching with real users

## Metrics contributed to the research plan

- Service profile transition latency
- Network selection decision time
- Compute placement response time
- Degradation detection time
- Recovery time after outage
- Energy savings from adaptive decisions
- QoE maintenance during degradation
- Mode transition overhead

## Evidence available for faculty review

- Docker-based prototype demonstrating mode management
- Device profile YAML specifications
- Mode manager Python code
- Deploy contract documentation (DS-XL Coder)
- Architecture documentation (phases 0 through 4)
- Privacy and security model

## What must not be claimed yet

- gunnchOS is a finished operating system
- The OS is deployed on real devices
- Service profiles are fully implemented
- Network selection is operational
- Real users have been tested
- The OS replaces existing solutions
- gunnchOS is the primary dissertation contribution

## Simulation and prototype fallback

- Rule-based service profile classifier on synthetic workload traces
- Discrete-event simulation for network selection evaluation
- Emulated network conditions (tc/netem) for degradation testing
- Docker containers mimicking device resource constraints
- Modeled edge/local/cloud response times for compute placement

## Ethics and permissions boundary

- Technical simulation and Docker testing: No ethics review needed
- Algorithm evaluation on synthetic data: No ethics review needed
- Real user testing: Ethics review required
- Minor/school deployment: Full ethics and governance required
- Telemetry from real devices with users: Ethics review required

## Definition of application-ready

This repository is application-ready when:
- Service profile definitions are formally documented with metrics
- Decision engine concept is specified with evaluation criteria
- Simulation plan exists for each decision component
- Open/private/reproducible boundaries are defined
- The repo clearly states gunnchOS is a research middleware concept, not a finished OS
