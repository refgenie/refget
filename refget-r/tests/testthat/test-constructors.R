# Test constructor edge cases

test_that("RefgetGenome with invalid digest errors", {
  skip_if_not_installed("gtars")

  store <- gtars::refget_store()

  # A digest that doesn't exist in the store
  expect_error(
    RefgetGenome(store, digest = "nonexistent_digest_abc123"),
    "not found"
  )
})

test_that("RefgetGenome.from_fasta with nonexistent file errors", {
  skip_if_not_installed("gtars")

  expect_error(
    RefgetGenome.from_fasta("/tmp/does_not_exist_xyz.fa")
  )
})

test_that("RefgetGenome.from_directory with nonexistent path errors", {
  skip_if_not_installed("gtars")

  expect_error(
    RefgetGenome.from_directory("/tmp/no_such_store_dir_xyz", digest = "abc")
  )
})

test_that("RefgetGenome with only namespace (missing alias) errors", {
  skip_if_not_installed("gtars")

  store <- gtars::refget_store()

  expect_error(
    RefgetGenome(store, namespace = "refseq"),
    "Must provide either"
  )
})

test_that("RefgetGenome with only alias (missing namespace) errors", {
  skip_if_not_installed("gtars")

  store <- gtars::refget_store()

  expect_error(
    RefgetGenome(store, alias = "hg38"),
    "Must provide either"
  )
})

test_that("RefgetGenome with neither digest nor alias errors", {
  skip_if_not_installed("gtars")

  store <- gtars::refget_store()

  expect_error(
    RefgetGenome(store),
    "Must provide either"
  )
})

test_that("RefgetGenome.from_fasta returns correct class", {
  skip_if_not_installed("gtars")

  fasta_file <- tempfile(fileext = ".fa")
  writeLines(c(">seq1", "ACGT"), fasta_file)
  on.exit(unlink(fasta_file))

  genome <- RefgetGenome.from_fasta(fasta_file)
  expect_s4_class(genome, "RefgetGenome")

  # Verify the digest was set
  d <- collection_digest(genome)
  expect_type(d, "character")
  expect_true(nchar(d) > 0)
})

test_that("RefgetGenome.from_directory roundtrip works", {
  skip_if_not_installed("gtars")

  # Create on-disk store and add FASTA
  store_dir <- tempfile()
  dir.create(store_dir)
  on.exit(unlink(store_dir, recursive = TRUE))

  store <- gtars::refget_store_on_disk(store_dir)
  fasta_file <- tempfile(fileext = ".fa")
  writeLines(c(">chr1", "AAAA", ">chr2", "CCCC"), fasta_file)
  on.exit(unlink(fasta_file), add = TRUE)

  result <- gtars::add_fasta(store, fasta_file)

  # Reload from directory
  genome <- RefgetGenome.from_directory(store_dir, digest = result$digest)
  expect_s4_class(genome, "RefgetGenome")
  expect_equal(length(genome), 2)
  expect_equal(sort(names(genome)), c("chr1", "chr2"))
})
