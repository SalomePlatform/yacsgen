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

mainMakefile="""include $(top_srcdir)/adm_local/make_common_starter.am
SUBDIRS = idl resources src
ACLOCAL_AMFLAGS = -I adm_local
"""

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
CHECK_BOOST
CHECK_OMNIORB
CHECK_PACO
CHECK_MPI

MODULE_NAME=${module}
AC_SUBST(MODULE_NAME)

AC_CHECK_ASTER

echo
echo
echo
echo "------------------------------------------------------------------------"
echo "$$PACKAGE $$VERSION"
echo "------------------------------------------------------------------------"
echo
echo "Configuration Options Summary:"
echo
echo "Mandatory products:"
echo "  Threads ................ : $$threads_ok"
echo "  OmniOrb (CORBA) ........ : $$omniORB_ok"
echo "  OmniOrbpy (CORBA) ...... : $$omniORBpy_ok"
echo "  Python ................. : $$python_ok"
echo "  Boost  ................. : $$boost_ok"
echo "  SALOME KERNEL .......... : $$Kernel_ok"
echo "  PaCO++ ................. : $$PaCO_ok"
echo "  MPI .................... : $$mpi_ok"
echo "  Code Aster ............. : $$Aster_ok"
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
salomeincludedir   = $(includedir)/salome
libdir             = $(prefix)/lib/salome
bindir             = $(prefix)/bin/salome
salomescriptdir    = $(bindir)
salomepythondir    = $(prefix)/lib/python$(PYTHON_VERSION)/site-packages/salome

# Directory for installing idl files
salomeidldir       = $(prefix)/idl/salome

# Directory for installing resource files
salomeresdir       = $(prefix)/share/salome/resources/${MODULE_NAME}

# Directories for installing admin files
admlocaldir       = $(prefix)/adm_local
admlocalunixdir     = $(admlocaldir)/unix
admlocalm4dir        = $(admlocaldir)/unix/config_files

# Shared modules installation directory
sharedpkgpythondir =$(pkgpythondir)/shared_modules

# Documentation directory
docdir             = $(datadir)/doc/salome

IDL_INCLUDES = -I$(KERNEL_ROOT_DIR)/idl/salome
KERNEL_LIBS= -L$(KERNEL_ROOT_DIR)/lib/salome -lSalomeContainer -lOpUtil -lSalomeDSCContainer -lSalomeDSCSuperv -lSalomeDatastream -lSalomeDSCSupervBasic -lCalciumC
KERNEL_INCLUDES= -I$(KERNEL_ROOT_DIR)/include/salome $(OMNIORB_INCLUDES) $(BOOST_CPPFLAGS)

SALOME_LIBS= ${KERNEL_LIBS}
SALOME_IDL_LIBS= -L$(KERNEL_ROOT_DIR)/lib/salome -lSalomeIDLKernel
SALOME_INCLUDES= ${KERNEL_INCLUDES}

"""

resMakefile="""
include $$(top_srcdir)/adm_local/make_common_starter.am
DATA_INST = ${module}Catalog.xml
salomeres_DATA = $${DATA_INST}
EXTRA_DIST = $${DATA_INST}
"""
resMakefile=Template(resMakefile)
