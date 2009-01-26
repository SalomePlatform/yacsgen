"""
  Module that defines PYComponent for SALOME components implemented in Python
"""
from gener import Component, Invalid
from pyth_tmpl import pyinitService, pyService, pyCompoEXE, pyCompo
from pyth_tmpl import pycompoEXEMakefile, pycompoMakefile

class PYComponent(Component):
  def __init__(self, name, services=None, python_path=None, kind="lib",
                     sources=None):
    self.python_path = python_path or []
    Component.__init__(self, name, services, impl="PY", kind=kind,
                             sources=sources)

  def validate(self):
    Component.validate(self)
    kinds = ("lib","exe")
    if self.kind not in kinds:
      raise Invalid("kind must be one of %s" % kinds)

  def makeCompo(self, gen):
    pyfile = "%s.py" % self.name
    sources = " ".join(self.sources)
    if self.kind == "lib":
      return {"Makefile.am":pycompoMakefile.substitute(module=gen.module.name, 
                                                       component=self.name,
                                                       sources=sources), 
              pyfile:self.makepy(gen)
             }
    if self.kind == "exe":
      return {"Makefile.am":pycompoEXEMakefile.substitute(module=gen.module.name, 
                                                          component=self.name,
                                                          sources=sources), 
              self.name+".exe":self.makepyexe(gen),
             }

  def makepy(self, gen):
    services = []
    inits = []
    defs = []
    for serv in self.services:
      defs.append(serv.defs)
      params = []
      pyparams = []
      for name, typ in serv.inport:
        params.append(name)
        if typ == "pyobj":
          pyparams.append("      %s=cPickle.loads(%s)" %(name, name))
      inparams = ",".join(params)
      convertinparams = '\n'.join(pyparams)

      params = []
      pyparams = []
      for name, typ in serv.outport:
        params.append(name)
        if typ == "pyobj":
          pyparams.append("      %s=cPickle.dumps(%s,-1)" %(name, name))
      outparams = ",".join(params)
      convertoutparams = '\n'.join(pyparams)
      service = pyService.substitute(component=self.name, service=serv.name, inparams=inparams,
                                     outparams=outparams, body=serv.body, 
                                     convertinparams=convertinparams,
                                     convertoutparams=convertoutparams)
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
    return pyCompo.substitute(component=self.name, module=gen.module.name,
                              servicesdef="\n".join(defs), servicesimpl="\n".join(services), 
                              initservice='\n'.join(inits),
                              python_path=python_path)

  def makepyexe(self, gen):
    services = []
    inits = []
    defs = []
    for serv in self.services:
      defs.append(serv.defs)
      params = []
      pyparams = []
      for name, typ in serv.inport:
        params.append(name)
        if typ == "pyobj":
          pyparams.append("      %s=cPickle.loads(%s)" %(name, name))
      inparams = ",".join(params)
      convertinparams = '\n'.join(pyparams)

      params = []
      pyparams = []
      for name, typ in serv.outport:
        params.append(name)
        if typ == "pyobj":
          pyparams.append("      %s=cPickle.dumps(%s,-1)" %(name, name))
      outparams = ",".join(params)
      convertoutparams = '\n'.join(pyparams)
      service = pyService.substitute(component=self.name, service=serv.name, 
                                     inparams=inparams, outparams=outparams, 
                                     body=serv.body, 
                                     convertinparams=convertinparams,
                                     convertoutparams=convertoutparams,
                                    )
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
    return pyCompoEXE.substitute(component=self.name, module=gen.module.name,
                                 servicesdef="\n".join(defs), 
                                 servicesimpl="\n".join(services),
                                 initservice='\n'.join(inits), 
                                 python_path=python_path)



