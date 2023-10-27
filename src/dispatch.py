from collections import defaultdict

import sys
import xml.dom.minicompat
from dataclasses import dataclass
from functools import singledispatch
import xml.dom.minidom as MD
import xml.dom.minicompat as MDC
from pathlib import Path
from typing import Tuple, Union, List, Dict, Set
import json
from frozendict import frozendict

gko_directory = "/home/marcel/projects/working-trees/ginkgo/document-create-functions/doc/doxygen/xml"
simple_directory = "/home/marcel/projects/simple-sphinx/doc/source/doxygen/xml"


def constructor(self, payload):
    self.payload = payload


def create_class(name):
    return f"xml_{name}", type(f"xml_{name}", (object,), {"name": name,
                                                          "__init__": constructor})


classes = dict(create_class(name) for name in [
    "compounddef",
    "compoundname",
    "basecompoundref",
    "derivedcompoundref",
    "briefdescription",
    "detaileddescription",
    "sectiondef",
    "memberdef",
    "templateparamlist",
    "para",
    "ref",
    "computeroutput",
    "sp",
    "programlisting",
    "highlight",
    "codeline",
    "type",
    "definition",
    "name",
    "qualifiedname",
    "argsstring",
    "location",
    "innerclass",
    "initializer",
    "formula",
    "simplesect",
    "parameterlist",
    "parametername",
    "itemizedlist",
    "orderedlist",
    "bold",
    "emphasis",
    "ulink",
    "ndash",
    "enumvalue",
    "templateparameterlist",
    # compounddef kinds
    "class",
    "struct",
    "union",
    "namespace",
    "group",
    "dir",
])


@singledispatch
def dispatch(expr, ctx):
    raise AssertionError(f"Unhandled type {type(expr)}")


@dispatch.register
def dispatch_nodelist(expr: list, ctx):
    if len(expr) > 1:
        raise AssertionError(f"Node list has to have length of 1. Please handle iteration at caller site")
    if len(expr) == 0:
        return []
    else:
        return dispatch(expr[0], ctx)


@dispatch.register
def dispatch_element(expr: MD.Element, ctx):
    return dispatch(classes[f"xml_{expr.tagName}"](expr), ctx)


def getElementsByTagName(node: MD.Element | MD.Document, tag):
    # This function is not recursive compared to Element.getElementsByTagName
    elements = []
    for child in node.childNodes:
        if isinstance(child, MD.Element) and child.tagName == tag:
            elements.append(child)
    return elements


@dispatch.register
def dispatch_(expr: classes['xml_group'] | classes["xml_dir"], ctx):
    print(f"Warning: encountered {expr.payload.attributes['kind'].value} documentation. This will be skipped!",
          file=sys.stderr)
    return None


@dispatch.register
def dispatch_class(expr: classes["xml_class"] | classes["xml_struct"] | classes["xml_union"], ctx):
    # Find the class id ( used for files/html/etc )
    payload = expr.payload
    name = dispatch(getElementsByTagName(payload, 'compoundname'), ctx)
    data = {
        'type': payload.attributes['kind'].value,
        'id': payload.attributes['id'].value,
        'prot': payload.attributes['prot'].value,
        'name': name,
        'templateparameters': dispatch(getElementsByTagName(payload, 'templateparamlist'), ctx),
        'basecompoundref': [dispatch(d, ctx) for d in getElementsByTagName(payload, 'basecompoundref')],
        'derivedcompoundref': [dispatch(d, ctx) for d in getElementsByTagName(payload, 'derivedcompoundref')],
        'briefdescription': dispatch(getElementsByTagName(payload, 'briefdescription'), ctx),
        'detaileddescription': dispatch(getElementsByTagName(payload, 'detaileddescription'), ctx),
        'sectiondef': [dispatch(sec, ctx) for sec in getElementsByTagName(payload, 'sectiondef')],
        'specializations': list(dict(**kwargs) for kwargs in ctx.specializations[name]),
        'specializationof': ctx.specializationof[name]
    }
    return data


@dispatch.register
def dispatch_compounddef(expr: classes['xml_compounddef'], ctx):
    kind = expr.payload.attributes['kind'].value
    return dispatch(classes[f"xml_{kind}"](expr.payload), ctx)


@dispatch.register
def dispatch_compounddef(expr: classes['xml_compoundname'], ctx):
    return dispatch(expr.payload.childNodes[0], ctx)


@dispatch.register
def dispatch_(expr: classes['xml_basecompoundref'] | classes['xml_derivedcompoundref'], ctx):
    return dispatch(expr.payload.childNodes[0], ctx)


@dispatch.register
def dispatch_(expr: classes['xml_briefdescription'] | classes['xml_detaileddescription'], ctx):
    para = getElementsByTagName(expr.payload, 'para')
    if para:
        return sum([dispatch(p, ctx) for p in para], start=[])
    else:
        return [""]


@dispatch.register
def dispatch_(expr: classes['xml_sectiondef'], ctx):
    return {
        'type': expr.payload.attributes['kind'].value,
        'members': [dispatch(member, ctx) for member in getElementsByTagName(expr.payload, "memberdef")]
    }


@dispatch.register
def dispatch_(expr: classes['xml_memberdef'], ctx):
    payload = expr.payload
    kind = payload.attributes["kind"].value
    base_data = {
        'type': 'member',
        **dict(payload.attributes.items()),
        'name': dispatch(getElementsByTagName(payload, 'name'), ctx),
        'briefdescription': dispatch(getElementsByTagName(payload, 'briefdescription'), ctx),
        'detaileddescription': dispatch(getElementsByTagName(payload, 'detaileddescription'), ctx),
        # ignore inbodydescription since that doesn't exist in C++
        'location': dispatch(getElementsByTagName(payload, 'location'), ctx)
    }

    if kind == 'variable':
        initializer = getElementsByTagName(payload, 'initializer')
        return {
            **base_data,
            'definition': dispatch(getElementsByTagName(payload, 'definition'), ctx),
            'initializer': dispatch(initializer, ctx) if initializer else "",
        }
    elif kind == 'function':
        return {
            **base_data,
            'templateparameters': dispatch(getElementsByTagName(payload, 'templateparamlist'), ctx),
            'definition': dispatch(getElementsByTagName(payload, 'definition'), ctx),
            'return_type': dispatch(getElementsByTagName(payload, 'type'), ctx),
            'argsstring': dispatch(getElementsByTagName(payload, 'argsstring'), ctx),
        }
    elif kind == 'enum':
        return {
            **base_data,
            # @todo: need qualified name?
            'items': [dispatch(item, ctx) for item in getElementsByTagName(payload, 'enumvalue')]
        }
    elif kind == 'typedef':
        return {
            **base_data,
            'base_type': dispatch(getElementsByTagName(payload, 'type'), ctx),
            'templateparameters': dispatch(getElementsByTagName(payload, 'templateparamlist'), ctx)
        }
    elif kind == 'friend':
        return {
            **base_data,
            'name': f"{dispatch(getElementsByTagName(payload, 'type'), ctx)} {base_data['name']}"
        }
    else:
        raise AssertionError(f"Encountered unexpected member kind: {kind}")


@dispatch.register
def dispatch_(expr: classes['xml_namespace'], ctx):
    payload = expr.payload
    data = {
        'type': 'namespace',
        'id': payload.attributes['id'].value,
        'name': dispatch(getElementsByTagName(payload, 'compoundname'), ctx),
        'innerclass': [dispatch(ic, ctx) for ic in getElementsByTagName(payload, 'innerclass')],
        'briefdescription': dispatch(getElementsByTagName(payload, 'briefdescription'), ctx),
        'detaileddescription': dispatch(getElementsByTagName(payload, 'detaileddescription'), ctx),
        'sectiondef': [dispatch(sec, ctx) for sec in getElementsByTagName(payload, 'sectiondef')]
    }
    return data


@dispatch.register
def dispatch_(expr: classes['xml_innerclass'], ctx):
    return {
        **dict(expr.payload.attributes.items()),
        'name': dispatch(expr.payload.childNodes[0], ctx)
    }


@dispatch.register
def dispatch_(expr: classes['xml_templateparamlist'], ctx):
    def dispatch_item(item):
        _type = dispatch(getElementsByTagName(item, 'type'), ctx)
        if declname := getElementsByTagName(item, 'declname'):
            defname = getElementsByTagName(item, 'defname')
            if dispatch(declname[0].childNodes[0], ctx) != dispatch(defname[0].childNodes[0], ctx):
                raise AssertionError(
                    f"Can't handle mismatched declaration and definition names: {declname}, {defname}.")
            _type += dispatch(declname[0].childNodes, ctx)
        return " ".join(_type)

    return [
        dispatch_item(item) for item in getElementsByTagName(expr.payload, 'param')
    ]


@dispatch.register
def dispatch_(expr: classes['xml_enumvalue'], ctx):
    return {
        'type': 'enumvalue',
        'name': dispatch(getElementsByTagName(expr.payload, 'name'), ctx),
        'briefdescription': dispatch(getElementsByTagName(expr.payload, 'briefdescription'), ctx),
        'detaileddescription': dispatch(getElementsByTagName(expr.payload, 'detaileddescription'), ctx)
    }


@dispatch.register
def dispatch_(expr: classes['xml_name'] | classes['xml_qualifiedname'] | classes['xml_definition'] | classes[
    'xml_parametername'], ctx):
    return dispatch(expr.payload.childNodes[0], ctx)


@dispatch.register
def dispatch_(expr: classes['xml_type'], ctx):
    if children := expr.payload.childNodes:
        return [dispatch(child, ctx) for child in children]
    else:
        return ["void"]


@dispatch.register
def dispatch_(expr: classes['xml_argsstring'] | classes['xml_initializer'], ctx):
    if expr.payload.childNodes:
        return dispatch(expr.payload.childNodes[0], ctx)
    else:
        return ""


@dispatch.register
def dispatch_(expr: classes['xml_location'], ctx):
    return {
        'type': 'location',
        **dict(expr.payload.attributes.items())
    }


@dispatch.register
def dispatch_(expr: classes['xml_para'], ctx):
    data = []
    for child in expr.payload.childNodes:
        child_data = dispatch(child, ctx)
        if isinstance(child_data, str):
            child_data = child_data.strip()
        if child_data:
            data.append(child_data)
    return data


@dispatch.register
def dispatch_(expr: classes['xml_bold'] | classes["xml_emphasis"], ctx):
    return {
        'type': 'markup',
        'kind': expr.payload.tagName,
        'body': dispatch(expr.payload.childNodes[0], ctx)
    }


@dispatch.register
def dispatch_(expr: classes['xml_ndash'], ctx):
    return "--"


@dispatch.register
def dispatch_(expr: classes['xml_ulink'], ctx):
    return {
        'type': 'hyperlink',
        'url': expr.payload.attributes["url"].value,
        'body': dispatch(expr.payload.childNodes[0], ctx)
    }


@dispatch.register
def dispatch_(expr: classes['xml_itemizedlist'] | classes["xml_orderedlist"], ctx):
    return {
        'type': expr.payload.tagName,
        'items': [dispatch(getElementsByTagName(item, 'para'), ctx) for item in
                  getElementsByTagName(expr.payload, "listitem")]
    }


@dispatch.register
def dispatch_(expr: classes['xml_ref'], ctx):
    return {
        'type': 'reference',
        'name': dispatch(expr.payload.childNodes[0], ctx),
        'refid': expr.payload.attributes['refid'].value
    }


@dispatch.register
def dispatch_(expr: classes['xml_simplesect'], ctx):
    return {
        'type': 'simplesect',
        'kind': expr.payload.attributes['kind'].value,
        'body': dispatch(expr.payload.childNodes[0], ctx)
    }


@dispatch.register
def dispatch_(expr: classes['xml_parameterlist'], ctx):
    def dispatch_item(item):
        return {
            'type': 'parameter',
            'name': dispatch(getElementsByTagName(getElementsByTagName(item, 'parameternamelist')[0],
                                                  'parametername'), ctx),
            'description': dispatch(getElementsByTagName(getElementsByTagName(item, 'parameterdescription')[0],
                                                         'para'), ctx),
        }

    return [
        dispatch_item(item) for item in getElementsByTagName(expr.payload, 'parameteritem')
    ]


@dispatch.register
def dispatch_(expr: classes['xml_computeroutput'], ctx):
    return {
        'type': 'inline_code',
        'code': dispatch(expr.payload.childNodes[0], ctx)
    }


@dispatch.register
def dispatch_(expr: classes['xml_sp'], ctx):
    return " "


@dispatch.register
def dispatch_(expr: classes['xml_programlisting'], ctx):
    first_cl = getElementsByTagName(expr.payload, 'codeline')[0]
    if first_cl is None:
        style = 'text'
        start_idx = 0
    else:
        style = dispatch(first_cl, ctx).strip(" {}")
        start_idx = 1

    return {'type': 'block_code',
            'style': style,
            'code': "\n".join(dispatch(cl, ctx) for cl in getElementsByTagName(expr.payload, 'codeline')[start_idx:])}


@dispatch.register
def dispatch_(expr: classes['xml_highlight'], ctx):
    # @todo: maybe handle highlighting?
    def sanitize(fragment):
        # let sphinx handle references
        match fragment:
            case {"name": name}:
                return name
            case str(body):
                return body
            case _:
                raise AssertionError(f"Can't reduce fragment to str: {fragment}")

    return "".join(
        sanitize(dispatch(child, ctx)) for child in expr.payload.childNodes
    )


@dispatch.register
def dispatch_(expr: classes['xml_codeline'], ctx):
    return "".join(
        dispatch(child, ctx) for child in expr.payload.childNodes
    )


@dispatch.register
def dispatch_(expr: classes['xml_formula'], ctx):
    code = expr.payload.childNodes[0].data
    if code.startswith("\\[") and code.endswith("\\]"):
        return {
            'type': 'block_math',
            'code': code.strip("\[] ")
        }
    elif code.startswith("$") and code.endswith("$"):
        return {
            'type': 'inline_math',
            'code': code.strip("$ ")
        }
    else:
        raise AssertionError(f"Unrecognized math formula: {code}")


@dispatch.register
def dispatch_text(expr: MD.Text, ctx):
    stripped_text = expr.data.strip()
    return stripped_text


@dispatch.register
def dispatch_document(expr: MD.Document, ctx):
    return dispatch(getElementsByTagName(getElementsByTagName(expr, "doxygen")[0], "compounddef"), ctx)


def dispatch_index(expr: MD.Document, ctx):
    data = defaultdict(list)
    index = getElementsByTagName(expr, 'doxygenindex')[0]

    def simplified_kind(kind):
        if kind in ["class", "struct", "union"]:
            return "class"
        else:
            return kind

    for compoud in getElementsByTagName(index, 'compound'):
        file = f"{ctx.directory}/{compoud.attributes['refid'].value}.xml"
        kind = compoud.attributes['kind'].value
        if kind != 'file':
            new_data = dispatch(MD.parse(file), ctx)
            if new_data:
                data[simplified_kind(kind)].append(new_data)
    return data


def parse_context(directory: str, dom: MD.Document):
    index = dom.getElementsByTagName('doxygenindex')[0]
    empty_ctx = Context(directory="", classes={}, specializations=defaultdict(set), specializationof=defaultdict(str))
    all_classes = dict()
    for compound in getElementsByTagName(index, 'compound'):
        kind = compound.attributes['kind'].value
        if kind in ['class', 'struct']:
            name = dispatch(getElementsByTagName(compound, 'name'), empty_ctx)
            all_classes[name] = compound.attributes['refid'].value

    def remove_specialization(name):
        return name.partition('<')[0]

    specializations = defaultdict(set)
    specializationof = defaultdict(dict)
    for cl, id in all_classes.items():
        base_name = remove_specialization(cl)
        if base_name != cl:
            specializations[base_name].add(frozendict(name=cl, id=id))
            specializationof[cl] = dict(name=base_name, id=all_classes[base_name])

    return Context(directory=directory, classes=all_classes,
                   specializations=specializations,
                   specializationof=specializationof)


@dataclass
class Context(object):
    directory: str
    classes: Dict[str, str]
    specializations: defaultdict[Set[frozendict]]
    specializationof: defaultdict[Dict]


xml_directory = simple_directory
index = Path(xml_directory) / "index.xml"
dom = MD.parse(str(index.resolve()))

ctx = parse_context(xml_directory, dom)

parsed = dispatch_index(dom, ctx)

print(json.dumps(parsed, indent=2))
