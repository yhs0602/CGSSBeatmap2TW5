# extractfile.py
# extract files from the given file
# usage : extractor.py /input/target/folder/ /output/file/folder < name file
#
# usage on CGSS : 1. file * | grep SQL > dbs.txt
#                 2. python extractor.py /input/target/folder/ /output/file/folder/ < dbs.txt
import sys
import os

idir = sys.argv[1]
odir = sys.argv[2]

for line in sys.stdin:
    strlist = line.split(':')
    # file name : strlist[0]
    filename = idir+strlist[0]
    ofname = odir + strlist[0]+".db"
    # appending db is just for my convenience
    os.rename(filename, ofname)
    print("Moved ", filename, "to ", ofname)
print("Done")
