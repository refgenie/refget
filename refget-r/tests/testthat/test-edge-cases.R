# Test edge cases and gaps in current coverage

# -- Single-sequence FASTA ------------------------------------------------

test_that("RefgetGenome works with single-sequence FASTA", {
  skip_if_not_installed("gtars")

  fasta_file <- tempfile(fileext = ".fa")
  writeLines(c(">only_seq", "ACGTACGT"), fasta_file)
  on.exit(unlink(fasta_file))

  genome <- RefgetGenome.from_fasta(fasta_file)

  expect_equal(length(genome), 1)
  expect_equal(names(genome), "only_seq")
  expect_equal(seqlengths(genome)[["only_seq"]], 8)
})

# -- Sequences with N/ambiguous bases -------------------------------------

test_that("getSeq handles sequences with N bases", {
  skip_if_not_installed("gtars")

  fasta_file <- tempfile(fileext = ".fa")
  writeLines(c(">chrN", "ACNNNGTACGT"), fasta_file)
  on.exit(unlink(fasta_file))

  genome <- RefgetGenome.from_fasta(fasta_file)
  seq <- getSeq(genome, "chrN", as.character = TRUE)
  expect_equal(seq, "ACNNNGTACGT")

  # Substring containing Ns
  sub <- getSeq(genome, "chrN", start = 2, end = 6, as.character = TRUE)
  expect_equal(sub, "CNNNG")
})

# -- Partial coordinates (only start or only end) -------------------------

test_that("getSeq with only start=NA returns full sequence", {
  skip_if_not_installed("gtars")

  fasta_file <- tempfile(fileext = ".fa")
  writeLines(c(">chr1", "ACGTACGT"), fasta_file)
  on.exit(unlink(fasta_file))

  genome <- RefgetGenome.from_fasta(fasta_file)

  # Both NA -> full sequence
  seq <- getSeq(genome, "chr1", start = NA, end = NA, as.character = TRUE)
  expect_equal(seq, "ACGTACGT")
})

# -- Coordinate boundary conditions ---------------------------------------

test_that("getSeq works at sequence boundaries", {
  skip_if_not_installed("gtars")

  fasta_file <- tempfile(fileext = ".fa")
  writeLines(c(">chr1", "ACGTACGT"), fasta_file)
  on.exit(unlink(fasta_file))

  genome <- RefgetGenome.from_fasta(fasta_file)

  # start=1, end=seqlength (full range)
  full <- getSeq(genome, "chr1", start = 1, end = 8, as.character = TRUE)
  expect_equal(full, "ACGTACGT")

  # First base only
  first <- getSeq(genome, "chr1", start = 1, end = 1, as.character = TRUE)
  expect_equal(first, "A")

  # Last base only
  last <- getSeq(genome, "chr1", start = 8, end = 8, as.character = TRUE)
  expect_equal(last, "T")
})

# -- extractRegions with single region ------------------------------------

test_that("extractRegions works with a single-row data.frame", {
  skip_if_not_installed("gtars")

  fasta_file <- tempfile(fileext = ".fa")
  writeLines(c(">chr1", "ACGTACGTACGTACGTACGT"), fasta_file)
  on.exit(unlink(fasta_file))

  genome <- RefgetGenome.from_fasta(fasta_file)

  regions <- data.frame(
    chrom = "chr1",
    start = 1,
    end = 4,
    stringsAsFactors = FALSE
  )
  seqs <- extractRegions(genome, regions, as.character = TRUE)

  expect_length(seqs, 1)
  expect_equal(names(seqs), "chr1:1-4")
})

# -- extractRegions error on missing columns ------------------------------

test_that("extractRegions errors on missing required columns", {
  skip_if_not_installed("gtars")

  fasta_file <- tempfile(fileext = ".fa")
  writeLines(c(">chr1", "ACGT"), fasta_file)
  on.exit(unlink(fasta_file))

  genome <- RefgetGenome.from_fasta(fasta_file)

  # Missing 'end' column
  bad_df <- data.frame(chrom = "chr1", start = 1)
  expect_error(extractRegions(genome, bad_df), "must have columns")

  # Wrong column names
  bad_df2 <- data.frame(chromosome = "chr1", begin = 1, finish = 4)
  expect_error(extractRegions(genome, bad_df2), "must have columns")
})

# -- exportChromosomes with nonexistent name ------------------------------

test_that("exportChromosomes with nonexistent chromosome", {
  skip_if_not_installed("gtars")

  fasta_file <- tempfile(fileext = ".fa")
  writeLines(c(">chr1", "ACGT"), fasta_file)
  on.exit(unlink(fasta_file))

  genome <- RefgetGenome.from_fasta(fasta_file)
  output <- tempfile(fileext = ".fa")
  on.exit(unlink(output), add = TRUE)

  # Requesting a nonexistent chromosome should error or produce empty output
  expect_error(exportChromosomes(genome, names = "chrX", output_path = output))
})

# -- show() method --------------------------------------------------------

test_that("show() produces expected output", {
  skip_if_not_installed("gtars")

  fasta_file <- tempfile(fileext = ".fa")
  writeLines(c(
    ">chr1", "ACGTACGT",
    ">chr2", "GGCCGGCC"
  ), fasta_file)
  on.exit(unlink(fasta_file))

  genome <- RefgetGenome.from_fasta(fasta_file)

  out <- capture.output(show(genome))
  expect_true(any(grepl("RefgetGenome with 2 sequences", out)))
  expect_true(any(grepl("collection_digest:", out)))
  expect_true(any(grepl("seqnames:", out)))
})

test_that("show() truncates when >5 sequences", {
  skip_if_not_installed("gtars")

  fasta_file <- tempfile(fileext = ".fa")
  lines <- unlist(lapply(paste0("seq", 1:7), function(nm) {
    c(paste0(">", nm), "ACGT")
  }))
  writeLines(lines, fasta_file)
  on.exit(unlink(fasta_file))

  genome <- RefgetGenome.from_fasta(fasta_file)

  out <- capture.output(show(genome))
  expect_true(any(grepl("more\\)", out)))
})

# -- length(), names(), seqnames() on multi-sequence genome ---------------

test_that("length, names, seqnames work on multi-sequence genome", {
  skip_if_not_installed("gtars")

  fasta_file <- tempfile(fileext = ".fa")
  writeLines(c(
    ">chr1", "AAAA",
    ">chr2", "CCCC",
    ">chr3", "GGGG"
  ), fasta_file)
  on.exit(unlink(fasta_file))

  genome <- RefgetGenome.from_fasta(fasta_file)

  expect_equal(length(genome), 3)
  expect_type(names(genome), "character")
  expect_length(names(genome), 3)

  sn <- seqnames(genome)
  expect_length(sn, 3)
  expect_true(all(c("chr1", "chr2", "chr3") %in% as.character(sn)))
})

# -- coordinate_system() returns a string ---------------------------------

test_that("coordinate_system returns a character string", {
  skip_if_not_installed("gtars")

  fasta_file <- tempfile(fileext = ".fa")
  writeLines(c(">chr1", "ACGTACGT"), fasta_file)
  on.exit(unlink(fasta_file))

  genome <- RefgetGenome.from_fasta(fasta_file)

  cs <- coordinate_system(genome)
  expect_type(cs, "character")
  expect_length(cs, 1)
  expect_true(nchar(cs) > 0)
})

# -- store() returns the underlying RefgetStore ---------------------------

test_that("store() returns the underlying RefgetStore", {
  skip_if_not_installed("gtars")

  fasta_file <- tempfile(fileext = ".fa")
  writeLines(c(">chr1", "ACGT"), fasta_file)
  on.exit(unlink(fasta_file))

  genome <- RefgetGenome.from_fasta(fasta_file)

  s <- store(genome)
  expect_false(is.null(s))
  # The store should be usable with gtars functions
  expect_true(inherits(s, "RefgetStore") || is(s, "RefgetStore"))
})

# -- getSeq as.character flag with Biostrings available -------------------

test_that("getSeq as.character=TRUE returns character even with Biostrings", {
  skip_if_not_installed("gtars")
  skip_if_not_installed("Biostrings")

  fasta_file <- tempfile(fileext = ".fa")
  writeLines(c(">chr1", "ACGTACGT"), fasta_file)
  on.exit(unlink(fasta_file))

  genome <- RefgetGenome.from_fasta(fasta_file)

  # as.character=TRUE should force character output
  seq <- getSeq(genome, "chr1", as.character = TRUE)
  expect_type(seq, "character")
  expect_equal(seq, "ACGTACGT")

  # as.character=FALSE should return DNAString
  seq2 <- getSeq(genome, "chr1", as.character = FALSE)
  expect_s4_class(seq2, "DNAString")
})

test_that("getSeq vectorized as.character=TRUE returns character vector", {
  skip_if_not_installed("gtars")
  skip_if_not_installed("Biostrings")

  fasta_file <- tempfile(fileext = ".fa")
  writeLines(c(
    ">chr1", "ACGTACGT",
    ">chr2", "GGCCGGCC"
  ), fasta_file)
  on.exit(unlink(fasta_file))

  genome <- RefgetGenome.from_fasta(fasta_file)

  seqs <- getSeq(genome, c("chr1", "chr2"), as.character = TRUE)
  expect_type(seqs, "character")
  expect_length(seqs, 2)

  seqs2 <- getSeq(genome, c("chr1", "chr2"), as.character = FALSE)
  expect_s4_class(seqs2, "DNAStringSet")
})

# -- seqinfo returns Seqinfo object ---------------------------------------

test_that("seqinfo returns a Seqinfo object", {
  skip_if_not_installed("gtars")

  fasta_file <- tempfile(fileext = ".fa")
  writeLines(c(
    ">chr1", "ACGTACGT",
    ">chr2", "GGCC"
  ), fasta_file)
  on.exit(unlink(fasta_file))

  genome <- RefgetGenome.from_fasta(fasta_file)

  si <- seqinfo(genome)
  expect_s4_class(si, "Seqinfo")
  expect_true("chr1" %in% GenomeInfoDb::seqnames(si))
})
