#' @import methods
#' @importFrom GenomeInfoDb Seqinfo seqnames seqlengths
NULL

.onLoad <- function(libname, pkgname) {
  # Check that gtars is available
  if (!requireNamespace("gtars", quietly = TRUE)) {
    packageStartupMessage(
      "Note: gtars package is required but not available. ",
      "Install from: https://github.com/databio/gtars"
    )
  }
}
