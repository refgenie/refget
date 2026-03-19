# Test getSeq methods

test_that("getSeq extracts full sequence", {
  skip_if_not_installed("gtars")

  fasta_file <- tempfile(fileext = ".fa")
  writeLines(c(
    ">chr1",
    "ACGTACGTACGTACGTACGT"
  ), fasta_file)
  on.exit(unlink(fasta_file))

  genome <- RefgetGenome.from_fasta(fasta_file)

  # Full sequence
  seq <- getSeq(genome, "chr1", as.character = TRUE)
  expect_equal(seq, "ACGTACGTACGTACGTACGT")
})

test_that("getSeq extracts regions by coordinates", {
  skip_if_not_installed("gtars")

  fasta_file <- tempfile(fileext = ".fa")
  writeLines(c(
    ">chr1",
    "ACGTACGTACGTACGTACGT"
  ), fasta_file)
  on.exit(unlink(fasta_file))

  genome <- RefgetGenome.from_fasta(fasta_file)

  # Region extraction (1-based, inclusive)
  seq <- getSeq(genome, "chr1", start = 1, end = 4, as.character = TRUE)
  expect_equal(seq, "ACGT")

  seq <- getSeq(genome, "chr1", start = 5, end = 8, as.character = TRUE)
  expect_equal(seq, "ACGT")
})

test_that("getSeq handles negative strand", {
  skip_if_not_installed("gtars")

  fasta_file <- tempfile(fileext = ".fa")
  writeLines(c(
    ">chr1",
    "ACGTACGTACGTACGTACGT"
  ), fasta_file)
  on.exit(unlink(fasta_file))

  genome <- RefgetGenome.from_fasta(fasta_file)

  # Forward strand
  seq_plus <- getSeq(genome, "chr1", 1, 4, strand = "+", as.character = TRUE)
  expect_equal(seq_plus, "ACGT")

  # Reverse complement
  seq_minus <- getSeq(genome, "chr1", 1, 4, strand = "-", as.character = TRUE)
  expect_equal(seq_minus, "ACGT")  # ACGT reverse complement is ACGT
})

test_that("getSeq vectorized extraction works", {
  skip_if_not_installed("gtars")

  fasta_file <- tempfile(fileext = ".fa")
  writeLines(c(
    ">chr1",
    "ACGTACGTACGTACGTACGT",
    ">chr2",
    "GGCCGGCCGGCCGGCC"
  ), fasta_file)
  on.exit(unlink(fasta_file))

  genome <- RefgetGenome.from_fasta(fasta_file)

  # Multiple regions
  seqs <- getSeq(genome,
                 names = c("chr1", "chr2"),
                 start = c(1, 1),
                 end = c(4, 4),
                 as.character = TRUE)

  expect_length(seqs, 2)
  expect_equal(seqs[[1]], "ACGT")
  expect_equal(seqs[[2]], "GGCC")
})

test_that("getSeq errors on out-of-range coordinates", {
  skip_if_not_installed("gtars")

  fasta_file <- tempfile(fileext = ".fa")
  writeLines(c(">chr1", "ACGT"), fasta_file)
  on.exit(unlink(fasta_file))

  genome <- RefgetGenome.from_fasta(fasta_file)

  expect_error(getSeq(genome, "chr1", 1, 100), "out of range")
})

test_that("getSeq with GRanges input works", {
  skip_if_not_installed("gtars")
  skip_if_not_installed("GenomicRanges")

  fasta_file <- tempfile(fileext = ".fa")
  writeLines(c(
    ">chr1",
    "ACGTACGTACGTACGTACGT",
    ">chr2",
    "GGCCGGCCGGCCGGCC"
  ), fasta_file)
  on.exit(unlink(fasta_file))

  genome <- RefgetGenome.from_fasta(fasta_file)

  # Create GRanges
  gr <- GenomicRanges::GRanges(c("chr1:1-4", "chr2:1-4"))

  seqs <- getSeq(genome, gr, as.character = TRUE)

  expect_length(seqs, 2)
  expect_equal(seqs[[1]], "ACGT")
  expect_equal(seqs[[2]], "GGCC")
})

test_that("getSeq returns DNAString when Biostrings available", {
  skip_if_not_installed("gtars")
  skip_if_not_installed("Biostrings")

  fasta_file <- tempfile(fileext = ".fa")
  writeLines(c(">chr1", "ACGT"), fasta_file)
  on.exit(unlink(fasta_file))

  genome <- RefgetGenome.from_fasta(fasta_file)

  seq <- getSeq(genome, "chr1")
  expect_s4_class(seq, "DNAString")
})

test_that("getSeq returns DNAStringSet for multiple sequences", {
  skip_if_not_installed("gtars")
  skip_if_not_installed("Biostrings")

  fasta_file <- tempfile(fileext = ".fa")
  writeLines(c(
    ">chr1",
    "ACGT",
    ">chr2",
    "GGCC"
  ), fasta_file)
  on.exit(unlink(fasta_file))

  genome <- RefgetGenome.from_fasta(fasta_file)

  seqs <- getSeq(genome, c("chr1", "chr2"))
  expect_s4_class(seqs, "DNAStringSet")
  expect_length(seqs, 2)
})
