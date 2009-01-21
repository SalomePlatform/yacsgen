import os
from module_generator import Generator,Module,Service,CPPComponent

context={'update':1,
         "prerequisites":"/local/cchris/.packages.d/envSalome50",
         "kernel":"/local/chris/SALOME2/RELEASES/Install/KERNEL_V5",
        }

cwd=os.getcwd()

body="""
std::cerr << "a: " << a << std::endl;
std::cerr << "b: " << b << std::endl;
int info;
double t1,t2;
int i=1;
int mval;
double val[10],rval[10];
val[0]=3.2;
cp_edb(component,CP_ITERATION,0.,1,"ba",1,val);
info=cp_ldb(component,CP_ITERATION,&t1,&t2,&i,"aa",1,&mval,rval);
std::cerr << "rval: " << rval[0] << std::endl;
c=2*rval[0];
std::cerr << "c: " << c << std::endl;
"""
c1=CPPComponent("compo1",services=[
          Service("s1",inport=[("a","double"),("b","double")],
                       outport=[("c","double")],
                       instream=[("aa","CALCIUM_double","I"),],
                       outstream=[("ba","CALCIUM_double","I"),],
                       defs="//def1",body=body,
                 ),
          ],
         includes="-I/usr/include",
         )


g=Generator(Module("cppcompos",components=[c1],prefix="./install"),context)
g.generate()
g.bootstrap()
g.configure()
g.make()
g.install()
g.make_appli("appli",restrict=["KERNEL","GUI","YACS"])

