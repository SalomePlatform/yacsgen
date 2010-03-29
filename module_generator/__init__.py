"""
  Package to generate SALOME modules with components
  implemented in C++, Fortran or Python
  that can use datastream ports
"""
from gener import Module, Service, Generator
from fcompo import F77Component
from cppcompo import CPPComponent
from pacocompo import PACOComponent
from pycompo import PYComponent
from astcompo import ASTERComponent
