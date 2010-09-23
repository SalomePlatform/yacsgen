A Python component dynamically loadable
===============================================

To build this example, modify the ../context.py file
to take into account your configuration.

1- your prerequisite file 
2- your KERNEL_ROOT_DIR

Then set the environment (including PYTHONPATH for YACSGEN, ../.. from here and execute components.py ::

  source <your prerequisite file>
  python components.py

You should get a SALOME module in source form (pycompos_SRC), its installation (install) and
a SALOME application (appli) composed of modules KERNEL, GUI, YACS and the new module pycompos.

Launch SALOME : ./appli/runAppli -k
activate the pycompos module, look at the doc, activate commands, ...
