import os
from module_generator import Generator,Module,Service,F77Component

#import context from ..
execfile("../context.py")

cwd=os.getcwd()

c1=F77Component("fcode1", services=[Service("serv1",inport=[("a","double"),("b","double")],
                         outport=[("c","double")],
                         outstream=[("PARAM","CALCIUM_double","I")],), ],
                libs="-L%s -lcode1" % cwd,
                rlibs="-Wl,--rpath -Wl,%s" % cwd,
               )

c2=F77Component("fcode2", services=[Service("serv1",inport=[("a","double"),("b","double")],
                         outport=[("c","double")],
                         instream=[("PARAM","CALCIUM_double","I")],), ],
               sources=["code2.f","bidul.f"])

g=Generator(Module("fcompos",components=[c1,c2],prefix="./install"),context)
g.generate()
g.bootstrap()
g.configure()
g.make()
g.install()
g.make_appli("appli",restrict=["KERNEL","GUI","YACS"])

