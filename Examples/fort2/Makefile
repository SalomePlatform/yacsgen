
include ../makefile.inc

FC=gfortran

all:prog1 prog2
prog1:code1.o
	  $(FC) -o prog1 code1.o -L./install/lib/salome -lfcode1Exelib
code1.o:code1.f
	  $(FC) -c code1.f -I$(KERNEL_ROOT_DIR)/include/salome -fexceptions 

prog2:code2.o
	  $(FC) -o prog2 code2.o -L./install/lib/salome -lfcode2Exelib
code2.o:code2.f
	  $(FC) -c code2.f -I$(KERNEL_ROOT_DIR)/include/salome -fexceptions 

clean:
	rm -rf *.o prog1 prog2 fcode1_inst_1  fcode2_inst_1  fcompos_SRC  install traceExec_proc
