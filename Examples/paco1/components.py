import os
from module_generator import Generator,Module,Service,PACOComponent

context={'update':1,
         "prerequisites":"/home/aribes/Dev/Scripts_env/prerequis.sh",
         "kernel":"/home/aribes/Dev/Install/SALOME/KERNEL_INSTALL-RIBES",
         "paco":"/home/aribes/Dev/Install/PaCO++_install"
        }

cwd=os.getcwd()

body="""
c = a + b;
"""

c1=PACOComponent("paco1",
                 "dummy",
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
g.make_appli("appli",
             restrict=["KERNEL","GUI","YACS"],
             altmodules={"GUI":"/home/aribes/Dev/Install/SALOME/GUI_INSTALL",
                         "YACS":"/home/aribes/Dev/Install/SALOME/YACS_INSTALL"})

