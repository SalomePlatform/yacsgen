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
    <parameter name="${module}" value="$${${module}_ROOT_DIR}/share/salome/resources/${lmodule}"/>
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
lib${module}_la_LIBADD   = -L$$(top_builddir)/idl -lSalomeIDL${module}

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
    <parameter name="${module}" value="$${${module}_ROOT_DIR}/share/salome/resources/${lmodule}"/>
  </section>
</document>
"""
cppsalomeapp=Template(cppsalomeapp)
