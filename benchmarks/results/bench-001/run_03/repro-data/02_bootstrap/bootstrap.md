# Bootstrap Report — bench-001 run_03

**Date**: 2026-07-16
**Phase**: 02_bootstrap
**Status**: partial

## Environment Summary

| Property | Value |
|----------|-------|
| OS | macOS (Apple M4) |
| CPU | Apple M4, 10 cores |
| Memory | 16 GB |
| Disk (root) | 228 GiB total, 102 GiB available (12% used) |
| GPU | Apple M4 integrated GPU |

## Runtime Components

### Java

| Component | Status | Version | Provider | Notes |
|-----------|--------|---------|----------|-------|
| Java (OpenJDK) | **Available, not on PATH** | 17.0.19 | Homebrew (`/opt/homebrew/opt/openjdk@17`) | `JAVA_HOME` not set; `java` not found on default `$PATH` |

### Nextflow

| Component | Status | Notes |
|-----------|--------|-------|
| Nextflow | **Not installed** | Required by `provision.nf` and downstream workflow |

### Container Runtime

| Runtime | Status | Version | Notes |
|---------|--------|---------|-------|
| Docker | **Available** | 29.4.0 | Primary runtime |
| Singularity | Not installed | — | — |
| Apptainer | Not installed | — | — |
| Conda | Not installed | — | — |

## Host Network

### Interfaces

| Interface | IP/Mask | Notes |
|-----------|---------|-------|
| en1 | 172.19.56.134/18 | Primary interface, default route |
| bridge100 | 192.168.139.3/23 | VM bridge (Docker may use) |
| lo0 | 127.0.0.1/8 | Loopback |

### Routing

| Destination | Gateway | Interface |
|-------------|---------|-----------|
| default | 172.19.63.254 | en1 |
| 192.168.138/23 | link#24 | bridge100 |

### DNS

| Nameserver |
|------------|
| 192.168.53.21 |
| 192.168.53.20 |

### Proxy

| Variable | Value |
|----------|-------|
| `http_proxy` | `http://127.0.0.1:7897` |
| `https_proxy` | `http://127.0.0.1:7897` |
| `HTTP_PROXY` | (unset) |
| `HTTPS_PROXY` | (unset) |
| `NO_PROXY` | (unset) |

## Resource Assessment

### Against Plan Requirements

The plan (`01_plan/plan.md`) lists the following environment requirements:

| Software | Required Version | Status |
|----------|-----------------|--------|
| R | 4.3.0 | Deferred to container (Phase 3) |
| DESeq2 | 1.42.0 | Deferred to container (Phase 3) |
| ggplot2 | 3.5.0 | Deferred to container (Phase 3) |
| apeglm | 1.24.0 | Deferred to container (Phase 3) |

No explicit Java or Nextflow version requirements are stated in the plan. However, the project uses Nextflow as the workflow engine (`provision.nf`, `nextflow` launcher in repo root).

### Disk

- 102 GiB available — sufficient for Bioconductor Docker image (~2–5 GiB typical) and small analysis data.

### Memory

- 16 GB — sufficient for the small-scale DESeq2 analysis (10 genes × 6 samples).

### CPU

- 10 cores — more than sufficient for the workload.

## Gaps

| Item | Status | Resolution |
|------|--------|------------|
| Java not on PATH | `JAVA_HOME` unset, `java` not in `$PATH` | Add `/opt/homebrew/opt/openjdk@17/bin` to `$PATH` and set `JAVA_HOME` |
| Nextflow not installed | `nextflow` command not found | Install Nextflow (recommend: `curl -s https://get.nextflow.io | bash`) |

## Nextflow Hello Test

Skipped — Nextflow is not yet installed. Will verify after installation.

## Container Test

Docker daemon appears running (version reported). Full container test deferred to Phase 3 (provision), which pulls the Bioconductor image and verifies R packages.