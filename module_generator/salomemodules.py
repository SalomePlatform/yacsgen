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

#######################################################################
#         SALOME modules                                              #
#######################################################################
salome_modules={}

#module GEOM
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

salome_modules["GEOM"]={"idldefs" : idldefs, "makefiledefs" : makefiledefs, "configdefs" : configdefs}

#module MED
idldefs="""
#include "MED_Gen.idl"
#include "MED.idl"
#include "MEDCouplingCorbaServant.idl"
"""
makefiledefs="""
#module MED
MED_IDL_INCLUDES = -I$(MED_ROOT_DIR)/idl/salome
MED_INCLUDES= -I${MED2HOME}/include -I${MED_ROOT_DIR}/include/salome -I${HDF5HOME}/include
MED_IDL_LIBS= -L$(MED_ROOT_DIR)/lib/salome -lSalomeIDLMED
MED_LIBS= -L${MED2HOME}/lib -lmed -L${HDF5HOME}/lib -lhdf5 -L${MED_ROOT_DIR}/lib/salome -lSalomeIDLMED -lMEDClientcmodule -lmedcouplingcorba -lmedcouplingclient 
SALOME_LIBS += ${MED_LIBS}
SALOME_IDL_LIBS += ${MED_IDL_LIBS}
SALOME_INCLUDES += ${MED_INCLUDES}
IDL_INCLUDES += ${MED_IDL_INCLUDES}
"""
configdefs="""
if test "x${MED_ROOT_DIR}" != "x" && test -d ${MED_ROOT_DIR} ; then
  AC_MSG_RESULT(Using MED installation in ${MED_ROOT_DIR})
else
  AC_MSG_ERROR([Cannot find module MED. Have you set MED_ROOT_DIR ?],1)
fi
"""

salome_modules["MED"]={"idldefs" : idldefs, "makefiledefs" : makefiledefs, "configdefs" : configdefs}

#module SMESH
idldefs="""
#include "SMESH_Gen.idl"
#include "SMESH_Mesh.idl"
"""
makefiledefs="""
#module SMESH
SMESH_IDL_INCLUDES = -I$(SMESH_ROOT_DIR)/idl/salome
SMESH_INCLUDES= -I$(SMESH_ROOT_DIR)/include/salome
SMESH_IDL_LIBS= -L$(SMESH_ROOT_DIR)/lib/salome -lSalomeIDLSMESH
SMESH_LIBS= -L$(SMESH_ROOT_DIR)/lib/salome
SALOME_LIBS += ${SMESH_LIBS}
SALOME_IDL_LIBS += ${SMESH_IDL_LIBS}
SALOME_INCLUDES += ${SMESH_INCLUDES}
IDL_INCLUDES += ${SMESH_IDL_INCLUDES}
"""
configdefs="""
if test "x${SMESH_ROOT_DIR}" != "x" && test -d ${SMESH_ROOT_DIR} ; then
  AC_MSG_RESULT(Using SMESH installation in ${SMESH_ROOT_DIR})
else
  AC_MSG_ERROR([Cannot find module SMESH. Have you set SMESH_ROOT_DIR ?],1)
fi
"""

salome_modules["SMESH"]={"idldefs" : idldefs, "makefiledefs" : makefiledefs, "configdefs" : configdefs,
                         "depends":["GEOM","MED"]}

#module VISU
idldefs="""
#include "VISU_Gen.idl"
"""
makefiledefs="""
#module VISU
VISU_IDL_INCLUDES = -I$(VISU_ROOT_DIR)/idl/salome
VISU_INCLUDES= -I$(VISU_ROOT_DIR)/include/salome
VISU_IDL_LIBS= -L$(VISU_ROOT_DIR)/lib/salome -lSalomeIDLVISU
VISU_LIBS= -L$(VISU_ROOT_DIR)/lib/salome
SALOME_LIBS += ${VISU_LIBS}
SALOME_IDL_LIBS += ${VISU_IDL_LIBS}
SALOME_INCLUDES += ${VISU_INCLUDES}
IDL_INCLUDES += ${VISU_IDL_INCLUDES}
"""
configdefs="""
if test "x${VISU_ROOT_DIR}" != "x" && test -d ${VISU_ROOT_DIR} ; then
  AC_MSG_RESULT(Using VISU installation in ${VISU_ROOT_DIR})
else
  AC_MSG_ERROR([Cannot find module VISU. Have you set VISU_ROOT_DIR ?],1)
fi
"""

salome_modules["VISU"]={"idldefs" : idldefs, "makefiledefs" : makefiledefs, "configdefs" : configdefs}
