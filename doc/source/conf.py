# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import os
import subprocess
from pathlib import Path

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Simple Sphinx'
copyright = '2023, Marcel Koch'
author = 'Marcel Koch'
release = '0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['breathe', 'sphinx.ext.duration', 'sphinx.ext.autosummary',
              'myst_parser']

templates_path = ['_templates']
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']


# -- Options for Doxygen

ginkgo_root = Path('..').resolve()
ginkgo_include = Path('../../src').resolve()
doxygen_dir = Path('doxygen').resolve()

doxyfile = f"""
QUIET                  = YES

# General project info
PROJECT_NAME           = "Ginkgo"
PROJECT_NUMBER         = "Generated from document-create-functions branch based on develop. Ginkgo version 1.7.0 "
PROJECT_BRIEF          = "A numerical linear algebra library targeting many-core architectures"
INLINE_INHERITED_MEMB  = YES

# Paths and in/exclusion patterns
#The INPUT variable is defined in the specific doxy files for usr and dev.
INPUT                  =

INCLUDE_PATH           = {ginkgo_include}
OUTPUT_DIRECTORY       = {doxygen_dir}
EXAMPLE_PATH           = 
RECURSIVE              = YES
EXAMPLE_RECURSIVE      = NO
FILE_PATTERNS          = *.cpp *.cu *.hpp *.cuh *.md
EXAMPLE_PATTERNS       = *.cpp *.hpp *.cuh *.cu
EXTENSION_MAPPING      = cu=c++ cuh=c++
FULL_PATH_NAMES        = YES
STRIP_FROM_PATH        = {ginkgo_include}
STRIP_FROM_INC_PATH    = {ginkgo_include}
EXCLUDE_PATTERNS       = */test/*
USE_MDFILE_AS_MAINPAGE = 

# Parsing options
PREDEFINED             = GKO_HAVE_PAPI_SDE=1 GINKGO_BUILD_MPI=1 GINKGO_BUILD_DOXYGEN=1
JAVADOC_AUTOBRIEF      = Yes
TAB_SIZE               = 4
MARKDOWN_SUPPORT       = YES
AUTOLINK_SUPPORT       = YES
DISTRIBUTE_GROUP_DOC   = NO
GROUP_NESTED_COMPOUNDS = NO
SUBGROUPING            = YES
INLINE_GROUPED_CLASSES = NO
MACRO_EXPANSION        = YES
SKIP_FUNCTION_MACROS   = YES
INLINE_INFO            = YES
SORT_MEMBER_DOCS       = YES
SORT_BRIEF_DOCS        = NO
SORT_MEMBERS_CTORS_1ST = NO
SORT_GROUP_NAMES       = NO
SORT_BY_SCOPE_NAME     = NO
STRICT_PROTO_MATCHING  = NO
GENERATE_TODOLIST      = NO
GENERATE_TESTLIST      = NO
GENERATE_BUGLIST       = NO
GENERATE_DEPRECATEDLIST= NO
ENABLED_SECTIONS       =
MAX_INITIALIZER_LINES  = 30
SHOW_USED_FILES        = YES
SHOW_FILES             = YES
SHOW_NAMESPACES        = YES
CITE_BIB_FILES         =
INHERIT_DOCS           = YES
USE_MATHJAX            = NO

BUILTIN_STL_SUPPORT    = YES

WARN_NO_PARAMDOC       = YES
WARN_AS_ERROR          = NO
WARN_IF_UNDOCUMENTED   = NO
WARN_IF_DOC_ERROR      = NO
WARNINGS               = YES
IMAGE_PATH             = 
INLINE_SOURCES         = NO
STRIP_CODE_COMMENTS    = YES
REFERENCED_BY_RELATION = YES
REFERENCES_RELATION    = YES
REFERENCES_LINK_SOURCE = YES
SOURCE_TOOLTIPS        = YES
VERBATIM_HEADERS       = YES
# CLANG_ASSISTED_PARSING = NO
# CLANG_OPTIONS          = -I{ginkgo_include} -std=c++14

# External references
ALLEXTERNALS           = NO
EXTERNAL_GROUPS        = YES

# Graph generation

GENERATE_XML             = YES
GENERATE_LATEX           = NO
GENERATE_HTML            = NO

# this is used to hide protected members
PREDEFINED = GKO_HAVE_PAPI_SDE=1 GINKGO_BUILD_MPI=1 GINKGO_BUILD_DOXYGEN=1 protected=private

INPUT = {ginkgo_include} 
EXTRACT_STATIC         = YES
EXTRACT_LOCAL_CLASSES  = YES
EXTRACT_PRIVATE        = YES
INTERNAL_DOCS          = YES
SOURCE_BROWSER         = YES
CALL_GRAPH             = NO
CALLER_GRAPH           = NO
EXCLUDE_SYMBOLS        = *detail::* std::*
WARN_LOGFILE           = 
"""


subprocess.run(['doxygen', '-'], input=doxyfile, universal_newlines=True)
xml_dir = f"{doxygen_dir}/xml"

# -- Options for breathe

breathe_projects = {
    "ginkgo-doxy": f"{doxygen_dir}/xml"}
breathe_default_project = "ginkgo-doxy"
breathe_default_members = ("members", "undoc-members")
breathe_order_parameters_first = True
breathe_show_include = True
