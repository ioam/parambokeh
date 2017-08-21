import param
from param.parameterized import classlist

from bokeh.layouts import widgetbox, row, column
from bokeh.models.widgets import (
    Button, TextInput, Div, Slider, Bool, CheckboxGroup, Toggle,
    DatePicker, MultiSelect, Select, PreText, RangeSlider
)

from .util import as_unicode
from .view import Plot, HTML


def TextWidget(*args, **kw):
    """Forces a parameter value to be text"""
    kw['value'] = str(kw['value'])
    kw.pop('options', None)
    return TextInput(*args,**kw)

def StaticText(*args, **kw):
    kw['text'] = '<b>{title}</b>: {value}'.format(title=kw.pop('title'),
                                                  value=as_unicode(kw.pop('value')))
    return Div(*args, **kw)

def ToggleWidget(*args, **kw):
    kw['active'] = kw.pop('value')
    kw['label'] = kw.pop('title')
    return Toggle(*args, **kw)

def ButtonWidget(*args, **kw):
    kw['label'] = kw.pop('title')
    cb = kw.pop('value')
    button = Button(*args, **kw)
    button.on_click(cb)
    return button

def IntSlider(*args, **kw):
    kw['step'] = 1
    return Slider(*args, **kw)

def DateWidget(*args, **kw):
    kw['min_date'] = kw.pop('start')
    kw['max_date'] = kw.pop('end')
    return DatePicker(*args,**kw)

def RangeWidget(*args, **kw):
    kw['start'], kw['end'] = kw.pop('value')
    if isinstance(kw['start'], int) and isinstance(kw['end'], int):
        kw['step'] = 1
    return RangeSlider(*args, **kw)

def PlotWidget(*args, **kw):
    return column(name=kw['title'])

def HTMLWidget(*args, **kw):
    return Div(name=kw['title'])


ptype2wtype = {
    param.Parameter:     TextWidget,
    param.Dict:          TextWidget,
    param.Selector:      Select,
    param.Boolean:       ToggleWidget,
    param.Number:        Slider,
    param.Integer:       IntSlider,
    param.Range:         RangeWidget,
    param.ListSelector:  MultiSelect,
    param.Action:        ButtonWidget,
    param.Date:          DateWidget,
    Plot:                PlotWidget,
    HTML:                HTMLWidget

}

def wtype(pobj):
    if pobj.constant: # Ensure constant parameters cannot be edited
        return StaticText
    for t in classlist(type(pobj))[::-1]:
        if t in ptype2wtype:
            return ptype2wtype[t]


# Define parameters which should be evaluated using ast.literal_eval
literal_params = (param.Dict, param.List, param.Tuple)
