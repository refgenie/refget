# import pephubclient
# from refget.agents import RefgetDBAgent
# import os
#
# # demo_results = {}
# # f ="/home/drc/Downloads/fasta_DL_test/GCA_000001405.29.fa.gz"
# # f="/home/drc/Downloads/hg38.p14.fa.masked.gz"
# # print("Fasta file to be loaded: {}".format(f))
# # demo_results[f] = dbc.seqcol.add_from_fasta_file(f)
# # print(demo_results[f])
# # ENSURE ENVs ARE SET!
# phc = pephubclient.PEPHubClient()
# p = phc.load_project("donaldcampbelljr/add_fasta_to_refget:default")
# fa_root = os.path.expandvars("/home/drc/Downloads/test_adding_fastas/")
# rga = RefgetDBAgent()
# results = rga.seqcol.add_from_fasta_pep(p, fa_root, update=True)
