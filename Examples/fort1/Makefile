
FC=gfortran

KERNEL_ROOT_DIR=/local/cchris/Salome/Install/KERNEL_V5

all:libcode1.so libcode2.so
libcode1.so:code1.o
	  $(FC) -shared -fPIC -o libcode1.so code1.o
code1.o:code1.f
	  $(FC) -c code1.f -fPIC -I$(KERNEL_ROOT_DIR)/include/salome -fexceptions
libcode2.so:code2.o
	  $(FC) -shared -fPIC -o libcode2.so code2.o
code2.o:code2.f
	  $(FC) -c code2.f -fPIC -I$(KERNEL_ROOT_DIR)/include/salome -fexceptions

clean:
	rm -rf *.o *.so 
