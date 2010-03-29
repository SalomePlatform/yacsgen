import os
from module_generator import Generator,Module,Service,PACOComponent

#import context from ..
execfile("../pacocontext.py")

cwd=os.getcwd()

body="""
c = a + b;
"""

c1=PACOComponent("paco1",
                 "mpi",
                 services=[
                   Service("run",inport=[("a","double"),("b","double")],
                           outport=[("c","double")],
                           body=body,
                           impl_type="parallel"
                          ),
                ],
               )


g=Generator(Module("pacocompos",components=[c1],prefix="./install"),context)
g.generate()
g.bootstrap()
g.configure()
g.make()
g.install()
g.make_appli("appli", restrict=["KERNEL"], altmodules={"GUI":GUI_ROOT_DIR, "YACS":YACS_ROOT_DIR})

