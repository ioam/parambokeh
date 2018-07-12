import sys
import inspect

import bokeh
from bokeh.models import Model, CustomJS, LayoutDOM

try:
    from IPython.display import publish_display_data
    import bokeh.embed.notebook
    from bokeh.util.string import encode_utf8
    from pyviz_comms import JupyterCommManager, JS_CALLBACK, bokeh_msg_handler, PYVIZ_PROXY
    IPYTHON_AVAILABLE = True
except:
    IPYTHON_AVAILABLE = False

if sys.version_info.major == 3:
    unicode = str
    basestring = str


embed_js = """
// Ugly hack - see HoloViews #2574 for more information
if (!(document.getElementById('{plot_id}')) && !(document.getElementById('_anim_img{widget_id}'))) {{
  console.log("Creating DOM nodes dynamically for assumed nbconvert export. To generate clean HTML output set HV_DOC_HTML as an environment variable.")
  var htmlObject = document.createElement('div');
  htmlObject.innerHTML = `{html}`;
  var scriptTags = document.getElementsByTagName('script');
  var parentTag = scriptTags[scriptTags.length-1].parentNode;
  parentTag.append(htmlObject)
}}
"""


def as_unicode(obj):
    """
    Safely casts any object to unicode including regular string
    (i.e. bytes) types in python 2.
    """
    if sys.version_info.major < 3 and isinstance(obj, str):
        obj = obj.decode('utf-8')
    return unicode(obj)


def named_objs(objlist):
    """
    Given a list of objects, returns a dictionary mapping from
    string name for the object to the object itself.
    """
    objs = []
    for k, obj in objlist:
        if hasattr(k, '__name__'):
            k = k.__name__
        else:
            k = as_unicode(k)
        objs.append((k, obj))
    return objs


def get_method_owner(meth):
    """
    Returns the instance owning the supplied instancemethod or
    the class owning the supplied classmethod.
    """
    if inspect.ismethod(meth):
        if sys.version_info < (3,0):
            return meth.im_class if meth.im_self is None else meth.im_self
        else:
            return meth.__self__


def patch_hv_plot(plot, plot_id, comm):
    """
    Update the plot id and comm on a HoloViews plot to allow embedding
    it in a bokeh layout.
    """
    if not hasattr(plot, '_update_callbacks'):
        return

    for subplot in plot.traverse(lambda x: x):
        subplot.comm = comm
        for cb in getattr(subplot, 'callbacks', []):
            for c in cb.callbacks:
                c.code = c.code.replace(plot.id, plot_id)


def patch_bk_plot(plot, plot_id):
    """
    Patches bokeh CustomJS models with top-level plot_id
    """
    for js in plot.select({'type': CustomJS}):
        js.code = js.code.replace(plot.ref['id'], plot_id)


def patch_widgets(plot, doc, plot_id, comm):
    """
    Patches parambokeh Widgets instances with top-level document, comm and plot id
    """
    plot.comm = comm
    plot.document = doc
    patch_bk_plot(plot.container, plot_id)


def process_plot(plot, doc, plot_id, comm):
    """
    Converts all acceptable plot and widget objects into displaybel
    bokeh models. Patches any HoloViews plots or parambokeh Widgets
    with the top-level comms and plot id.
    """
    from . import Widgets
    if isinstance(plot, LayoutDOM):
        if plot_id:
            patch_bk_plot(plot, plot_id)
        return plot
    elif isinstance(plot, Widgets):
        patch_widgets(plot, doc, plot_id, comm)
        return plot.container
    elif hasattr(plot, 'kdims') and hasattr(plot, 'vdims'):
        from holoviews import renderer
        renderer = renderer('bokeh').instance(mode='server' if comm is None else 'default')
        plot = renderer.get_plot(plot, doc=doc)

    if not hasattr(plot, '_update_callbacks'):
        raise ValueError('Can only render bokeh models or HoloViews objects.')

    patch_hv_plot(plot, plot_id, comm)
    return plot.state


def add_to_doc(obj, doc, hold=False):
    """
    Adds a model to the supplied Document removing it from any existing Documents.
    """
    # Handle previously displayed models
    for model in obj.select({'type': Model}):
        prev_doc = model.document
        model._document = None
        if prev_doc:
            prev_doc.remove_root(model)

    # Add new root
    doc.add_root(obj)
    if doc._hold is None and hold:
        doc.hold()


def render(obj, doc, comm):
    """
    Displays bokeh output inside a notebook using the PyViz display
    and comms machinery.
    """
    if not isinstance(obj, LayoutDOM): 
        raise ValueError('Can only render bokeh LayoutDOM models')

    add_to_doc(obj, doc, True)

    target = obj.ref['id']
    load_mime = 'application/vnd.holoviews_load.v0+json'
    exec_mime = 'application/vnd.holoviews_exec.v0+json'

    # Publish plot HTML
    bokeh_script, bokeh_div, _ = bokeh.embed.notebook.notebook_content(obj, comm.id)
    html = encode_utf8(bokeh_div)

    # Publish comm manager
    JS = '\n'.join([PYVIZ_PROXY, JupyterCommManager.js_manager])
    publish_display_data(data={load_mime: JS, 'application/javascript': JS})

    # Publish bokeh plot JS
    msg_handler = bokeh_msg_handler.format(plot_id=target)
    comm_js = comm.js_template.format(plot_id=target, comm_id=comm.id, msg_handler=msg_handler)
    bokeh_js = '\n'.join([comm_js, bokeh_script])
    bokeh_js = embed_js.format(widget_id=target, plot_id=target, html=html) + bokeh_js

    data = {exec_mime: '', 'text/html': html, 'application/javascript': bokeh_js}
    metadata = {exec_mime: {'id': target}}
    return data, metadata

