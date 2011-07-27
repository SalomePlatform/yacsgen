#  Copyright (C) 2009-2011  EDF R&D
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 2.1 of the License.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA
#
#  See http://www.salome-platform.org/ or email : webmaster.salome@opencascade.com
#

import os,sys
#sys.path.insert(0,"../..")

KERNEL_ROOT_DIR=os.getenv("KERNEL_ROOT_DIR","/local/cchris/Salome/Install/KERNEL_V5")
GUI_ROOT_DIR=os.getenv("GUI_ROOT_DIR","/local/cchris/Salome/Install/GUI_V5")
YACS_ROOT_DIR=os.getenv("YACS_ROOT_DIR","/local/cchris/Salome/Install/YACS_V5")

context={'update':1,
         "makeflags":"",
         "prerequisites":"/local/cchris/.packages.d/envSalome51main",
         "kernel":KERNEL_ROOT_DIR,
         "gui":GUI_ROOT_DIR,
        }


aster_home="/local/cchris/Aster/V10.1/aster"
aster_version="STA10.1"
#aster_home="/local/cchris/Aster/V10/Install"
#aster_version="STA10.0"


