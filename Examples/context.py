
import os

KERNEL_ROOT_DIR=os.getenv("KERNEL_ROOT_DIR","/local/cchris/Salome/Install/KERNEL_V5")
GUI_ROOT_DIR=os.getenv("GUI_ROOT_DIR","/local/cchris/Salome/Install/GUI_V5")
YACS_ROOT_DIR=os.getenv("YACS_ROOT_DIR","/local/cchris/Salome/Install/YACS_V5_1_main")

context={'update':1,
         "makeflags":"",
         "prerequisites":"/local/cchris/.packages.d/envSalome5",
         "kernel":KERNEL_ROOT_DIR,
         "paco":"/local/cchris/pkg/paco/install",
         "mpi":"/usr/lib/openmpi",
        }


aster_home="/local/cchris/Aster/V10/Install"
aster_version="STA10.0"


