import json
import uuid
import sys
import traceback
try:
    from StringIO import StringIO
except:
    from io import StringIO

import bokeh.embed.notebook
import bokeh.io.notebook
from bokeh.util.string import encode_utf8

from IPython.display import publish_display_data




JS_CALLBACK = """
    function unique_events(events) {{
        // Processes the event queue ignoring duplicate events
        // of the same type
        var unique = [];
        var unique_events = [];
        for (var i=0; i<events.length; i++) {{
            [event, data] = events[i];
            if (!unique_events.includes(event)) {{
                unique.unshift(data);
                unique_events.push(event);
            }}
        }}
        return unique;
    }}

    function process_events(comm_state) {{
        // Iterates over event queue and sends events via Comm
        var events = unique_events(comm_state.event_buffer);
        for (var i=0; i<events.length; i++) {{
            var data = events[i];
            var comm = Bokeh.comms[data["comm_id"]];
            comm.send(data);
        }}
        comm_state.event_buffer = [];
    }}

    function on_msg(msg){{
      // Receives acknowledgement from Python, processing event
      // and unblocking Comm if event queue empty
      msg = JSON.parse(msg.content.data);
      var comm_id = msg["comm_id"]
      var comm_state = Bokeh.comm_state[comm_id];
      if (comm_state.event_buffer.length) {{
        process_events(comm_state);
        comm_state.blocked = true;
        comm_state.time = Date.now()+{debounce};
      }} else {{
        comm_state.blocked = false;
      }}
      comm_state.event_buffer = [];
      if ((msg.msg_type == "Ready") && msg.content) {{
        console.log("Python callback returned following output:", msg.content);
      }} else if (msg.msg_type == "Error") {{
        console.log("Python failed with the following traceback:", msg['traceback'])
      }}
    }}

    // Initialize Comm
    if (Bokeh.comms == null) {{
      Bokeh.comms = {{}};
      Bokeh.comm_state = {{}};
    }}

    if ((window.Jupyter !== undefined) && (Jupyter.notebook.kernel != null)) {{
      var comm_manager = Jupyter.notebook.kernel.comm_manager;
      var comm = Bokeh.comms["{comm_id}"];
      if (comm == null) {{
        comm = comm_manager.new_comm("{comm_id}", {{}}, {{}}, {{}});
        comm.on_msg(on_msg);
        comm_manager["{comm_id}"] = comm;
        Bokeh.comms["{comm_id}"] = comm;
      }}
    }} else {{
      return
    }}

    // Initialize event queue and timeouts for Comm
    var comm_state = Bokeh.comm_state["{comm_id}"];
    if (comm_state === undefined) {{
        comm_state = {{event_buffer: [], blocked: false, time: Date.now()}}
        Bokeh.comm_state["{comm_id}"] = comm_state
    }}

    // Add current event to queue and process queue if not blocked
    event_name = cb_obj.event_name
    data['comm_id'] = "{comm_id}";
    timeout = comm_state.time + {timeout};
    if ((window.Jupyter == null) | (Jupyter.notebook.kernel == null)) {{
    }} else if ((comm_state.blocked && (Date.now() < timeout))) {{
        comm_state.event_buffer.unshift([event_name, data]);
    }} else {{
        comm_state.event_buffer.unshift([event_name, data]);
        setTimeout(function() {{ process_events(comm_state); }}, {debounce});
        comm_state.blocked = true;
        comm_state.time = Date.now()+{debounce};
    }}
"""


def notebook_show(obj, doc, target):
    """
    Displays bokeh output inside a notebook and returns a CommsHandle.
    """
    bokeh_script, bokeh_div, _ = bokeh.embed.notebook.notebook_content(obj, target)

    bokeh_output = """
    {bokeh_div}
    <script type="application/javascript">{bokeh_script}</script>
    """.format(bokeh_div=bokeh_div, bokeh_script=bokeh_script)

    publish_display_data({'text/html': encode_utf8(bokeh_output)})
    return bokeh.io.notebook.CommsHandle(bokeh.io.notebook.get_comms(target), doc)


class StandardOutput(list):
    """
    Context manager to capture standard output for any code it
    is wrapping and make it available as a list, e.g.:

    >>> with StandardOutput() as stdout:
    ...   print('This gets captured')
    >>> print(stdout[0])
    This gets captured
    """

    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        sys.stdout = self._stdout


class JupyterCommJS(object):
    """
    JupyterCommJS provides a comms channel for the Jupyter notebook,
    which is initialized on the frontend. This allows sending events
    initiated on the frontend to python.
    """

    template = """
    <script>
      function msg_handler(msg) {{
        var msg = msg.content.data;
        {msg_handler}
      }}

      if ((window.Jupyter !== undefined) && (Jupyter.notebook.kernel != null)) {{
        var comm_manager = Jupyter.notebook.kernel.comm_manager;
        comm = comm_manager.new_comm("{comm_id}", {{}}, {{}}, {{}}, "{comm_id}");
        comm.on_msg(msg_handler);
      }}
    </script>

    <div id="fig_{comm_id}">
      {init_frame}
    </div>
    """

    def __init__(self, id=None, on_msg=None):
        """
        Initializes a Comms object
        """
        self.id = id if id else uuid.uuid4().hex
        self._on_msg = on_msg
        self._comm = None

        from IPython import get_ipython
        self.manager = get_ipython().kernel.comm_manager
        self.manager.register_target(self.id, self._handle_open)


    def _handle_open(self, comm, msg):
        self._comm = comm
        self._comm.on_msg(self._handle_msg)


    def send(self, data):
        """
        Pushes data across comm socket.
        """
        self.comm.send(data)


    @classmethod
    def decode(cls, msg):
        """
        Decodes messages following Jupyter messaging protocol.
        If JSON decoding fails data is assumed to be a regular string.
        """
        return msg['content']['data']


    @property
    def comm(self):
        if not self._comm:
            raise ValueError('Comm has not been initialized')
        return self._comm


    def _handle_msg(self, msg):
        """
        Decode received message before passing it to on_msg callback
        if it has been defined.
        """
        comm_id = None
        try:
            stdout = []
            msg = self.decode(msg)
            comm_id = msg.pop('comm_id', None)
            if self._on_msg:
                # Comm swallows standard output so we need to capture
                # it and then send it to the frontend
                with StandardOutput() as stdout:
                    self._on_msg(msg)
        except Exception as e:
            # TODO: isn't this cutting out info needed to understand what's gone wrong?
            # Since it's only going to the js console, maybe we could just show everything
            # (error = traceback.format_exc() or something like that)? Separately we do need a mechanism
            # to report reasonable messages to users, though.
            frame =traceback.extract_tb(sys.exc_info()[2])[-2]
            fname,lineno,fn,text = frame
            error_kwargs = dict(type=type(e).__name__, fn=fn, fname=fname,
                                line=lineno, error=str(e))
            error = '{fname} {fn} L{line}\n\t{type}: {error}'.format(**error_kwargs)
            if stdout:
                stdout = '\n\t'+'\n\t'.join(stdout)
                error = '\n'.join([stdout, error])
            reply = {'msg_type': "Error", 'traceback': error}
        else:
            stdout = '\n\t'+'\n\t'.join(stdout) if stdout else ''
            reply = {'msg_type': "Ready", 'content': stdout}

        # Returning the comm_id in an ACK message ensures that
        # the correct comms handle is unblocked
        if comm_id:
            reply['comm_id'] = comm_id
        self.send(json.dumps(reply))
