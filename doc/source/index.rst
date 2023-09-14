.. Simple Sphinx documentation master file, created by
   sphinx-quickstart on Thu Sep 14 10:08:46 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Simple Sphinx's documentation!
=========================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:


.. cpp:class:: ClassA

  Documentation of ClassA

.. cpp:class:: ClassB: public ClassA

  Documentation of ClassB

.. cpp:class:: ClassC

  Documentation

.. cpp:class:: ClassD

  Documentation

.. cpp:class:: MultiParents: public ClassB, public ClassC, public ClassD

  Documentation

.. cpp:class:: MultiParentsNewLine: \
               public ClassB, \
               public ClassC, \
               public ClassD

  Documentation

.. cpp:class:: template<typename A, typename B> TemplateClass

.. cpp:function:: int function(int int1, int int2, int int3, int int4, int int5, int int6, int int7, int int8, int int9, int int10, int int11)



API
===

.. doxygenclass:: test::A

.. doxygenclass:: test::B

.. doxygenclass:: test::C

.. doxygenclass:: test::D

.. doxygenclass:: test::E

.. doxygenclass:: test::MultiParent


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
