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

###########################################################
#             Types definitions                           #
###########################################################
corbaTypes = {"double":"CORBA::Double", "long":"CORBA::Long",
              "string":"const char*", "dblevec":"const %s::dblevec&",
              "stringvec":"const %s::stringvec&", "intvec":"const %s::intvec&",
              "file":None, "boolean":"CORBA::Boolean", "void":"void"
             }

corbaOutTypes = {"double":"CORBA::Double&", "long":"CORBA::Long&",
                 "string":"CORBA::String_out", "dblevec":"%s::dblevec_out",
                 "stringvec":"%s::stringvec_out", "intvec":"%s::intvec_out",
                 "file":None, "boolean":"CORBA::Boolean_out", "void":None
                }
moduleTypes = {"double":"", "long":"", "string":"", "dblevec":"", "stringvec":"", "intvec":"", "file":"", "pyobj":"", "boolean":"", "void":"" }

idlTypes = {"double":"double", "long":"long", "string":"string", "dblevec":"dblevec", "stringvec":"stringvec", "intvec":"intvec", 
            "file":"", "boolean":"boolean", "void":"void" }

corbaRtnTypes = {"double":"CORBA::Double", "long":"CORBA::Long",
                 "string":"char*", "dblevec":"%s::dblevec*",
                 "stringvec":"%s::stringvec*", "intvec":"%s::intvec*",
                 "file":None, "boolean":"CORBA::Boolean", "void":"void"
                }



def corba_in_type(typ, module):
  if corbaTypes[typ].count("%s")>0:
    return corbaTypes[typ] % (module+"_ORB")
  else:
    return corbaTypes[typ]

def corba_out_type(typ, module):
  if corbaOutTypes[typ].count("%s")>0:
    return corbaOutTypes[typ] % (module+"_ORB")
  else:
    return corbaOutTypes[typ]

def corba_rtn_type(typ, module):
  if corbaRtnTypes[typ].count("%s")>0:
    return corbaRtnTypes[typ] % (module+"_ORB")
  else:
    return corbaRtnTypes[typ]

ValidTypes = corbaTypes.keys()
PyValidTypes = ValidTypes+["pyobj"]

def add_type(typename, corbaType, corbaOutType, module, idltype, corbaRtnType):
  """ add a data type YACS from other module than KERNEL to the list of available types

       :param typename: YACS data type name
       :type typename: string
       :param corbaType: representation for C++ CORBA in parameter
       :type corbaType: string
       :param corbaOutType: representation for C++ CORBA out parameter
       :type corbaOutType: string
       :param module: name of the module that defines the data type (GEOM for GEOM_Object)
       :type module: string
       :param idltype: representation for CORBA idl
       :type idltype: string
       :param corbaRtnType: representation for C++ CORBA return parameter
       :type corbaRtnType: string
  """
  corbaTypes[typename] = corbaType
  corbaOutTypes[typename] = corbaOutType
  corbaRtnTypes[typename] = corbaRtnType
  moduleTypes[typename] = module
  idlTypes[typename] = idltype
  ValidTypes.append(typename)
  PyValidTypes.append(typename)

calciumTypes = {"CALCIUM_double":"CALCIUM_double",
                "CALCIUM_integer":"CALCIUM_integer",
                "CALCIUM_real":"CALCIUM_real",
                "CALCIUM_string":"CALCIUM_string",
                "CALCIUM_complex":"CALCIUM_complex",
                "CALCIUM_logical":"CALCIUM_logical",
                "CALCIUM_long":"CALCIUM_long",
               }

DatastreamParallelTypes = {"Param_Double_Port":"Param_Double_Port"}

ValidImpl = ("CPP", "PY", "F77", "ASTER", "PACO")
ValidImplTypes = ("sequential", "parallel")
ValidStreamTypes = calciumTypes.keys()
ValidParallelStreamTypes = DatastreamParallelTypes.keys()
ValidDependencies = ("I", "T")

add_type("dataref", "const Engines::dataref&", "Engines::dataref_out", "", "dataref","Engines::dataref*")
add_type("GEOM_Object", "GEOM::GEOM_Object_ptr", "GEOM::GEOM_Object_out", "GEOM", "GEOM::GEOM_Object","GEOM::GEOM_Object_ptr")
add_type("SMESH_Mesh", "SMESH::SMESH_Mesh_ptr", "SMESH::SMESH_Mesh_out", "SMESH", "SMESH::SMESH_Mesh","SMESH::SMESH_Mesh_ptr")
add_type("SMESH_Hypothesis", "SMESH::SMESH_Hypothesis_ptr", "SMESH::SMESH_Hypothesis_out", "SMESH", "SMESH::SMESH_Hypothesis", "SMESH::SMESH_Hypothesis_ptr")
add_type("SALOME_MED/MED", "SALOME_MED::MED_ptr", "SALOME_MED::MED_out", "MED", "SALOME_MED::MED", "SALOME_MED::MED_ptr")
add_type("SALOME_MED/MESH", "SALOME_MED::MESH_ptr", "SALOME_MED::MESH_out", "MED", "SALOME_MED::MESH", "SALOME_MED::MESH_ptr")
add_type("SALOME_MED/SUPPORT", "SALOME_MED::SUPPORT_ptr", "SALOME_MED::SUPPORT_out", "MED", "SALOME_MED::SUPPORT", "SALOME_MED::SUPPORT_ptr")
add_type("SALOME_MED/FIELD", "SALOME_MED::FIELD_ptr", "SALOME_MED::FIELD_out", "MED", "SALOME_MED::FIELD", "SALOME_MED::FIELD_ptr")
add_type("SALOME_MED/FIELDDOUBLE", "SALOME_MED::FIELDDOUBLE_ptr", "SALOME_MED::FIELDDOUBLE_out", "MED", "SALOME_MED::FIELDDOUBLE", "SALOME_MED::FIELDDOUBLE_ptr")
add_type("SALOME_MED/FIELDINT", "SALOME_MED::FIELDINT_ptr", "SALOME_MED::FIELDINT_out", "MED", "SALOME_MED::FIELDINT", "SALOME_MED::FIELDINT_ptr")
add_type("SALOME/Matrix", "SALOME::Matrix_ptr", "SALOME::Matrix_out", "", "SALOME::Matrix", "SALOME::Matrix_ptr")
add_type("SALOME_MED/MEDCouplingFieldDoubleCorbaInterface", "SALOME_MED::MEDCouplingFieldDoubleCorbaInterface_ptr", "SALOME_MED::MEDCouplingFieldDoubleCorbaInterface_out", "MED", "SALOME_MED::MEDCouplingFieldDoubleCorbaInterface", "SALOME_MED::MEDCouplingFieldDoubleCorbaInterface_ptr")
add_type("SALOME_MED/MEDCouplingUMeshCorbaInterface", "SALOME_MED::MEDCouplingUMeshCorbaInterface_ptr", "SALOME_MED::MEDCouplingUMeshCorbaInterface_out", "MED", "SALOME_MED::MEDCouplingUMeshCorbaInterface", "SALOME_MED::MEDCouplingUMeshCorbaInterface_ptr")
