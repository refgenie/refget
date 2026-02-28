#' Extract regions from a RefgetGenome
#'
#' Efficiently extract multiple genomic regions using BED-based extraction.
#'
#' @param genome A RefgetGenome object
#' @param regions A GRanges object or data.frame with columns: chrom, start, end
#' @param as.character If TRUE, return character vector instead of DNAStringSet
#'
#' @return DNAStringSet or character vector of extracted sequences
#'
#' @examples
#' \dontrun{
#' genome <- RefgetGenome.from_fasta("genome.fa")
#'
#' # From GRanges
#' library(GenomicRanges)
#' regions <- GRanges(c("chr1:1000-2000", "chr2:5000-6000"))
#' seqs <- extractRegions(genome, regions)
#'
#' # From data.frame
#' regions_df <- data.frame(
#'   chrom = c("chr1", "chr2"),
#'   start = c(1000, 5000),
#'   end = c(2000, 6000)
#' )
#' seqs <- extractRegions(genome, regions_df)
#' }
#'
#' @export
extractRegions <- function(genome, regions, as.character = FALSE) {
  # Convert GRanges to data.frame
  if (inherits(regions, "GRanges")) {
    if (!requireNamespace("GenomicRanges", quietly = TRUE)) {
      stop("GenomicRanges package required for GRanges input")
    }
    regions <- data.frame(
      chrom = as.character(GenomicRanges::seqnames(regions)),
      start = GenomicRanges::start(regions),
      end = GenomicRanges::end(regions),
      stringsAsFactors = FALSE
    )
  }

  # Validate columns
  required_cols <- c("chrom", "start", "end")
  if (!all(required_cols %in% names(regions))) {
    stop("regions must have columns: chrom, start, end")
  }

  # Write temp BED file (0-based coordinates for BED)
  bed_file <- tempfile(fileext = ".bed")
  on.exit(unlink(bed_file), add = TRUE)

  bed_df <- data.frame(
    chrom = regions$chrom,
    start = as.integer(regions$start - 1),  # Convert to 0-based
    end = as.integer(regions$end)
  )
  write.table(bed_df, bed_file, sep = "\t", row.names = FALSE,
              col.names = FALSE, quote = FALSE)

  # Use gtars BED extraction
  retrieved <- gtars::get_seqs_bed_file_to_vec(
    genome@store,
    genome@collection_digest,
    bed_file
  )

  # Extract sequence strings
  seqs <- vapply(retrieved, function(r) r@sequence, character(1))

  # Name by region
  result_names <- sprintf("%s:%d-%d", regions$chrom, regions$start, regions$end)
  names(seqs) <- result_names

  # Convert to DNAStringSet if requested
  if (!as.character && requireNamespace("Biostrings", quietly = TRUE)) {
    return(Biostrings::DNAStringSet(seqs))
  }

  seqs
}

#' Extract regions to a FASTA file
#'
#' Write extracted sequences directly to a FASTA file.
#'
#' @param genome A RefgetGenome object
#' @param regions A GRanges object or data.frame with columns: chrom, start, end
#' @param output_path Path for output FASTA file
#'
#' @return Invisibly returns the output path
#'
#' @examples
#' \dontrun{
#' genome <- RefgetGenome.from_fasta("genome.fa")
#' regions <- data.frame(
#'   chrom = c("chr1", "chr2"),
#'   start = c(1000, 5000),
#'   end = c(2000, 6000)
#' )
#' extractToFasta(genome, regions, "extracted.fa")
#' }
#'
#' @export
extractToFasta <- function(genome, regions, output_path) {
  # Convert GRanges to data.frame
  if (inherits(regions, "GRanges")) {
    if (!requireNamespace("GenomicRanges", quietly = TRUE)) {
      stop("GenomicRanges package required for GRanges input")
    }
    regions <- data.frame(
      chrom = as.character(GenomicRanges::seqnames(regions)),
      start = GenomicRanges::start(regions),
      end = GenomicRanges::end(regions),
      stringsAsFactors = FALSE
    )
  }

  # Validate columns
  required_cols <- c("chrom", "start", "end")
  if (!all(required_cols %in% names(regions))) {
    stop("regions must have columns: chrom, start, end")
  }

  # Write temp BED file (0-based coordinates for BED)
  bed_file <- tempfile(fileext = ".bed")
  on.exit(unlink(bed_file), add = TRUE)

  bed_df <- data.frame(
    chrom = regions$chrom,
    start = as.integer(regions$start - 1),  # Convert to 0-based
    end = as.integer(regions$end)
  )
  write.table(bed_df, bed_file, sep = "\t", row.names = FALSE,
              col.names = FALSE, quote = FALSE)

  # Use gtars BED extraction to FASTA
  gtars::get_seqs_bed_file(
    genome@store,
    genome@collection_digest,
    bed_file,
    output_path
  )

  invisible(output_path)
}

#' Export specific chromosomes to FASTA
#'
#' Export one or more complete chromosomes to a FASTA file.
#'
#' @param genome A RefgetGenome object
#' @param names Character vector of chromosome names to export (NULL = all)
#' @param output_path Path for output FASTA file
#' @param line_width Number of bases per line in output (default: 80)
#'
#' @return Invisibly returns the output path
#'
#' @examples
#' \dontrun{
#' genome <- RefgetGenome.from_fasta("genome.fa")
#'
#' # Export specific chromosomes
#' exportChromosomes(genome, c("chr1", "chr2"), "subset.fa")
#'
#' # Export all chromosomes
#' exportChromosomes(genome, NULL, "all.fa")
#' }
#'
#' @export
exportChromosomes <- function(genome, names = NULL, output_path, line_width = 80L) {
  gtars::export_fasta(
    genome@store,
    genome@collection_digest,
    output_path,
    sequence_names = names,
    line_width = as.integer(line_width)
  )
  invisible(output_path)
}
