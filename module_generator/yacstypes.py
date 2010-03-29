###########################################################
#             Types definitions                           #
###########################################################
corbaTypes = {"double":"CORBA::Double", "long":"CORBA::Long",
              "string":"const char*", "dblevec":"const %s::dblevec&",
              "stringvec":"const %s::stringvec&", "intvec":"const %s::intvec&",
              "file":None
             }

corbaOutTypes = {"double":"CORBA::Double&", "long":"CORBA::Long&",
                 "string":"CORBA::String_out", "dblevec":"%s::dblevec_out",
                 "stringvec":"%s::stringvec_out", "intvec":"%s::intvec_out",
                 "file":None
                }
moduleTypes = {"double":"", "long":"", "string":"", "dblevec":"", "stringvec":"", "intvec":"", "file":"" }

idlTypes = {"double":"double", "long":"long", "string":"string", "dblevec":"dblevec", "stringvec":"stringvec", "intvec":"intvec", "file":"" }

def corba_in_type(typ, module):
  if corbaTypes[typ].count("%s")>0:
    return corbaTypes[typ] % module
  else:
    return corbaTypes[typ]

def corba_out_type(typ, module):
  if corbaOutTypes[typ].count("%s")>0:
    return corbaOutTypes[typ] % module
  else:
    return corbaOutTypes[typ]

ValidTypes = corbaTypes.keys()
PyValidTypes = ValidTypes+["pyobj"]

def add_type(typename, corbaType, corbaOutType, module, idltype):
  corbaTypes[typename] = corbaType
  corbaOutTypes[typename] = corbaOutType
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

add_type("dataref", "const Engines::dataref&", "Engines::dataref_out", "", "dataref")
add_type("GEOM_Object", "GEOM::GEOM_Object_ptr", "GEOM::GEOM_Object_out", "GEOM", "GEOM::GEOM_Object")
