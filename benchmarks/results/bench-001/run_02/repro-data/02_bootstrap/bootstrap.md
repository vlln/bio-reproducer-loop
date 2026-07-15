# Bootstrap Report: bench-001 run_02

**Generated:** 2026-07-15T13:25:54Z

## 1. Summary

| Component | Required by Plan | Available | Status |
|-----------|-----------------|-----------|--------|
| Docker | Yes (Bioconductor image) | Yes (29.4.0) | Ready |
| Java 11+ | No (analysis is R-only) | No | Not needed |
| Nextflow | No (no pipeline in plan) | No | Not needed |
| Singularity/Apptainer | No | No | N/A |
| Conda | No | No | N/A |

**Verdict:** Environment is ready. Docker is available and working — the only runtime required by the plan. Java and Nextflow are not required for this reproduction (an R/DESeq2 script running in a Bioconductor Docker container; no Nextflow pipeline).

## 2. Java

- **Status:** NOT installed
- **Details:** `/usr/bin/java` exists but points to the macOS stub. No JDK or JRE found in `/Library/Java/JavaVirtualMachines/`, Homebrew, or system paths.
- **Impact:** None. The plan specifies an R/DESeq2 analysis running in a Docker container. No Java-based tools are required. Nextflow is not used by this analysis.

## 3. Nextflow

- **Status:** NOT available
- **Details:** `nextflow` command not found. The project root contains a Nextflow launcher script, but it requires Java 11+ which is not installed.
- **Impact:** None. The plan does not use Nextflow. The analysis is a standalone R script reconstructed from the Methods section.

## 4. Container Runtime

### Docker

- **Status:** Available and working
- **Version:** Docker Desktop 29.4.0, build 9d7ad9f
- **Path:** `/usr/local/bin/docker`
- **Test:** `docker run --rm hello-world` — passed. Docker daemon is running and can pull/run images.

### Singularity/Apptainer

- **Status:** Not found

### Conda

- **Status:** Not found

## 5. System Resources

| Resource | Available | Plan Requirement | Adequate? |
|----------|-----------|------------------|-----------|
| Disk (/) | 104 GiB free (228 GiB total) | Not specified | Yes |
| Memory | 16 GB (17179869184 bytes) | Not specified | Yes |
| CPU | 10 cores (Apple M4) | Not specified | Yes |
| GPU | Apple M4 (10 GPU cores, Metal 4) | Not specified | N/A |

## 6. Host Network

### Network Interfaces

| Interface | Address | Subnet |
|-----------|---------|--------|
| lo0 | 127.0.0.1 | /8 |
| en1 (primary) | 172.19.56.134 | /18 |
| bridge100 (Docker?) | 192.168.139.3 | /23 |

### Routing

- Default gateway: `172.19.63.254` via `en1`
- Docker bridge network: `192.168.138.0/23` via `bridge100`

### DNS

- Primary: `192.168.53.21` (via en1)
- Secondary: `192.168.53.20` (via en1)

### Proxy

- `HTTP_PROXY`: unset
- `HTTPS_PROXY`: unset
- `NO_PROXY`: unset

## 7. Tests

| Test | Result | Notes |
|------|--------|-------|
| `docker run hello-world` | Passed | Docker daemon operational |
| `nextflow run hello` | Skipped | Java not available; Nextflow not required |

## 8. Nextflow Base Config

**Not generated.** The plan does not use Nextflow — no executor, profile, or resource defaults needed. The reproduction will run an R script directly in a Bioconductor Docker container.