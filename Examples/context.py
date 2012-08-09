# Copyright (C) 2009-2012  EDF R&D
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

import os,sys
sys.path.insert(0,"../..")

SALOME_ROOT=os.path.expanduser("~/Salome/Install")
SALOME_PREREQ=os.path.expanduser("~/.packages.d/envSalome6main")

KERNEL_ROOT_DIR=os.getenv("KERNEL_ROOT_DIR",os.path.join(SALOME_ROOT,"KERNEL_V6"))
GUI_ROOT_DIR=os.getenv("GUI_ROOT_DIR",os.path.join(SALOME_ROOT,"GUI_V6"))
YACS_ROOT_DIR=os.getenv("YACS_ROOT_DIR",os.path.join(SALOME_ROOT,"YACS_V6"))
GEOM_ROOT_DIR=os.getenv("GEOM_ROOT_DIR",os.path.join(SALOME_ROOT,"GEOM_V6"))

context={'update':1,
         "makeflags":"",
         "prerequisites":SALOME_PREREQ,
         "kernel":KERNEL_ROOT_DIR,
         "gui":GUI_ROOT_DIR,
         "geom":GEOM_ROOT_DIR,
        }


aster_home=os.path.expanduser("~/Aster/V10.3/aster")
aster_version="STA10.3"
