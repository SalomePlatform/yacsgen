"""
 Example with one Code_Aster component and one fortran component
"""
import os
from module_generator import Generator,Module,ASTERComponent,Service,F77Component

#import context from ..
execfile("../context.py")

aster_root=os.path.join(aster_home,aster_version)

fcompodir=os.path.join(os.getcwd(),"fcompo")
myasterdir=os.path.join(os.getcwd(),"myaster","bibpyt")

install_prefix="./install"
appli_dir="appli"

c1=ASTERComponent("caster",services=[
          Service("s1",inport=[("jdc","file"),("a","double"),("b","long"),("c","string")],
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
         kind="exe",
         exe_path=os.path.join(os.getcwd(),"exeaster"),
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
         ],
         kind="exe",
         exe_path=os.path.join(fcompodir,"prog"),
         )

g=Generator(Module("astmod",components=[c1,c2],prefix=install_prefix),context)
g.generate()
g.bootstrap()
g.configure()
g.make()
g.install()
g.make_appli(appli_dir,restrict=["KERNEL","GUI","YACS"])
