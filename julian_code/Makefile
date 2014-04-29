CC = g++
CFLAGS = -Wall -O3 -fopenmp -Iliblbfgs-1.10/include
LDFLAGS = -llbfgs -lgomp -Lliblbfgs-1.10/lib/.libs

all: train

liblbfgs-1.10/lib/.libs/liblbfgs.so:
	tar xzvvf liblbfgs-1.10.tar.gz
	cd liblbfgs-1.10 && ./configure && make

train: experience.cpp experience.hpp common.hpp liblbfgs-1.10/lib/.libs/liblbfgs.so
	$(CC) $(CFLAGS) -o train experience.cpp $(LDFLAGS)

clean:
	rm train
