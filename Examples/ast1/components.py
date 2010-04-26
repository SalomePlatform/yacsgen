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

"""
 Example with one Code_Aster component and one fortran component
"""
import os
from module_generator import Generator,Module,ASTERComponent,Service,F77Component

#import context from ..
execfile("../context.py")

aster_root=os.path.join(aster_home,aster_version)

libfcompodir=os.path.join(os.getcwd(),"fcompo")
myasterdir=os.path.join(os.getcwd(),"myaster","bibpyt")
install_prefix="./install"
appli_dir="appli"

c1=ASTERComponent("caster",services=[
          Service("s1",inport=[("argv","string"),("a","double"),("b","long"),("c","string")],
                       outport=[("d","double")],
                       instream=[("aa","CALCIUM_double","T"),("ab","CALCIUM_double","I"),
                                 ("ac","CALCIUM_integer","I"),("ad","CALCIUM_real","I"),
                                 ("ae","CALCIUM_string","I"),("af","CALCIUM_complex","I"),
                                 ("ag","CALCIUM_logical","I"),
                         ],
                       outstream=[("ba","CALCIUM_double","T"),("bb","CALCIUM_double","I")],
                 ),
         ],
         aster_dir=aster_root,
         python_path=[myasterdir],
         argv=["-memjeveux","4",'-rep_outils',os.path.join(aster_home,'outils')],
         )

c2=F77Component("cfort",services=[
          Service("s1",inport=[("a","double"),("b","long"),("c","string")],
                       outport=[("d","double"),("e","long"),("f","string")],
                       instream=[("a","CALCIUM_double","T"),("b","CALCIUM_double","I")],
                       outstream=[("ba","CALCIUM_double","T"),("bb","CALCIUM_double","I"),
                                  ("bc","CALCIUM_integer","I"),("bd","CALCIUM_real","I"),
                                  ("be","CALCIUM_string","I"),("bf","CALCIUM_complex","I"),
                                  ("bg","CALCIUM_logical","I"),
                         ],
                       defs="",body="",
                 ),
         ],libs="-L%s -lfcompo" % libfcompodir,
           rlibs="-Wl,--rpath -Wl,%s" % libfcompodir)

g=Generator(Module("astmod",components=[c1,c2],prefix=install_prefix),context)
g.generate()
g.bootstrap()
g.configure()
g.make()
g.install()
g.make_appli("appli", restrict=["KERNEL"], altmodules={"GUI":GUI_ROOT_DIR, "YACS":YACS_ROOT_DIR})
