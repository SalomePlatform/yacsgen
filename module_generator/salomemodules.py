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


