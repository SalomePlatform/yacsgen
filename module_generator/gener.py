#  Copyright (C) 2009-2010  EDF R&D
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 2.1 of the License.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA
#
#  See http://www.salome-platform.org/ or email : webmaster.salome@opencascade.com
#

import os, shutil, glob, socket
import traceback
import warnings

try:
  from string import Template
except:
  from compat import Template, set

class Invalid(Exception):
  pass

debug=0

from mod_tmpl import resMakefile, makecommon, configure, paco_configure
from mod_tmpl import mainMakefile, autogen, application
from mod_tmpl import check_sphinx
from cata_tmpl import catalog, interface, idl, idlMakefile, parallel_interface
from cata_tmpl import xml, xml_interface, xml_service
from cata_tmpl import idlMakefilePaCO_BUILT_SOURCES, idlMakefilePaCO_nodist_salomeinclude_HEADERS
from cata_tmpl import idlMakefilePACO_salomepython_DATA, idlMakefilePACO_salomeidl_DATA
from cata_tmpl import idlMakefilePACO_INCLUDES
from cata_tmpl import cataOutStream, cataInStream, cataOutparam, cataInparam
from cata_tmpl import cataOutParallelStream, cataInParallelStream
from cata_tmpl import cataService, cataCompo
from aster_tmpl import check_aster
from salomemodules import salome_modules
from yacstypes import corbaTypes, corbaOutTypes, moduleTypes, idlTypes, corba_in_type, corba_out_type
from yacstypes import ValidTypes, PyValidTypes, calciumTypes, DatastreamParallelTypes
from yacstypes import ValidImpl, ValidImplTypes, ValidStreamTypes, ValidParallelStreamTypes, ValidDependencies
from gui_tmpl import pyguimakefile, pysalomeapp, cppguimakefile, cppsalomeapp
from doc_tmpl import docmakefile, docconf

def makedirs(namedir):
  """Create a new directory named namedir. If a directory already exists copy it to namedir.bak"""
  if os.path.exists(namedir):
    dirbak = namedir+".bak"
    if os.path.exists(dirbak):
      shutil.rmtree(dirbak)
    os.rename(namedir, dirbak)
    os.listdir(dirbak) #needed to update filesystem on special machines (cluster with NFS, for example)
  os.makedirs(namedir)

class Module(object):
  def __init__(self, name, components=None, prefix="",layout="multidir", doc=None, gui=None):
    self.name = name
    self.components = components or []
    self.prefix = prefix or "%s_INSTALL" % name
    self.layout=layout
    self.doc = doc
    self.gui = gui
    try:
      self.validate()
    except Invalid,e:
      if debug:
        traceback.print_exc()
      print "Error in module %s: %s" % (name,e)
      raise SystemExit

  def validate(self):
    # Test Module name, canot have a "-" in the name
    if self.name.find("-") != -1:
      raise Invalid("Module name %s is not valid, remove character - in the module name" % self.name)
    lcompo = set()
    for compo in self.components:
      if compo.name in lcompo:
        raise Invalid("%s is already defined as a component of the module" % compo.name)
      lcompo.add(compo.name)
      compo.validate()
    if self.gui and self.layout != "multidir":
      raise Invalid("A module with GUI can not be generated if layout is not multidir")
    if self.doc and not self.gui:
      warnings.warn("You can't have an help doc without a GUI. doc parameter will be ignored")

class Component(object):
  def __init__(self, name, services=None, impl="PY", libs="", rlibs="",
                     includes="", kind="lib", sources=None,
                     inheritedclass="",compodefs=""):
    self.name = name
    self.impl = impl
    self.kind = kind
    self.services = services or []
    self.libs = libs
    self.rlibs = rlibs
    self.includes = includes
    self.sources = sources or []
    self.inheritedclass=inheritedclass
    self.compodefs=compodefs

  def validate(self):
    if self.impl not in ValidImpl:
      raise Invalid("%s is not a valid implementation. It should be one of %s" % (self.impl, ValidImpl))

    lnames = set()
    for serv in self.services:
      serv.impl = self.impl
      if serv.name in lnames:
        raise Invalid("%s is already defined as a service of the module" % serv.name)
      lnames.add(serv.name)
      serv.validate()

    for src in self.sources:
      if not os.path.exists(src):
        raise Invalid("Source file %s does not exist" % src)

  def getImpl(self):
    return "SO", ""

  def getMakefileItems(self,gen):
    return {}

class Service(object):
  def __init__(self, name, inport=None, outport=None, instream=None, 
                     outstream=None, parallel_instream=None, parallel_outstream=None, body="", defs="", impl_type="sequential"):
    self.name = name
    self.inport = inport or []
    self.outport = outport or []
    self.instream = instream or []
    self.outstream = outstream or []
    self.parallel_instream = parallel_instream or []
    self.parallel_outstream = parallel_outstream or []
    self.defs = defs
    self.body = body
    self.impl = ""
    self.impl_type = impl_type

  def validate(self):
    lports = set()
    for port in self.inport:
      name, typ = self.validatePort(port)
      if name in lports:
        raise Invalid("%s is already defined as a service parameter" % name)
      lports.add(name)

    for port in self.outport:
      name, typ = self.validatePort(port)
      if name in lports:
        raise Invalid("%s is already defined as a service parameter" % name)
      lports.add(name)

    lports = set()
    for port in self.instream:
      name, typ, dep = self.validateStream(port)
      if name in lports:
        raise Invalid("%s is already defined as a stream port" % name)
      lports.add(name)

    for port in self.outstream:
      name, typ, dep = self.validateStream(port)
      if name in lports:
        raise Invalid("%s is already defined as a stream port" % name)
      lports.add(name)
    
    for port in self.parallel_instream:
      name, typ = self.validateParallelStream(port)
      if name in lports:
        raise Invalid("%s is already defined as a stream port" % name)
      lports.add(name)

    for port in self.parallel_outstream:
      name, typ = self.validateParallelStream(port)
      if name in lports:
        raise Invalid("%s is already defined as a stream port" % name)
      lports.add(name)

    self.validateImplType()

  def validatePort(self, port):
    try:
      name, typ = port
    except:
      raise Invalid("%s is not a valid definition of an data port (name,type)" % (port,))

    if self.impl in ("PY", "ASTER"):
      validtypes = PyValidTypes
    else:
      validtypes = ValidTypes

    if typ not in validtypes:
      raise Invalid("%s is not a valid type. It should be one of %s" % (typ, validtypes))
    return name, typ

  def validateImplType(self):
    if self.impl_type not in ValidImplTypes:
      raise Invalid("%s is not a valid impl type. It should be one of %s" % (self.impl_type, ValidImplTypes))

  def validateStream(self, port):
    try:
      name, typ, dep = port
    except:
      raise Invalid("%s is not a valid definition of a stream port (name,type,dependency)" % (port,))
    if typ not in ValidStreamTypes:
      raise Invalid("%s is not a valid type. It should be one of %s" % (typ, ValidStreamTypes))
    if dep not in ValidDependencies:
      raise Invalid("%s is not a valid dependency. It should be one of %s" % (dep, ValidDependencies))
    return name, typ, dep

  def validateParallelStream(self, port):
    try:
      name, typ = port
    except:
      raise Invalid("%s is not a valid definition of a parallel stream port (name,type)" % (port,))
    if typ not in ValidParallelStreamTypes:
      raise Invalid("%s is not a valid type. It should be one of %s" % (typ, ValidParallelStreamTypes))
    return name, typ

class Generator(object):
  def __init__(self, module, context=None):
    self.module = module
    self.context = context or {}
    self.kernel = self.context["kernel"]
    self.gui = self.context.get("gui")
    self.makeflags = self.context.get("makeflags")
    self.aster = ""
    if self.module.gui and not self.gui:
      raise Invalid("To generate a module with GUI, you need to set the 'gui' parameter in the context dictionnary")

  def generate(self):
    """generate SALOME module as described by module attribute"""
    module = self.module
    namedir = module.name+"_SRC"
    force = self.context.get("force")
    update = self.context.get("update")
    paco = self.context.get("paco")
    if os.path.exists(namedir):
      if force:
        shutil.rmtree(namedir)
      elif not update:
        raise Invalid("The directory %s already exists" % namedir)
    if update:
      makedirs(namedir)
    else:
      os.makedirs(namedir)

    srcs = {}
    makefile = "SUBDIRS="
    makefileItems={"header":"""
include $(top_srcdir)/adm_local/make_common_starter.am
AM_CFLAGS=$(SALOME_INCLUDES) -fexceptions
""",
                   "salomepython_PYTHON":[],
                   "dist_salomescript_SCRIPTS":[],
                   "salomeres_DATA":[],
                   "lib_LTLIBRARIES":[],
                   "salomeinclude_HEADERS":[],
                   "body":"",
                  }

    #get the list of SALOME modules used and put it in used_modules attribute
    def get_dependent_modules(mod,modules):
      modules[mod]=1
      if not salome_modules[mod].has_key("depends"):return
      for m in salome_modules[mod]["depends"]:
        if modules.has_key(m):continue
        get_dependent_modules(m,modules)

    modules = {}
    for compo in module.components:
      for serv in compo.services:
        for name, typ in serv.inport + serv.outport:
          mod = moduleTypes[typ]
          if mod:
            get_dependent_modules(mod,modules)

    self.used_modules = modules.keys()

    for compo in module.components:
      #for components files
      fdict=compo.makeCompo(self)
      if self.module.layout=="multidir":
        srcs[compo.name] = fdict
        #for src/Makefile.am
        makefile = makefile + " " + compo.name
      else:
        srcs.update(fdict)
        #for src/Makefile.am
        mdict=compo.getMakefileItems(self)
        makefileItems["salomepython_PYTHON"]=makefileItems["salomepython_PYTHON"]+mdict.get("salomepython_PYTHON",[])
        makefileItems["dist_salomescript_SCRIPTS"]=makefileItems["dist_salomescript_SCRIPTS"]+mdict.get("dist_salomescript_SCRIPTS",[])
        makefileItems["salomeres_DATA"]=makefileItems["salomeres_DATA"]+mdict.get("salomeres_DATA",[])
        makefileItems["lib_LTLIBRARIES"]=makefileItems["lib_LTLIBRARIES"]+mdict.get("lib_LTLIBRARIES",[])
        makefileItems["salomeinclude_HEADERS"]=makefileItems["salomeinclude_HEADERS"]+mdict.get("salomeinclude_HEADERS",[])
        makefileItems["body"]=makefileItems["body"]+mdict.get("body","")+'\n'

    if module.gui:
      GUIname=module.name+"GUI"
      fdict=self.makeGui(namedir)
      srcs[GUIname] = fdict
      #for src/Makefile.am
      makefile = makefile + " " + GUIname

    if self.module.layout == "multidir":
      srcs["Makefile.am"] = makefile+'\n'
    else:
      srcs["Makefile.am"] = self.makeMakefile(makefileItems)

    docsubdir=""
    if module.gui and module.doc:
      docsubdir="doc"

    #for catalog files
    catalogfile = "%sCatalog.xml" % module.name

    #add makefile definitions to make_common_starter.am
    common_starter = makecommon
    for mod in self.used_modules:
      common_starter = common_starter + salome_modules[mod]["makefiledefs"] + '\n'

    adm_local={"make_common_starter.am": common_starter, "check_aster.m4":check_aster}
    if module.gui and module.doc:
      adm_local["check_sphinx.m4"]=check_sphinx

    self.makeFiles({"autogen.sh":autogen,
                    "Makefile.am":mainMakefile.substitute(docsubdir=docsubdir),
                    "README":"", "NEWS":"", "AUTHORS":"", "ChangeLog":"",
                    "src":srcs,
                    "resources":{"Makefile.am":resMakefile.substitute(module=module.name), catalogfile:self.makeCatalog()},
                    "adm_local":adm_local,
                    }, namedir)

    #add checks for modules in configure.ac
    configure_modules=""
    for mod in self.used_modules:
      configure_modules = configure_modules + salome_modules[mod]["configdefs"] + '\n'

    #for configure.ac
    configure_makefiles = []
    if self.module.layout=="multidir":
      for compo in module.components:
        configure_makefiles.append("     src/"+compo.name+"/Makefile")

    if module.gui:
      configure_makefiles.append("     src/%sGUI/Makefile" % module.name)
      if module.doc:
        configure_makefiles.append("     doc/Makefile")

    other_check=""
    other_summary=""
    other_require=""

    if module.gui:
      other_check=other_check + """CHECK_SALOME_GUI
CHECK_QT
"""
      other_summary=other_summary+'''echo "  SALOME GUI ............. : $SalomeGUI_ok"
echo "  Qt ..................... : $qt_ok"
'''
      other_require=other_require + """
      if test "x$SalomeGUI_ok" = "xno"; then
        AC_MSG_ERROR([SALOME GUI is required],1)
      fi
      if test "x$qt_ok" = "xno"; then
        AC_MSG_ERROR([Qt library is required],1)
      fi
"""
      if module.doc:
        other_check=other_check+"CHECK_SPHINX\n"
        other_summary=other_summary+'''echo "  Sphinx ................. : $sphinx_ok"\n'''
        other_require=other_require + """
      if test "x$sphinx_ok" = "xno"; then
        AC_MSG_ERROR([Sphinx documentation generator is required],1)
      fi
"""

    files={}
    #for idl files
    idlfile = "%s.idl" % module.name
    paco_config=""
    PACO_BUILT_SOURCES=""
    PACO_SALOMEINCLUDE_HEADERS=""
    PACO_INCLUDES=""
    PACO_salomepython_DATA=""
    PACO_salomeidl_DATA=""

    if paco:
      PACO_BUILT_SOURCES = idlMakefilePaCO_BUILT_SOURCES.substitute(module=module.name)
      PACO_SALOMEINCLUDE_HEADERS = idlMakefilePaCO_nodist_salomeinclude_HEADERS.substitute(module=module.name)
      PACO_salomepython_DATA = idlMakefilePACO_salomepython_DATA.substitute(module=module.name)
      PACO_salomeidl_DATA = idlMakefilePACO_salomeidl_DATA.substitute(module=module.name)
      PACO_INCLUDES = idlMakefilePACO_INCLUDES
      paco_config=paco_configure

    files["configure.ac"]=configure.substitute(module=module.name.lower(),
                                               makefiles='\n'.join(configure_makefiles),
                                               paco_configure=paco_config,
                                               modules=configure_modules,
                                               other_check=other_check,
                                               other_summary=other_summary,
                                               other_require=other_require,
                                              )

    idlfiles={"Makefile.am":    idlMakefile.substitute(module=module.name,
                                                       PACO_BUILT_SOURCES=PACO_BUILT_SOURCES,
                                                       PACO_SALOMEINCLUDE_HEADERS=PACO_SALOMEINCLUDE_HEADERS,
                                                       PACO_INCLUDES=PACO_INCLUDES,
                                                       PACO_salomepython_DATA=PACO_salomepython_DATA,
                                                       PACO_salomeidl_DATA=PACO_salomeidl_DATA),
              idlfile : self.makeidl(),
             }
    if paco:
      idlfiles["%s.xml" % module.name]=self.makexml()

    files["idl"]=idlfiles

    self.makeFiles(files,namedir)

    os.chmod(os.path.join(namedir, "autogen.sh"), 0777)
    #copy source files if any in created tree
    for compo in module.components:
      for src in compo.sources:
        if self.module.layout=="multidir":
          shutil.copyfile(src, os.path.join(namedir, "src", compo.name, os.path.basename(src)))
        else:
          shutil.copyfile(src, os.path.join(namedir, "src", os.path.basename(src)))

    for m4file in ("check_Kernel.m4", "check_omniorb.m4",
                   "ac_linker_options.m4", "ac_cxx_option.m4",
                   "python.m4", "enable_pthreads.m4", "check_f77.m4",
                   "acx_pthread.m4", "check_boost.m4", "check_paco++.m4",
                   "check_mpi.m4", "check_lam.m4", "check_openmpi.m4", "check_mpich.m4"):
      shutil.copyfile(os.path.join(self.kernel, "salome_adm", "unix", "config_files", m4file),
                      os.path.join(namedir, "adm_local", m4file))
    if self.module.gui:
      for m4file in ("check_GUI.m4", "check_qt.m4", "check_opengl.m4"):
        shutil.copyfile(os.path.join(self.gui, "adm_local", "unix", "config_files", m4file),
                        os.path.join(namedir, "adm_local", m4file))

    self.makeDoc(namedir)
    return

  def makeDoc(self,namedir):
    if not self.module.gui:
      return
    if not self.module.doc:
      return
    rep=os.path.join(namedir,"doc")
    os.makedirs(rep)
    for docs in self.module.doc:
      for doc in glob.glob(docs):
        name = os.path.basename(doc)
        shutil.copyfile(doc, os.path.join(rep, name))
    d={}
    if not os.path.exists(os.path.join(namedir, "doc", "Makefile.am")):
      #create a minimal makefile.am
      d["Makefile.am"]=docmakefile
    if not os.path.exists(os.path.join(namedir, "doc", "conf.py")):
      #create a minimal conf.py
      d["conf.py"]=docconf.substitute(module=self.module.name)
    self.makeFiles(d,os.path.join(namedir,"doc"))

  def makeGui(self,namedir):
    if not self.module.gui:
      return
    ispython=False
    iscpp=False
    #Force creation of intermediate directories
    os.makedirs(os.path.join(namedir, "src", self.module.name+"GUI"))

    for srcs in self.module.gui:
      for src in glob.glob(srcs):
        shutil.copyfile(src, os.path.join(namedir, "src", self.module.name+"GUI", os.path.basename(src)))
        if src[-3:]==".py":ispython=True
        if src[-4:]==".cxx":iscpp=True
    if ispython and iscpp:
      raise Invalid("Module GUI must be pure python or pure C++ but not mixed")
    if ispython:
      return self.makePyGUI(namedir)
    if iscpp:
      return self.makeCPPGUI(namedir)

  def makePyGUI(self,namedir):
    d={}
    if not os.path.exists(os.path.join(namedir, "src", self.module.name+"GUI", "Makefile.am")):
      #create a minimal makefile.am
      sources=[]
      other=[]
      for srcs in self.module.gui:
        for src in glob.glob(srcs):
          if src[-3:]==".py":
            sources.append(os.path.basename(src))
          else:
            other.append(os.path.basename(src))
      makefile=pyguimakefile.substitute(sources=" ".join(sources),other_sources=" ".join(other))
      d["Makefile.am"]=makefile

    if not os.path.exists(os.path.join(namedir, "src", self.module.name+"GUI", "SalomeApp.xml")):
      #create a minimal SalomeApp.xml
      salomeapp=pysalomeapp.substitute(module=self.module.name)
      d["SalomeApp.xml"]=salomeapp
    return d

  def makeCPPGUI(self,namedir):
    return {}

  def makeMakefile(self,makefileItems):
    makefile=""
    if makefileItems.has_key("header"):
      makefile=makefile + makefileItems["header"]+'\n'
    if makefileItems.has_key("lib_LTLIBRARIES"):
      makefile=makefile+"lib_LTLIBRARIES= "+" ".join(makefileItems["lib_LTLIBRARIES"])+'\n'
    if makefileItems.has_key("salomepython_PYTHON"):
      makefile=makefile+"salomepython_PYTHON= "+" ".join(makefileItems["salomepython_PYTHON"])+'\n'
    if makefileItems.has_key("dist_salomescript_SCRIPTS"):
      makefile=makefile+"dist_salomescript_SCRIPTS= "+" ".join(makefileItems["dist_salomescript_SCRIPTS"])+'\n'
    if makefileItems.has_key("salomeres_DATA"):
      makefile=makefile+"salomeres_DATA= "+" ".join(makefileItems["salomeres_DATA"])+'\n'
    if makefileItems.has_key("salomeinclude_HEADERS"):
      makefile=makefile+"salomeinclude_HEADERS= "+" ".join(makefileItems["salomeinclude_HEADERS"])+'\n'
    if makefileItems.has_key("body"):
      makefile=makefile+makefileItems["body"]+'\n'
    return makefile

  def makeArgs(self, service):
    """generate source service for arguments"""
    params = []
    for name, typ in service.inport:
      if typ=="file":continue #files are not passed through service interface
      params.append("%s %s" % (corba_in_type(typ, self.module.name), name))
    for name, typ in service.outport:
      if typ=="file":continue #files are not passed through service interface
      params.append("%s %s" % (corba_out_type(typ, self.module.name), name))
    return ",".join(params)

  def makeCatalog(self):
    """generate SALOME components catalog source"""
    components = []
    for compo in self.module.components:
      services = []
      for serv in compo.services:
        params = []
        for name, typ in serv.inport:
          params.append(cataInparam.substitute(name=name, type=typ))
        inparams = "\n".join(params)
        params = []
        for name, typ in serv.outport:
          params.append(cataOutparam.substitute(name=name, type=typ))
        outparams = "\n".join(params)
        streams = []
        for name, typ, dep in serv.instream:
          streams.append(cataInStream.substitute(name=name, type=calciumTypes[typ], dep=dep))
        for name, typ, dep in serv.outstream:
          streams.append(cataOutStream.substitute(name=name, type=calciumTypes[typ], dep=dep))
        for name, typ in serv.parallel_instream:
          streams.append(cataInParallelStream.substitute(name=name, type=DatastreamParallelTypes[typ]))
        for name, typ in serv.parallel_outstream:
          streams.append(cataOutParallelStream.substitute(name=name, type=DatastreamParallelTypes[typ]))
        datastreams = "\n".join(streams)
        services.append(cataService.substitute(service=serv.name, author="EDF-RD",
                                               inparams=inparams, outparams=outparams, datastreams=datastreams))
      impltype, implname = compo.getImpl()
      components.append(cataCompo.substitute(component=compo.name, author="EDF-RD", impltype=impltype, implname=implname,
                                             services='\n'.join(services)))
    return catalog.substitute(components='\n'.join(components))

  def makeidl(self):
    """generate module IDL file source (CORBA interface)"""
    from pacocompo import PACOComponent
    interfaces = []
    for compo in self.module.components:
      if isinstance(compo, PACOComponent):
        services = []
        for serv in compo.services:
          params = []
          for name, typ in serv.inport:
            if typ == "file":continue #files are not passed through IDL interface
            params.append("in %s %s" % (idlTypes[typ], name))
          for name, typ in serv.outport:
            if typ == "file":continue #files are not passed through IDL interface
            params.append("out %s %s" % (idlTypes[typ], name))
          service = "    void %s(" % serv.name
          service = service+",".join(params)+");"
          services.append(service)
        interfaces.append(parallel_interface.substitute(component=compo.name, services="\n".join(services)))
      else:
        services = []
        for serv in compo.services:
          params = []
          for name, typ in serv.inport:
            if typ == "file":continue #files are not passed through IDL interface
            if compo.impl in ("PY", "ASTER") and typ == "pyobj":
              typ = "Engines::fileBlock"
            else:
              typ=idlTypes[typ]
            params.append("in %s %s" % (typ, name))
          for name, typ in serv.outport:
            if typ == "file":continue #files are not passed through IDL interface
            if compo.impl in ("PY", "ASTER") and typ == "pyobj":
              typ = "Engines::fileBlock"
            else:
              typ=idlTypes[typ]
            params.append("out %s %s" % (typ, name))
          service = "    void %s(" % serv.name
          service = service+",".join(params)+") raises (SALOME::SALOME_Exception);"
          services.append(service)
        interfaces.append(interface.substitute(component=compo.name, services="\n".join(services)))

    #build idl includes for SALOME modules
    idldefs=""
    for mod in self.used_modules:
      idldefs = idldefs + salome_modules[mod]["idldefs"]

    return idl.substitute(module=self.module.name, interfaces='\n'.join(interfaces),idldefs=idldefs)

  # For PaCO++
  def makexml(self):
    from pacocompo import PACOComponent
    interfaces = []
    for compo in self.module.components:
      if isinstance(compo, PACOComponent):
        services = []
        for serv in compo.services:
          if serv.impl_type == "parallel":
            service = xml_service.substitute(service_name=serv.name)
            services.append(service)
        interfaces.append(xml_interface.substitute(component=compo.name, xml_services="\n".join(services)))
    return xml.substitute(module=self.module.name, interfaces='\n'.join(interfaces))

  def makeFiles(self, dic, basedir):
    """create files and directories defined in dictionary dic in basedir directory
       dic key = file name to create
       dic value = file content or dictionary defining the content of a sub directory
    """
    for name, content in dic.items():
      filename = os.path.join(basedir, name)
      if isinstance(content, str):
        fil =  open(filename, 'w')
        fil.write(content)
        fil.close()
      else:
        if not os.path.exists(filename):
          os.makedirs(filename)
        self.makeFiles(content, filename)

  def bootstrap(self):
    """execute module autogen.sh script: execution of libtool, autoconf, automake"""
    ier = os.system("cd %s_SRC;sh autogen.sh" % self.module.name)
    if ier != 0:
      raise Invalid("bootstrap has ended in error")

  def configure(self):
    """execute module configure script with installation prefix (prefix attribute of module)"""
    prefix = self.module.prefix
    paco = self.context.get("paco")
    mpi = self.context.get("mpi")
    args = (self.module.name, self.kernel, self.aster)
    cmd = "cd %s_SRC;./configure --with-kernel=%s --with-aster=%s" % args
    if self.gui:
      cmd = cmd + " --with-gui=%s" % self.gui
    if prefix:
      prefix = os.path.abspath(prefix)
      cmd = cmd + " --prefix=%s" % prefix
    if paco:
      cmd += " --with-paco=%s" % paco
    if mpi:
      cmd += " --with-mpi=%s" % mpi

    ier = os.system(cmd)
    if ier != 0:
      raise Invalid("configure has ended in error")

  def make(self):
    """execute module Makefile : make"""
    make_command = "make "
    if self.makeflags:
      make_command += self.makeflags
    ier = os.system("cd %s_SRC;%s" % (self.module.name, make_command))
    if ier != 0:
      raise Invalid("make has ended in error")

  def install(self):
    """install module: make install """
    makedirs(self.module.prefix)
    ier = os.system("cd %s_SRC;make install" % self.module.name)
    if ier != 0:
      raise Invalid("install has ended in error")

  def make_appli(self, appliname, restrict=None, altmodules=None, resources=""):
    """generate SALOME application"""
    makedirs(appliname)

    rootdir, kerdir = os.path.split(self.kernel)

    #collect modules besides KERNEL module with the same suffix if any
    modules_dict = {}
    if kerdir[:6] == "KERNEL":
      suffix = kerdir[6:]
      for mod in os.listdir(rootdir):
        if mod[-len(suffix):] == suffix:
          module = mod[:-len(suffix)]
          path = os.path.join(rootdir, mod)
          #try to find catalog files
          lcata = glob.glob(os.path.join(path, "share", "salome", "resources", "*", "*Catalog.xml"))
          if not lcata:
            #catalogs have not been found : try the upper level
            lcata = glob.glob(os.path.join(path, "share", "salome", "resources", "*Catalog.xml"))
          if lcata:
            #catalogs have been found : add the corresponding entries in the application
            for cata in lcata:
              catadir, catafile = os.path.split(cata)
              name = catafile[:-11]
              modules_dict[name] = '  <module name="%s" path="%s"/>' % (name, path)
          else:
            modules_dict[module] = '  <module name="%s" path="%s"/>' % (module, path)

    modules_dict["KERNEL"] = '  <module name="KERNEL" path="%s"/>' % self.kernel

    #keep only the modules which names are in restrict if given
    modules = []
    if restrict:
      for mod in restrict:
        if modules_dict.has_key(mod):
          modules.append(modules_dict[mod])
    else:
      modules = modules_dict.values()

    #add the alternate modules if given
    if altmodules:
      for module, path in altmodules.items():
        modules.append('  <module name="%s" path="%s"/>' % (module, path))

    #add the generated module
    modules.append('  <module name="%s" path="%s"/>' % (self.module.name, os.path.abspath(self.module.prefix)))

    #try to find a prerequisites file
    prerequisites = self.context.get("prerequisites")
    if not prerequisites:
      #try to find one in rootdir
      prerequisites = os.path.join(rootdir, "profile%s.sh" % suffix)
    if not os.path.exists(prerequisites):
      raise Invalid("Can not create an application : prerequisites file not defined or does not exist")

    #add resources catalog if it exists
    resources_spec=""
    if os.path.isfile(resources):
      resources_spec='<resources path="%s" />' % os.path.abspath(resources)

    #create config_appli.xml file
    appli = application.substitute(prerequisites=prerequisites,
                                   modules="\n".join(modules),
                                   resources=resources_spec)
    fil = open(os.path.join(appliname, "config_appli.xml"), 'w')
    fil.write(appli)
    fil.close()

    #execute appli_gen.py script
    appligen = os.path.join(self.kernel, "bin", "salome", "appli_gen.py")
    ier = os.system("cd %s;%s" % (appliname, appligen))
    if ier != 0:
      raise Invalid("make_appli has ended in error")

    #add CatalogResources.xml if not created by appli_gen.py
    if not os.path.exists(os.path.join(appliname, "CatalogResources.xml")):
      #CatalogResources.xml does not exist create a minimal one
      fil  = open(os.path.join(appliname, 'CatalogResources.xml'), 'w')
      command = """<!DOCTYPE ResourcesCatalog>
<resources>
    <machine hostname="%s" protocol="ssh" mode="interactive" />
</resources>
"""
      host = socket.gethostname().split('.')[0]
      fil.write(command % host)
      fil.close()

