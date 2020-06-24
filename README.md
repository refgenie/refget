# refget-py

I made two demos:

- [demo](demo.ipynb): shows how to create a redis or local database, load up some sequences and collections, and use refget to retrieve a fasta file
- [advanced](advanced.ipynb): shows how to do sequence-level comparisons between two checksums, revealing structure of the relationship (*e.g.* ordering differences, naming mismatches, sequence subsets).


```
docker run -it --network "host" mongo


```

To link to persistent data on rivanna:

```
docker run --user=854360:25014 -p 27017:27017 -v /ext/qumulo/database/mongo:/data/db mongo
```
I have to use the user that matches the one on the filesystem.