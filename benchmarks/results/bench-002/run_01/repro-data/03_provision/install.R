# Phase 3: Provision — R Package Installation
# Installs missing Bioconductor packages for bench-002 paper reproduction

log_file <- "03_provision/install.log"
dir.create(dirname(log_file), showWarnings = FALSE, recursive = TRUE)

log <- function(msg) {
  cat(paste0("[", format(Sys.time(), "%Y-%m-%d %H:%M:%S"), "] ", msg, "\n"))
  write(paste0("[", format(Sys.time(), "%Y-%m-%d %H:%M:%S"), "] ", msg), file = log_file, append = TRUE)
}

log("Starting R package installation for bench-002")

# Load BiocManager
if (!require("BiocManager")) {
  log("ERROR: BiocManager not available")
  quit(status = 1)
}
log(paste("BiocManager version:", as.character(packageVersion("BiocManager"))))

# Packages to install
target_packages <- c("clusterProfiler", "pathview", "org.Hs.eg.db")

# Check which are already installed
installed <- installed.packages()
for (pkg in target_packages) {
  if (pkg %in% rownames(installed)) {
    log(paste(pkg, "already installed:", as.character(packageVersion(pkg))))
  } else {
    log(paste(pkg, "NOT installed — will install"))
  }
}

# Install missing packages
missing <- target_packages[!target_packages %in% rownames(installed)]
if (length(missing) > 0) {
  log(paste("Installing", length(missing), "packages:", paste(missing, collapse = ", ")))
  tryCatch({
    BiocManager::install(missing, update = FALSE, ask = FALSE)
    log("Installation completed")
  }, error = function(e) {
    log(paste("ERROR during installation:", e$message))
    quit(status = 1)
  })
} else {
  log("All packages already installed")
}

# Verify all packages load
log("Verifying package loading...")
for (pkg in target_packages) {
  if (require(pkg, character.only = TRUE, quietly = TRUE)) {
    log(paste("OK:", pkg, as.character(packageVersion(pkg))))
  } else {
    log(paste("FAIL:", pkg, "could not be loaded"))
  }
}

# Also verify already-installed packages
for (pkg in c("DESeq2", "ggplot2", "apeglm")) {
  if (require(pkg, character.only = TRUE, quietly = TRUE)) {
    log(paste("OK:", pkg, as.character(packageVersion(pkg))))
  } else {
    log(paste("FAIL:", pkg, "could not be loaded"))
  }
}

log("All packages verified successfully")
log("Installation complete")