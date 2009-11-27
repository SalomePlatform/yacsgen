include ../../makefile.inc

FC=gfortran

KERNEL_LIBS= -L$(KERNEL_ROOT_DIR)/lib/salome -lCalciumC -lSalomeDSCSuperv -lSalomeDSCContainer -lSalomeDatastream -lSalomeDSCSupervBasic

all: libfcompo.so

libfcompo.so:compo.o 
	$(FC) -shared -fPIC -o libfcompo.so compo.o ${KERNEL_LIBS} -Wl,--rpath -Wl,$(KERNEL_ROOT_DIR)/lib/salome -fexceptions
compo.o:compo.f
	$(FC) -c compo.f -fPIC -I$(KERNEL_ROOT_DIR)/include/salome -fexceptions

clean:
	rm -f *.o *.so

