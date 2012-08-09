A Fortran component dynamically loadable
=============================================

To build this example, modify the ../context.py, ../makefile.inc and Makefile files
to take into account your configuration.

1- your prerequisite file 
2- your KERNEL_ROOT_DIR
3- your FORTRAN compiler

Then set the environment (including PYTHONPATH for YACSGEN, ../.. from here)::

  source <your prerequisite file>

Build the code1 et code2 libraries ::

  make

and process components.py ::

  python components.py

You should get a SALOME module in source form (fcompos_SRC), its installation (install) and
a SALOME application (appli) composed of modules KERNEL, GUI, YACS and the new module fcompos.

To run a coupling:

 1. start SALOME in background : ./appli/runAppli -t
 2. start a SALOME session : ./appli/runSession
 3. start YACS coupler with coupling file : driver coupling.xml
 4. examine output files in /tmp
 5. shutdown SALOME : shutdowSalome.py
 6. exit session : CTRL-D (or exit)
