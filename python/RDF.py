# 
# RDF.py - Redland Python RDF module
#
# $Id$
#
# Copyright (C) 2000-2003 David Beckett - http://purl.org/net/dajobe/
# Institute for Learning and Research Technology - http://www.ilrt.org/
# University of Bristol - http://www.bristol.ac.uk/
# 
# This package is Free Software or Open Source available under the
# following licenses (these are alternatives):
#   1. GNU Lesser General Public License (LGPL)
#   2. GNU General Public License (GPL)
#   3. Mozilla Public License (MPL)
#
# and as a this one file RDF.py is also available under the
#   4. BSD License without advertising (MIT license - from
#        http://www.opensource.org/licenses/mit-license.html)
#      -------------------------------------------------------------------
#      Copyright (c) 2003, David Beckett, ILRT, University of Bristol
#
#      Permission is hereby granted, free of charge, to any person
#      obtaining a copy of this software and associated documentation
#      files (the "Software"), to deal in the Software without
#      restriction, including without limitation the rights to use, copy,
#      modify, merge, publish, distribute, sublicense, and/or sell copies
#      of the Software, and to permit persons to whom the Software is
#      furnished to do so, subject to the following conditions:
#      
#      The above copyright notice and this permission notice shall be
#      included in all copies or substantial portions of the Software.
#      
#      THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#      EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#      MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#      NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
#      BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
#      ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
#      CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#      SOFTWARE.
#     --------------------------------------------------------------------
#
# 
# See LICENSE.html or LICENSE.txt at the top of this package for the
# full license terms.
# 
# 
#

# TODO:
# * express failure conditions with Exceptions -- create a class hierarchy
#   of exceptions for Redland
# * rename modules: Redland as _Redland, RDF as Redland


"""Redland Python API

  import RDF

  storage=RDF.Storage(...)
  model=RDF.Model(storage)

  ... do stuff

The Python interface to the Redland RDF library.  See
  http://www.redland.opensource.ac.uk/
for full details.

The main class that is used is Model which represents the RDF graph
formed from triples or Statement s.  These statements consist of
three Node objects for resource or literals and can be stored in
a Storage (persistent or in-memory) as well as serialized to/from
syntaxes via the Serializer or Parser classes.

"""

import sys
import string

__all__ = [ "World",
            "Node",
            "Statement",
            "Model",
            "Iterator",
            "Serializer",
            "Stream",
            "Storage",
            "MemoryStorage",
            "HashStorage",
            "Uri",
            "Parser"]

__version__ = "0.8"

# For pydoc
__date__ = '$Date$'
__author__ = 'Dave Beckett - http://purl.org/net/dajobe'
__credits__ = """Edd Dumbill and Matt Biddulph for properly
                 Pythonisising my Perl translation"""

# Package variables [globals]
#   Python style says to use _ to prevent exporting
#   Use two underscores "(class-private names,
#     enforced by Python 1.4) in those cases where it is important
#     that only the current class accesses an attribute"
#      -- http://python.sourceforge.net/peps/pep-0008.html

_debug = 0
_world = None

_node_types={
    'NODE_TYPE_UNKNOWN'   : 0,
    'NODE_TYPE_RESOURCE'  : 1,
    'NODE_TYPE_LITERAL'   : 2,
    'NODE_TYPE_BLANK'     : 4}

import Redland;

class RedlandError(Exception):
    """Redland Runtime errors"""
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return `self.value`

class NodeTypeError(RedlandError):
    pass

class RedlandWarning(RedlandError):
    pass

def node_type(name):
    """Return the Redland node type of a node name"""
    if _node_types.has_key(name):
        return _node_types[name]
    else:
        raise NodeTypeError('Unknown node type %s' % name)

def node_type_name(num):
    """Return the name of a Redland node type"""
    for n in _node_types.keys():
        if num==_node_types[n]:
            return n
    raise NodeTypeError('Unknown node type number %d' % num)

def message_handler (type, message):
  """Internal message dispatcher from Redland to python"""
  global _debug
  if _debug:
      print "message_handler: type, message = ",type,message
  if type == 0:
    raise RedlandError(message)
  else:
    raise RedlandWarning(message)

def set_message_handler(handler):
  """Set the Redland message handler for Python.  It takes
     a single function that takes (integer, string) arguments."""
  import Redland_python;
  Redland_python.set_callback(handler)


class World(object):
  """Redland Initialisation class.

  There are no user methods (can only be constructed).

  """

  def __init__(self,digest_name="",uri_hash=None):
    """Create new RDF World object (constructor)"""
    self._world=Redland.librdf_new_world()
    Redland.librdf_world_open(self._world)
    Redland.librdf_python_world_init(self._world)
    import Redland_python;
    Redland_python.set_callback(message_handler)

  def __del__(self):
    """Destroy RDF World object (destructor)."""
    global _debug    
    if _debug:
      print "Destroying RDF.World"
    Redland.librdf_free_world(self._world)

# end class World


def debug(value=-1):
  global _debug
  if value >= 0:
    _debug=value
  else:
    return _debug


class Node(object):
  """Redland Node (RDF Resource, Property, Literal) Class

    import RDF
    node1=RDF.Node()
    node2=RDF.Node(uri_string="http://example.com/")
    node3=RDF.Node(uri=RDF.Uri("http://example.com/"))
    node4=RDF.Node(literal="Hello, World!")
    node5=RDF.Node(literal="<tag>content</tag>", is_wf_xml=1)
    node5=RDF.Node(blank="abc")
    node7=RDF.Node(node=node5)
  ...

    print node2
    if node7.is_resource():
      print "Resource with URI", node7.uri()

    if node5.is_blank():
      print "Resource with blank node name ", node5.get_blank_identifier()

  """

  def __init__(self, **args):
    """Create an RDF Node (constructor).

Creates a new RDF Node using the following fields:
  uri_string  - create a resource node from a string URI
  uri         - create a resource node from a URI object
  literal     - create a literal node from a literal string   
    datatype     - the datatype URI
    is_wf_xml    - the literal is XML (alternative to datatype)
    xml_language - the literal XML language
  blank       - create a resource node from with a blank node identiifer
  node        - copy a node

    """
    global _world
    global _debug
    if _debug:
      print "Creating RDF.Node args=",args
    self._node=None

    if args.has_key('uri_string'):
      self._node=Redland.librdf_new_node_from_uri_string(_world._world,
        args['uri_string'])

    elif args.has_key('uri'):
      # no need to copy the underlying uri as the redland C api does
      # this on node construction
      self._node=Redland.librdf_new_node_from_uri(args['uri']._reduri)

    elif args.has_key('literal'):
      if args.has_key('xml_language'):
        xml_language=args['xml_language']
      else:
        xml_language=""
      if args.has_key('is_wf_xml'):
        is_wf_xml=args['is_wf_xml']
      else:
        is_wf_xml=0
      if args.has_key('datatype'):
        datatype=args['datatype']
        self._node=Redland.librdf_new_node_from_typed_literal(_world._world,
          args['literal'], xml_language, datatype._uri)
      else:
        self._node=Redland.librdf_new_node_from_literal(_world._world,
          args['literal'], xml_language, is_wf_xml)

    elif args.has_key('node'):
      self._node=Redland.librdf_new_node_from_node(args['node']._node)

    elif args.has_key('blank'):
      self._node=Redland.librdf_new_node_from_blank_identifier(_world._world, args['blank'])

    elif args.has_key('from_object'):
      if args.has_key('do_not_copy'):
        self._node=args['from_object']
      else:
        self._node=Redland.librdf_new_node_from_node(args['from_object'])
    else:
      self._node=Redland.librdf_new_node(_world._world)

  def __del__(self):
    """Free an RDF Node (destructor)."""
    global _debug    
    if _debug:
      print "Destroying RDF.Node"
    if self._node:
      if _debug:
        print "Deleting Redland node object"
      Redland.librdf_free_node(self._node)

  def _get_uri(self):
    # we return a copy of our internal uri
    if self._get_type()==node_type('NODE_TYPE_RESOURCE'):
        return Uri(from_object=Redland.librdf_node_get_uri(self._node))
    else:
        raise NodeTypeError("Can't get URI for node type %s (%d)" % \
            (node_type_name(self._get_type()), self._get_type()))

  def _get_type(self):
    return Redland.librdf_node_get_type(self._node)

  uri = property (_get_uri)
  type = property (_get_type)

  def get_literal_value (self):
    """Get a dictionary containing the value of the Node literal"""
    dt_uri=Redland.librdf_node_get_literal_value_datatype_uri(self._node)
    if dt_uri:
      dt_uri=Uri(uri_string=Redland.librdf_uri_to_string(dt_uri))
    val={
        'string': Redland.librdf_node_get_literal_value(self._node),
        'language': Redland.librdf_node_get_literal_value_language(self._node),
        'datatype': dt_uri
        }
    return val

  def get_blank_identifier(self):
    """Get the blank node identifier of the Node"""
    if self.type != _node_types['NODE_TYPE_BLANK']:
      return ""
    else:
      return Redland.librdf_node_get_blank_identifier(self._node)

  def __str__(self):
    """Get a string representation of an RDF Node."""
    if self._node == None:
        return ""
    else:
        return Redland.librdf_node_to_string(self._node)

  def __eq__ (self,other):
    """Equality of an RDF Node compared to another RDF Node."""
    if type(other)==type(None):
        if type(self)==type(None):
            return 1
        else:
            return 0
    return (Redland.librdf_node_equals(self._node, other._node) != 0)

  def __ne__ (self,other):
    """Inequality of an RDF Node compared to another RDF Node."""
    if type(other)==type(None):
        if type(self)==type(None):
            return 0
        else:
            return 1
    return (Redland.librdf_node_equals(self._node, other._node) == 0)

  def __hash__(self):
    return hash(str(self))

  def is_resource(self):
    """Return true if node is a resource  with a URI"""   
    return (Redland.librdf_node_is_resource(self._node) != 0)

  def is_literal(self):
    """Return true if node is a literal"""
    return (Redland.librdf_node_is_literal(self._node) != 0)
  
  def is_blank(self):
    """Return true if node is a blank node"""   
    return (Redland.librdf_node_is_blank(self._node) != 0)
  
# end class Node


class Statement(object):
  """Redland Statement (triple) class

    import RDF
    statement1=RDF.Statement(subject=node1, predicate=node2, object=node3)
    statement2=RDF.Statement(statement=statement1)

    if statement2.subject.is_resource:
      print "statement2 subject is URI ",statement2.subject.uri

    Statements can also be used as if they are Python lists:

    for statement in parser.parse_as_stream(source):
      model.add_statement(statement)

    for statement in model.find_statements(s):
      print statement

    If you need the context, use the context_iter() method which
    returns a 2-tuple of (statement, context node):

    for s,c in m.find_statements(s):
      print c

    
  """

  def __init__(self, **args):
    """Create an RDF Statement (constructor).

Creates a new RDF Statement from either of the two forms:

    s1=RDF.Statement(subject=node1, predicate=node2, object=node3)
Create a Statement from three Node objects.

    s2=RDF.Statement(statement=s1)
Copy an existing Statement s1.

    """
    global _world
    global _debug    
    if _debug:
      print "Creating RDF.Statement object args",args
    self._statement=None

    if args.has_key('statement'):
        self._statement=Redland.librdf_new_statement_from_statement(
            args['statement']._statement)

    elif args.has_key('subject'):
        subject=args['subject']
        predicate=args['predicate']
        object=args['object']

        if subject==None:
            s=None
        else:
            s=Redland.librdf_new_node_from_node(subject._node)

        if predicate==None:
            p=None
        else:
            p=Redland.librdf_new_node_from_node(predicate._node)

        if object==None:
            o=None
        else:
            o=Redland.librdf_new_node_from_node(object._node)

        self._statement=Redland.librdf_new_statement_from_nodes(
            _world._world, s, p, o)

    elif args.has_key('from_object'):
      self._statement=Redland.librdf_new_statement_from_statement(args['from_object'])
    else:
      self._statement=Redland.librdf_new_statement(_world._world)

  def __del__(self):
    global _debug    
    if _debug:
      print "Destroying RDF.Statement"
    if self._statement:
      if _debug:
        print "Deleting Redland statement object"
      Redland.librdf_free_statement(self._statement)

  def _wrap_node(self, rednode):
    return Node(from_object=rednode)

  def _get_subject(self):
    return self._wrap_node(
        Redland.librdf_statement_get_subject(self._statement))

  def _get_object(self):
    return self._wrap_node(
        Redland.librdf_statement_get_object(self._statement))

  def _get_predicate(self):
    return self._wrap_node(
        Redland.librdf_statement_get_predicate(self._statement))

  def _set_subject(self, value):
    if value==None:
        Redland.librdf_statement_set_subject(self._statement, None)
    else:
        Redland.librdf_statement_set_subject(self._statement,
            Redland.librdf_new_node_from_node(value._node))

  def _set_object(self, value):
    if value==None:
        Redland.librdf_statement_set_object(self._statement, None)
    else:
        Redland.librdf_statement_set_object(self._statement,
            Redland.librdf_new_node_from_node(value._node))

  def _set_predicate(self, value):
    if value==None:
        Redland.librdf_statement_set_predicate(self._statement, None)
    else:
        Redland.librdf_statement_set_predicate(self._statement,
            Redland.librdf_new_node_from_node(value._node))

  object = property (_get_object, _set_object)
  subject = property (_get_subject, _set_subject)
  predicate = property (_get_predicate, _set_predicate)
  
  def __str__ (self):
    if self._statement == None:
        return ""
    else:
        return Redland.librdf_statement_to_string(self._statement)

# end class Statement

class Model(object):
  """Redland Graph class

    import RDF
    m1=RDF.Model(storage=s)

  The main interface to the Redland RDF graph (formed from triples, or
  RDF statements).  There are many methods for adding, removing, querying
  statements and serializing them to/from syntaxes using the Serializer
  or Parser classes.

  Models can also be used as Python lists to give every triple in the
  model (via the serialise() method):

  for statement in model:
    print statement

  """

  def __init__(self, storage=None, **args):
    """Create an RDF Model (constructor).

Create a new RDF Model using any of these forms

  m1=RDF.Model(storage=s1)
Create a Model from an existing Storage (most common use).  
Optional fields:
  options_string - A string of options for the Model
  options_hash   - A Hash of options for the Model

  m2=RDF.Model(model=m1)
Copy an existing model m1, copying the underlying Storage of m1

  m3=RDF.Model()
Create a model using an in memory storage.

    """
    global _world
    global _debug    
    if _debug:
      print "Creating RDF.Model args=",args
    self._model=None
    self._storage=None

    if storage is None:
      storage = MemoryStorage()

    if args.has_key('options_string'):
      self._model=Redland.librdf_new_model(_world._world, storage._storage,
        args['options_string'])
    elif args.has_key('options_hash'):
      self._model=Redland.librdf_new_model_with_options( _world._world,
        storage._storage, args['options_hash'].hash)
    elif args.has_key('model'):
      self._model=Redland.librdf_new_model_from_model(storage._storage,
                                                     args['model']._model)
    else:
      self._model=Redland.librdf_new_model(_world._world, storage._storage, "")

    if self._model == "NULL" or self._model == None:
      self._model=None
      raise "new RDF.Model failed"
    else:
      # keep a reference around so storage object is destroyed after this
      self._storage=storage

  def __iter__(self):
    return self.serialise().__iter__()

  def __del__(self):
    global _debug    
    if _debug:
      print "Destroying RDF.Model"
    if self._model:
      Redland.librdf_free_model(self._model)

  def __len__(self):
    return self.size()

  def size(self):
    """Return the size of the Model in number of statements (<0 if not countabl)"""
    return Redland.librdf_model_size(self._model)

  def add(self,subject,predicate,object):
    """Add the statement (subject,predicate,object) to the model"""
    return Redland.librdf_model_add(self._model, 
        Redland.librdf_new_node_from_node(subject._node),
        Redland.librdf_new_node_from_node(predicate._node),
        Redland.librdf_new_node_from_node(object._node));

  def add_typed_literal_statement (self,subject,predicate,
                                   string,xml_language=None,datatype=None):
    """Add the Statement (subject,predicate, typed literal) to the Model
       where the typed literal is constructed from the
       literal string, optional XML language and optional datatype URI."""
    if datatype !=None:
        datatype=datatype._reduri
    subject_copy=Redland.librdf_new_node_from_node(subject._node)
    predicate_copy=Redland.librdf_new_node_from_node(predicate._node)
    return Redland.librdf_model_add_typed_literal_statement(self._model,
        subject_copy, predicate_copy, string, xml_language, datatype)

  def add_statement (self,statement,context=None):
    """Add the Statement to the Model with optional context Node"""
    # adding a statement means it gets *copied* into the model
    # we are free to re-use the statement after adding it
    if context != None:
      return Redland.librdf_model_context_add_statement(self._model,
                                                        context._node,
                                                        statement._statement)
    else:
      return Redland.librdf_model_add_statement(self._model,
                                                statement._statement)

  def add_statements (self,statement_stream,context=None):
    """Add the Stream of Statements to the Model with the optional context Node"""
    if context != None:
      return Redland.librdf_model_context_add_statements(self._model,
                                                         context._node,
                                                         statement_stream._stream)
    else:
      return Redland.librdf_model_add_statements(self._model,
                                                 statement_stream.stream)

  def remove_statement (self,statement,context=None):
    """Remove the Statement from the Model with the optional context Node"""
    if context != None:
      return Redland.librdf_model_context_remove_statement(self._model,
                                                           context._node,
                                                           statement._statement)
    else:
      return Redland.librdf_model_remove_statement(self._model,
                                                   statement._statement)

  def context_remove_statements (self,context):
    """Remove all Statement s from the Model with the given context Node"""
    return Redland.librdf_model_context_remove_statements(self._model,
                                                          context._node),

  def contains_statement (self,statement):
    """Return true if the Statement is in the Model"""
    return Redland.librdf_model_contains_statement(self._model,
        statement._statement)

  def serialise (self,context=None):
    """Return the Model as a Stream of Statements"""
    if context is None:
        my_stream=Redland.librdf_model_serialise(self._model)
    else:
        my_stream=Redland.librdf_model_context_serialize(self._model,context._node)
    return Stream(my_stream,self)

  def find_statements (self,statement):
    """Return a Stream of Statements matching the given
       partial Statement - the missing nodes of the
       partial statement match any node in the Model."""
    my_stream=Redland.librdf_model_find_statements(self._model,
        statement._statement)
    return Stream(my_stream,self)

  def sources (self,arc,target):
    """Return a sequence of Node s that are the source
       of Statements in the Model matching (?, arc, target)."""
    my_iterator=Redland.librdf_model_get_sources(self._model, arc._node,
        target._node)
    if my_iterator is None:
      return []

    user_iterator=Iterator(my_iterator,self,arc,target)
    if user_iterator is None:
      return []

    results=[]
    while not user_iterator.end():
      results.append(user_iterator.current())
      user_iterator.next()

    user_iterator=None
    return results

  def arcs (self,source,target):
    """Return a sequence of Node s that are the arcs
       of Statements in the Model matching (source, ?, target)."""
    my_iterator=Redland.librdf_model_get_arcs(self._model, source._node,
        target._node)
    if my_iterator is None:
      return []

    user_iterator=Iterator(my_iterator,self,source,target)
    if user_iterator is None:
      return []

    results=[]
    while not user_iterator.end():
      results.append(user_iterator.current())
      user_iterator.next()

    user_iterator=None
    return results

  def targets (self,source,arc):
    """Return a sequence of Node s that are the targets
       of Statements in the Model matching (source, arc, ?)."""
    my_iterator=Redland.librdf_model_get_targets(self._model, source._node,
        arc._node)
    if my_iterator is None:
      return []

    user_iterator=Iterator(my_iterator,self,source,arc)
    if user_iterator is None:
      return []

    results=[]
    while not user_iterator.end():
      results.append(user_iterator.current())
      user_iterator.next()

    user_iterator=None
    return results

  def get_sources_iterator (self,arc,target):
    """Return an Iterator of Node s that are the sources
       of Statements in the Model matching (?, arc, target).
       The sources method is recommended in preference to this."""
    my_iterator=Redland.librdf_model_get_sources(self._model, arc._node,
        target._node)
    return Iterator(my_iterator,self,arc,target)

  def get_arcs_iterator (self,source,target):
    """Return an Iterator of Node s that are the arcs
       of Statements in the Model matching (source, ?, target).
       The arcs method is recommended in preference to this."""
    my_iterator=Redland.librdf_model_get_arcs(self._model, source._node,
        target._node)
    return Iterator(my_iterator,self,source,target)

  def get_targets_iterator (self,source,arc):
    """Return an Iterator of Node s that are the targets
       of Statements in the Model matching (source, arc, ?).
       The targets method is recommended in preference to this."""
    my_iterator=Redland.librdf_model_get_targets(self._model, source._node,
        arc._node)
    return Iterator(my_iterator,self,source,arc)

  def get_source (self,arc,target):
    """Return one Node in the Model matching (?, arc, target)."""
    my_node=Redland.librdf_model_get_source(self._model, arc._node,
        target._node)
    if not my_node:
      return None
    else:
      return Node(from_object=my_node, do_not_copy=1)

  def get_arc (self,source,target):
    """Return one Node in the Model matching (source, ?, target)."""
    my_node=Redland.librdf_model_get_arc(self._model, source._node,
        target._node)
    if not my_node:
      return None
    else:
      return Node(from_object=my_node, do_not_copy=1)

  def get_target (self,source,arc):
    """Return one Node in the Model matching (source, arc, ?)."""
    my_node=Redland.librdf_model_get_target(self._model, source._node,
        arc._node)
    if not my_node:
      return None
    else:
      return Node(from_object=my_node, do_not_copy=1)

# end class Model


class Iterator(object):
  """Redland Node Iterator class

     A class for iterating over a sequence of Node s such as
     those returned from a Model query.  Some methods return
     Iterator s or Python sequences.  If this is used, it works
     as follows:

       iterator=model.get_targets_iterator(source, arc)
       while not iterator.end():
         # get the current Node
         node=iterator.current()
         # do something with it
         # (it is shared; you must copy it you want to keep it)
         ...
         iterator.next()
       iterator=None

     """

  def __init__(self,object,creator1=None,creator2=None,creator3=None):
    """Create an RDF Iterator (constructor)."""
    global _debug    
    if _debug:
      print "Creating RDF.Iterator object=",object,"creator=",creator1
    self._iterator=object
    # keep references to the things we're iterating over so they
    # don't get destroyed before we're done with them.
    self._creator1=creator1
    self._creator2=creator2
    self._creator3=creator3

  def __del__(self):
    global _debug    
    if _debug:
      print "Destroying RDF.Iterator"
    Redland.librdf_free_iterator(self._iterator)

  def end (self):
    """Return true if the iterator is exhausted"""
    return Redland.librdf_iterator_end(self._iterator)

  def have_elements (self):
    print """RDF.Iterator method have_elements is deprecated,
please use 'not iterator.end' instead."""
    return Redland.librdf_iterator_have_elements(self._iterator)

  def current (self):
    """Return the current object on the Iterator"""
    my_node=Redland.librdf_iterator_get_object(self._iterator)
    if my_node == "NULL" or my_node == None:
      return None

    return Node(from_object=my_node)

  def next (self):
    """Move to the next object on the Iterator"""
    Redland.librdf_iterator_next(self._iterator)

  def context (self):
    """Return the context Node of the current object on the Iterator"""
    my_node=Redland.librdf_iterator_get_context(self._iterator)
    if my_node == "NULL" or my_node == None:
      return None

    return Node(from_object=my_node)

# end class Iterator

class StreamWithContextIter(object):
  def __init__(self,stream):
    global _debug
    if _debug:
      print "Creating StreamWithContextIter for Stream "+repr(stream)  
    self.stream = stream
    self.first = 1

  def __iter__(self):
    return self

  def next(self):
    if self.first:
      self.first = 0
    else:
      self.stream.next()
    if self.stream is None or self.stream.end():
      raise StopIteration
    return (self.stream.current(),self.stream.context())

class IteratorWithContextIter(object):
  def __init__(self,iterator):
    global _debug
    if _debug:
      print "Creating IteratorWithContextIter for Iterator "+repr(iterator)  
    self.iterator = iterator
    self.first = 1

  def __iter__(self):
    return self

  def next(self):
    if self.first:
      self.first = 0
    else:
      self.iterator.next()
    if self.iterator is None or self.iterator.end():
      raise StopIteration
    try:
      return (self.iterator.current(),self.iterator.context())
    except AttributeError:
      return (self.iterator.current(),None)

class IteratorIter(object):
  def __init__(self,iterator):
    global _debug
    if _debug:
      print "Creating IteratorIter for Iterator "+repr(iterator)  
    self.iterator = iterator
    self.first = 1

  def __iter__(self):
    return self

  def next(self):
    if self.first:
      self.first = 0
    else:
      self.iterator.next()
    if self.iterator is None or self.iterator.end():
      raise StopIteration
    return self.iterator.current()

class StreamIter:
  def __init__(self,stream):
    global _debug
    if _debug:
      print "Creating StreamIter for Stream "+repr(stream)  
    self.stream = stream
    self.first = 1

  def __iter__(self):
    return self

  def next(self):
    if self.first:
      self.first = 0
    else:
      self.stream.next()
    if self.stream is None or self.stream.end():
      raise StopIteration
    return self.stream.current()

class Stream(object):
  """Redland Statement Stream class

     A class for iterating over a sequence of Statement s such as
     those returned from a Model query.  Some methods return
     Statement s or Python sequences.  If this is used, it works
     as follows:

       stream=model.serialise()
       while not stream.end():
         # get the current Statement
         statement=stream.current()
         # do something with it
         # (it is shared; you must copy it you want to keep it)
         ...
         stream.next()
       stream=None

     """

  def __init__(self, object, creator):
    """Create an RDF Stream (constructor)."""
    global _debug    
    if _debug:
      print "Creating RDF.Stream for object",object, \
        "creator",creator

    self._stream=object;

    # Keep around a reference to the object that created the stream
    # so that Python does not destroy them before us.
    self.creator=creator;

  def context_iter(self):
    """Return an iterator over this tstream that
       returns (stream, context) tuples each time it is iterated."""
    return StreamWithContextIter(self)

  def __iter__(self):
    return StreamIter(self)

  def __del__(self):
    global _debug    
    if _debug:
      print "Destroying RDF.Stream"
    if self._stream:
      Redland.librdf_free_stream(self._stream)

  def end (self):
    """Return true if the stream is exhausted"""
    if not self._stream:
      return 1
    return Redland.librdf_stream_end(self._stream)

  def current (self):
    """Return the current Statement on the Stream"""
    if not self._stream:
      return None

    my_statement=Redland.librdf_stream_get_object(self._stream)
    if my_statement == "NULL" or my_statement == None:
      return None
    return Statement(from_object=my_statement)

  def next (self):
    """Move to the next Statement on the Stream"""
    if not self._stream:
      return 1

    return Redland.librdf_stream_next(self._stream)

  def context (self):
    """Return the context Node of the current object on the Stream"""
    if not self._stream:
      return 1

    my_node=Redland.librdf_stream_get_context(self._stream)
    if my_node == "NULL" or my_node == None:
      return None

    return Node(from_object=my_node)

# end class Stream


class Storage(object):

  """Redland Statement Storage class

     import RDF
     storage=RDF.Storage(storage_name="memory")

  The Redland abstraction for storing RDF graphs as Statement s.

  There are no user methods (can only be constructed).

  """

  def __init__(self, **args):
    """Create an RDF Storage (constructor).

    Create a new RDF Storage using any of these forms

  s1=RDF.Storage(storage_name="name")
Create a Storage with the given name.  Currently the built in
storages are "memory" and "hashes".  "hashes" takes extra
arguments passed in the field options_string, some of which are
required:
  options_string="hash-type='memory',new='yes',write='yes'"
    hash-type - required and can be the name of any Hash type supported.
      'memory' is always present, and 'bdb' is available
      when BerkeleyDB is compiled in.
    new - optional and takes a boolean value (default false)
      If true, it allows updating of an existing Storage 
    write - optional and takes a boolean value (default true)
      If false, the Storage is opened read-only and for file-based
      Storages or those with locks, may be shared-read.

The other form is:
  s2=RDF.Storage(storage=s1)
Copy an existing Storage s1.

"""
    global _world
    global _debug    
    if _debug:
      print "Creating RDF.Storage args=",args
    self._storage=None

    if (args.has_key('storage_name') and
        args.has_key('name') and 
        args.has_key('options_string')):
      self._storage=Redland.librdf_new_storage(_world._world,
          args['storage_name'], args['name'], args['options_string']);
    elif args.has_key('storage'):
      self._storage=Redland.librdf_new_storage_from_storage(
          args['storage']._storage);
    else:
      raise "new RDF.Storage failed - illegal arguments"

    if self._storage == "NULL" or self._storage == None:
      self._storage=None
      raise "new RDF.Storage failed"

  def __del__(self):
    global _debug    
    if _debug:
      print "Destroying RDF.Storage"
    if self._storage:
      Redland.librdf_free_storage(self._storage)

# end class Storage


class HashStorage(Storage):
  """Redland Hashed Storage class

     import RDF
     h1=RDF.HashStorage("abc", options="hash-type='memory'")

  Class of hashed Storage for a particular type of hash (typically
  hash-type is "memory" or "bdb") and any other options.
  """
  def __init__(self,hash_name,options):
    return Storage.__init__(self,name=hash_name,storage_name="hashes",options_string=options)


class MemoryStorage(Storage):
  """Redland memory Storage class

     import RDF
     h1=RDF.MemoryStorage()
     h1=RDF.MemoryStorage("abc")
     h2=RDF.MemoryStorage("abc", "write='no'")

  Class of memory Storage with optional name, additional options.
  """
  def __init__(self,mem_name="",options_string=""):
    return Storage.__init__(self,name=mem_name,storage_name="memory",options_string=options_string)


class Uri(object):
  """Redland URI Class

  import RDF
  uri1=RDF.Uri(string="http://example.com/")
  uri2=RDF.Uri(uri=uri1)

  """
  
  def __init__(self, **args):
    """Create an RDF URI (constructor).

Creates a new RDF URI from either of the following forms:

  uri1=RDF.Uri(string="http://example.com/")
Create a URI from the given string.

  uri2=RDF.Uri(uri=uri1)
Copy an existing URI uri1.

    """
    global _world
    global _debug    
    if _debug:
      print "Creating RDF.Uri args=",args
    self._reduri=None

    if args.has_key('string') and args['string']!=None:
        self._reduri=Redland.librdf_new_uri(_world._world, args['string'])
    elif args.has_key('uri'):
        self._reduri=Redland.librdf_new_uri_from_uri(args['uri']._reduri)
    elif args.has_key('from_object'):
        if args['from_object']!=None:
            self._reduri=Redland.librdf_new_uri_from_uri(args['from_object'])
        else:
            raise 'RDF.py: attempt to create new URI from null URI'

  def __del__(self):
    global _debug    
    if _debug:
      print "Destroying RDF.Uri"
    if self._reduri:
      if _debug:
        print "Deleting Redland uri object"
      Redland.librdf_free_uri(self._reduri)

  def __str__(self):
    """Get a string representation of an RDF URI."""
    return Redland.librdf_uri_to_string(self._reduri)

  def __hash__(self):
    return hash(self._reduri)
  
  def __eq__(self,other):
    """Equality of RDF URI to another RDF URI."""
    if type(other)==type(None):
        if type(self)==type(None):
            return 1
        else:
            return 0
    return (Redland.librdf_uri_equals(self._reduri, other._reduri) != 0)

  def __ne__(self,other):
    """Inequality of RDF URI to another RDF URI."""
    if type(other)==type(None):
        if type(self)==type(None):
            return 0
        else:
            return 1
    return (Redland.librdf_uri_equals(self._reduri, other._reduri) == 0)

# end class Uri


class Parser(object):
  """Redland Syntax Parser Class

  import RDF
  parser1=RDF.Parser()
  parser2=RDF.Parser(name="rdfxml")
  parser3=RDF.Parser(mime_type="application/rdf+xml")

  stream=parser2.parse_as_stream("file://dir/file.rdf")
  parser3.parse_into_model(model, "file://dir/file.rdf", "http://example.org/")

  The default parser type if not given explicitly is raptor,
  for the RDF/XML syntax.
  """
  
  def __init__(self, name="raptor", mime_type="application/rdf+xml", uri=None):
    """Create an RDF Parser (constructor).

Create a new RDF Parser for a particular syntax.  The parser is
chosen by the fields given to the constructor, all of which are
optional.  When any are given, they must all match.

  name      - parser name (currently "raptor" and "ntriples")
  mime_type - currently "application/rdf+xml" (default) or "text/plain" (ntriples)
  uri       - URI identifying the syntax
              currently only "http://www.w3.org/TR/rdf-testcases/#ntriples"

    """
    global _world
    global _debug    
    if _debug:
      print "Creating RDF.Parser name=",name,"mime_type=",mime_type, \
        "uri=",uri

    if uri!=None:
        uri=uri._reduri

    self._parser=Redland.librdf_new_parser(_world._world, name,
        mime_type, uri)

  def __del__(self):
    global _debug    
    if _debug:
      print "Destroying RDF.Parser"
    if self._parser:
      Redland.librdf_free_parser(self._parser)

  def parse_as_stream (self, uri, base_uri=None):
    """"Return a Stream of Statements from parsing the content at
        (file: only at present) URI, for the optional base URI
        or None if the parsing fails."""
    if type(uri) is str:
        uri = Uri(string=uri)
    if base_uri==None:
        base_uri=uri
    my_stream=Redland.librdf_parser_parse_as_stream(self._parser,
        uri._reduri, base_uri._reduri)
    if my_stream==None:
      return None
    return Stream(my_stream, self)

  def parse_string_as_stream (self, string, base_uri):
    """"Return a Stream of Statements from parsing the content in
        string with the required base URI or None if the parsing fails."""
    if base_uri is None:
      raise "RDF.py: A base URI is required when parsing a string"
    my_stream=Redland.librdf_parser_parse_string_as_stream(self._parser,
        string, base_uri._reduri)
    if my_stream==None:
      return None
    return Stream(my_stream, self)

  def parse_into_model (self, model, uri, base_uri=None):
    """"Parse into the Model model from the content at
        (file: only at present) URI, for the optional base URI"""
    if type(uri) is str:
        uri = Uri(string=uri)
    if base_uri==None:
        base_uri=uri
    try:
        r = Redland.librdf_parser_parse_into_model(self._parser,
          uri._reduri, base_uri._reduri, model._model)
    except RedlandError, err:
        print "Caught error",err
        raise err
    return 1

  def parse_string_into_model (self, model, string, base_uri):
    """"Parse into the Model model from the content ain string
        with the required base URI"""
    if base_uri is None:
      raise "RDF.py: A base URI is required when parsing a string"
    return Redland.librdf_parser_parse_string_into_model(self._parser,
      string, base_uri._reduri, model._model)

  def get_feature(self, uri):
    """Return the value of Parser feature URI uri"""
    if not isinstance(uri, Uri):
      uri=Uri(string=uri)
    return Redland.librdf_parser_get_feature(self._parser,uri._reduri)

  def set_feature(self, uri, value):
    """Set the value of Parser feature URI uri."""
    if not isinstance(uri, Uri):
      uri=Uri(string=uri)
    Redland.librdf_parser_set_feature(self._parser,uri._reduri,value)

# end class Parser


class Serializer(object):
  """ Redland Syntax Serializer Class

  import RDF
  ser1=RDF.Serializer(mime_type="application/rdf+xml")

  A class for turning a Model into a syntax serialization (at present
  only to local files).
  """
  
  def __init__(self, name="", mime_type="application/rdf+xml", uri=None):
    """Create an RDF Serializer (constructor)."""
    global _world
    global _debug    
    if _debug:
      print "Creating RDF.Serializer name=",name,"mime_type=",mime_type, \
        "uri=",uri

    if uri!=None:
        uri=uri._reduri

    self._serializer=Redland.librdf_new_serializer(_world._world, name,
        mime_type, uri)

  def __del__(self):
    global _debug    
    if _debug:
      print "Destroying RDF.Serializer"
    if self._serializer:
      Redland.librdf_free_serializer(self._serializer)

  def serialize_model_to_file (self, name, model, base_uri=None):
    """Serialize to filename name the Model model using the
       optional base URI."""
    if base_uri !=None:
        base_uri=base_uri._reduri
    return Redland.librdf_serializer_serialize_model_to_file(self._serializer,
      name, base_uri, model._model)

  def get_feature(self, uri):
    """Return the value of Serializer feature URI uri"""
    if not isinstance(uri, Uri):
      uri=Uri(string=uri)
    return Redland.librdf_serializer_get_feature(self._serializer,uri._reduri)

  def set_feature(self, uri, value):
    """Set the value of Serializer feature URI uri."""
    if not isinstance(uri, Uri):
      uri=Uri(string=uri)
    Redland.librdf_serializer_set_feature(self._serializer,uri._reduri,value)

# end class Serializer


class NS(object):
  """ Redland Namespace Utility Class

  import RDF
  nspace = RDF.NS("http://example.com/foo#")

  # creates an RDF Node for http://example.com/foo#blah   
  node1 = nspace.blah

  # creates an RDF Node for http://example.com/foo#blah   
  node2 = nspace['blah']

  A class for generating RDF Nodes with URIs from the same vocabulary
  (such as XML Namespace) varying only in the appended name in
  the vocabulary.  Each node returned is a pointer to a shared copy.

  """

  def __init__(self,prefix):
    self.prefix = prefix
    self.nodecache = {}

  def node(self,localName):
    if localName not in self.nodecache:
      self.nodecache[localName] = Node(uri_string=self.prefix+localName)
    return self.nodecache[localName]

  def __getitem__(self,localName):
    return self.node(localName)

  def __getattr__(self,localName):
    return self.node(localName)


# global init, create our world.

_world=World()
