Compile using "make".

You will need to export liblbfgs to your LD_LIBRARY_PATH to run the code (export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$PWD/liblbfgs-1.10/lib/.libs/).

Run using ./train and specifying an input file (e.g. the beeradvocate.votes file provided). Input files should be a list of quadruples of the form (userID, itemID, rating, time). The file provided has "collapsed" users and items with fewer than 50 ratings so that they are treated as a single user.

For additional datasets see snap.stanford.edu/data

Questions and comments to julian.mcauley@gmail.com
