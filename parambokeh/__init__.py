from __future__ import absolute_import

import ast
import uuid
import itertools
import functools

import param

from bokeh.document import Document
from bokeh.io import push_notebook, curdoc
from bokeh.layouts import row, column, widgetbox
from bokeh.models.widgets import Div, Button, CheckboxGroup, TextInput
from bokeh.models import CustomJS

try:
    from .comms import JupyterCommJS, JS_CALLBACK, notebook_show
    IPYTHON_AVAILABLE = True
except:
    IPYTHON_AVAILABLE = False
from .widgets import wtype, literal_params
from .util import named_objs, get_method_owner
from .view import _View

try:
    __version__ = param.Version(release=(0,2,1), fpath=__file__,
                                commit="$Format:%h$", reponame='parambokeh')
except:
    __version__ = '0.2.1-unknown'


class Widgets(param.ParameterizedFunction):

    callback = param.Callable(default=None, doc="""
        Custom callable to execute on button press
        (if `button`) else whenever a widget is changed,
        Should accept a Parameterized object argument.""")

    view_position = param.ObjectSelector(default='below',
                                         objects=['below', 'right', 'left', 'above'],
                                         doc="""
        Layout position of any View parameter widgets.""")

    next_n = param.Parameter(default=0, doc="""
        When executing cells, integer number to execute (or 'all').
        A value of zero means not to control cell execution.""")

    on_init = param.Boolean(default=False, doc="""
        Whether to do the action normally taken (executing cells
        and/or calling a callable) when first instantiating this
        object.""")

    button = param.Boolean(default=False, doc="""
        Whether to show a button to control cell execution.
        If false, will execute `next` cells on any widget
        value change.""")

    button_text = param.String(default="Run", doc="""
        Text to show on the 'next_n'/run button.""")

    show_labels = param.Boolean(default=True)

    display_threshold = param.Number(default=0,precedence=-10,doc="""
        Parameters with precedence below this value are not displayed.""")

    default_precedence = param.Number(default=1e-8,precedence=-10,doc="""
        Precedence value to use for parameters with no declared precedence.
        By default, zero predecence is available for forcing some parameters
        to the top of the list, and other values above the default_precedence
        values can be used to sort or group parameters arbitrarily.""")

    initializer = param.Callable(default=None, doc="""
        User-supplied function that will be called on initialization,
        usually to update the default Parameter values of the
        underlying parameterized object.""")

    layout = param.ObjectSelector(default='column',
                                  objects=['row','column'],doc="""
        Whether to lay out the buttons as a row or a column.""")

    continuous_update = param.Boolean(default=False, doc="""
        If true, will continuously update the next_n and/or callback,
        if any, as a slider widget is dragged.""")

    mode = param.ObjectSelector(default='notebook', objects=['server', 'raw', 'notebook'], doc="""
        Whether to use the widgets in server or notebook mode. In raw mode
        the widgets container will simply be returned.""")

    push = param.Boolean(default=True, doc="""
        Whether to push data in notebook mode. Allows disabling pushing
        of data if the callback handles this itself.""")

    width = param.Integer(default=300, bounds=(0, None), doc="""
        Width of widgetbox the parameter widgets are displayed in.""")

    # Timeout if a notebook comm message is swallowed
    timeout = 20000

    # Timeout before the first event is processed
    debounce = 20

    def __call__(self, parameterized, doc=None, plots=[], **params):
        self.p = param.ParamOverrides(self, params)
        if self.p.initializer:
            self.p.initializer(parameterized)

        self._widgets = {}
        self.parameterized = parameterized
        self.document = None
        self.comm_target = None
        if self.p.mode == 'notebook':
            if not IPYTHON_AVAILABLE:
                raise ImportError('IPython is not available, cannot use '
                                  'Widgets in notebook mode.')
            self.comm = JupyterCommJS(on_msg=self.on_msg)
            # HACK: Detects HoloViews plots and lets them handle the comms
            hv_plots = [plot for plot in plots if hasattr(plot, 'comm')]
            if hv_plots:
                self.comm_target = [p.comm.id for p in hv_plots][0]
                self.document = [p.document for p in hv_plots][0]
                plots = [p.state for p in plots]
                self.p.push = False
            else:
                self.comm_target = uuid.uuid4().hex
                self.document = doc or Document()
        else:
            self.document = doc or curdoc()

        self._queue = []
        self._active = False

        self._widget_options = {}
        self.shown = False

        widgets, views = self.widgets()
        plots = views + plots
        container = widgetbox(widgets, width=self.p.width)
        if plots:
            view_box = column(plots)
            layout = self.p.view_position
            if layout in ['below', 'right']:
                children = [container, view_box]
            else:
                children = [view_box, container]
            container_type = column if layout in ['below', 'above'] else row
            container = container_type(children=children)
        for view in views:
            p_obj = self.parameterized.params(view.name)
            value = getattr(self.parameterized, view.name)
            if value is not None:
                rendered = p_obj.renderer(value, p_obj)
                self._update_trait(view.name, rendered)

        # Keeps track of changes between button presses
        self._changed = {}

        if self.p.on_init:
            self.execute()

        if self.p.mode == 'raw':
            return container

        self.document.add_root(container)
        if self.p.mode == 'notebook':
            self.notebook_handle = notebook_show(container, self.document,
                                                 self.comm_target)
            if self.document._hold is None:
                self.document.hold()
            self.shown = True
            return
        return self.document


    def on_msg(self, msg):
        p_name = msg['p_name']
        p_obj = self.parameterized.params(p_name)
        if isinstance(p_obj, param.Action):
            getattr(self.parameterized, p_name)(self.parameterized)
            return
        w = self._widgets[p_name]
        self._queue.append((w, p_obj, p_name, None, None, msg['value']))
        self.change_event()


    def on_change(self, w, p_obj, p_name, attr, old, new):
        self._queue.append((w, p_obj, p_name, attr, old, new))
        if not self._active:
            self.document.add_timeout_callback(self.change_event, 50)
            self._active = True


    def change_event(self):
        if not self._queue:
            self._active = False
            return
        w, p_obj, p_name, attr, old, new_values = self._queue[-1]
        self._queue = []

        error = False
        # Apply literal evaluation to values
        if (isinstance(w, TextInput) and isinstance(p_obj, literal_params)):
            try:
                new_values = ast.literal_eval(new_values)
            except:
                error = 'eval'

        if p_name in self._widget_options:
            mapping = self._widget_options[p_name]
            if isinstance(new_values, list):
                new_values = [mapping[el] for el in new_values]
            else:
                new_values = mapping.get(new_values, new_values)

        if isinstance(p_obj, param.Range):
            new_values = tuple(new_values)

        if isinstance(w, CheckboxGroup):
            new_values = True if (len(new_values)>0 and new_values[0]==0) else False

        # If no error during evaluation try to set parameter
        if not error:
            try:
                setattr(self.parameterized, p_name, new_values)
            except ValueError:
                error = 'validation'

        # Style widget to denote error state
        # apply_error_style(w, error)

        if not error and not self.p.button:
            self.execute({p_name: new_values})
        else:
            self._changed[p_name] = new_values

        # document.hold() must have been done already? because this seems to work
        if self.p.mode == 'notebook' and self.p.push and self.document._held_events:
            push_notebook(handle=self.notebook_handle, document=self.document)
        self._active = False


    def _update_trait(self, p_name, p_value, widget=None):
        widget = self._widgets[p_name] if widget is None else widget
        if isinstance(p_value, tuple):
            p_value, size = p_value
        if isinstance(widget, Div):
            widget.text = p_value
        elif self.p.mode == 'notebook' and self.shown:
            return
        else:
            if widget.children:
                widget.children.remove(widget.children[0])
            widget.children.append(p_value)


    def _make_widget(self, p_name):
        p_obj = self.parameterized.params(p_name)

        if isinstance(p_obj, _View):
            p_obj._comm_target = self.comm_target
            p_obj._document = self.document
            p_obj._notebook = self.p.mode == 'notebook'

        widget_class = wtype(p_obj)
        value = getattr(self.parameterized, p_name)

        kw = dict(value=value)

        kw['title'] = p_name

        if hasattr(p_obj, 'get_range') and not isinstance(kw['value'], dict):
            options = named_objs(p_obj.get_range().items())
            value = kw['value']
            lookup = {v: k for k, v in options}
            if isinstance(value, list):
                kw['value'] = [lookup[v] for v in value]
            else:
                kw['value'] = lookup[value]
            opt_lookup = {k: v for k, v in options}
            self._widget_options[p_name] = opt_lookup
            options = [(k, k) for k, v in options]
            kw['options'] = options

        if hasattr(p_obj, 'get_soft_bounds'):
            kw['start'], kw['end'] = p_obj.get_soft_bounds()

        w = widget_class(**kw)

        if hasattr(p_obj, 'callbacks') and value is not None:
            rendered = p_obj.renderer(value, p_obj)
            self._update_trait(p_name, rendered, w)

        if hasattr(p_obj, 'callbacks'):
            p_obj.callbacks[id(self.parameterized)] = functools.partial(self._update_trait, p_name)
        elif isinstance(w, CheckboxGroup):
            if self.p.mode in ['server', 'raw']:
                w.on_change('active', functools.partial(self.on_change, w, p_obj, p_name))
            else:
                js_callback = self._get_customjs('active', p_name)
                w.js_on_change('active', js_callback)
        elif isinstance(w, Button):
            if self.p.mode in ['server', 'raw']:
                w.on_click(functools.partial(value,self.parameterized))
            else:
                w.js_on_click(self._get_customjs('active', p_name))
        elif not p_obj.constant:
            if self.p.mode in ['server', 'raw']:
                cb = functools.partial(self.on_change, w, p_obj, p_name)
                if 'value' in w.properties():
                    w.on_change('value', cb)
                elif 'range' in w.properties():
                    w.on_change('range', cb)
            else:
                if 'value' in w.properties():
                    change = 'value'
                elif 'range' in w.properties():
                    change = 'range'
                customjs = self._get_customjs(change, p_name)
                w.js_on_change(change, customjs)

        return w


    def _get_customjs(self, change, p_name):
        """
        Returns a CustomJS callback that can be attached to send the
        widget state across the notebook comms.
        """
        data_template = "data = {{p_name: '{p_name}', value: cb_obj['{change}']}};"
        fetch_data = data_template.format(change=change, p_name=p_name)
        self_callback = JS_CALLBACK.format(comm_id=self.comm.id,
                                           timeout=self.timeout,
                                           debounce=self.debounce)
        js_callback = CustomJS(code=fetch_data+self_callback)
        return js_callback


    def widget(self, param_name):
        """Get widget for param_name"""
        if param_name not in self._widgets:
            self._widgets[param_name] = self._make_widget(param_name)
        return self._widgets[param_name]


    def execute(self, changed={}):
        if self.p.callback is not None:
            if get_method_owner(self.p.callback) is self.parameterized:
                self.p.callback(**changed)
            else:
                self.p.callback(self.parameterized, **changed)

    def widgets(self):
        """Return name,widget boxes for all parameters (i.e., a property sheet)"""

        params = self.parameterized.params().items()
        key_fn = lambda x: x[1].precedence if x[1].precedence is not None else self.p.default_precedence
        sorted_precedence = sorted(params, key=key_fn)
        outputs = [k for k, p in sorted_precedence if isinstance(p, _View)]
        filtered = [(k,p) for (k,p) in sorted_precedence
                    if ((p.precedence is None) or (p.precedence >= self.p.display_threshold))
                    and k not in outputs]
        groups = itertools.groupby(filtered, key=key_fn)
        sorted_groups = [sorted(grp) for (k,grp) in groups]
        ordered_params = [el[0] for group in sorted_groups for el in group]

        # Format name specially
        ordered_params.pop(ordered_params.index('name'))
        widgets = [Div(text='<b>{0}</b>'.format(self.parameterized.name))]

        def format_name(pname):
            p = self.parameterized.params(pname)
            # omit name for buttons, which already show the name on the button
            name = "" if issubclass(type(p),param.Action) else pname
            return Div(text=name)

        if self.p.show_labels:
            widgets += [self.widget(pname) for pname in ordered_params]
        else:
            widgets += [self.widget(pname) for pname in ordered_params]

        if self.p.button and not (self.p.callback is None and self.p.next_n==0):
            display_button = Button(label=self.p.button_text)
            def click_cb():
                # Execute and clear changes since last button press
                try:
                    self.execute(self._changed)
                except Exception as e:
                    self._changed.clear()
                    raise e
                self._changed.clear()
            display_button.on_click(click_cb)
            widgets.append(display_button)

        outputs = [self.widget(pname) for pname in outputs]
        return widgets, outputs
