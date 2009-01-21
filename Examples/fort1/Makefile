
FC=g77

KERNEL_ROOT_DIR=/local/chris/SALOME2/RELEASES/Install/KERNEL_V5

all:libcode1.so libcode2.so
libcode1.so:code1.o
	  $(FC) -shared -o libcode1.so code1.o
code1.o:code1.f
	  $(FC) -c code1.f -I$(KERNEL_ROOT_DIR)/include/salome -fexceptions
libcode2.so:code2.o
	  $(FC) -shared -o libcode2.so code2.o
code2.o:code2.f
	  $(FC) -c code2.f -I$(KERNEL_ROOT_DIR)/include/salome -fexceptions

clean:
	rm -rf *.o *.so 
