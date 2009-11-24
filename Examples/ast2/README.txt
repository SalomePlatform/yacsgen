A Code_Aster standalone component (in executable form)
===========================================================

To build this example, modify the files components.py, fcompo/Makefile, myaster/config.txt, myaster/Makefile
to take into account your configuration.

1- your prerequisite file 
2- your KERNEL_ROOT_DIR
3- your Code_Aster installation

Then set the environment (including PYTHONPATH for YACGEN, ../.. from here and execute components.py ::

  source <your prerequisite file>

process components.py ::

  python components.py

You should get a SALOME module in source form (pycompos_SRC), its installation (install) and
a SALOME application (appli) composed of modules KERNEL, GUI, YACS and astmod_SRC.

Build the fcompo library ::

  cd fcompo
  make

Build the Code_Aster library ::

  cd myaster
  make

To run a coupling:

 1. start SALOME in background : ./appli/runAppli -t
 2. start a SALOME session : ./appli/runSession
 3. start YACS coupler with coupling file : driver coupling.xml
 4. examine output files in /tmp
 5. shutdown SALOME : shutdownSalome.py
 6. exit session : CTRL-D (or exit)
