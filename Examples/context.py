# Copyright (C) 2009-2016  EDF R&D
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
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

SALOME_ROOT=os.getenv("SALOME_DIR")
SALOME_PREREQ=os.path.join(SALOME_ROOT, "salome_prerequisites.sh")
#SALOME_PREREQ=os.path.join(SALOME_ROOT, "salome_prerequisites_appli.sh")

KERNEL_ROOT_DIR=os.getenv("KERNEL_ROOT_DIR","")
GUI_ROOT_DIR=os.getenv("GUI_ROOT_DIR","")
YACS_ROOT_DIR=os.getenv("YACS_ROOT_DIR","")
GEOM_ROOT_DIR=os.getenv("GEOM_ROOT_DIR","")

context={'update':1,
         "makeflags":"",
         "prerequisites":SALOME_PREREQ,
         "kernel":KERNEL_ROOT_DIR,
         "gui":GUI_ROOT_DIR,
         "geom":GEOM_ROOT_DIR,
        }


aster_home=os.path.expanduser("~/Aster/V10.3/aster")
aster_version="STA10.3"
