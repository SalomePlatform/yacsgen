"""
  This module defines the ASTERComponent class for ASTER component generation
  An ASTER component comes in 3 flavors :
   - implemented as a dynamic library (kind='lib')
   - implemented as a standalone component (kind='exe')
   - implemented as a specific container (kind='cexe')
"""
import re, os, sys

from gener import Component, Invalid, makedirs

from pyth_tmpl import pyinitEXEService, pyinitCEXEService, pyinitService
import aster_tmpl
from aster_tmpl import asterCEXEService, asterEXEService
from aster_tmpl import asterService, asterEXECompo, asterCEXECompo, asterCompo
from aster_tmpl import comm, make_etude, cexe, exeaster
from aster_tmpl import container, component

class ASTERComponent(Component):
  def __init__(self, name, services=None, libs="", rlibs="", aster_dir="", 
                     python_path=None, argv=None, kind="lib", exe_path=None):
    """initialise component attributes"""
    self.aster_dir = aster_dir
    self.python_path = python_path or []
    self.argv = argv or []
    self.exe_path = exe_path
    Component.__init__(self, name, services, impl="ASTER", libs=libs, 
                             rlibs=rlibs, kind=kind)

  def validate(self):
    """validate the component definition"""
    Component.validate(self)
    if not self.aster_dir:
      raise Invalid("aster_dir must be defined for component %s" % self.name)

    kinds = ("lib", "cexe", "exe")
    if self.kind not in kinds:
      raise Invalid("kind must be one of %s for component %s" % (kinds,self.name))
    if self.kind == "lib" and not self.python_path:
      raise Invalid("python_path must be defined for component %s" % self.name)
    if self.kind == "cexe" :
      if not self.exe_path:
        raise Invalid("exe_path must be defined for component %s" % self.name)
    if self.kind == "exe" :
      if not self.exe_path:
        raise Invalid("exe_path must be defined for component %s" % self.name)

    #Si un port de nom jdc n'est pas defini dans la liste des inports du service,
    #on en ajoute un de type string en premiere position
    for serv in self.services:
      found=False
      for port_name,port_type in serv.inport:
        if port_name == "jdc":
          found=True
          break
      if not found:
        serv.inport.insert(0, ("jdc", "string"))

  def makeCompo(self, gen):
    """drive the generation of SALOME module files and code files
       depending on the choosen component kind
    """
    filename = "%s.py" % self.name
    #on suppose que les composants ASTER sont homogenes (utilisent meme install)
    gen.aster = self.aster_dir

    #get ASTER version
    f = os.path.join(self.aster_dir, "bibpyt", 'Accas', 'properties.py')
    self.version=(0,0,0)
    if os.path.isfile(f):
      mydict = {}
      execfile(f, mydict)
      v,r,p = mydict['version'].split('.')
      self.version=(int(v),int(r),int(p))

    if self.kind == "lib":
      return {"Makefile.am":gen.makeMakefile(self.getMakefileItems(gen)),
              filename:self.makeaster(gen)}
    elif self.kind == "cexe":
      fdict=self.makecexepath(gen)
      d= {"Makefile.am":gen.makeMakefile(self.getMakefileItems(gen)),
           self.name+".exe":cexe.substitute(compoexe=self.exe_path),
           filename:self.makecexeaster(gen)
         }
      d.update(fdict)
      return d
    elif self.kind == "exe":
      fdict=self.makeexepath(gen)
      d= {"Makefile.am":gen.makeMakefile(self.getMakefileItems(gen)),
           self.name+".exe":exeaster.substitute(compoexe=self.exe_path),
           self.name+"_module.py":self.makeexeaster(gen)
         }
      d.update(fdict)
      return d

  def getMakefileItems(self,gen):
    makefileItems={"header":"include $(top_srcdir)/adm_local/make_common_starter.am"}
    if self.kind == "lib":
      makefileItems["salomepython_PYTHON"]=[self.name+".py"]
    elif self.kind == "exe":
      makefileItems["salomepython_PYTHON"]=[self.name+"_module.py",self.name+"_component.py","E_SUPERV.py"]
      makefileItems["dist_salomescript_SCRIPTS"]=[self.name+".exe"]
      makefileItems["salomeres_DATA"]=[self.name+"_config.txt"]
    elif self.kind == "cexe":
      makefileItems["salomepython_PYTHON"]=[self.name+".py",self.name+"_container.py","E_SUPERV.py"]
      makefileItems["dist_salomescript_SCRIPTS"]=[self.name+".exe"]
      makefileItems["salomeres_DATA"]=[self.name+"_config.txt"]
    return makefileItems


  def makeexepath(self, gen):
    """standalone component: generate files for calculation code"""

    #copy and patch E_SUPERV.py
    fil = open(os.path.join(self.aster_dir, "bibpyt", "Execution", "E_SUPERV.py"))
    esuperv = fil.read()
    fil.close()

    if self.version < (10,1,2):
      #patch to E_SUPERV.py
      esuperv = re.sub("def Execute\(self\)", "def Execute(self, params)", esuperv)
      esuperv = re.sub("j=self.JdC", "self.jdc=j=self.JdC", esuperv)
      esuperv = re.sub("\*\*args", "context_ini=params, **args", esuperv)
      esuperv = re.sub("def main\(self\)", "def main(self,params={})", esuperv)
      esuperv = re.sub("return self.Execute\(\)", "return self.Execute(params)", esuperv)

    #use a specific main program (modification of config.txt file)
    fil = open(os.path.join(self.aster_dir, "config.txt"))
    config = fil.read()
    fil.close()
    config = re.sub("profile.sh", os.path.join(self.aster_dir, "profile.sh"), config)

    path=os.path.join(os.path.abspath(gen.module.prefix),'lib',
                      'python%s.%s' % (sys.version_info[0], sys.version_info[1]),
                      'site-packages','salome','%s_component.py'%self.name)
    config = re.sub("Execution\/E_SUPERV.py", path, config)

    fdict= {
             "%s_component.py"%self.name:component.substitute(component=self.name),
             "%s_config.txt" % self.name:config,
             "E_SUPERV.py":esuperv,
           }
    return fdict

  def makecexepath(self, gen):
    """specific container: generate files"""

    #copy and patch E_SUPERV.py
    fil = open(os.path.join(self.aster_dir, "bibpyt", "Execution", "E_SUPERV.py"))
    esuperv = fil.read()
    fil.close()

    if self.version < (10,1,2):
      #patch to E_SUPERV.py
      esuperv = re.sub("def Execute\(self\)", "def Execute(self, params)", esuperv)
      esuperv = re.sub("j=self.JdC", "self.jdc=j=self.JdC", esuperv)
      esuperv = re.sub("\*\*args", "context_ini=params, **args", esuperv)
      esuperv = re.sub("def main\(self\)", "def main(self,params={})", esuperv)
      esuperv = re.sub("return self.Execute\(\)", "return self.Execute(params)", esuperv)


    #use a specific main program
    fil = open(os.path.join(self.aster_dir, "config.txt"))
    config = fil.read()
    fil.close()
    config = re.sub("profile.sh", os.path.join(self.aster_dir, "profile.sh"), config)
    path=os.path.join(os.path.abspath(gen.module.prefix),'lib',
                      'python%s.%s' % (sys.version_info[0], sys.version_info[1]),
                      'site-packages','salome','%s_container.py' % self.name)
    config = re.sub("Execution\/E_SUPERV.py", path, config)

    fdict= {
             "%s_container.py" % self.name:container,
             "%s_config.txt" % self.name:config,
             "E_SUPERV.py":esuperv,
           }
    return fdict

  def makeexeaster(self, gen):
    """standalone component: generate SALOME component source"""
    services = []
    inits = []
    defs = []
    for serv in self.services:
      defs.append(serv.defs)
      params = []
      datas = []
      for name, typ in serv.inport:
        if typ=="file":continue #files are not passed through service interface
        params.append(name)
        if typ == "pyobj":
          datas.append('"%s":cPickle.loads(%s)' % (name, name))
        else:
          datas.append('"%s":%s' % (name, name))
      #ajout de l'adresse du composant
      datas.append('"component":self.proxy.ptr()')
      dvars = "{"+','.join(datas)+"}"
      inparams = ",".join(params)

      params = []
      datas = []
      for name, typ in serv.outport:
        if typ=="file":continue #files are not passed through service interface
        params.append(name)
        if typ == "pyobj":
          datas.append('cPickle.dumps(j.g_context["%s"],-1)'%name)
        else:
          datas.append('j.g_context["%s"]'%name)
      outparams = ",".join(params)
      rvars = ",".join(datas)

      service = asterEXEService.substitute(component=self.name, 
                                           service=serv.name, 
                                           inparams=inparams,
                                           outparams=outparams, 
                                           body=serv.body, 
                                           dvars=dvars, rvars=rvars)
      streams = []
      for name, typ, dep in serv.instream:
        streams.append('       calcium.create_calcium_port(self.proxy,"%s","%s","IN","%s")'% (name, typ, dep))
      instream = "\n".join(streams)
      streams = []
      for name, typ, dep in serv.outstream:
        streams.append('       calcium.create_calcium_port(self.proxy,"%s","%s","OUT","%s")'% (name, typ, dep))
      outstream = "\n".join(streams)

      init = pyinitEXEService.substitute(component=self.name, service=serv.name,
                                         instream=instream, outstream=outstream)
      services.append(service)
      inits.append(init)

    return asterEXECompo.substitute(component=self.name, module=gen.module.name,
                                    servicesdef="\n".join(defs), 
                                    servicesimpl="\n".join(services), 
                                    initservice='\n'.join(inits),
                                    aster_dir=self.aster_dir)

  def makecexeaster(self, gen):
    """specific container: generate SALOME component source"""
    services = []
    inits = []
    defs = []
    for serv in self.services:
      defs.append(serv.defs)
      params = []
      datas = []
      for name, typ in serv.inport:
        if typ=="file":continue #files are not passed through service interface
        params.append(name)
        if typ == "pyobj":
          datas.append('"%s":cPickle.loads(%s)' % (name, name))
        else:
          datas.append('"%s":%s' % (name, name))
      #ajout de l'adresse du composant
      datas.append('"component":self.proxy.ptr()')
      dvars = "{"+','.join(datas)+"}"
      inparams = ",".join(params)

      params = []
      datas = []
      for name, typ in serv.outport:
        params.append(name)
        if typ == "pyobj":
          datas.append('cPickle.dumps(j.g_context["%s"],-1)'%name)
        else:
          datas.append('j.g_context["%s"]'%name)
      outparams = ",".join(params)
      rvars = ",".join(datas)

      service = asterCEXEService.substitute(component=self.name, 
                                            service=serv.name, 
                                            inparams=inparams,
                                            outparams=outparams, 
                                            body=serv.body, 
                                            dvars=dvars, rvars=rvars)
      streams = []
      for name, typ, dep in serv.instream:
        streams.append('       calcium.create_calcium_port(self.proxy,"%s","%s","IN","%s")'% (name, typ, dep))
      instream = "\n".join(streams)
      streams = []
      for name, typ, dep in serv.outstream:
        streams.append('       calcium.create_calcium_port(self.proxy,"%s","%s","OUT","%s")'% (name, typ, dep))
      outstream = "\n".join(streams)

      init = pyinitCEXEService.substitute(component=self.name, 
                                          service=serv.name,
                                          instream=instream, 
                                          outstream=outstream)
      services.append(service)
      inits.append(init)

    return asterCEXECompo.substitute(component=self.name, 
                                     module=gen.module.name,
                                     servicesdef="\n".join(defs), 
                                     servicesimpl="\n".join(services), 
                                     initservice='\n'.join(inits),
                                     aster_dir=self.aster_dir)

  def getImpl(self):
    if self.kind == "cexe":
      return "CEXE", self.name+".exe"
    else:
      return "SO", ""

  def makeaster(self, gen):
    """library component: generate SALOME component source"""
    services = []
    inits = []
    defs = []
    for serv in self.services:
      defs.append(serv.defs)
      params = []
      datas = []
      for name, typ in serv.inport:
        if typ=="file":continue #files are not passed through service interface
        params.append(name)
        if typ == "pyobj":
          datas.append('"%s":cPickle.loads(%s)' % (name, name))
        else:
          datas.append('"%s":%s' % (name, name))
      #ajout de l'adresse du composant
      datas.append('"component":self.proxy.ptr()')
      dvars = "{"+','.join(datas)+"}"
      inparams = ",".join(params)

      params = []
      datas = []
      for name, typ in serv.outport:
        params.append(name)
        if typ == "pyobj":
          datas.append('cPickle.dumps(j.g_context["%s"],-1)'%name)
        else:
          datas.append('j.g_context["%s"]'%name)
      outparams = ",".join(params)
      rvars = ",".join(datas)

      service = asterService.substitute(component=self.name, service=serv.name, 
                                        inparams=inparams, outparams=outparams, 
                                        body=serv.body, 
                                        dvars=dvars, rvars=rvars)
      streams = []
      for name, typ, dep in serv.instream:
        streams.append('       calcium.create_calcium_port(self.proxy,"%s","%s","IN","%s")'% (name, typ, dep))
      instream = "\n".join(streams)
      streams = []
      for name, typ, dep in serv.outstream:
        streams.append('       calcium.create_calcium_port(self.proxy,"%s","%s","OUT","%s")'% (name, typ, dep))
      outstream = "\n".join(streams)

      init = pyinitService.substitute(component=self.name, service=serv.name,
                                      instream=instream, outstream=outstream)
      services.append(service)
      inits.append(init)

    python_path = ",".join([repr(p) for p in self.python_path])
    argv = ",".join([repr(p) for p in self.argv])
    return asterCompo.substitute(component=self.name, module=gen.module.name,
                                 servicesdef="\n".join(defs), 
                                 servicesimpl="\n".join(services), 
                                 initservice='\n'.join(inits),
                                 aster_dir=self.aster_dir, 
                                 python_path=python_path, argv=argv)

