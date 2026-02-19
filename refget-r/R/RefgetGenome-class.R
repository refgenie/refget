#' RefgetGenome Class
#'
#' A BSgenome-compatible wrapper around a RefgetStore collection that provides
#' chromosome-name-based sequence access.
#'
#' @slot store A gtars RefgetStore object
#' @slot collection_digest Character string containing the seqcol digest
#' @slot seqinfo A Seqinfo object with sequence metadata
#'
#' @exportClass RefgetGenome
setClass(
  "RefgetGenome",
  slots = list(
    store = "ANY",  # gtars RefgetStore
    collection_digest = "character",
    seqinfo = "ANY"  # GenomeInfoDb::Seqinfo
  )
)

#' Create a RefgetGenome object
#'
#' Creates a BSgenome-compatible genome object backed by a RefgetStore.
#'
#' @param store A gtars RefgetStore object
#' @param digest Optional. The collection digest to use.
#' @param namespace Optional. Alias namespace (e.g., "refseq", "genbank")
#' @param alias Optional. Alias name (e.g., "hg38", "GRCh38")
#'
#' @return A RefgetGenome object
#'
#' @details
#' You must provide either `digest` or both `namespace` and `alias`.
#' If using aliases, the function will resolve the alias to a digest using
#' the store's alias system.
#'
#' @examples
#' \dontrun{
#' # Load by digest
#' store <- gtars::refget_store_open_local("/path/to/store")
#' genome <- RefgetGenome(store, digest = "abc123...")
#'
#' # Load by alias
#' genome <- RefgetGenome(store, namespace = "refseq", alias = "GRCh38")
#' }
#'
#' @export
RefgetGenome <- function(store, digest = NULL, namespace = NULL, alias = NULL) {
  # Validate inputs
  if (is.null(digest) && (is.null(namespace) || is.null(alias))) {
    stop("Must provide either 'digest' or both 'namespace' and 'alias'")
  }

  # Resolve alias to digest if needed
  if (is.null(digest)) {
    collection_meta <- gtars::get_collection_by_alias(store, namespace, alias)
    if (is.null(collection_meta)) {
      stop(sprintf("No collection found for alias '%s/%s'", namespace, alias))
    }
    digest <- collection_meta@digest
  }

  # Get level2 data for building Seqinfo
  level2 <- gtars::get_level2(store, digest)
  if (is.null(level2)) {
    stop(sprintf("Collection '%s' not found in store", digest))
  }

  # Build Seqinfo from level2 data
  seqinfo <- GenomeInfoDb::Seqinfo(
    seqnames = level2$names,
    seqlengths = as.integer(level2$lengths)
  )

  new("RefgetGenome",
      store = store,
      collection_digest = digest,
      seqinfo = seqinfo)
}

#' Create RefgetGenome from a directory
#'
#' Convenience constructor that loads a RefgetStore from a directory.
#'
#' @param path Path to the RefgetStore directory
#' @param digest The collection digest to use
#' @param namespace Optional alias namespace
#' @param alias Optional alias name
#'
#' @return A RefgetGenome object
#'
#' @examples
#' \dontrun{
#' genome <- RefgetGenome.from_directory("/path/to/store", digest = "abc123...")
#' }
#'
#' @export
RefgetGenome.from_directory <- function(path, digest = NULL, namespace = NULL, alias = NULL) {
  store <- gtars::refget_store_open_local(path)
  RefgetGenome(store, digest = digest, namespace = namespace, alias = alias)
}

#' Create RefgetGenome from a FASTA file
#'
#' Creates an in-memory RefgetStore from a FASTA file and returns a RefgetGenome.
#'
#' @param fasta_path Path to a FASTA file
#'
#' @return A RefgetGenome object
#'
#' @examples
#' \dontrun{
#' genome <- RefgetGenome.from_fasta("/path/to/genome.fa")
#' }
#'
#' @export
RefgetGenome.from_fasta <- function(fasta_path) {
  store <- gtars::refget_store()
  digest <- gtars::add_fasta(store, fasta_path)
  RefgetGenome(store, digest = digest)
}

#' Create RefgetGenome from a remote store
#'
#' Creates a RefgetGenome backed by a remote RefgetStore with local caching.
#'
#' @param cache_path Local directory for caching downloaded data
#' @param remote_url URL of the remote RefgetStore
#' @param digest The collection digest to use
#' @param namespace Optional alias namespace
#' @param alias Optional alias name
#'
#' @return A RefgetGenome object
#'
#' @examples
#' \dontrun{
#' genome <- RefgetGenome.from_remote(
#'   cache_path = "~/.cache/refget",
#'   remote_url = "https://refget.databio.org/store",
#'   namespace = "refseq",
#'   alias = "GRCh38"
#' )
#' }
#'
#' @export
RefgetGenome.from_remote <- function(cache_path, remote_url, digest = NULL, namespace = NULL, alias = NULL) {
  store <- gtars::refget_store_open_remote(cache_path, remote_url)
  RefgetGenome(store, digest = digest, namespace = namespace, alias = alias)
}

# =============================================================================
# Accessor Methods
# =============================================================================

#' Get the collection digest
#'
#' @param genome A RefgetGenome object
#' @return The seqcol digest string
#' @export
collection_digest <- function(genome) {
  genome@collection_digest
}

#' Get the coordinate system digest
#'
#' Returns the sorted_name_length_pairs digest which identifies the coordinate
#' system. Two genomes with the same coordinate_system() are compatible for
#' coordinate-based operations.
#'
#' @param genome A RefgetGenome object
#' @return The sorted_name_length_pairs digest string
#' @export
coordinate_system <- function(genome) {
  meta <- gtars::get_collection_metadata(genome@store, genome@collection_digest)
  meta@sorted_name_length_pairs_digest
}

#' Get the underlying RefgetStore
#'
#' @param genome A RefgetGenome object
#' @return The gtars RefgetStore object
#' @export
store <- function(genome) {
  genome@store
}

#' Get per-sequence SHA512t24u digests
#'
#' @param genome A RefgetGenome object
#' @return Named character vector of sequence digests
#' @export
sequence_digests <- function(genome) {
  level2 <- gtars::get_level2(genome@store, genome@collection_digest)
  digests <- level2$sequences
  names(digests) <- level2$names
  digests
}

# Standard BSgenome-like accessors via S4 methods

#' @rdname RefgetGenome-class
#' @export
setMethod("seqinfo", "RefgetGenome", function(x) {
  x@seqinfo
})

#' @rdname RefgetGenome-class
#' @export
setMethod("seqnames", "RefgetGenome", function(x) {
  GenomeInfoDb::seqnames(x@seqinfo)
})

#' @rdname RefgetGenome-class
#' @export
setMethod("seqlengths", "RefgetGenome", function(x) {
  GenomeInfoDb::seqlengths(x@seqinfo)
})

#' @rdname RefgetGenome-class
#' @export
setMethod("length", "RefgetGenome", function(x) {
  length(GenomeInfoDb::seqnames(x@seqinfo))
})

#' @rdname RefgetGenome-class
#' @export
setMethod("names", "RefgetGenome", function(x) {
  as.character(GenomeInfoDb::seqnames(x@seqinfo))
})

#' Extract a full sequence by name
#'
#' @param x A RefgetGenome object
#' @param i Sequence name (e.g., "chr1")
#' @return Sequence string or DNAString if Biostrings is available
#' @rdname RefgetGenome-class
#' @export
setMethod("[[", c("RefgetGenome", "character"), function(x, i) {
  record <- gtars::get_sequence_by_name(x@store, x@collection_digest, i)
  if (is.null(record)) {
    stop(sprintf("Sequence '%s' not found in collection", i))
  }
  seq_string <- record@data

  # Convert to DNAString if Biostrings is available
  if (requireNamespace("Biostrings", quietly = TRUE)) {
    return(Biostrings::DNAString(seq_string))
  }
  seq_string
})

#' Show method for RefgetGenome
#'
#' @param object A RefgetGenome object
#' @rdname RefgetGenome-class
#' @export
setMethod("show", "RefgetGenome", function(object) {
  n_seqs <- length(object)
  cat(sprintf("RefgetGenome with %d sequences\n", n_seqs))
  cat(sprintf("  collection_digest: %s\n", object@collection_digest))

  # Show first few sequence names
  seq_names <- names(object)
  if (length(seq_names) > 5) {
    cat(sprintf("  seqnames: %s ... (%d more)\n",
                paste(seq_names[1:5], collapse = ", "),
                length(seq_names) - 5))
  } else {
    cat(sprintf("  seqnames: %s\n", paste(seq_names, collapse = ", ")))
  }
})
