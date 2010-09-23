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

salomeres_DATA =SalomeApp.xml
"""
cppguimakefile=Template(cppguimakefile)

cppsalomeapp="""
<document>
  <section name="${module}">
    <parameter name="name" value="${module}"/>
  </section>
</document>
"""
cppsalomeapp=Template(cppsalomeapp)
