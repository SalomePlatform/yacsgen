try:
  from string import Template
except:
  from compat import Template,set

pyguimakefile="""
include $$(top_srcdir)/adm_local/make_common_starter.am

# Scripts to be installed
salomepython_PYTHON= ${sources}

salomeres_DATA =SalomeApp.xml ${other_sources}
"""
pyguimakefile=Template(pyguimakefile)


pysalomeapp="""
<document>
  <section name="${module}">
    <parameter name="name" value="${module}"/>
    <parameter name="icon" value="${module}.png"/>
    <parameter name="library" value="SalomePyQtGUI"/>
  </section>
  <section name="resources">
    <parameter name="${module}" value="$${${module}_ROOT_DIR}/share/salome/resources/${module}"/>
  </section>
</document>
"""
pysalomeapp=Template(pysalomeapp)

cppguimakefile="""
include $$(top_srcdir)/adm_local/make_common_starter.am

BUILT_SOURCES=${uisources}

lib_LTLIBRARIES= lib${module}.la
lib${module}_la_SOURCES = ${sources}
lib${module}_la_CPPFLAGS = $$(SALOME_INCLUDES) $$(GUI_CXXFLAGS) $$(QT_INCLUDES) -I$$(top_builddir)/idl
lib${module}_la_LIBADD   = -L$$(top_builddir)/idl -l${module}

salomeres_DATA =SalomeApp.xml ${other_sources}

# meta object implementation files generation (moc)
%_moc.cxx: %.h
	$$(MOC) $$< -o $$@

# qt forms files generation (uic)
ui_%.h: %.ui
	$$(UIC) -o $$@ $$<

"""
cppguimakefile=Template(cppguimakefile)

cppsalomeapp="""
<document>
  <section name="${module}">
    <parameter name="name" value="${module}"/>
    <parameter name="icon" value="${module}.png"/>
  </section>
  <section name="resources">
    <parameter name="${module}" value="$${${module}_ROOT_DIR}/share/salome/resources/${module}"/>
  </section>
</document>
"""
cppsalomeapp=Template(cppsalomeapp)
