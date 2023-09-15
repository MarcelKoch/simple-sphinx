import xml.dom.minicompat
from functools import singledispatch
import xml.dom.minidom as MD
import xml.dom.minicompat as MDC
from typing import Tuple, Union

file = "/home/marcel/projects/simple-sphinx/doc/source/doxygen/xml/classtest_1_1E.xml"


def constructor(self, payload):
    self.payload = payload


def create_class(name):
    return name, type(name, (object,), {"name": name,
                                        "__init__": constructor})


classes = dict(create_class(name) for name in [
    "compounddef",
    "compoundname",
    "basecompoundref",
    "derivedcompoundref",
    "briefdescription",
    "detaileddescription",
    "sectiondef",
    "para",
    "ref",
    "computeroutput",
    "sp",
    "programlisting",
    "highlight",
    "codeline",
    # compounddef kinds
    "xclass"
])


@singledispatch
def dispatch(expr, ctx):
    raise AssertionError(f"Unhandled type {type(expr)}")


@dispatch.register
def dispatch_nodelist(expr: MDC.NodeList, ctx):
    return [dispatch(expr.item(i), ctx) for i in range(len(expr))]


@dispatch.register
def dispatch_element(expr: MD.Element, ctx):
    return dispatch(classes[expr.tagName](expr), ctx)


def getElementsByTagName(node, tag):
    # This function is not recursive compared to Element.getElementsByTagName
    elements = []
    for child in node.childNodes:
        if isinstance(child, MD.Element) and child.tagName == tag:
            elements.append(child)
    return elements


@dispatch.register
def dispatch_class(expr: classes["xclass"], ctx):
    # Find the class id ( used for files/html/etc )
    payload = expr.payload
    data = {
        'type': 'class',
        'id': payload.attributes['id'].value,
        'compoundname': dispatch(getElementsByTagName(payload, 'compoundname')[0], ctx),
        'basecompoundref': [dispatch(d, ctx) for d in getElementsByTagName(payload, 'basecompoundref')],
        'derivedcompoundref': [dispatch(d, ctx) for d in getElementsByTagName(payload, 'derivedcompoundref')],
        'briefdescription': dispatch(getElementsByTagName(payload, 'briefdescription')[0], ctx),
        'detaileddescription': dispatch(getElementsByTagName(payload, 'detaileddescription')[0], ctx),
        'sectiondef': [dispatch(sec, ctx) for sec in getElementsByTagName(payload, 'sectiondef')]
    }
    return data


@dispatch.register
def dispatch_compounddef(expr: classes['compounddef'], ctx):
    kind = expr.payload.attributes['kind'].value
    return dispatch(classes[f"x{kind}"](expr.payload), ctx)


@dispatch.register
def dispatch_compounddef(expr: classes['compoundname'], ctx):
    return dispatch(expr.payload.childNodes[0], ctx)


@dispatch.register
def dispatch_(expr: classes['basecompoundref'] | classes['derivedcompoundref'], ctx):
    return dispatch(expr.payload.childNodes[0], ctx)


@dispatch.register
def dispatch_(expr: classes['briefdescription'] | classes['detaileddescription'], ctx):
    para = getElementsByTagName(expr.payload, 'para')[0]
    if para:
        return dispatch(para, ctx)
    else:
        return [""]


@dispatch.register
def dispatch_(expr: classes['sectiondef'], ctx):
    return [dispatch(member, ctx) for member in getElementsByTagName(expr.payload, "memberdef")]


@dispatch.register
def dispatch_(expr: classes['memberdef'], ctx):
    payload = expr.payload
    data = {
        'type': 'member',
        **payload.attributes.items(),
        'return_type': dispatch(getElementsByTagName(payload, "type"), ctx),

    }
    return dispatch(getElementsByTagName(expr.payload, "memberdef"), ctx)


@dispatch.register
def dispatch_(expr: classes['para'], ctx):
    data = []
    for child in expr.payload.childNodes:
        child_data = dispatch(child, ctx)
        if isinstance(child_data, str):
            child_data = child_data.strip()
        if child_data:
            data.append(child_data)
    return data


@dispatch.register
def dispatch_(expr: classes['ref'], ctx):
    return {
        'type': 'reference',
        'name': dispatch(expr.payload.childNodes[0], ctx),
        'refid': expr.payload.attributes['refid'].value
    }


@dispatch.register
def dispatch_(expr: classes['computeroutput'], ctx):
    return {
        'type': 'inline_code',
        'code': dispatch(expr.payload.childNodes[0], ctx)
    }


@dispatch.register
def dispatch_(expr: classes['sp'], ctx):
    return " "


@dispatch.register
def dispatch_(expr: classes['programlisting'], ctx):
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
def dispatch_(expr: classes['highlight'], ctx):
    # @todo: maybe handle highlighting?
    return "".join(
        dispatch(child, ctx) for child in expr.payload.childNodes
    )


@dispatch.register
def dispatch_(expr: classes['codeline'], ctx):
    return "".join(
        dispatch(child, ctx) for child in expr.payload.childNodes
    )


@dispatch.register
def dispatch_text(expr: MD.Text, ctx):
    stripped_text = expr.data.strip()
    return stripped_text or None


@dispatch.register
def dispatch_document(expr: MD.Document, ctx):
    return dispatch(getElementsByTagName(getElementsByTagName(expr, "doxygen")[0], "compounddef")[0], ctx)


dom = MD.parse(file)

print(dispatch(dom, {}))

pass
