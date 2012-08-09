# Copyright (C) 2009-2012  EDF R&D
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

application="""
<application>
<prerequisites path="${prerequisites}"/>
${resources}
<modules>
${modules}
</modules>
</application>
"""
application=Template(application)

autogen="""#!/bin/sh

rm -rf autom4te.cache
rm -f aclocal.m4 adm_local/ltmain.sh

echo "Running aclocal..."    ;
aclocal --force -I adm_local || exit 1
echo "Running autoheader..." ; autoheader --force -I adm_local            || exit 1
echo "Running autoconf..."   ; autoconf --force                    || exit 1
echo "Running libtoolize..." ; libtoolize --copy --force           || exit 1
echo "Running automake..."   ; automake --add-missing --copy       || exit 1
"""

mainMakefile="""include $$(top_srcdir)/adm_local/make_common_starter.am
SUBDIRS = idl resources src ${docsubdir}
ACLOCAL_AMFLAGS = -I adm_local
"""
mainMakefile=Template(mainMakefile)

configure="""
AC_INIT(${module}, 1.0)
AC_CONFIG_AUX_DIR(adm_local)
AM_INIT_AUTOMAKE
AM_CONFIG_HEADER(${module}_config.h)

dnl Check Salome Install
CHECK_KERNEL
if test "x$$Kernel_ok" = "xno"; then
  AC_MSG_ERROR([You must define a correct KERNEL_ROOT_DIR or use the --with-kernel= configure option !])
fi

dnl Check Salome modules Install
${modules}

AC_PROG_LIBTOOL
AC_PROG_CC
AC_PROG_CXX
CHECK_F77
CHECK_OMNIORB
CHECK_PACO
CHECK_MPI

MODULE_NAME=${module}
AC_SUBST(MODULE_NAME)

AC_CHECK_ASTER

${other_check}

echo
echo
echo
echo "------------------------------------------------------------------------"
echo "$$PACKAGE $$VERSION"
echo "------------------------------------------------------------------------"
echo
echo "Configuration Options Summary:"
echo
echo "  Threads ................ : $$threads_ok"
echo "  OmniOrb (CORBA) ........ : $$omniORB_ok"
echo "  OmniOrbpy (CORBA) ...... : $$omniORBpy_ok"
echo "  Python ................. : $$python_ok"
echo "  SALOME KERNEL .......... : $$Kernel_ok"
echo "  PaCO++ ................. : $$PaCO_ok"
echo "  MPI .................... : $$mpi_ok"
echo "  Code Aster ............. : $$Aster_ok"
${other_summary}
echo
echo "------------------------------------------------------------------------"
echo

if test "x$$threads_ok" = "xno"; then
  AC_MSG_ERROR([Thread is required],1)
fi
if test "x$$python_ok" = "xno"; then
  AC_MSG_ERROR([Python is required],1)
fi
if test "x$$omniORB_ok" = "xno"; then
  AC_MSG_ERROR([OmniOrb is required],1)
fi
if test "x$$omniORBpy_ok" = "xno"; then
  AC_MSG_ERROR([OmniOrbpy is required],1)
fi
if test "x$$Kernel_ok" = "xno"; then
  AC_MSG_ERROR([SALOME KERNEL is required],1)
fi
${other_require}

${paco_configure}

AC_CONFIG_FILES([
        Makefile
        idl/Makefile
        resources/Makefile
        src/Makefile
${makefiles}
        ])
AC_OUTPUT
"""
configure=Template(configure)

paco_configure="""\
if test "x$$PaCO_ok" = "xno"; then
  AC_MSG_ERROR([PaCO++ is required],1)
fi
"""

makecommon="""
# Standard directory for installation
salomeincludedir   = $$(includedir)/salome
libdir             = $$(prefix)/lib/salome
bindir             = $$(prefix)/bin/salome
salomescriptdir    = $$(bindir)
salomepythondir    = $$(prefix)/lib/python$$(PYTHON_VERSION)/site-packages/salome

# Directory for installing idl files
salomeidldir       = $$(prefix)/idl/salome

# Directory for installing resource files
salomeresdir       = $$(prefix)/share/salome/resources/$${MODULE_NAME}

# Directories for installing admin files
admlocaldir       = $$(prefix)/adm_local
admlocalunixdir     = $$(admlocaldir)/unix
admlocalm4dir        = $$(admlocaldir)/unix/config_files

# Shared modules installation directory
sharedpkgpythondir =$$(pkgpythondir)/shared_modules

# Documentation directory
salomedocdir             = $$(prefix)/share/doc/salome/gui/$${MODULE_NAME}

IDL_INCLUDES = -I$$(KERNEL_ROOT_DIR)/idl/salome
KERNEL_LIBS= -L$$(KERNEL_ROOT_DIR)/lib/salome -lSalomeContainer -lOpUtil -lSalomeDSCContainer -lSalomeDSCSuperv -lSalomeDatastream -lSalomeDSCSupervBasic -lCalciumC
KERNEL_INCLUDES= -I$$(KERNEL_ROOT_DIR)/include/salome $$(OMNIORB_INCLUDES) ${other_includes}

SALOME_LIBS= $${KERNEL_LIBS}
SALOME_IDL_LIBS= -L$$(KERNEL_ROOT_DIR)/lib/salome -lSalomeIDLKernel
SALOME_INCLUDES= $${KERNEL_INCLUDES}

"""
makecommon=Template(makecommon)

resMakefile="""
include $$(top_srcdir)/adm_local/make_common_starter.am
DATA_INST = ${module}Catalog.xml
salomeres_DATA = $${DATA_INST}
EXTRA_DIST = $${DATA_INST}
"""
resMakefile=Template(resMakefile)

check_sphinx="""
AC_DEFUN([CHECK_SPHINX],[

AC_CHECKING(for sphinx doc generator)

sphinx_ok=yes
dnl where is sphinx ?
AC_PATH_PROG(SPHINX,sphinx-build)
if test "x$SPHINX" = "x"
then
  AC_MSG_WARN(sphinx not found)
  sphinx_ok=no
fi

dnl Can I load ths sphinx module ?
dnl This code comes from the ax_python_module macro.
if test -z $PYTHON;
then
   PYTHON="python"
fi
PYTHON_NAME=`basename $PYTHON`
AC_MSG_CHECKING($PYTHON_NAME module: sphinx)
   $PYTHON -c "import sphinx" 2>/dev/null
   if test $? -eq 0;
   then
     AC_MSG_RESULT(yes)
     eval AS_TR_CPP(HAVE_PYMOD_sphinx)=yes
   else
     AC_MSG_RESULT(no)
     eval AS_TR_CPP(HAVE_PYMOD_sphinx)=no
     sphinx_ok=no
   fi

AM_CONDITIONAL(SPHINX_IS_OK, [test x"$sphinx_ok" = xyes])

])
"""

