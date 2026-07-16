# Bootstrap Report — bench-002 run_01

Generated: 2026-07-15T11:48 UTC

## 1. Plan Requirements Summary

Per `01_plan/plan.md`, the paper describes a pure R analysis pipeline (DESeq2 → clusterProfiler → pathview). The plan does not require Java, Nextflow, or a workflow engine.

| Component | Required | Version Required |
|-----------|----------|-----------------|
| R | Yes | 4.3.0 |
| Java | No | — |
| Nextflow | No | — |
| Container Runtime | No (R available natively) | — |

## 2. Environment Check Results

### 2.1 Java

**Status: Not installed.**

Java is not required by this plan (pure R analysis). No action needed.

### 2.2 Nextflow

**Status: Not installed.**

Nextflow is not required by this plan (pure R analysis). No action needed.

### 2.3 Container Runtime

| Runtime | CLI | Daemon | Notes |
|---------|-----|--------|-------|
| Docker | 29.4.0 (installed) | Not running | OrbStack socket missing; OrbStack not running |
| Singularity | Not installed | — | — |
| Apptainer | Not installed | — | — |
| Conda | Not installed | — | — |

Docker CLI is installed but the daemon is not running (OrbStack is not started). Since R 4.6.1 is available natively and the plan is a pure R script pipeline, a container runtime is not strictly required. If container-based reproducibility is desired, start OrbStack (`orbstack start`) to enable Docker.

### 2.4 R

**Status: Available.**

```
R version 4.6.1 (2026-06-24) — "Happy Hop"
Platform: aarch64-apple-darwin25.4.0
Library paths:
  - /opt/homebrew/lib/R/4.6/site-library
  - /opt/homebrew/Cellar/r/4.6.1/lib/R/library
```

R 4.6.1 exceeds the plan's requirement of 4.3.0. R package installation will be handled in Phase 3 (Provision).

### 2.5 System Resources

| Resource | Value | Assessment |
|----------|-------|------------|
| CPU | 10 cores (Apple M4) | Adequate for small-scale R analysis |
| Memory | 16 GB | Adequate (20 genes × 6 samples) |
| Disk (/) | 105 GiB free (11% used) | Adequate |
| Disk (/System/Volumes/Data) | 105 GiB free (46% used) | Adequate |
| GPU | Apple M4 (Metal 4) | Not required by plan |

The dataset is small (20 genes × 6 samples). Resource requirements are minimal and well within available capacity.

## 3. Host Network

### 3.1 Interfaces

| Interface | Status | IPv4 | Subnet |
|-----------|--------|------|--------|
| en1 | active | 172.19.56.134 | 172.19.56.0/18 |
| lo0 | active | 127.0.0.1 | /8 |

Other interfaces (en0, en2–en7, bridge0, awdl0, llw0, utun0–3) are inactive or loopback/virtual.

### 3.2 Routing

| Destination | Gateway | Interface |
|-------------|---------|-----------|
| default | 172.19.63.254 | en1 |

### 3.3 DNS

- Primary: 192.168.53.21 (via en1)
- Secondary: 192.168.53.20 (via en1)

### 3.4 Proxy

| Variable | Value |
|----------|-------|
| `HTTP_PROXY` | unset |
| `HTTPS_PROXY` | unset |
| `NO_PROXY` | unset |
| `http_proxy` | http://127.0.0.1:7897 |
| `https_proxy` | http://127.0.0.1:7897 |
| `no_proxy` | unset |

A local HTTP/HTTPS proxy is configured via lowercase environment variables (127.0.0.1:7897). R package installation (`install.packages`, `BiocManager::install`) will use this proxy automatically. Container-based workflows would need explicit proxy configuration.

## 4. Test Results

No tests were run. The plan does not require Nextflow (`nextflow run hello` is not applicable). R installation is verified via `R --version`. Container runtime test is skipped (Docker daemon not running).

## 5. Summary

| Category | Status |
|----------|--------|
| R (required) | Available (4.6.1 ≥ 4.3.0) |
| Java (not required) | Not installed |
| Nextflow (not required) | Not installed |
| Docker | CLI installed, daemon not running |
| Resources | Adequate |
| Network | Recorded |

The environment is ready for Phase 3 (Provision) — R package installation. No blocking issues.