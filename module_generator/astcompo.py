import re, os

from gener import Component, Invalid, makedirs

from pyth_tmpl import pyinitEXEService, pyinitCEXEService, pyinitService
from aster_tmpl import asterCEXEService, asterEXEService
from aster_tmpl import asterService, asterEXECompo, asterCEXECompo, asterCompo
from aster_tmpl import asterexeMakefile, astercexeMakefile, astercompoMakefile
from aster_tmpl import comm, make_etude, cexe, exeaster
from aster_tmpl import container, component

class ASTERComponent(Component):
  def __init__(self, name, services=None, libs="", rlibs="", aster_dir="", 
                     python_path=None, argv=None, kind="lib", exe_path=None,
                     asrun=None, export_extras=""):
    self.aster_dir = aster_dir
    self.python_path = python_path or []
    self.argv = argv or []
    self.exe_path = exe_path
    self.asrun = asrun
    self.export_extras = export_extras
    Component.__init__(self, name, services, impl="ASTER", libs=libs, 
                             rlibs=rlibs, kind=kind)

  def validate(self):
    Component.validate(self)
    if not self.aster_dir:
      raise Invalid("aster_dir must be defined for component %s" % self.name)

    kinds = ("lib", "cexe", "exe")
    if self.kind not in kinds:
      raise Invalid("kind must be one of %s" % kinds)
    if self.kind == "lib" and not self.python_path:
      raise Invalid("python_path must be defined for component %s" % self.name)
    if self.kind == "cexe" :
      if not self.exe_path:
        raise Invalid("exe_path must be defined for component %s" % self.name)
      if not self.asrun:
        raise Invalid("asrun must be defined for component %s" % self.name)
      if not os.path.exists(self.asrun):
        raise Invalid("asrun does not exist for component %s" % self.name)
    if self.kind == "exe" :
      if not self.exe_path:
        raise Invalid("exe_path must be defined for component %s" % self.name)
      if not self.asrun:
        raise Invalid("asrun must be defined for component %s" % self.name)
      if not os.path.exists(self.asrun):
        raise Invalid("asrun does not exist for component %s" % self.name)

    for serv in self.services:
      #on ajoute un inport string de nom jdc en premier dans la liste des ports de chaque service
      serv.inport.insert(0, ("jdc", "string"))

  def makeCompo(self, gen):
    filename = "%s.py" % self.name
    #on suppose que les composants ASTER sont homogenes (utilisent meme install)
    gen.aster = self.aster_dir
    if self.kind == "lib":
      return {"Makefile.am":astercompoMakefile.substitute(module=gen.module.name, 
                                                          component=self.name),
             filename:self.makeaster(gen)}
    elif self.kind == "cexe":
      #creation de l'installation aster dans exe_path
      self.makecexepath(gen)
      return {"Makefile.am":astercexeMakefile.substitute(module=gen.module.name, 
                                                         component=self.name),
             filename:self.makecexeaster(gen)}
    elif self.kind == "exe":
      #creation de l'installation aster dans exe_path
      self.makeexepath(gen)
      return {"Makefile.am":asterexeMakefile.substitute(module=gen.module.name, 
                                                        component=self.name),
               self.name+".exe":exeaster.substitute(export=os.path.join(self.exe_path, "make_etude.export"), asrun=self.asrun),
               self.name+"_module.py":self.makeexeaster(gen)}

  def makeexepath(self, gen):
    makedirs(self.exe_path)
    #patch to E_SUPERV.py
    fil = open(os.path.join(self.aster_dir, "bibpyt", "Execution", "E_SUPERV.py"))
    esuperv = fil.read()
    esuperv = re.sub("j=self.JdC", "self.jdc=j=self.JdC", esuperv)
    fil.close()
    #utilisation d'un programme principal python different
    fil = open(os.path.join(self.aster_dir, "config.txt"))
    config = fil.read()
    config = re.sub("Execution\/E_SUPERV.py", os.path.join(self.exe_path, "aster_component.py"), config)
    fil.close()

    gen.makeFiles({
                   "aster_component.py":component.substitute(component=self.name),
                   "make_etude.export":make_etude.substitute(config=os.path.join(self.exe_path, "config.txt"),
                                                             comm=os.path.join(self.exe_path, self.name+".comm"),
                                                             extras=self.export_extras),
                   self.name+".comm":comm,
                   "config.txt":config,
                   "profile.sh":os.path.join(self.aster_dir, "profile.sh"),
                   "E_SUPERV.py":esuperv,
                  }, self.exe_path)

  def makecexepath(self, gen):
    makedirs(self.exe_path)
    #patch to E_SUPERV.py
    fil = open(os.path.join(self.aster_dir, "bibpyt", "Execution", "E_SUPERV.py"))
    esuperv = fil.read()
    esuperv = re.sub("j=self.JdC", "self.jdc=j=self.JdC", esuperv)
    fil.close()
    #utilisation d'un programme principal python different
    fil = open(os.path.join(self.aster_dir, "config.txt"))
    config = fil.read()
    config = re.sub("Execution\/E_SUPERV.py", os.path.join(self.exe_path, "aster_container.py"), config)
    fil.close()
    gen.makeFiles({self.name+".exe":cexe.substitute(export=os.path.join(self.exe_path, "make_etude.export"),
                                                    asrun=self.asrun),
                   "aster_container.py":container,
                   "make_etude.export":make_etude.substitute(config=os.path.join(self.exe_path, "config.txt"),
                                                             comm=os.path.join(self.exe_path, self.name+".comm"),
                                                             extras=self.export_extras),
                   self.name+".comm":comm,
                   "config.txt":config,
                   "profile.sh":os.path.join(self.aster_dir, "profile.sh"),
                   "E_SUPERV.py":esuperv,
                  }, self.exe_path)
    #make exe executable
    os.chmod(os.path.join(self.exe_path, self.name+".exe"), 0777)

  def makeexeaster(self, gen):
    services = []
    inits = []
    defs = []
    for serv in self.services:
      defs.append(serv.defs)
      params = []
      datas = []
      for name, typ in serv.inport:
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
    services = []
    inits = []
    defs = []
    for serv in self.services:
      defs.append(serv.defs)
      params = []
      datas = []
      for name, typ in serv.inport:
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
      return "CEXE", os.path.join(self.exe_path, self.name+".exe")
    else:
      return "SO", ""

  def makeaster(self, gen):
    services = []
    inits = []
    defs = []
    for serv in self.services:
      defs.append(serv.defs)
      params = []
      datas = []
      for name, typ in serv.inport:
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

