
FC=g77

KERNEL_ROOT_DIR=/local/chris/SALOME2/RELEASES/Install/KERNEL_V5

all:prog
prog:compo.o
	$(FC) -o prog compo.o -L../install/lib/salome -lcfortExelib
compo.o:compo.f
	$(FC) -c compo.f -I$(KERNEL_ROOT_DIR)/include/salome -fexceptions

clean:
	rm -rf *.o prog

