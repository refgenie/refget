# This is the function as it stood before I modified it to allow updating an existing colleciton in the database:
# I can probably remove this if the new function works as expected.
# This was on the SequenceCollectionAgent class.


def add(self, seqcol: SequenceCollection) -> SequenceCollection:
    """
    Add a sequence collection to the database, given a SequenceCollection object
    """
    with Session(self.engine, expire_on_commit=False) as session:
        with session.no_autoflush:
            csc = session.get(SequenceCollection, seqcol.digest)
            if csc:  # already exists
                return csc

            csc_simplified = SequenceCollection(
                digest=seqcol.digest,
                sorted_name_length_pairs_digest=seqcol.sorted_name_length_pairs_digest,
            )  # not linked to attributes

            # Check if attributes exist; only create them if they don't
            names = session.get(NamesAttr, seqcol.names.digest)
            if not names:
                names = NamesAttr(**seqcol.names.model_dump())
                session.add(names)

            sequences = session.get(SequencesAttr, seqcol.sequences.digest)
            if not sequences:
                sequences = SequencesAttr(**seqcol.sequences.model_dump())
                session.add(sequences)

            sorted_sequences = session.get(SortedSequencesAttr, seqcol.sorted_sequences.digest)
            if not sorted_sequences:
                sorted_sequences = SortedSequencesAttr(**seqcol.sorted_sequences.model_dump())
                session.add(sorted_sequences)

            lengths = session.get(LengthsAttr, seqcol.lengths.digest)
            if not lengths:
                lengths = LengthsAttr(**seqcol.lengths.model_dump())
                session.add(lengths)

            # This is a transient attribute
            # sorted_name_length_pairs = session.get(
            #     SortedNameLengthPairsAttr, seqcol.sorted_name_length_pairs.digest
            # )
            # if not sorted_name_length_pairs:
            #     sorted_name_length_pairs = SortedNameLengthPairsAttr(
            #         **seqcol.sorted_name_length_pairs.model_dump()
            #     )
            #     session.add(sorted_name_length_pairs)

            name_length_pairs = session.get(NameLengthPairsAttr, seqcol.name_length_pairs.digest)
            if not name_length_pairs:
                name_length_pairs = NameLengthPairsAttr(**seqcol.name_length_pairs.model_dump())
                session.add(name_length_pairs)

            # Link the attributes back to the sequence collection
            names.collection.append(csc_simplified)
            sequences.collection.append(csc_simplified)
            sorted_sequences.collection.append(csc_simplified)
            lengths.collection.append(csc_simplified)
            # sorted_name_length_pairs.collection.append(csc_simplified)
            name_length_pairs.collection.append(csc_simplified)

            session.commit()
            return csc_simplified
