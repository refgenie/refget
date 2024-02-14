from itertools import compress
from functools import reduce

import seqcol

sc1 = {"names": ["chr1", "chr2"], "sequences": ["ay89fw", "we4f9x"]}

sc2 = {"names": ["1", "2", "3"], "sequences": ["ay89fw", "we4f9x", "3n20xk2"]}

sc3 = {"names": ["2", "3", "1"], "sequences": ["we4f9x", "3n20xk2", "ay89fw"]}

sc4 = {"names": ["chr1", "3", "2"], "sequences": ["zyt2fw", "9snm23k", "fsd2x3"]}

sc5 = {
    "names": ["chr1", "3", "2"],
    "sequences": ["zyt2fw", "9snm23k", "fsd2x3"],
    "topologies": ["circular", "linear", "linear"],
}



def compat(A, B):
    ainb = [x in B for x in A]
    bina = [x in A for x in B]
    if any(ainb):
        order = list(compress(B, bina)) == list(compress(A, ainb))
    else:
        order = False

    any(ainb)

    flag = 0
    flag += 2 if all(ainb) else 0
    flag += 4 if all(bina) else 0
    flag += 8 if order else 0
    flag += 1 if any(ainb) else 0

    return flag


# New compat function that adds true/false
def compat(A, B):
    ainb = [x in B for x in A]
    bina = [x in A for x in B]
    if any(ainb):
        order = list(compress(B, bina)) == list(compress(A, ainb))
    else:
        order = False

    any(ainb)

    flag = 0
    flag += 2 if all(ainb) else 0
    flag += 4 if all(bina) else 0
    flag += 8 if order else 0
    flag += 1 if any(ainb) else 0
    result = {
        "any-elements-shared": any(ainb),
        "a-subset-of-b": all(ainb),
        "b-subset-of-a": all(bina),
        "order-match": order,
        "flag": flag,
    }
    return result


# For each array:
# - any-elements-shared (1) (0001)
# - all-a-in-b        (2) (0010)
# - all-b-in-a        (4) (0100)
# - order-match       (8) (1000)

# no match: 0000 = 0
# one or more shared elements: 0001 = 1
# all-a-in-b (a is a subset of b, in different order) = 0011 = 3
# all-b-in-a (b is a subset of a, in different order) = 0101 = 5
# same content, different order: 0111 = 7
# a is a subset of b, in same order: 1011 = 11
# b is a subset of a, in same order: 1101 = 13
# identity: 1111 = 15


compat(sc1["sequences"], sc2["sequences"])
compat(sc1["names"], sc2["names"])

compat(sc3["sequences"], sc2["sequences"])
compat(sc3["names"], sc2["names"])

compat(sc1["sequences"], sc3["sequences"])


def compat_all(A, B):
    all_keys = list(A.keys()) + list(set(B.keys()) - set(list(A.keys())))
    result = {}
    for k in all_keys:
        if k not in A or k not in B:
            result[k] = {"flag": -1}
        else:
            result[k] = compat(A[k], B[k])
    # result["all"] = reduce(lambda x,y: x['flag']&y['flag'], list(result.values()))
    return result


compat_all(sc1, sc2)
compat_all(sc3, sc2)
compat_all(sc1, sc3)
compat_all(sc1, sc5)
