// -*- Mode: java; c-basic-offset: 2 -*-
//
// model.java - Redland Java Model class
//
// $Id$
//
// Copyright (C) 2001 David Beckett - http://purl.org/net/dajobe/
// Institute for Learning and Research Technology - http://www.ilrt.org/
// University of Bristol - http://www.bristol.ac.uk/
// 
// This package is Free Software or Open Source available under the
// following licenses (these are alternatives):
//   1. GNU Lesser General Public License (LGPL)
//   2. GNU General Public License (GPL)
//   3. Mozilla Public License (MPL)
// 
// See LICENSE.html or LICENSE.txt at the top of this package for the
// full license terms.
// 
// 
//

package org.librdf.redland;

import org.librdf.redland.Storage;
import org.librdf.redland.Node;
import org.librdf.redland.Statement;
import org.librdf.redland.Stream;
import org.librdf.redland.Iterator;
import org.librdf.redland.Hash;


public class Model
{
  private World world;
  private long object;
  private Storage storage;

  public Model(World world, Storage storage, String options_string) 
  {
    this.world=world;
    this.object=core.librdf_new_model(world.__get_object(), storage.__get_object(), options_string);
    this.storage=storage;
  }

  public Model(World world, Storage storage, Hash options) 
  {
    this.world=world;
    this.object=core.librdf_new_model_with_options(world.__get_object(), storage.__get_object(), options.__get_object());
    this.storage=storage;
  }

  public Model(Model old_model) 
  {
    this.world=old_model.world;
    this.object=core.librdf_new_model_from_model(old_model.__get_object());
  }


  protected void finalize() throws Throwable
  {
    core.librdf_free_model(this.object);
    this.object=0;

    super.finalize();
  }


  public int size() 
  {
    return core.librdf_model_size(this.object);
  }

  public int add(Node subject, Node predicate, Node object) 
  {
    return core.librdf_model_add(this.object, subject.__get_object(), predicate.__get_object(), object.__get_object());
  }

  public int add(Node subject, Node predicate, String string, String xml_language, boolean is_wf_xml) 
  {
    int is_wf_xml_int=is_wf_xml ? 1 : 0;
    return core.librdf_model_add_string_literal_statement(this.object, subject.__get_object(), predicate.__get_object(), string, xml_language, is_wf_xml_int);
  }

  public int add(Statement statement) 
  {
    return core.librdf_model_add_statement(this.object, statement.__get_object());
  }

  public int add(Stream statement_stream) 
  {
    return core.librdf_model_add_statements(this.object, statement_stream.__get_object());
  }

  public int remove(Statement statement) 
  {
    return core.librdf_model_remove_statement(this.object, statement.__get_object());
  }

  public boolean contains(Statement statement) 
  {
    int contains_int=core.librdf_model_contains_statement(this.object, statement.__get_object());
    return (contains_int != 0);
  }

  public Stream serialise() 
  {
    return new Stream(this.world, core.librdf_model_serialise(this.object), this);
  }

  public Stream findStatements(Statement statement) 
  {
    return new Stream(this.world, core.librdf_model_find_statements(this.object, statement.__get_object()), this);
  }

  public Iterator getSources(Node arc, Node target) 
  {
    return new Iterator(this.world, core.librdf_model_get_sources(this.object, arc.__get_object(), target.__get_object()), this, arc, target);
  }

  public Iterator getArcs(Node source, Node target) 
  {
    return new Iterator(this.world, core.librdf_model_get_arcs(this.object, source.__get_object(), target.__get_object()), this, source, target);
  }

  public Iterator getTargets(Node source, Node arc) 
  {
    return new Iterator(this.world, core.librdf_model_get_targets(this.object, source.__get_object(), arc.__get_object()), this, source, arc);
  }

  public Node getSource(Node arc, Node target) 
  {
    return new Node(this.world, core.librdf_model_get_source(this.object, arc.__get_object(), target.__get_object()), true);
  }

  public Node getArc(Node source, Node target) 
  {
    return new Node(this.world, core.librdf_model_get_arc(this.object, source.__get_object(), target.__get_object()), true);
  }

  public Node getTarget(Node source, Node arc) 
  {
    return new Node(this.world, core.librdf_model_get_target(this.object, source.__get_object(), arc.__get_object()), true);
  }


  protected long __get_object() 
  {
    return this.object;
  }
}
