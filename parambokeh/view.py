import param

def render_function(obj, view):
    """
    The default Renderer function which handles HoloViews objects.
    """
    try:
        import holoviews as hv
    except:
        hv = None

    if hv and isinstance(obj, hv.Dimensioned):
        renderer = hv.renderer('bokeh')
        if not view._notebook:
            renderer = renderer.instance(mode='server')
        plot = renderer.get_plot(obj, doc=view._document)
        if view._notebook:
            from holoviews.plotting.comms import JupyterComm
            comm = JupyterComm(plot, view._comm_target)
            plot.comm = comm
        plot.document = view._document
        return plot.state
    return obj


class _View(param.Parameter):
    """
    View parameters hold displayable output, they may have a callback,
    which is called when a new value is set on the parameter.
    Additionally they allow supplying a renderer function which renders
    the display output. The renderer function should return the
    appropriate output for the View parameter (e.g. HTML or PNG data),
    and may optionally supply the desired size of the viewport.
    """

    __slots__ = ['callbacks', 'renderer', '_comm_target', '_document', '_notebook']

    def __init__(self, default=None, callback=None, renderer=None, **kwargs):
        self.callbacks = {}
        self.renderer = (render_function if renderer is None else renderer)
        super(_View, self).__init__(default, **kwargs)
        self._comm_target = None
        self._document = None
        self._notebook = False

    def __set__(self, obj, val):
        super(_View, self).__set__(obj, val)
        obj_id = id(obj)
        if obj_id in self.callbacks:
            self.callbacks[obj_id](self.renderer(val, self))


class Plot(_View):
    """
    Plot is a View parameter that allows displaying bokeh plots as output.
    """


class HTML(_View):
    """
    HTML is a View parameter that allows displaying arbitrary HTML.
    """
