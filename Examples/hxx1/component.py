import os
from module_generator import Generator,Module,Service
from module_generator import CPPComponent,PYComponent,HXX2SALOMEComponent

kernel_root_dir=os.environ["KERNEL_ROOT_DIR"]
gui_root_dir=os.environ["GUI_ROOT_DIR"]
yacs_root_dir=os.environ["YACS_ROOT_DIR"]
med_root_dir=os.environ["MED_ROOT_DIR"]
geom_root_dir=os.environ["GEOM_ROOT_DIR"]

#import context from ..
execfile("../context.py")

cwd=os.getcwd()
cpppath=os.path.join(cwd,"COMPONENTCPP_INSTALL")

    
# PUT HERE DEFINITIONS OF THE COMPONENTS AND THE SERVICES


os.environ["CALCULCPP_ROOT_DIR"]=cpppath
os.environ["MEDCALCCPP_ROOT_DIR"]=cpppath
os.environ["TESTMEDCPP_ROOT_DIR"]=cpppath
os.environ["ICOCOCPP_ROOT_DIR"]=cpppath
os.environ["TESTMEMCPP_ROOT_DIR"]=cpppath
c1=HXX2SALOMEComponent("CALCUL.hxx","libCALCULCXX.so" , cpppath )
c2=HXX2SALOMEComponent("MEDCALC.hxx","libMEDCALCCXX.so" , cpppath )
c3=HXX2SALOMEComponent("TESTMED.hxx","libTESTMEDCXX.so" , cpppath )
c4=HXX2SALOMEComponent("ICOCO.hxx","libICOCOCXX.so" , cpppath )
c5=HXX2SALOMEComponent("TESTMEM.hxx","libTESTMEMCXX.so" , cpppath )


g=Generator(Module("hxxcompos",components=[c4,c1,c2,c3,c5],prefix="./install"),context)
g.generate()
g.bootstrap()
g.configure()
g.make()
g.install()
g.make_appli("appli",
             restrict=["KERNEL","GUI","YACS"],
             altmodules={"GUI":gui_root_dir,
                         "MED":med_root_dir,
                         "YACS":yacs_root_dir,
                         "GEOM":geom_root_dir})
cppenv=""" export CALCULCPP_ROOT_DIR=%(cpppath)s
export MEDCALCCPP_ROOT_DIR=%(cpppath)s
export TESTMEDCPP_ROOT_DIR=%(cpppath)s
export ICOCOCPP_ROOT_DIR=%(cpppath)s
export TESTMEMCPP_ROOT_DIR=%(cpppath)s"""  % {"cpppath" : cpppath}

cppenvfile=open("appli/env.d/cppEnv.sh","w")
cppenvfile.write(cppenv)
cppenvfile.close()

