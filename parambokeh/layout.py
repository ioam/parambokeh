import param

from bokeh.document import Document
from bokeh.io import curdoc
from bokeh.layouts import Column as BkColumn, Row as BkRow 

from .util import render, process_plot, add_to_doc

class Viewable(param.Parameterized):
    """
    A Viewable is an abstract baseclass for objects which wrap bokeh
    models and display them using the PyViz display and comms machinery.
    """

    __abstract = True

    def _get_model(self, doc, comm=None, plot_id=None):
        """
        Should return the bokeh model to be rendered. 
        """

    def _repr_mimebundle_(self, include=None, exclude=None):
        from pyviz_comms import JupyterCommManager
        doc = Document()
        comm = JupyterCommManager.get_server_comm()
        return render(self._get_model(doc, comm), doc, comm)

    def server_doc(self, doc=None):
        doc = doc or curdoc()
        model = self._get_model(doc)
        add_to_doc(model, doc)
        return doc


class Plot(Viewable):
    """
    A wrapper for bokeh plots and objects that can be converted to
    bokeh plots.
    """

    def __init__(self, obj, **params):
        self.object = obj
        super(Plot, self).__init__(**params)
    
    def _get_model(self, doc, comm=None, plot_id=None):
        """
        Should return the bokeh model to be rendered. 
        """
        return process_plot(self.object, doc, plot_id, comm)


class WidgetBox(Plot):
    """
    A wrapper for bokeh WidgetBox and parambokeh.Widgets making them
    displayable in the notebook.
    """


class Layout(Viewable):

    children = param.List(default=[])

    _bokeh_model = None

    __abstract = True

    def __init__(self, *children, **params):
        super(Layout, self).__init__(children=list(children), **params)
    
    def _get_model(self, doc, comm=None, plot_id=None):
        """
        Should return the bokeh model to be rendered. 
        """
        model = self._bokeh_model()
        plot_id = model.ref['id'] if plot_id is None else plot_id
        children = []
        for child in self.children:
            if not isinstance(child, Viewable):
                child = Plot(child)
            children.append(child._get_model(doc, comm, plot_id))
        model.children = children
        return model


class Row(Layout):

    _bokeh_model = BkRow


class Column(Layout):

    _bokeh_model = BkColumn
