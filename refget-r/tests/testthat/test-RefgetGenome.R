# Test RefgetGenome class construction and accessors

test_that("RefgetGenome can be created from FASTA", {
  # Skip if gtars not available
  skip_if_not_installed("gtars")

  # Create test FASTA
  fasta_file <- tempfile(fileext = ".fa")
  writeLines(c(
    ">chr1",
    "ACGTACGTACGTACGTACGT",
    ">chr2",
    "GGCCGGCCGGCCGGCC"
  ), fasta_file)
  on.exit(unlink(fasta_file))

  # Create genome
  genome <- RefgetGenome.from_fasta(fasta_file)

  # Test basic properties
  expect_s4_class(genome, "RefgetGenome")
  expect_equal(length(genome), 2)
  expect_equal(sort(names(genome)), c("chr1", "chr2"))
})

test_that("RefgetGenome accessors work", {
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

  # Test seqlengths
  lens <- seqlengths(genome)
  expect_equal(lens[["chr1"]], 20)
  expect_equal(lens[["chr2"]], 16)

  # Test collection_digest
  digest <- collection_digest(genome)
  expect_type(digest, "character")
  expect_true(nchar(digest) > 0)

  # Test sequence_digests
  seq_digests <- sequence_digests(genome)
  expect_named(seq_digests)
  expect_true(all(c("chr1", "chr2") %in% names(seq_digests)))
})

test_that("RefgetGenome [[ extraction works", {
  skip_if_not_installed("gtars")

  fasta_file <- tempfile(fileext = ".fa")
  writeLines(c(
    ">chr1",
    "ACGTACGTACGTACGTACGT"
  ), fasta_file)
  on.exit(unlink(fasta_file))

  genome <- RefgetGenome.from_fasta(fasta_file)

  # Extract full sequence
  seq <- genome[["chr1"]]

  # Should be character or DNAString depending on Biostrings availability
  if (requireNamespace("Biostrings", quietly = TRUE)) {
    expect_s4_class(seq, "DNAString")
    expect_equal(as.character(seq), "ACGTACGTACGTACGTACGT")
  } else {
    expect_type(seq, "character")
    expect_equal(seq, "ACGTACGTACGTACGTACGT")
  }
})

test_that("RefgetGenome errors on missing sequence", {
  skip_if_not_installed("gtars")

  fasta_file <- tempfile(fileext = ".fa")
  writeLines(c(
    ">chr1",
    "ACGT"
  ), fasta_file)
  on.exit(unlink(fasta_file))

  genome <- RefgetGenome.from_fasta(fasta_file)

  expect_error(genome[["chrX"]], "not found")
})

test_that("RefgetGenome from_directory works", {
  skip_if_not_installed("gtars")

  # Create a store on disk
  store_dir <- tempfile()
  dir.create(store_dir)
  on.exit(unlink(store_dir, recursive = TRUE))

  store <- gtars::refget_store_on_disk(store_dir)

  fasta_file <- tempfile(fileext = ".fa")
  writeLines(c(">seq1", "ACGT"), fasta_file)
  on.exit(unlink(fasta_file), add = TRUE)

  digest <- gtars::add_fasta(store, fasta_file)

  # Load from directory
  genome <- RefgetGenome.from_directory(store_dir, digest = digest)
  expect_s4_class(genome, "RefgetGenome")
  expect_equal(names(genome), "seq1")
})

test_that("RefgetGenome constructor requires digest or alias", {
  skip_if_not_installed("gtars")

  store <- gtars::refget_store()

  expect_error(RefgetGenome(store), "Must provide either")
})
