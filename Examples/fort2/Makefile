# Copyright (C) 2009-2013  EDF R&D
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA
#
# See http://www.salome-platform.org/ or email : webmaster.salome@opencascade.com
#

include ../makefile.inc

all:prog1 prog2
prog1:code1.o
	  $(FC) -o prog1 code1.o -L./install/lib/salome -lfcode1Exelib -L$(KERNEL_ROOT_DIR)/lib/salome -lCalciumC
code1.o:code1.f
	  $(FC) -c code1.f -I$(KERNEL_ROOT_DIR)/include/salome -fexceptions 

prog2:code2.o
	  $(FC) -o prog2 code2.o -L./install/lib/salome -lfcode2Exelib -L$(KERNEL_ROOT_DIR)/lib/salome -lCalciumC
code2.o:code2.f
	  $(FC) -c code2.f -I$(KERNEL_ROOT_DIR)/include/salome -fexceptions 

clean:
	rm -rf *.o prog1 prog2 fcode1_inst_1  fcode2_inst_1  fcompos_SRC  install traceExec_proc install.bak fcompos_SRC.bak appli appli.bak
