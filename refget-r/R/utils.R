#' Reverse complement a DNA sequence
#'
#' @param seq DNA sequence string
#' @return Reverse complement string
#' @keywords internal
.reverse_complement <- function(seq) {
  # Use Biostrings if available (faster and handles IUPAC codes)
  if (requireNamespace("Biostrings", quietly = TRUE)) {
    rc <- Biostrings::reverseComplement(Biostrings::DNAString(seq))
    return(as.character(rc))
  }

  # Pure R fallback for basic ACGT
  complement_map <- c(
    A = "T", T = "A", G = "C", C = "G",
    a = "t", t = "a", g = "c", c = "g",
    N = "N", n = "n"
  )

  chars <- strsplit(seq, "")[[1]]
  complemented <- complement_map[chars]
  # Handle unknown characters by keeping them
  complemented[is.na(complemented)] <- chars[is.na(complemented)]
  paste(rev(complemented), collapse = "")
}

#' Null coalescing operator
#' @keywords internal
`%||%` <- function(x, y) if (is.null(x)) y else x
