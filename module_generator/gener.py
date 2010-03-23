import os, shutil, glob, socket
import traceback

try:
  from string import Template
except:
  from compat import Template, set

class Invalid(Exception):
  pass

debug=0

from mod_tmpl import resMakefile, makecommon, configure, paco_configure
from mod_tmpl import mainMakefile, autogen, application
from cata_tmpl import catalog, interface, idl, idlMakefile, parallel_interface
from cata_tmpl import xml, xml_interface, xml_service
from cata_tmpl import idlMakefilePaCO_BUILT_SOURCES, idlMakefilePaCO_nodist_salomeinclude_HEADERS
from cata_tmpl import idlMakefilePACO_salomepython_DATA, idlMakefilePACO_salomeidl_DATA
from cata_tmpl import idlMakefilePACO_INCLUDES
from cata_tmpl import cataOutStream, cataInStream, cataOutparam, cataInparam
from cata_tmpl import cataOutParallelStream, cataInParallelStream
from cata_tmpl import cataService, cataCompo
from aster_tmpl import check_aster

corbaTypes = {"double":"CORBA::Double", "long":"CORBA::Long",
              "string":"const char*", "dblevec":"const %s::dblevec&",
              "stringvec":"const %s::stringvec&", "intvec":"const %s::intvec&",
              "dataref":"const Engines::dataref&","file":None
             }

corbaOutTypes = {"double":"CORBA::Double&", "long":"CORBA::Long&",
                 "string":"CORBA::String_out", "dblevec":"%s::dblevec_out",
                 "stringvec":"%s::stringvec_out", "intvec":"%s::intvec_out",
                 "dataref":"Engines::dataref_out","file":None
                }

def corba_in_type(typ, module):
  if typ in ("dblevec", "intvec", "stringvec"):
    return corbaTypes[typ] % module
  else:
    return corbaTypes[typ]

def corba_out_type(typ, module):
  if typ in ("dblevec", "intvec", "stringvec"):
    return corbaOutTypes[typ] % module
  else:
    return corbaOutTypes[typ]

calciumTypes = {"CALCIUM_double":"CALCIUM_double",
                "CALCIUM_integer":"CALCIUM_integer",
                "CALCIUM_real":"CALCIUM_real",
                "CALCIUM_string":"CALCIUM_string",
                "CALCIUM_complex":"CALCIUM_complex",
                "CALCIUM_logical":"CALCIUM_logical",
                "CALCIUM_long":"CALCIUM_long",
               }

DatastreamParallelTypes = {"Param_Double_Port":"Param_Double_Port"}

ValidImpl = ("CPP", "PY", "F77", "ASTER", "PACO")
ValidImplTypes = ("sequential", "parallel")
ValidTypes = corbaTypes.keys()
ValidStreamTypes = calciumTypes.keys()
ValidParallelStreamTypes = DatastreamParallelTypes.keys()
ValidDependencies = ("I", "T")
PyValidTypes = ValidTypes+["pyobj"]

def makedirs(namedir):
  if os.path.exists(namedir):
    dirbak = namedir+".bak"
    if os.path.exists(dirbak):
      shutil.rmtree(dirbak)
    os.rename(namedir, dirbak)
    os.listdir(dirbak) #sert seulement a mettre a jour le systeme de fichier sur certaines machines
  os.makedirs(namedir)

class Module(object):
  def __init__(self, name, components=None, prefix="",layout="multidir"):
    self.name = name
    self.components = components or []
    self.prefix = prefix or "%s_INSTALL" % name
    self.layout=layout
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
      raise Invalid("Module name %s is not valid, remove caracter - in the module name" % self.name)
    lcompo = set()
    for compo in self.components:
      if compo.name in lcompo:
        raise Invalid("%s is already defined as a component of the module" % compo.name)
      lcompo.add(compo.name)
      compo.validate()

class Component(object):
  def __init__(self, name, services=None, impl="PY", libs="", rlibs="", 
                     includes="", kind="lib", sources=None):
    self.name = name
    self.impl = impl
    self.kind = kind
    self.services = services or []
    self.libs = libs
    self.rlibs = rlibs
    self.includes = includes
    self.sources = sources or []

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
    self.makeflags = self.context.get("makeflags")
    self.aster = ""

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
AM_CFLAGS=$$(KERNEL_INCLUDES) -fexceptions
""",
                   "salomepython_PYTHON":[],
                   "dist_salomescript_SCRIPTS":[],
                   "salomeres_DATA":[],
                   "lib_LTLIBRARIES":[],
                   "salomeinclude_HEADERS":[],
                   "body":"",
                  }

    for compo in module.components:
      #for components files
      fdict=compo.makeCompo(self)
      if self.module.layout=="multidir":
        srcs[compo.name] = fdict
        #for src/Makefile.am
        makefile = makefile+" "+compo.name
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

    if self.module.layout=="multidir":
      srcs["Makefile.am"] = makefile+'\n'
    else:
      srcs["Makefile.am"] = self.makeMakefile(makefileItems)

    #for catalog files
    catalogfile = "%sCatalog.xml" % module.name

    self.makeFiles({"autogen.sh":autogen,
                    "Makefile.am":mainMakefile,
                    "README":"", "NEWS":"", "AUTHORS":"", "ChangeLog":"",
                    "src":srcs,
                    "resources":{"Makefile.am":resMakefile.substitute(module=module.name), catalogfile:self.makeCatalog()},
                    "adm_local":{"make_common_starter.am":makecommon, "check_aster.m4":check_aster},
                    }, namedir)

    #for configure.ac
    configure_makefiles = []
    if self.module.layout=="multidir":
      for compo in module.components:
        configure_makefiles.append("     src/"+compo.name+"/Makefile")
    #for idl files
    idlfile = "%s.idl" % module.name

    if paco:
      xmlfile = "%s.xml" % module.name
      PACO_BUILT_SOURCES = idlMakefilePaCO_BUILT_SOURCES.substitute(module=module.name)
      PACO_SALOMEINCLUDE_HEADERS = idlMakefilePaCO_nodist_salomeinclude_HEADERS.substitute(module=module.name)
      PACO_salomepython_DATA = idlMakefilePACO_salomepython_DATA.substitute(module=module.name)
      PACO_salomeidl_DATA = idlMakefilePACO_salomeidl_DATA.substitute(module=module.name)
      PACO_INCLUDES = idlMakefilePACO_INCLUDES

      self.makeFiles({"configure.ac":configure.substitute(module=module.name.lower(),
                                                          makefiles='\n'.join(configure_makefiles),
                                                          paco_configure=paco_configure),
                      "idl":{"Makefile.am":idlMakefile.substitute(module=module.name, 
                                                                  PACO_BUILT_SOURCES=PACO_BUILT_SOURCES,
                                                                  PACO_SALOMEINCLUDE_HEADERS=PACO_SALOMEINCLUDE_HEADERS,
                                                                  PACO_INCLUDES=PACO_INCLUDES,
                                                                  PACO_salomepython_DATA=PACO_salomepython_DATA,
                                                                  PACO_salomeidl_DATA=PACO_salomeidl_DATA), 
                             idlfile:self.makeidl(),
                             xmlfile:self.makexml()},
                      }, namedir)
    else :
      self.makeFiles({"configure.ac":configure.substitute(module=module.name.lower(), 
                                                          makefiles='\n'.join(configure_makefiles),
                                                          paco_configure=""),
                      "idl":{"Makefile.am":idlMakefile.substitute(module=module.name,
                                                                  PACO_BUILT_SOURCES="",
                                                                  PACO_SALOMEINCLUDE_HEADERS="",
                                                                  PACO_INCLUDES="",
                                                                  PACO_salomepython_DATA="",
                                                                  PACO_salomeidl_DATA=""), 
                             idlfile:self.makeidl()},
                      }, namedir)

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

    return

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
            params.append("in %s %s" % (typ, name))
          for name, typ in serv.outport:
            if typ == "file":continue #files are not passed through IDL interface
            params.append("out %s %s" % (typ, name))
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
            params.append("in %s %s" % (typ, name))
          for name, typ in serv.outport:
            if typ == "file":continue #files are not passed through IDL interface
            if compo.impl in ("PY", "ASTER") and typ == "pyobj":
              typ = "Engines::fileBlock"
            params.append("out %s %s" % (typ, name))
          service = "    void %s(" % serv.name
          service = service+",".join(params)+") raises (SALOME::SALOME_Exception);"
          services.append(service)
        interfaces.append(interface.substitute(component=compo.name, services="\n".join(services)))
    return idl.substitute(module=self.module.name, interfaces='\n'.join(interfaces))

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
    if prefix:
      prefix = os.path.abspath(prefix)
      cmd = "cd %s_SRC;./configure --with-kernel=%s --with-aster=%s --prefix=%s"
      if paco:
        cmd += " --with-paco=%s"
        if mpi:
          cmd += " --with-mpi=%s"
          ier = os.system(cmd % (self.module.name, self.kernel, self.aster, prefix, paco, mpi))
        else :  
          ier = os.system(cmd % (self.module.name, self.kernel, self.aster, prefix, paco))
      else :  
        ier = os.system(cmd % (self.module.name, self.kernel, self.aster, prefix))
    else:
      cmd = "cd %s_SRC;./configure --with-kernel=%s --with-aster=%s"
      if paco:
        cmd += " --with-paco=%s"
        if mpi:
          cmd += " --with-mpi=%s"
          ier = os.system(cmd % (self.module.name, self.kernel, self.aster, paco, mpi))
        else:  
          ier = os.system(cmd % (self.module.name, self.kernel, self.aster, paco))
      else:  
        ier = os.system(cmd % (self.module.name, self.kernel, self.aster))
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

