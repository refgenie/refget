# Test bulk extraction functions

test_that("extractRegions works with data.frame", {
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

  regions <- data.frame(
    chrom = c("chr1", "chr2"),
    start = c(1, 1),
    end = c(4, 4)
  )

  seqs <- extractRegions(genome, regions, as.character = TRUE)

  expect_length(seqs, 2)
  expect_equal(seqs[[1]], "ACGT")
  expect_equal(seqs[[2]], "GGCC")
})

test_that("extractRegions works with GRanges", {
  skip_if_not_installed("gtars")
  skip_if_not_installed("GenomicRanges")

  fasta_file <- tempfile(fileext = ".fa")
  writeLines(c(
    ">chr1",
    "ACGTACGTACGTACGTACGT"
  ), fasta_file)
  on.exit(unlink(fasta_file))

  genome <- RefgetGenome.from_fasta(fasta_file)

  gr <- GenomicRanges::GRanges(c("chr1:1-4", "chr1:5-8"))

  seqs <- extractRegions(genome, gr, as.character = TRUE)

  expect_length(seqs, 2)
  expect_equal(seqs[[1]], "ACGT")
  expect_equal(seqs[[2]], "ACGT")
})

test_that("extractToFasta writes correct output", {
  skip_if_not_installed("gtars")

  fasta_file <- tempfile(fileext = ".fa")
  writeLines(c(
    ">chr1",
    "ACGTACGTACGTACGTACGT"
  ), fasta_file)
  on.exit(unlink(fasta_file))

  genome <- RefgetGenome.from_fasta(fasta_file)

  regions <- data.frame(
    chrom = c("chr1"),
    start = c(1),
    end = c(8)
  )

  output_file <- tempfile(fileext = ".fa")
  on.exit(unlink(output_file), add = TRUE)

  result <- extractToFasta(genome, regions, output_file)

  expect_equal(result, output_file)
  expect_true(file.exists(output_file))

  # Check content
  content <- readLines(output_file)
  expect_true(length(content) > 0)
})

test_that("exportChromosomes works", {
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

  output_file <- tempfile(fileext = ".fa")
  on.exit(unlink(output_file), add = TRUE)

  # Export just chr1
  result <- exportChromosomes(genome, "chr1", output_file)

  expect_equal(result, output_file)
  expect_true(file.exists(output_file))

  # Read and verify
  content <- readLines(output_file)
  expect_true(any(grepl(">chr1", content)))
  expect_false(any(grepl(">chr2", content)))
})

test_that("exportChromosomes exports all when names is NULL", {
  skip_if_not_installed("gtars")

  fasta_file <- tempfile(fileext = ".fa")
  writeLines(c(
    ">chr1",
    "ACGT",
    ">chr2",
    "GGCC"
  ), fasta_file)
  on.exit(unlink(fasta_file))

  genome <- RefgetGenome.from_fasta(fasta_file)

  output_file <- tempfile(fileext = ".fa")
  on.exit(unlink(output_file), add = TRUE)

  exportChromosomes(genome, NULL, output_file)

  content <- readLines(output_file)
  expect_true(any(grepl(">chr1", content)))
  expect_true(any(grepl(">chr2", content)))
})
