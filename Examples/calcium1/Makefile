
include ../makefile.inc

all:libcode1.so

libcode1.so:code1.o
	  $(FC) -shared -fPIC -o libcode1.so code1.o
code1.o:code1.f
	  $(FC) -c code1.f -fPIC -I$(KERNEL_ROOT_DIR)/include/salome -fexceptions

clean:
	rm -rf *.o *.so install install.bak traceExec_proc appli appli.bak pycompos_SRC pycompos_SRC.bak
