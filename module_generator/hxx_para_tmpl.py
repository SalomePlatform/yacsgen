# Copyright (C) 2009-2016  EDF R&D
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
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

try:
  from string import Template
except:
  from module_generator.compat import Template,set

cxxCompo="""
// this cxx file was generated by yacsgen
#include "${component}_i.hxx"
#include "${cxx_include_file}"
using namespace std;
#include <string>
#include <vector>
#include <pthread.h>
#include "SenderFactory.hxx"
#include "MultiCommException.hxx"
#include "ReceiverFactory.hxx"
#include "SALOME_Matrix_i.hxx"
#include "MatrixClient.hxx"
#include "Utils_CorbaException.hxx"
#include "MEDCouplingFieldDouble.hxx"

typedef struct
{
  bool exception;
  string msg;
} except_st;


//DEFS
${servicesdef}
//ENDDEF

//=============================================================================
/*!
 *  standard constructor
 */
//=============================================================================
${component}_i::${component}_i(CORBA::ORB_ptr orb,
	PortableServer::POA_ptr poa,
	PortableServer::ObjectId * contId, 
	const char *instanceName, 
        const char *interfaceName,
	bool regist) :
  ParaMEDMEMComponent_i(orb,poa,contId,instanceName,interfaceName,regist),${inheritedconstructor}cppCompo_(new ${component})
{
  MESSAGE("activate object");
  _thisObj = this ;
  _id = _poa->activate_object(_thisObj);
}

${component}_i::~${component}_i()
{
}

${servicesimpl}

${thread_impl}

extern "C"
{
  PortableServer::ObjectId * ${component}Engine_factory(
			       CORBA::ORB_ptr orb,
			       PortableServer::POA_ptr poa, 
			       PortableServer::ObjectId * contId,
			       const char *instanceName, 
		       	       const char *interfaceName)
  {

   bool regist;
   int numproc;
   int flag;

   MPI_Initialized(&flag);
   if (!flag) {
      int argc = 0;
      char ** argv = NULL;
      MPI_Init(&argc, &argv);
   }

   MPI_Comm_rank( MPI_COMM_WORLD, &numproc );
   if( numproc == 0 )
      regist = true;
   else
      regist = false;
   ${component}_i * my${component} = new ${component}_i(orb, poa, contId, instanceName, interfaceName, regist);
   return my${component}->getId();
  }
}
"""
cxxCompo=Template(cxxCompo)

hxxCompo="""
//this file was generated by yacsgen
#ifndef __${component}_hxx2salome__
#define __${component}_hxx2salome__

#include <SALOMEconfig.h>
#include "Utils_CorbaException.hxx"
#include CORBA_SERVER_HEADER(${module})
#include "Utils_CorbaException.hxx"
#include <memory>  // for std::auto_ptr

${compodefs}

// thread functions declaration
${thread_func_decl}

// thread structures declaration
${thread_str_decl}

class ${component};  // forward declaration

class ${component}_i: ${inheritedclass}
  public POA_${module}_ORB::${component}_Gen,
  public MEDCoupling::ParaMEDMEMComponent_i
{

public:
    ${component}_i(CORBA::ORB_ptr orb,
	    PortableServer::POA_ptr poa,
	    PortableServer::ObjectId * contId, 
	    const char *instanceName, 
	    const char *interfaceName,
	    bool regist);
    virtual ~${component}_i();

${servicesdef}

// (re)defined methods of Driver

private:
    std::auto_ptr<${component}> cppCompo_;

};


extern "C"
    PortableServer::ObjectId * ${component}Engine_factory(
	    CORBA::ORB_ptr orb,
	    PortableServer::POA_ptr poa,
	    PortableServer::ObjectId * contId,
	    const char *instanceName,
	    const char *interfaceName);


#endif
"""
hxxCompo=Template(hxxCompo)

cxxService="""
${ret} ${component}_i::${service}(${parameters}) throw (SALOME::SALOME_Exception)
{
    beginService("${component}_i::${service}");
    BEGIN_OF("${component}_i::${service}");
    except_st *est;
    void *ret_th;
    pthread_t *th;
    try
    {
${body}
	endService("${component}_i::${service}");
	END_OF("${component}_i::${service}");

    }
    catch (std::exception& ex)
    {
        THROW_SALOME_CORBA_EXCEPTION( ex.what(), SALOME::INTERNAL_ERROR );
    }
}
"""
cxxService=Template(cxxService)


#compoMakefile="""
#
#dist_lib${component}Engine_la_SOURCES = \
#	${component}_i.cxx
#
#lib${component}Engine_la_CXXFLAGS = -I$$(top_builddir)/idl  $$(SALOME_INCLUDES) $$(MPI_INCLUDES) ${includes}
#lib${component}Engine_la_LIBADD   = ${libs} -L$$(top_builddir)/idl -lSalomeIDL${module} $${SALOME_LIBS} -lSalomeMPIContainer -lparamedmemcompo $$(FLIBS)
#
#
#"""
#
#compoMakefile=Template(compoMakefile)


# CMakeLists.txt in src/<component>
# template parameters:
#   module : module name
#   component : component name
#   componentlib : name of the target library
#   includes : additional headers, separated by spaces or \n. can be empty
#   libs : additional libraries
#   find_libs : find_library commands
#   target_properties : additional properties of the target
cmake_src_compo_hxxpara = """
# --- options ---
# additional include directories
INCLUDE_DIRECTORIES(
  $${KERNEL_INCLUDE_DIRS}
  $${OMNIORB_INCLUDE_DIR}
  $${PROJECT_BINARY_DIR}
  $${PROJECT_BINARY_DIR}/idl
  $${MEDCOUPLING_INCLUDE_DIRS}
  ${includes}
)

# --- definitions ---
ADD_DEFINITIONS(
  $${OMNIORB_DEFINITIONS}
)

# find additional libraries
${find_libs}

# libraries to link to
SET(_link_LIBRARIES
  $${OMNIORB_LIBRARIES}
  $${KERNEL_SalomeIDLKernel}
  $${KERNEL_OpUtil}
  $${KERNEL_SalomeContainer}
  $${KERNEL_SalomeMPIContainer}
  $${MED_paramedmemcompo}
  $${MED_paramedcouplingcorba}
  SalomeIDL${module}
  ${libs}
)

# --- headers ---

# header files / no moc processing

SET(${module}_HEADERS
  ${component}_i.hxx
)

# --- sources ---

# sources / static
SET(${module}_SOURCES
  ${component}_i.cxx
)

# --- rules ---

ADD_LIBRARY(${componentlib} $${${module}_SOURCES})
TARGET_LINK_LIBRARIES(${componentlib} $${_link_LIBRARIES} )
${target_properties}

INSTALL(TARGETS ${componentlib} EXPORT $${PROJECT_NAME}TargetGroup DESTINATION $${SALOME_INSTALL_LIBS})

INSTALL(FILES $${${module}_HEADERS} DESTINATION $${SALOME_INSTALL_HEADERS})
"""
cmake_src_compo_hxxpara = Template(cmake_src_compo_hxxpara)

#, SALOME_MED::MED_Gen_Driver, SALOME::MultiCommClass
interfaceidlhxx="""
  interface ${component}_Gen: ${inherited}
  {
${services}
  };
"""
interfaceidlhxx=Template(interfaceidlhxx)

