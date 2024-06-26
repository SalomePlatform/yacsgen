# Copyright (C) 2009-2024  EDF
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

application="""
<application>
<prerequisites path="${prerequisites}"/>
<context path="${context}"/>
${resources}
<env_modules>
${env_modules}
</env_modules>
<modules>
${modules}
</modules>
</application>
"""
application=Template(application)

paco_configure="""\
if test "x$$PaCO_ok" = "xno"; then
  AC_MSG_ERROR([PaCO++ is required],1)
fi
"""

# CMakeLists.txt in root module directory
# template parameters:
#   module : name of the module
#   module_min : module name with only lowercase
#   compolibs : list of component libraries
#   with_doc : ON|OFF
#   with_gui : ON|OFF - module has its own GUI
#   add_modules : code to find other modules
#   major_version : major version of the module
#   minor_version : minor version of the module
#   patch_version : patch version of the module
cmake_root_cpp = """
CMAKE_MINIMUM_REQUIRED(VERSION 2.8.8 FATAL_ERROR)

# You can remove "Fortran" if you don't have any fortran component
PROJECT(Salome${module} C CXX Fortran)

# Ensure a proper linker behavior:
CMAKE_POLICY(SET CMP0003 NEW)

# Versioning
# ===========
# Project name, upper case
STRING(TOUPPER $${PROJECT_NAME} PROJECT_NAME_UC)

SET($${PROJECT_NAME_UC}_MAJOR_VERSION ${major_version})
SET($${PROJECT_NAME_UC}_MINOR_VERSION ${minor_version})
SET($${PROJECT_NAME_UC}_PATCH_VERSION ${patch_version})
SET($${PROJECT_NAME_UC}_VERSION
  $${$${PROJECT_NAME_UC}_MAJOR_VERSION}.$${$${PROJECT_NAME_UC}_MINOR_VERSION}.$${$${PROJECT_NAME_UC}_PATCH_VERSION})
SET($${PROJECT_NAME_UC}_VERSION_DEV 1)

# ===================
SET(CONFIGURATION_ROOT_DIR $$ENV{CONFIGURATION_ROOT_DIR} CACHE PATH "Path to the Salome CMake configuration files")
IF(EXISTS $${CONFIGURATION_ROOT_DIR})
  LIST(APPEND CMAKE_MODULE_PATH "$${CONFIGURATION_ROOT_DIR}/cmake")
  INCLUDE(SalomeMacros)
ELSE()
  MESSAGE(FATAL_ERROR "We absolutely need the Salome CMake configuration files, please define CONFIGURATION_ROOT_DIR !")
ENDIF()

# Find KERNEL
# ===========
SET(KERNEL_ROOT_DIR $$ENV{KERNEL_ROOT_DIR} CACHE PATH "Path to the Salome KERNEL")
IF(EXISTS $${KERNEL_ROOT_DIR})
  LIST(APPEND CMAKE_MODULE_PATH "$${KERNEL_ROOT_DIR}/salome_adm/cmake_files")
  FIND_PACKAGE(SalomeKERNEL REQUIRED)
ELSE(EXISTS $${KERNEL_ROOT_DIR})
  MESSAGE(FATAL_ERROR "We absolutely need a Salome KERNEL, please define KERNEL_ROOT_DIR")
ENDIF(EXISTS $${KERNEL_ROOT_DIR})

IF(SALOME_LIGHT_ONLY)
  MESSAGE(FATAL_ERROR "${module} module can't be built in Light mode (without CORBA)")
ENDIF()

# Platform setup
# ==============
INCLUDE(SalomeSetupPlatform)   # From KERNEL
# Always build libraries as shared objects:
SET(BUILD_SHARED_LIBS TRUE)
# Local macros:
LIST(APPEND CMAKE_MODULE_PATH "$${PROJECT_SOURCE_DIR}/adm_local/cmake_files")

# User options
# (some options have already been defined in KERNEL) 
# ============
# OPTION(SALOME_BUILD_TESTS "Build SALOME tests" ON) #For use in the future

OPTION(SALOME_BUILD_DOC "Generate SALOME ${module} documentation" ${with_doc})

IF(SALOME_BUILD_DOC)
  FIND_PACKAGE(SalomeSphinx)
  SALOME_LOG_OPTIONAL_PACKAGE(Sphinx SALOME_BUILD_DOC)
  #FIND_PACKAGE(SalomeDoxygen)
  #SALOME_LOG_OPTIONAL_PACKAGE(Doxygen SALOME_BUILD_DOC)
ENDIF()

##
## From KERNEL:
##
FIND_PACKAGE(SalomePythonInterp REQUIRED)
FIND_PACKAGE(SalomePythonLibs REQUIRED)

FIND_PACKAGE(SalomeOmniORB REQUIRED)
FIND_PACKAGE(SalomeOmniORBPy REQUIRED)
  
# Find GUI
# ===========
OPTION(SALOME_GUI_MODULE "Module ${module} has GUI." ${with_gui})

IF(SALOME_GUI_MODULE)
  SET(GUI_ROOT_DIR $$ENV{GUI_ROOT_DIR} CACHE PATH "Path to the Salome GUI")
  IF(EXISTS $${GUI_ROOT_DIR})
    LIST(APPEND CMAKE_MODULE_PATH "$${GUI_ROOT_DIR}/adm_local/cmake_files")
    FIND_PACKAGE(SalomeGUI REQUIRED)
    ADD_DEFINITIONS($${GUI_DEFINITIONS})
    INCLUDE_DIRECTORIES($${GUI_INCLUDE_DIRS})
  ELSE(EXISTS $${GUI_ROOT_DIR})
    MESSAGE(FATAL_ERROR "We absolutely need a Salome GUI, please define GUI_ROOT_DIR")
  ENDIF(EXISTS $${GUI_ROOT_DIR})

  ##
  ## From GUI:
  ##
  FIND_PACKAGE(SalomeOpenCASCADE REQUIRED)
  # Qt5
  FIND_PACKAGE(SalomeQt5 REQUIRED)
ENDIF(SALOME_GUI_MODULE)

${add_modules}

# Detection summary:
SALOME_PACKAGE_REPORT_AND_CHECK()

# Directories
# (default values taken from KERNEL)
# ===========
SET(SALOME_INSTALL_BINS "$${SALOME_INSTALL_BINS}" CACHE PATH "Install path: SALOME binaries")
SET(SALOME_INSTALL_LIBS "$${SALOME_INSTALL_LIBS}" CACHE PATH "Install path: SALOME libs")
SET(SALOME_INSTALL_IDLS "$${SALOME_INSTALL_IDLS}" CACHE PATH "Install path: SALOME IDL files")
SET(SALOME_INSTALL_HEADERS "$${SALOME_INSTALL_HEADERS}" CACHE PATH "Install path: SALOME headers")
SET(SALOME_INSTALL_SCRIPT_SCRIPTS "$${SALOME_INSTALL_SCRIPT_SCRIPTS}" CACHE PATH 
   "Install path: SALOME scripts")
SET(SALOME_INSTALL_SCRIPT_DATA "$${SALOME_INSTALL_SCRIPT_DATA}" CACHE PATH 
   "Install path: SALOME script data")
SET(SALOME_INSTALL_SCRIPT_PYTHON "$${SALOME_INSTALL_SCRIPT_PYTHON}" CACHE PATH 
   "Install path: SALOME Python scripts")
SET(SALOME_INSTALL_APPLISKEL_SCRIPTS "$${SALOME_INSTALL_APPLISKEL_SCRIPTS}" CACHE PATH 
   "Install path: SALOME application skeleton - scripts")
SET(SALOME_INSTALL_APPLISKEL_PYTHON "$${SALOME_INSTALL_APPLISKEL_PYTHON}" CACHE PATH 
   "Install path: SALOME application skeleton - Python")
SET(SALOME_INSTALL_PYTHON "$${SALOME_INSTALL_PYTHON}" CACHE PATH "Install path: SALOME Python stuff")
SET(SALOME_INSTALL_PYTHON_SHARED "$${SALOME_INSTALL_PYTHON_SHARED}" CACHE PATH 
   "Install path: SALOME Python shared modules")
SET(SALOME_INSTALL_CMAKE_LOCAL "$${SALOME_INSTALL_CMAKE_LOCAL}" CACHE PATH 
    "Install path: local SALOME CMake files") 
#SET(SALOME_INSTALL_AMCONFIG_LOCAL "$${SALOME_INSTALL_AMCONFIG_LOCAL}" CACHE PATH
#  "Install path: local SALOME config files (obsolete, to be removed)")
SET(SALOME_INSTALL_RES "$${SALOME_INSTALL_RES}" CACHE PATH "Install path: SALOME resources")
SET(SALOME_INSTALL_DOC "$${SALOME_INSTALL_DOC}" CACHE PATH "Install path: SALOME documentation")

# Specific to component:
SET(SALOME_${module}_INSTALL_RES_DATA "$${SALOME_INSTALL_RES}/${module_min}" CACHE PATH 
    "Install path: SALOME ${module} specific data")

MARK_AS_ADVANCED(SALOME_INSTALL_BINS SALOME_INSTALL_LIBS SALOME_INSTALL_IDLS SALOME_INSTALL_HEADERS)
MARK_AS_ADVANCED(SALOME_INSTALL_SCRIPT_SCRIPTS SALOME_INSTALL_SCRIPT_DATA SALOME_INSTALL_SCRIPT_PYTHON)
MARK_AS_ADVANCED(SALOME_INSTALL_APPLISKEL_SCRIPTS  SALOME_INSTALL_APPLISKEL_PYTHON SALOME_INSTALL_CMAKE_LOCAL SALOME_INSTALL_RES)
MARK_AS_ADVANCED(SALOME_INSTALL_PYTHON SALOME_INSTALL_PYTHON_SHARED)
MARK_AS_ADVANCED(SALOME_INSTALL_AMCONFIG_LOCAL SALOME_INSTALL_DOC)
MARK_AS_ADVANCED(SALOME_${module}_INSTALL_RES_DATA)

# Accumulate environment variables for component module
SALOME_ACCUMULATE_ENVIRONMENT(PYTHONPATH NOCHECK $${CMAKE_INSTALL_PREFIX}/$${SALOME_INSTALL_BINS}
                                                 $${CMAKE_INSTALL_PREFIX}/$${SALOME_INSTALL_PYTHON})
SALOME_ACCUMULATE_ENVIRONMENT(LD_LIBRARY_PATH NOCHECK $${CMAKE_INSTALL_PREFIX}/$${SALOME_INSTALL_LIBS}) 

# Sources 
# ========

ADD_SUBDIRECTORY(idl)
#ADD_SUBDIRECTORY(adm_local)
ADD_SUBDIRECTORY(resources)
ADD_SUBDIRECTORY(src)
#ADD_SUBDIRECTORY(bin)
IF(SALOME_BUILD_DOC)
  ADD_SUBDIRECTORY(doc)
ENDIF()

# Header configuration
# ====================
SALOME_XVERSION($${PROJECT_NAME})
#SALOME_CONFIGURE_FILE(HELLO_version.h.in HELLO_version.h INSTALL $${SALOME_INSTALL_HEADERS})

# Configuration export
# (here only the level 1 prerequisites are exposed)
# ====================
INCLUDE(CMakePackageConfigHelpers)

# List of targets in this project we want to make visible to the rest of the world.
# They all have to be INSTALL'd with the option "EXPORT $${PROJECT_NAME}TargetGroup"
SET(_$${PROJECT_NAME}_exposed_targets 
  ${compolibs} SalomeIDL${module}
)

# Add all targets to the build-tree export set
EXPORT(TARGETS $${_$${PROJECT_NAME}_exposed_targets}
  FILE $${PROJECT_BINARY_DIR}/$${PROJECT_NAME}Targets.cmake)

# Create the configuration files:
#   - in the build tree:

# Ensure the variables are always defined for the configure:
# !
IF(SALOME_GUI_MODULE)
  SET(GUI_ROOT_DIR "$${GUI_ROOT_DIR}")
ENDIF(SALOME_GUI_MODULE)
 
SET(CONF_INCLUDE_DIRS "$${PROJECT_SOURCE_DIR}/include" "$${PROJECT_BINARY_DIR}/include")

# Build variables that will be expanded when configuring Salome<MODULE>Config.cmake:
# SALOME_CONFIGURE_PREPARE() #For use in the future

#CONFIGURE_PACKAGE_CONFIG_FILE($${PROJECT_NAME}Config.cmake.in
#    $${PROJECT_BINARY_DIR}/$${PROJECT_NAME}Config.cmake
#    INSTALL_DESTINATION "$${SALOME_INSTALL_CMAKE_LOCAL}"
#    PATH_VARS CONF_INCLUDE_DIRS SALOME_INSTALL_CMAKE_LOCAL CMAKE_INSTALL_PREFIX
#    )

#WRITE_BASIC_PACKAGE_VERSION_FILE($${PROJECT_BINARY_DIR}/$${PROJECT_NAME}ConfigVersion.cmake
#    VERSION $${$${PROJECT_NAME_UC}_VERSION}
#    COMPATIBILITY AnyNewerVersion)
  
# Install the CMake configuration files:
#INSTALL(FILES
#  "$${PROJECT_BINARY_DIR}/$${PROJECT_NAME}Config.cmake"
#  "$${PROJECT_BINARY_DIR}/$${PROJECT_NAME}ConfigVersion.cmake"
#  DESTINATION "$${SALOME_INSTALL_CMAKE_LOCAL}")

# Install the export set for use with the install-tree
#INSTALL(EXPORT $${PROJECT_NAME}TargetGroup DESTINATION "$${SALOME_INSTALL_CMAKE_LOCAL}" 
#  FILE $${PROJECT_NAME}Targets.cmake)
"""
cmake_root_cpp = Template(cmake_root_cpp)

# CMakeLists.txt in resources
# template parameters:
#   module : module name
cmake_ressources = """
SET(${module}_RESOURCES_FILES
  ${module}Catalog.xml
)

INSTALL(FILES $${${module}_RESOURCES_FILES} DESTINATION $${SALOME_${module}_INSTALL_RES_DATA})
"""
cmake_ressources = Template(cmake_ressources)

# CMakeLists.txt in src
# template parameters:
#   components : names of the components, separated by spaces or \n
cmake_src = """
SET(SUBDIRS
  ${components}
)

FOREACH(dir $${SUBDIRS})
 ADD_SUBDIRECTORY($${dir})
ENDFOREACH(dir $${SUBDIRS})
"""
cmake_src = Template(cmake_src)

# CMakeLists.txt in idl
# template parameters:
#   module : module name
#   extra_idl : additional idl files
#   extra_include : additional include paths
#   extra_link : additional include options
cmake_idl = """
INCLUDE(UseOmniORB)  # Provided by KERNEL

INCLUDE_DIRECTORIES(
  $${OMNIORB_INCLUDE_DIR}
  $${KERNEL_INCLUDE_DIRS}
  $${PROJECT_BINARY_DIR}/idl
)

SET(SalomeIDL${module}_IDLSOURCES
  ${module}.idl
  ${extra_idl}
)

SET(_idl_include_dirs
  $${KERNEL_ROOT_DIR}/idl/salome
  ${extra_include}
)

SET(_idl_link_flags
  $${KERNEL_SalomeIDLKernel}
  ${extra_link}
)

OMNIORB_ADD_MODULE(SalomeIDL${module} "$${SalomeIDL${module}_IDLSOURCES}" "$${_idl_include_dirs}" "$${_idl_link_flags}")
INSTALL(TARGETS SalomeIDL${module} EXPORT $${PROJECT_NAME}TargetGroup DESTINATION $${SALOME_INSTALL_LIBS})
"""
cmake_idl = Template(cmake_idl)

#cmake code to find a SALOME module
# template parameters:
#   module : module name (GEOM, SMESH, etc)
cmake_find_module = """

#####################################
# FIND ${module}
#####################################
SET(${module}_ROOT_DIR $$ENV{${module}_ROOT_DIR} CACHE PATH "Path to ${module} module")
IF(EXISTS $${${module}_ROOT_DIR})
  LIST(APPEND CMAKE_MODULE_PATH "$${${module}_ROOT_DIR}/adm_local/cmake_files")
  FIND_PACKAGE(Salome${module} REQUIRED)
  ADD_DEFINITIONS($${${module}_DEFINITIONS})
  INCLUDE_DIRECTORIES($${${module}_INCLUDE_DIRS})
ELSE(EXISTS $${${module}_ROOT_DIR})
  MESSAGE(FATAL_ERROR "We absolutely need ${module} module, please define ${module}_ROOT_DIR")
ENDIF(EXISTS $${${module}_ROOT_DIR})
#####################################

"""
cmake_find_module = Template(cmake_find_module)
