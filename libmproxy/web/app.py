import os.path
import sys
import tornado.web
import tornado.websocket
import logging
import json
from .. import flow


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        _ = self.xsrf_token  # https://github.com/tornadoweb/tornado/issues/645
        self.render("index.html")


class WebSocketEventBroadcaster(tornado.websocket.WebSocketHandler):
    connections = None  # raise an error if inherited class doesn't specify its own instance.

    def open(self):
        self.connections.add(self)

    def on_close(self):
        self.connections.remove(self)

    @classmethod
    def broadcast(cls, **kwargs):
        message = json.dumps(kwargs)
        for conn in cls.connections:
            try:
                conn.write_message(message)
            except:
                logging.error("Error sending message", exc_info=True)


class ClientConnection(WebSocketEventBroadcaster):
    connections = set()


class Flows(tornado.web.RequestHandler):
    def get(self):
        self.write(dict(
            data=[f.get_state(short=True) for f in self.application.state.flows]
        ))


class AcceptFlows(tornado.web.RequestHandler):
    def post(self):
        self.application.state.flows.accept_all(self.application.master)


class AcceptFlow(tornado.web.RequestHandler):
    def post(self, flow_id):
        flow_id = str(flow_id)
        for flow in self.application.state.flows:
            if flow.id == flow_id:
                flow.accept_intercept(self.application.master)
                break

class Events(tornado.web.RequestHandler):
    def get(self):
        self.write(dict(
            data=list(self.application.state.events)
        ))


class Settings(tornado.web.RequestHandler):
    def get(self):
        self.write(dict(
            data=dict(
                showEventLog=True,
                intercept=self.application.state.intercept_txt
            )
        ))

    def put(self, *update, **kwargs):
        update = {}
        for k, v in self.request.arguments.iteritems():
            if len(v) != 1:
                print "Warning: Unknown length for setting {}: {}".format(k, v)
                continue

            if k == "_xsrf":
                continue
            elif k == "intercept":
                self.application.state.set_intercept(v[0])
                update[k] = v[0]
            else:
                print "Warning: Unknown setting {}: {}".format(k, v)

        ClientConnection.broadcast(
            type="settings",
            cmd="update",
            data=update
        )


class Clear(tornado.web.RequestHandler):
    def post(self):
        self.application.state.clear()


class Application(tornado.web.Application):

    @property
    def state(self):
        return self.master.state

    def __init__(self, master, debug):
        self.master = master
        handlers = [
            (r"/", IndexHandler),
            (r"/updates", ClientConnection),
            (r"/events", Events),
            (r"/flows", Flows),
            (r"/flows/accept", AcceptFlows),
            (r"/flows/([0-9a-f\-]+)/accept", AcceptFlow),
            (r"/settings", Settings),
            (r"/clear", Clear),
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True,
            cookie_secret=os.urandom(256),
            debug=debug,
        )
        tornado.web.Application.__init__(self, handlers, **settings)

