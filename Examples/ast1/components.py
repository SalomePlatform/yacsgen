"""
 Example with one Code_Aster component and one fortran component
"""
import os
from module_generator import Generator,Module,ASTERComponent,Service,F77Component

context={'update':1,"prerequisites":"/local/cchris/.packages.d/envSalome50",
          "kernel":"/local/chris/SALOME2/RELEASES/Install/KERNEL_V5"}
aster_root="/local/chris/ASTER/instals/NEW9"

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
         argv=["-memjeveux","4",'-rep_outils','/local/chris/ASTER/instals/outils'],
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
g.make_appli(appli_dir,restrict=["KERNEL","GUI","YACS"])