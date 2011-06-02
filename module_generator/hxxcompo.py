# Copyright (C) 2009-2011  EDF R&D
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA
#
# See http://www.salome-platform.org/ or email : webmaster.salome@opencascade.com
#
"""
  Module that generates SALOME c++ Component from a non SALOME c++ component (its header and its shares library)
"""

debug=1
import os
from gener import Component, Invalid
from hxx_tmpl import cxxService, hxxCompo, cxxCompo, compoMakefile
from module_generator import Service
import string
from tempfile import mkstemp
from yacstypes import corba_rtn_type,moduleTypes

class HXX2SALOMEComponent(Component):
  def __init__(self, hxxfile , cpplib , cpp_path ):
    # search a file within a directory tree
    import fnmatch
    def search_file(pattern, root):
        matches = []
        for path, dirs, files in os.walk(os.path.abspath(root)):
            for filename in fnmatch.filter(files, pattern):
                 matches.append(os.path.join(path, filename))
        return matches

    hxxfileful=search_file(hxxfile,cpp_path)
    cpplibful=search_file(cpplib,cpp_path)
    assert len(hxxfileful) > 0  ,'Error in HXX2SALOMEComponent : file ' + hxxfile + ' not found in ' + cpp_path
    assert len(cpplibful) > 0   ,'Error in HXX2SALOMEComponent : file ' + cpplib + ' not found in ' + cpp_path
    hxxfile=hxxfileful[0]
    cpplib=cpplibful[0]

    # grab name of c++ component
    from hxx_awk import parse01,parse1,parse2,parse3
    cmd1="""awk '$1 == "class" && $0 !~ /;/ {print $2}' """ + hxxfile + """|awk -F: '{printf "%s",$1}' """
    f=os.popen(cmd1)
    class_name=f.readlines()[0]
    name=class_name
    print "classname=",class_name
    f.close()

    # create temporary awk files
    (fd01,p01n)=mkstemp()
    f01=os.fdopen(fd01,"w")
    f01.write(parse01)
    f01.close()

    (fd1,p1n)=mkstemp()
    f1=os.fdopen(fd1,"w")
    f1.write(parse1)
    f1.close()

    (fd2,p2n)=mkstemp()
    f2=os.fdopen(fd2,"w")
    f2.write(parse2)
    f2.close()

    (fd3,p3n)=mkstemp()
    f3=os.fdopen(fd3,"w")
    f3.write(parse3)
    f3.close()

    # awk parsing of hxx files - result written in file parse_type_result
    cmd2="cat " + hxxfile + " | awk -f " + p01n + """ | sed 's/virtual //g' | sed 's/MEDMEM_EXPORT//g' | sed 's/throw.*;/;/g' | awk -f """ + p1n + " | awk -f " + p2n + " | awk -v class_name=" + class_name + " -f " + p3n
    os.system(cmd2)
    os.remove(p01n)
    os.remove(p1n)
    os.remove(p2n)
    os.remove(p3n)

    # Retrieve the information which was generated in the file parse_type_result.
    # The structure of the file is :
    #
    #   Function  return_type   function_name
    #   [arg1_type  arg1_name]
    #   [arg2_type  arg2_name]
    #   ...
    # The information is stored in a list of dictionnaries (service_definition)
    from hxx_awk import cpp2idl_mapping
    list_of_services=[]
    service_definition={}
    result_parsing=open("parse_type_result","r")
    for line in result_parsing.readlines():
	line=line[0:-1] # get rid of trailing \n
        words = string.split(line,';')

        if len(words) >=3 and words[0] == "Function": # detect a new service
	    function_name=words[2]
            list_of_services.append(function_name)
            service_definition[function_name]={}
            service_definition[function_name]["ret"]=words[1]  # return type
            service_definition[function_name]["inports"]=[]
            service_definition[function_name]["outports"]=[]
            service_definition[function_name]["ports"]=[]
            service_definition[function_name]["impl"]=[]

        if len(words) == 2:  # an argument type and argument name of a previous service
            typename=words[0]
            argname=words[1]
            service_definition[list_of_services[-1]]["ports"].append( (argname,typename) ) # store in c++ order the arg names

            # separate in from out parameters
            inout=cpp2idl_mapping[typename][0:2]
            assert inout=="in" or inout=="ou",'Error in table cpp2idl_mapping'
            if inout == "in":
                service_definition[list_of_services[-1]]["inports"].append( (argname,typename) )
            else:
                service_definition[list_of_services[-1]]["outports"].append( (argname,typename) )

    # generate implementation of c++ servant
    from hxx_awk import cpp_impl_a,cpp_impl_b,cpp_impl_c  # these tables contain the part of code which depends upon c++ types
    for serv in list_of_services:
	if debug:
	    print "service : ",serv
	    print "  inports  -> ",service_definition[serv]["inports"]
	    print "  outports -> ",service_definition[serv]["outports"]
	    print "  return   -> ",service_definition[serv]["ret"]


	# Part 1 : Argument pre-processing
	s_argument_processing="//\tArguments processing\n"
	for (argname,argtype) in service_definition[serv]["inports"] + service_definition[serv]["outports"]:
	    format=cpp_impl_a[argtype]
	    s_argument_processing += format % {"arg" : argname }
	if s_argument_processing=="//\tArguments processing\n": # if there was no args
	    s_argument_processing=""


	# Part 2 : Call to the underlying c++ function
	s_call_cpp_function="//\tCall cpp component\n\t"
	rtn_type=service_definition[serv]["ret"]
	if rtn_type == "void" : # if return type is void, the call syntax is different
	    s_call_cpp_function += "cppCompo_->%s(" % serv
	else:
	    s_call_cpp_function += "%s _rtn_cpp = cppCompo_->%s(" % (rtn_type ,serv )

	for (argname,argtype) in service_definition[serv]["ports"]:
	      # special treatment for some arguments
	      post=""
	      pre=""
	      if string.find(cpp_impl_a[argtype],"auto_ptr" ) != -1 :
	          post=".get()" # for auto_ptr argument, retrieve the raw pointer behind
	      if  argtype == "const MEDMEM::MESH&"  or  argtype == "const MEDMEM::SUPPORT&" : 
                  pre="*"  # we cannot create MESHClient on the stack (private constructor), so we create it on the heap and dereference it
	      post+="," # separator between arguments
	      s_call_cpp_function += " %s_%s%s" % ( pre,argname,post)
	if s_call_cpp_function[-1]==',':
	    s_call_cpp_function=s_call_cpp_function[0:-1] # get rid of trailing comma
	s_call_cpp_function=s_call_cpp_function+');\n'

	# Part 3.a : Out Argument Post-processing
	s_argument_postprocessing="//\tPost-processing & return\n"
	for (argname,argtype) in service_definition[serv]["outports"]:
	    format=cpp_impl_c[argtype]
	    s_argument_postprocessing += format % {"arg" : argname, "module" : "%(module)s" } # the treatment of %(module) is postponed in makecxx() 
	                                                                                      # because we don't know here the module name
	# Part 3.b : In Argument Post-processing
	for (argname,argtype) in service_definition[serv]["inports"]:
	    if cpp_impl_c.has_key(argtype): # not all in types require a treatment
		format=cpp_impl_c[argtype]
		s_argument_postprocessing += format % {"arg" : argname, "module" : "%(module)s" } # id : treatment of %(module) is postponed in makecxx

	# Part 3.c : return processing
	s_rtn_processing=cpp_impl_b[rtn_type]
	s_rtn_processing += "\tendService(\"%(class_name)s_i::%(serv_name)s\");\n\tEND_OF(\"%(class_name)s_i::%(serv_name)s\");\n" % { "serv_name" : serv, "class_name" : class_name }
	if  rtn_type != "void":
	    s_rtn_processing += "\treturn _rtn_ior;"

        service_definition[serv]["impl"] = s_argument_processing + s_call_cpp_function + s_argument_postprocessing + s_rtn_processing
	if debug:
            print "implementation :\n",service_definition[serv]["impl"]

    #
    # Create a list of services, and give it to Component constructor
    services=[]
    from hxx_awk import cpp2yacs_mapping
    self.use_medmem=False
    self.use_medcoupling=False
    for serv in list_of_services:
	# for inports and outports, Service class expects a list of tuples, each tuple containing the name and the yacs type of the port
	# thus we need to convert c++ types to yacs types  (we use for that the cpp2yacs_mapping table
        inports=[]
        for i in range( len(service_definition[serv]["inports"]) ):
	    inports.append( [service_definition[serv]["inports"][i][0], cpp2yacs_mapping[service_definition[serv]["inports"][i][1]] ] )
        outports=[]
        for i in range( len(service_definition[serv]["outports"]) ):
	    outports.append( [service_definition[serv]["outports"][i][0], cpp2yacs_mapping[service_definition[serv]["outports"][i][1]] ] )

	Return="void"
	if service_definition[serv]["ret"] != "void":
            Return=cpp2yacs_mapping[service_definition[serv]["ret"]]

	# find out if component uses medmem types and/or medcoupling types
	for (argname,argtype) in inports + outports + [("return",Return)]:
	    if moduleTypes[argtype]=="MED":
		if argtype.count("Coupling")>0:
		    self.use_medcoupling=True
		else:
		    self.use_medmem=True
		break

        code=service_definition[serv]["impl"]
	if debug:
	    print "service : ",serv
	    print "  inports  -> ",service_definition[serv]["inports"]
	    print "  converted inports  -> ",inports
	    print "  outports -> ",service_definition[serv]["outports"]
	    print "  converted outports  -> ",outports
	    print "  Return  -> ",service_definition[serv]["ret"]
	    print "  converted Return  -> ",Return

        services.append(Service(serv, 
           inport=inports, 
           outport=outports,
           ret=Return, 
           defs="", 
           body=code,
           ) )

    Includes="-I${"+name+"CPP_ROOT_DIR}/include"
    Libs="-L${"+name+"CPP_ROOT_DIR}/lib -l"+name+"CXX"
    Compodefs=""
    Inheritedclass=""
    self.inheritedconstructor=""
    if self.use_medmem:
	Compodefs="""
#include CORBA_CLIENT_HEADER(MED)
#include CORBA_CLIENT_HEADER(MED_Gen)
#include "FIELDClient.hxx"
#include "MESHClient.hxx"
#include "MEDMEM_Support_i.hxx"
#include "MEDMEM_Mesh_i.hxx"
#include "MEDMEM_FieldTemplate_i.hxx"
#include "Med_Gen_Driver_i.hxx"
"""
        Inheritedclass="Med_Gen_Driver_i"
	self.inheritedconstructor="Med_Gen_Driver_i(orb),"

    if self.use_medcoupling:
	Compodefs+="""
#include CORBA_CLIENT_HEADER(MEDCouplingCorbaServant)
#include CORBA_CLIENT_HEADER(MED_Gen)
#include "MEDCouplingFieldDoubleServant.hxx"
#include "MEDCouplingUMeshServant.hxx"
#include "MEDCouplingFieldDouble.hxx"
#include "MEDCouplingUMesh.hxx"
#include "MEDCouplingUMeshClient.hxx"
#include "MEDCouplingFieldDouble.hxx"
#include "MEDCouplingFieldDoubleClient.hxx"
"""

    Component.__init__(self, name, services, impl="CPP", libs=Libs,
                             rlibs="", includes=Includes, kind="lib",
                             sources=None,inheritedclass=Inheritedclass,
                             compodefs=Compodefs)

  def makeCompo(self, gen):
    """generate files for C++ component

       return a dict where key is the file name and value is the content of the file
    """
    cxxfile = "%s_i.cxx" % self.name
    hxxfile = "%s_i.hxx" % self.name
    return {"Makefile.am":gen.makeMakefile(self.getMakefileItems(gen)),
            cxxfile:self.makecxx(gen),
            hxxfile:self.makehxx(gen)
           }

  def getMakefileItems(self,gen):
      makefileItems={"header":"""
include $(top_srcdir)/adm_local/make_common_starter.am

"""}
      makefileItems["lib_LTLIBRARIES"]=["lib"+self.name+"Engine.la"]
      makefileItems["salomeinclude_HEADERS"]=["%s_i.hxx" % self.name]
      makefileItems["body"]=compoMakefile.substitute(module=gen.module.name,
                                                     component=self.name,
                                                     libs=self.libs,
                                                     includes=self.includes)
      return makefileItems

  def makehxx(self, gen):
    """return a string that is the content of .hxx file
    """
    services = []
    for serv in self.services:
      service = "    %s %s(" % (corba_rtn_type(serv.ret,gen.module.name),serv.name)
      service = service+gen.makeArgs(serv)+") throw (SALOME::SALOME_Exception);"
      services.append(service)
    servicesdef = "\n".join(services)

    inheritedclass=self.inheritedclass
    if self.inheritedclass:
      inheritedclass= " public virtual " + self.inheritedclass + ","

    return hxxCompo.substitute(component=self.name, module=gen.module.name,
                               servicesdef=servicesdef, inheritedclass=inheritedclass,
			       compodefs=self.compodefs)

  def makecxx(self, gen, exe=0):
    """return a string that is the content of .cxx file
    """
    services = []
    inits = []
    defs = []
    for serv in self.services:
      defs.append(serv.defs)
      service = cxxService.substitute(component=self.name, service=serv.name,ret=corba_rtn_type(serv.ret,gen.module.name),
                                      parameters=gen.makeArgs(serv),
				      body=serv.body % {"module":gen.module.name+"_ORB"} )
      services.append(service)
    return cxxCompo.substitute(component=self.name, 
	                       inheritedconstructor=self.inheritedconstructor,
                               servicesdef="\n".join(defs),
                               servicesimpl="\n".join(services))

