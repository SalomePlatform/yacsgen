try:
  from string import Template
except:
  from compat import Template,set

# CORBA idl

idl="""
#ifndef _${module}_IDL_
#define _${module}_IDL_

#include "DSC_Engines.idl"
#include "SALOME_Exception.idl"
#include "SALOME_PACOExtension.idl"

module ${module}
{
typedef sequence<string> stringvec;
typedef sequence<double> dblevec;
typedef sequence<long> intvec;
typedef Engines::dataref dataref;

${interfaces}
};

#endif
"""
idl=Template(idl)

interface="""
  interface ${component}:Engines::Superv_Component
  {
${services}
  };
"""
interface=Template(interface)

parallel_interface="""
interface ${component} : Engines::Parallel_DSC
  {
${services}
  };
"""
parallel_interface=Template(parallel_interface)

xml="""\
<?xml version="1.0"?>
<!-- YACSGEN -->

<PaCO_Interface_description>
  <Module>
    <Name>${module}</Name>
${interfaces}
  </Module>
</PaCO_Interface_description>
"""
xml = Template(xml)

xml_interface="""\
    <Interface>
      <Name>${component}</Name>
${xml_services}
    </Interface>"""
xml_interface = Template(xml_interface)

xml_service = """\
      <Method>
        <Name>${service_name}</Name>
        <Type>distributed</Type>
      </Method>"""
xml_service = Template(xml_service)

idlMakefile="""
include $$(top_srcdir)/adm_local/make_common_starter.am

BUILT_SOURCES = ${module}SK.cc ${PACO_BUILT_SOURCES}
IDL_FILES=${module}.idl

lib_LTLIBRARIES = lib${module}.la
salomeidl_DATA = $$(IDL_FILES) ${PACO_salomeidl_DATA}
salomepython_DATA = ${module}_idl.py ${PACO_salomepython_DATA}
lib${module}_la_SOURCES      =
nodist_lib${module}_la_SOURCES = ${module}SK.cc
nodist_salomeinclude_HEADERS= ${module}.hh ${PACO_SALOMEINCLUDE_HEADERS}
lib${module}_la_CXXFLAGS     = -I.  $$(KERNEL_INCLUDES)
lib${module}_la_LIBADD     = $$(KERNEL_LIBS)
##########################################################
%SK.cc %.hh : %.idl
\t$$(OMNIORB_IDL) -bcxx $$(IDLCXXFLAGS) $$(OMNIORB_IDLCXXFLAGS) $$(IDL_INCLUDES) $$<
%_idl.py : %.idl
\t$$(OMNIORB_IDL) -bpython $$(IDL_INCLUDES) ${PACO_INCLUDES} $$<
%PaCO.hxx %PaCO.cxx : %.idl %.xml
\t$$(OMNIORB_IDL) -I@KERNEL_ROOT_DIR@/idl/salome -p@PACOPATH@/lib/python -bpaco -Wb$$(top_srcdir)/idl/$$*.xml,$$(srcdir):@PACOPATH@/idl:@KERNEL_ROOT_DIR@/idl/salome $$(top_srcdir)/idl/$$*.idl

CLEANFILES = *.hh *SK.cc *.py *.hxx *.cxx

EXTRA_DIST = $$(IDL_FILES)

clean-local:
\trm -rf ${module} ${module}__POA

install-data-local:
\t$${mkinstalldirs} $$(DESTDIR)$$(salomepythondir)
\tcp -R ${module} ${module}__POA $$(DESTDIR)$$(salomepythondir)

uninstall-local:
\trm -rf $$(DESTDIR)$$(salomepythondir)/${module}
\trm -rf $$(DESTDIR)$$(salomepythondir)/${module}__POA
"""
idlMakefile=Template(idlMakefile)

# PACO Part
idlMakefilePaCO_BUILT_SOURCES = "${module}PaCO.cxx "
idlMakefilePaCO_nodist_salomeinclude_HEADERS = "${module}PaCO.hxx "
idlMakefilePaCO_BUILT_SOURCES = Template(idlMakefilePaCO_BUILT_SOURCES)
idlMakefilePaCO_nodist_salomeinclude_HEADERS = Template(idlMakefilePaCO_nodist_salomeinclude_HEADERS)
idlMakefilePACO_INCLUDES = "-I@PACOPATH@/idl"
idlMakefilePACO_salomepython_DATA = "${module}PaCO_idl.py"
idlMakefilePACO_salomepython_DATA = Template(idlMakefilePACO_salomepython_DATA)
idlMakefilePACO_salomeidl_DATA = "${module}PaCO.idl"
idlMakefilePACO_salomeidl_DATA = Template(idlMakefilePACO_salomeidl_DATA)

#SALOME catalog

catalog="""<?xml version='1.0' encoding='us-ascii' ?>

<!-- XML component catalog -->
<begin-catalog>

<!-- Path prefix information -->

<path-prefix-list>
</path-prefix-list>

<!-- Commonly used types  -->
<type-list>
  <objref name="pyobj" id="python:obj:1.0"/>
</type-list>

<!-- Component list -->
<component-list>
${components}
</component-list>
</begin-catalog>
"""
catalog=Template(catalog)

cataCompo="""
  <component>
        <!-- Component identification -->
        <component-name>${component}</component-name>
        <component-username>${component}</component-username>
        <component-type>Data</component-type>
        <component-author>${author}</component-author>
        <component-version>1.0</component-version>
        <component-comment></component-comment>
        <component-multistudy>0</component-multistudy>
        <component-impltype>${impltype}</component-impltype>
        <component-implname>${implname}</component-implname>
        <component-interface-list>
            <component-interface-name>${component}</component-interface-name>
            <component-interface-comment></component-interface-comment>
            <component-service-list>
${services}
            </component-service-list>
        </component-interface-list>
  </component>"""
cataCompo=Template(cataCompo)

cataService="""                <component-service>
                    <!-- service-identification -->
                    <service-name>${service}</service-name>
                    <service-author>${author}</service-author>
                    <service-version>1.0</service-version>
                    <service-comment></service-comment>
                    <service-by-default>0</service-by-default>
                    <!-- service-connexion -->
                    <inParameter-list>
${inparams}
                    </inParameter-list>
                    <outParameter-list>
${outparams}
                    </outParameter-list>
                    <DataStream-list>
${datastreams}
                    </DataStream-list>
                </component-service>"""
cataService=Template(cataService)

cataInparam="""                        <inParameter>
                          <inParameter-name>${name}</inParameter-name>
                          <inParameter-type>${type}</inParameter-type>
                       </inParameter>"""
cataInparam=Template(cataInparam)

cataOutparam="""                        <outParameter>
                          <outParameter-name>${name}</outParameter-name>
                          <outParameter-type>${type}</outParameter-type>
                       </outParameter>"""
cataOutparam=Template(cataOutparam)

cataInStream="""                       <inParameter>
                          <inParameter-name>${name}</inParameter-name>
                          <inParameter-type>${type}</inParameter-type>
                          <inParameter-dependency>${dep}</inParameter-dependency>
                       </inParameter>"""
cataInStream=Template(cataInStream)

cataOutStream="""                       <outParameter>
                          <outParameter-name>${name}</outParameter-name>
                          <outParameter-type>${type}</outParameter-type>
                          <outParameter-dependency>${dep}</outParameter-dependency>
                       </outParameter>"""
cataOutStream=Template(cataOutStream)

cataInParallelStream="""                       <inParameter>
                          <inParameter-name>${name}</inParameter-name>
                          <inParameter-type>${type}</inParameter-type>
                       </inParameter>"""
cataInParallelStream=Template(cataInParallelStream)

cataOutParallelStream="""                       <outParameter>
                          <outParameter-name>${name}</outParameter-name>
                          <outParameter-type>${type}</outParameter-type>
                       </outParameter>"""
cataOutParallelStream=Template(cataOutParallelStream)
