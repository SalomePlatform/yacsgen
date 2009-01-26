import os
from module_generator import Generator,Module,Service,PYComponent

context={'update':1,
         "prerequisites":"/local/cchris/.packages.d/envSalome50",
         "kernel":"/local/chris/SALOME2/RELEASES/Install/KERNEL_V5",
        }

cwd=os.getcwd()

defs="""
import bidul
"""

body="""
      #b1
      dep=calcium.CP_ITERATION
      val=numpy.zeros(10,'d')
      val[5]=a*b
      nval=10
      print "--------> Appel calcium.cp_edb"
      info=calcium.cp_edb(component, dep, 0., 1, "ba", nval,val)
      val=numpy.zeros(10,'d')
      info,tt,ii,mval=calcium.cp_ldb(component, dep, 0.,1., 1, "aa", nval,val)
      print mval,val
      bidul.f()
      c=a+b
      d=a-b
      err=calcium.cp_fin(component,calcium.CP_ARRET)
"""
c1=PYComponent("compo2",services=[
          Service("s1",inport=[("a","double"),("b","double")],
                       outport=[("c","double"),("d","double")],
                       instream=[("aa","CALCIUM_double","I"),],
                       outstream=[("ba","CALCIUM_double","I"),],
                       defs=defs,body=body,
                 ),
         ],
         sources=["bidul.py"],
         )


g=Generator(Module("pycompos",components=[c1],prefix="./install"),context)
g.generate()
g.bootstrap()
g.configure()
g.make()
g.install()
g.make_appli("appli",restrict=["KERNEL","GUI","YACS"])

