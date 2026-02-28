#' Convert sequence to DNAString
#'
#' @param seq_string Character string containing a DNA sequence
#' @return A Biostrings DNAString object
#'
#' @examples
#' \dontrun{
#' dna <- as_DNAString("ACGTACGT")
#' }
#'
#' @export
as_DNAString <- function(seq_string) {
  if (!requireNamespace("Biostrings", quietly = TRUE)) {
    stop("Biostrings package required for DNAString conversion. ",
         "Install with: BiocManager::install('Biostrings')")
  }
  Biostrings::DNAString(seq_string)
}

#' Convert sequences to DNAStringSet
#'
#' @param seq_strings Character vector of DNA sequences
#' @param names Optional names for the sequences
#' @return A Biostrings DNAStringSet object
#'
#' @examples
#' \dontrun{
#' seqs <- as_DNAStringSet(c("ACGT", "GGCC"), names = c("seq1", "seq2"))
#' }
#'
#' @export
as_DNAStringSet <- function(seq_strings, names = NULL) {
  if (!requireNamespace("Biostrings", quietly = TRUE)) {
    stop("Biostrings package required for DNAStringSet conversion. ",
         "Install with: BiocManager::install('Biostrings')")
  }
  result <- Biostrings::DNAStringSet(seq_strings)
  if (!is.null(names)) {
    names(result) <- names
  }
  result
}
