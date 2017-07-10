import param

def render_function(obj, document, target):
    """
    The default Renderer function which handles HoloViews objects.
    """
    try:
        import holoviews as hv
    except:
        hv = None

    if hv and isinstance(obj, hv.Dimensioned):
        from holoviews.plotting.comms import JupyterComm
        renderer = hv.renderer('bokeh')
        plot = renderer.get_plot(obj)
        comm = JupyterComm(plot, target)
        plot.document = document
        plot.comm = comm
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

    __slots__ = ['callbacks', 'renderer', '_comm_target', '_document']

    def __init__(self, default=None, callback=None, renderer=None, **kwargs):
        self.callbacks = {}
        self.renderer = (render_function if renderer is None else renderer)
        super(_View, self).__init__(default, **kwargs)
        self._comm_target = None
        self._document = None

    def __set__(self, obj, val):
        super(_View, self).__set__(obj, val)
        obj_id = id(obj)
        if obj_id in self.callbacks:
            self.callbacks[obj_id](self.renderer(val, self._document, self._comm_target))


class Plot(_View):
    """
    Plot is a View parameter that allows displaying bokeh plots as output.
    """


class HTML(_View):
    """
    HTML is a View parameter that allows displaying arbitrary HTML.
    """
