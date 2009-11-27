"""
  Module that defines PYComponent for SALOME components implemented in Python
"""
import os
from gener import Component, Invalid
from pyth_tmpl import pyinitService, pyService, pyCompoEXE, pyCompo
import textwrap
from string import split,rstrip,join

def indent(text, prefix='    '):
  """Indent text by prepending a given prefix to each line."""
  if not text: return ''
  lines = split(text, '\n')
  lines = map(lambda line, prefix=prefix: prefix + line, lines)
  if lines: lines[-1] = rstrip(lines[-1])
  return join(lines, '\n')

class PYComponent(Component):
  def __init__(self, name, services=None, python_path=None, kind="lib",
                     sources=None):
    """initialise component attributes"""
    self.python_path = python_path or []
    Component.__init__(self, name, services, impl="PY", kind=kind,
                             sources=sources)

  def validate(self):
    """validate component attributes"""
    Component.validate(self)
    kinds = ("lib","exe")
    if self.kind not in kinds:
      raise Invalid("kind must be one of %s for component %s" % (kinds,self.name))

  def makeCompo(self, gen):
    """generate component sources as a dictionary containing
       file names (key) and file content (values)
    """
    pyfile = "%s.py" % self.name
    sources = " ".join(map(os.path.basename,self.sources))
    if self.kind == "lib":
      return {"Makefile.am":gen.makeMakefile(self.getMakefileItems(gen)),
              pyfile:self.makepy(gen)
             }
    if self.kind == "exe":
      return {"Makefile.am":gen.makeMakefile(self.getMakefileItems(gen)),
              self.name+".exe":self.makepyexe(gen),
             }

  def getMakefileItems(self,gen):
    makefileItems={"header":"include $(top_srcdir)/adm_local/make_common_starter.am"}
    if self.kind == "lib":
      makefileItems["salomepython_PYTHON"]=[self.name+".py"]+self.sources
    if self.kind == "exe":
      makefileItems["salomepython_PYTHON"]=self.sources
      makefileItems["dist_salomescript_SCRIPTS"]=[self.name+".exe"]
    return makefileItems

  def makepy(self, gen):
    """generate standard SALOME component source (python module)"""
    services = []
    inits = []
    defs = []
    for serv in self.services:
      defs.append(serv.defs)
      params = []
      pyparams = []
      for name, typ in serv.inport:
        if typ=="file":continue #files are not passed through service interface
        params.append(name)
        if typ == "pyobj":
          pyparams.append("      %s=cPickle.loads(%s)" %(name, name))
      inparams = ",".join(params)
      convertinparams = '\n'.join(pyparams)

      params = []
      pyparams = []
      for name, typ in serv.outport:
        if typ=="file":continue #files are not passed through service interface
        params.append(name)
        if typ == "pyobj":
          pyparams.append("      %s=cPickle.dumps(%s,-1)" %(name, name))
      outparams = ",".join(params)
      convertoutparams = '\n'.join(pyparams)
      #dedent and indent the body
      body=textwrap.dedent(serv.body)
      body=indent(body,' '*6)

      service = pyService.substitute(component=self.name, service=serv.name, inparams=inparams,
                                     outparams=outparams, body= body,
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
    """generate standalone component source (python executable)"""
    services = []
    inits = []
    defs = []
    for serv in self.services:
      defs.append(serv.defs)
      params = []
      pyparams = []
      for name, typ in serv.inport:
        if typ=="file":continue #files are not passed through service interface
        params.append(name)
        if typ == "pyobj":
          pyparams.append("      %s=cPickle.loads(%s)" %(name, name))
      inparams = ",".join(params)
      convertinparams = '\n'.join(pyparams)

      params = []
      pyparams = []
      for name, typ in serv.outport:
        if typ=="file":continue #files are not passed through service interface
        params.append(name)
        if typ == "pyobj":
          pyparams.append("      %s=cPickle.dumps(%s,-1)" %(name, name))
      outparams = ",".join(params)
      convertoutparams = '\n'.join(pyparams)
      #dedent and indent the body
      body=textwrap.dedent(serv.body)
      body=indent(body,' '*6)
      service = pyService.substitute(component=self.name, service=serv.name,
                                     inparams=inparams, outparams=outparams,
                                     body=body,
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



