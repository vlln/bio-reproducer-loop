# Bootstrap Report — Environment Status

## System Overview

| Attribute | Value |
|-----------|-------|
| OS | macOS (Darwin) |
| Architecture | aarch64 (Apple Silicon) |
| CPU | Apple M4, 10 cores |
| Memory | 16 GB (17,179,869,184 bytes) |
| Disk (/) | 228 GB total, 83 GB available |
| Disk (/System/Volumes/Data) | 228 GB total, 83 GB available |

## Runtime Components

### Available

| Component | Version | Provider | Notes |
|-----------|---------|----------|-------|
| R | 4.6.1 | Homebrew (/opt/homebrew/bin/R) | Meets paper requirement (≥ 4.3.0) |
| Docker | 29.4.0 | OrbStack | Working; `hello-world` runs successfully |
| Rscript | 4.6.1 | Homebrew | CLI available |

### Missing

| Component | Required By | Install Option | Notes |
|-----------|------------|----------------|-------|
| Java (≥ 11) | Nextflow runtime | Install via Homebrew (`brew install openjdk@17`) or SDKMAN | Not required by this paper (R-based analysis) |
| Nextflow | Workflow orchestration | Install via `curl -s https://get.nextflow.io \| bash` | Not required by this paper (R-based analysis) |
| Singularity/Apptainer | Alternative container runtime | N/A | Not required; Docker is available |
| Conda | Alternative environment manager | N/A | Not required; R is available natively |

## Container Runtime

- **Docker 29.4.0** (OrbStack) — available and verified
  - Storage Driver: overlayfs
  - Architecture: aarch64
  - CPUs available to Docker: 10
  - Memory available to Docker: 7.818 GiB
  - `docker run hello-world` — PASSED

## Resource Assessment

### Disk
- 83 GB available on root volume — sufficient for R packages and container images
- No paper-specified disk requirements; DESeq2 analysis is lightweight

### Memory
- 16 GB total — sufficient for differential expression analysis of 10 genes × 6 samples

### CPU
- 10 cores — more than sufficient for the minimal analysis

### GPU
- Apple M4 integrated GPU — not required for this analysis

## Host Network

### Active Interfaces

| Interface | IP | Subnet | Notes |
|-----------|-----|--------|-------|
| en1 | 172.19.56.134 | 172.19.0.0/18 | Primary network interface |
| bridge100 | 192.168.139.3 | 192.168.138.0/23 | VM bridge (OrbStack) |
| bridge101 | 192.168.215.0 | 192.168.215.0/24 | VM bridge |
| lo0 | 127.0.0.1 | 127.0.0.0/8 | Loopback |

### DNS
```
nameserver 192.168.53.21
nameserver 192.168.53.20
```

### Proxy
No proxy environment variables configured.

### Routing
- Default route via en1 (172.19.63.254)
- VM bridge default routes via bridge100 and bridge101

## Environment Suitability

This paper is a minimal R-based differential expression analysis using DESeq2. The analysis does not require Java, Nextflow, or a workflow orchestrator. The core runtime (R 4.6.1) is available and exceeds the paper's requirement (R ≥ 4.3.0). Docker is available as a container runtime for any additional dependencies.

### Recommended Approach
- Use native R (4.6.1) for the analysis — it meets the paper requirement and is the simplest path
- Use Docker for R package isolation if needed
- Java and Nextflow are not needed and can be skipped for this benchmark