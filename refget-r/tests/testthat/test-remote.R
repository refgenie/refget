# Test remote store access

test_that("RefgetGenome.from_remote constructor works", {
  skip_if_not_installed("gtars")
  skip("Requires a live remote server")

  # This test requires a live remote server
  cache_dir <- tempfile()
  dir.create(cache_dir)
  on.exit(unlink(cache_dir, recursive = TRUE))

  # Example (would need real server and digest)
  # genome <- RefgetGenome.from_remote(
  #   cache_path = cache_dir,
  #   remote_url = "https://refget.databio.org/store",
  #   digest = "known_digest_here"
  # )
  # expect_s4_class(genome, "RefgetGenome")
})

test_that("coordinate_system accessor works", {
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

  # coordinate_system should return sorted_name_length_pairs_digest
  coord_sys <- coordinate_system(genome)
  expect_type(coord_sys, "character")
  expect_true(nchar(coord_sys) > 0)
})
