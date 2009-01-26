FC=g77

KERNEL_ROOT_DIR=/local/chris/SALOME2/RELEASES/Install/KERNEL_V5

KERNEL_LIBS= -L$(KERNEL_ROOT_DIR)/lib/salome -lCalciumC -lSalomeDSCSuperv -lSalomeDSCContainer -lSalomeDatastream -lSalomeDSCSupervBasic

all: libfcompo.so

libfcompo.so:compo.o 
	$(FC) -shared -o libfcompo.so compo.o ${KERNEL_LIBS} -Wl,--rpath -Wl,$(KERNEL_ROOT_DIR)/lib/salome -fexceptions
compo.o:compo.f
	$(FC) -c compo.f -I$(KERNEL_ROOT_DIR)/include/salome -fexceptions

clean:
	rm -f *.o *.so

