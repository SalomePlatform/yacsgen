#  Copyright (C) 2009-2010  EDF R&D
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

#import context from ..
execfile("../context.py")

import os
from module_generator import Generator,Module,Service,CPPComponent

body="""
std::cerr << "a: " << a << std::endl;
std::cerr << "b: " << b << std::endl;
c=a+b;
std::cerr << "c: " << c << std::endl;
"""
c1=CPPComponent("compo1",services=[
          Service("s1",inport=[("a","double"),("b","double")],
                       outport=[("c","double")],
                       defs="//def1",body=body,
                 ),
          ],
         includes="-I/usr/include",
         )

modul=Module("cppcompos",components=[c1],prefix="./install",
             doc=["*.rst",],
             gui=["cppcomposGUI.cxx","cppcomposGUI.h","Makefile.am","demo.ui","*.png"],
            )

g=Generator(modul,context)
g.generate()
g.bootstrap()
g.configure()
g.make()
g.install()
g.make_appli("appli", restrict=["KERNEL"], altmodules={"GUI":GUI_ROOT_DIR, "YACS":YACS_ROOT_DIR})

