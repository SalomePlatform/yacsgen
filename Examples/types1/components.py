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

import os

#import context from ..
execfile("../context.py")

from module_generator import Generator,Module,Service,CPPComponent,PYComponent,add_type,add_module

#overload module GEOM definition
idldefs="""
#include "GEOM_Gen.idl"
"""
makefiledefs="""
#module GEOM
GEOM_IDL_INCLUDES = -I$(GEOM_ROOT_DIR)/idl/salome
GEOM_INCLUDES= -I$(GEOM_ROOT_DIR)/include/salome
GEOM_IDL_LIBS= -L$(GEOM_ROOT_DIR)/lib/salome -lSalomeIDLGEOM
GEOM_LIBS= -L$(GEOM_ROOT_DIR)/lib/salome
SALOME_LIBS += ${GEOM_LIBS}
SALOME_IDL_LIBS += ${GEOM_IDL_LIBS}
SALOME_INCLUDES += ${GEOM_INCLUDES}
IDL_INCLUDES += ${GEOM_IDL_INCLUDES}
"""
configdefs="""
if test "x${GEOM_ROOT_DIR}" != "x" && test -d ${GEOM_ROOT_DIR} ; then
  AC_MSG_RESULT(Using GEOM installation in ${GEOM_ROOT_DIR})
else
  AC_MSG_ERROR([Cannot find module GEOM. Have you set GEOM_ROOT_DIR ?],1)
fi
"""
add_module("GEOM",idldefs,makefiledefs,configdefs)

#overload GEOM_Object definition
add_type("GEOM_Object", "GEOM::GEOM_Object_ptr", "GEOM::GEOM_Object_out", "GEOM", "GEOM::GEOM_Object","GEOM::GEOM_Object_ptr")


cwd=os.getcwd()

defs="""
"""

body="""
//inputs
//Parameter
std::cerr << "a: " << a.name << "=" << a.value << std::endl;

//ParameterList
for(CORBA::ULong i = 0;i<b.length();i++)
  std::cerr << "b["<<i<<"]:"<<b[i].name <<"="<<b[i].value << std::endl;

//Value
for(CORBA::ULong i = 0;i<c.length();i++)
  for(CORBA::ULong j = 0;j<c[i].length();j++)
    std::cerr << "c["<<i<<"]["<< j<< "]="<<c[i][j] << std::endl;

//VarList
for(CORBA::ULong i = 0;i<d.length();i++)
  std::cerr << "d["<<i<<"]="<<d[i] << std::endl;

//ValueList
for(CORBA::ULong i = 0;i<e.length();i++)
  for(CORBA::ULong j = 0;j<e[i].length();j++)
    for(CORBA::ULong k = 0;k<e[i][j].length();k++)
      std::cerr << "e["<<i<<"]["<< j<< "]["<<k<<"]="<<e[i][j][k] << std::endl;

//ParametricInput
for(CORBA::ULong i = 0;i<f.inputVarList.length();i++)
  std::cerr << "f.inputVarList["<<i<<"]="<<f.inputVarList[i] << std::endl;
for(CORBA::ULong i = 0;i<f.outputVarList.length();i++)
  std::cerr << "f.outputVarList["<<i<<"]="<<f.outputVarList[i] << std::endl;
for(CORBA::ULong i = 0;i<f.inputValues.length();i++)
  for(CORBA::ULong j = 0;j<f.inputValues[i].length();j++)
    for(CORBA::ULong k = 0;k<f.inputValues[i][j].length();k++)
      std::cerr << "f.inputValues["<<i<<"]["<< j<< "]["<<k<<"]="<<f.inputValues[i][j][k] << std::endl;
for(CORBA::ULong i = 0;i<f.specificParameters.length();i++)
  std::cerr << "f.specificParameters["<<i<<"]:"<<f.specificParameters[i].name <<"="<<f.specificParameters[i].value << std::endl;

//ParametricOutput
for(CORBA::ULong i = 0;i<g.outputValues.length();i++)
  for(CORBA::ULong j = 0;j<g.outputValues[i].length();j++)
    for(CORBA::ULong k = 0;k<g.outputValues[i][j].length();k++)
      std::cerr << "g.outputValues["<<i<<"]["<< j<< "]["<<k<<"]="<<g.outputValues[i][j][k] << std::endl;

//outputs
//Parameter
aa=new SALOME_TYPES::Parameter;
aa->name=CORBA::string_dup(a.name);
aa->value=CORBA::string_dup(a.value);
std::cerr << "aa: " << aa->name << "=" << aa->value << std::endl;
//ParameterList
ab=new SALOME_TYPES::ParameterList;
ac= new SALOME_TYPES::Value;
ad= new SALOME_TYPES::VarList;
ae= new SALOME_TYPES::ValueList;
af= new SALOME_TYPES::ParametricInput;
ag= new SALOME_TYPES::ParametricOutput;
"""

s2body="""
std::cerr << "service s2 C++ component" << std::endl;
aa=GEOM::GEOM_Object::_duplicate(a);
a->Register();
"""

c1=CPPComponent("compo1",services=[
          Service("s1",inport=[("a","SALOME_TYPES/Parameter"),("b","SALOME_TYPES/ParameterList"),("c","SALOME_TYPES/Value"),
                               ("d","SALOME_TYPES/VarList"),("e","SALOME_TYPES/ValueList"),("f","SALOME_TYPES/ParametricInput"),
                               ("g","SALOME_TYPES/ParametricOutput"),
                              ],
                       outport=[("aa","SALOME_TYPES/Parameter"),
                                ("ab","SALOME_TYPES/ParameterList"),
                                ("ac","SALOME_TYPES/Value"),
                                ("ad","SALOME_TYPES/VarList"),("ae","SALOME_TYPES/ValueList"),("af","SALOME_TYPES/ParametricInput"),
                                ("ag","SALOME_TYPES/ParametricOutput"),
                               ],
                       defs=defs,body=body,
                 ),
          Service("s2",inport=[("a","GEOM_Object"),],outport=[("aa","GEOM_Object"),],body=s2body,),
                                  ],
         )

pydefs="""import SALOME_TYPES"""

pybody="""
print a,b,c,d,e,f,g
aa=SALOME_TYPES.Parameter(name="a",value="45.")
ab=[]
ac=[[1,2,3]]
ad=["aaa","bbb"]
ae=[[[1,2,3]]]
af=SALOME_TYPES.ParametricInput(inputVarList=ad,outputVarList=ad, inputValues=[[[1,2,3]]],specificParameters=[])
ag=SALOME_TYPES.ParametricOutput(outputValues=[[[1,2,3]]], specificOutputInfos=[], returnCode=1, errorMessage="error")
print aa,ab,ac,ad,ae,af,ag
"""

s2pybody="""
print "service s2 python component"
aa=a
a.Register()
"""

c2=PYComponent("compo2",services=[
          Service("s1",inport=[("a","SALOME_TYPES/Parameter"),("b","SALOME_TYPES/ParameterList"),("c","SALOME_TYPES/Value"),
                               ("d","SALOME_TYPES/VarList"),("e","SALOME_TYPES/ValueList"),("f","SALOME_TYPES/ParametricInput"),
                               ("g","SALOME_TYPES/ParametricOutput"),
                              ],
                       outport=[("aa","SALOME_TYPES/Parameter"),
                                ("ab","SALOME_TYPES/ParameterList"),
                                ("ac","SALOME_TYPES/Value"),
                                ("ad","SALOME_TYPES/VarList"),("ae","SALOME_TYPES/ValueList"),("af","SALOME_TYPES/ParametricInput"),
                                ("ag","SALOME_TYPES/ParametricOutput"),
                               ],
                       body=pybody,defs=pydefs,
                 ),
          Service("s2",inport=[("a","GEOM_Object"),],outport=[("aa","GEOM_Object"),],body=s2pybody,),
                                 ],
              )


g=Generator(Module("mymodule",components=[c1,c2],prefix="./install"),context)
g.generate()
g.bootstrap()
g.configure()
g.make()
g.install()
g.make_appli("appli", restrict=["KERNEL"], altmodules={"GUI":GUI_ROOT_DIR, "YACS":YACS_ROOT_DIR, "GEOM":GEOM_ROOT_DIR})
