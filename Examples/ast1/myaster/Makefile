include ../../makefile.inc

ASTER_INSTALL=$(ASTER_ROOT)/$(ASTER_VERSION)
ASTER_PUB=$(ASTER_ROOT)/public
ASTER_OUTILS=$(ASTER_ROOT)/outils

ASTER_LIBS = -L$(ASTER_INSTALL)/lib -laster \
             -L$(ASTER_PUB)/scotch_4.0/bin -lscotch -lscotcherr \
             -L/local/chris/pkg/med23/install/lib -lmed \
             -lferm -llapack -lhdf5

KERNEL_INCLUDES=-I$(KERNEL_ROOT_DIR)/include/salome
KERNEL_LIBS= -L$(KERNEL_ROOT_DIR)/lib/salome -lCalciumC -lSalomeDSCSuperv -lSalomeDSCContainer \
             -lSalomeDatastream -lSalomeDSCSupervBasic -Wl,--rpath -Wl,$(KERNEL_ROOT_DIR)/lib/salome

FC=gfortran
LD=gfortran
FFLAGS=
CC=gcc
SOURCES= src/op0078.f src/op0189.f src/op0181.f
OBJETS=op0078.o op0189.o op0181.o

CATAPY=catalo/ecrire_maillage.capy  catalo/lecture_force.capy catalo/yacs_init.capy

all:pyth cata astermodule

pyth:
	cp -rf $(ASTER_INSTALL)/bibpyt .

cata: commande/cata.py 
	cp -rf commande/cata.py* bibpyt/Cata

commande/cata.py:$(CATAPY)
	./make_cata $(ASTER_ROOT)/ASTK/ASTK_SERV/bin/as_run $(ASTER_VERSION)

astermodule:astermodule.so pyth
	cp -rf astermodule.so bibpyt

op0078.o:src/op0078.f
	$(FC) -c -fpic $(FFLAGS) $(KERNEL_INCLUDES) src/op0078.f
op0189.o:src/op0189.f
	$(FC) -c -fpic $(FFLAGS) $(KERNEL_INCLUDES) src/op0189.f
op0181.o:src/op0181.f
	$(FC) -c -fpic $(FFLAGS) $(KERNEL_INCLUDES) src/op0181.f
astermodule.so: $(OBJETS)
	$(LD) -shared -o $@ $(OBJETS) $(KERNEL_LIBS) $(ASTER_LIBS)
clean:
	rm -rf *.o *.so bibpyt commande/cata.py*
