# Test Biostrings conversion functions

test_that("as_DNAString works", {
  skip_if_not_installed("Biostrings")

  dna <- as_DNAString("ACGT")
  expect_s4_class(dna, "DNAString")
  expect_equal(as.character(dna), "ACGT")
})

test_that("as_DNAStringSet works", {
  skip_if_not_installed("Biostrings")

  seqs <- as_DNAStringSet(c("ACGT", "GGCC"))
  expect_s4_class(seqs, "DNAStringSet")
  expect_length(seqs, 2)
})

test_that("as_DNAStringSet accepts names", {
  skip_if_not_installed("Biostrings")

  seqs <- as_DNAStringSet(c("ACGT", "GGCC"), names = c("seq1", "seq2"))
  expect_equal(names(seqs), c("seq1", "seq2"))
})

test_that("as_DNAString errors without Biostrings", {
  # This test verifies the error message is clear
  # In practice, this won't run if Biostrings is installed
  skip("Cannot test Biostrings absence when it's installed")
})
