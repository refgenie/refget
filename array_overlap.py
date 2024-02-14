# from itertools import compress
# from collections import Counter
# overlap = sum((Counter(A) & Counter(B)).values())
# A=example1
# B=example4
# overlap
# all = list(A) + list(set(B) - set(list(A)))
# A_compressed = list(compress(A, B))
# B_compressed = list(compress(B, A))
# A_filtered = list(filter(lambda x: x in B, A))
# B_filtered = list(filter(lambda x: x in A, B))
# len(A_compressed) == len(B_compressed)
# C_compressed = list(compress(C, A))

# from itertools import filter


def array_overlap(A, B):
    A_filtered = list(filter(lambda x: x in B, A))
    B_filtered = list(filter(lambda x: x in A, B))
    A_count = len(A_filtered)
    B_count = len(B_filtered)
    overlap = min(len(A_filtered), len(B_filtered))
    if A_count + B_count < 1:
        # order match requires at least 2 matching elements
        order = None
    elif not (A_count == B_count):
        # duplicated matches means order match is undefined
        order = None
    else:
        order = A_filtered == B_filtered
    return {"overlap": overlap, "order-match": order}


example1 = ["A", "B", "C", "D"]
example2 = ["A", "B", "C"]
example3 = ["A", "B", "C", "B"]
example4 = ["B", "B", "B", "B"]
example5 = ["X", "A", "B", "Y", "C", "D", "E"]
example6 = ["A", "B", "C", "D", "B"]
example7 = ["A", "B", "C", "D", "A"]
example8 = ["A", "B", "C", "D", "B", "A"]


compatoverlap(example1, example2)
compatoverlap(example1, example3)
compatoverlap(example2, example3)
compatoverlap(example1, example4)
compatoverlap(example1, example5)
compatoverlap(example3, example5)
compatoverlap(example5, example3)
compatoverlap(example3, example6)
compatoverlap(example6, example7)
compatoverlap(example7, example8)
compatoverlap(example8, example8)
