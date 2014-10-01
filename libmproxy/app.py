import flask
import os.path
# I know is circular, but as master is integrating a web interfase it will make sense to 
#  do it right there.
import flow

mapp = flask.Flask(__name__)
mapp.debug = True

def master():
    return flask.request.environ["mitmproxy.master"]

@mapp.route("/")
def index():
    return flask.render_template("index.html", section="home")


@mapp.route("/cert/pem")
def certs_pem():
    capath = master().server.config.cacert
    p = os.path.splitext(capath)[0] + "-cert.pem"
    return flask.Response(open(p).read(), mimetype='application/x-x509-ca-cert')


@mapp.route("/cert/p12")
def certs_p12():
    capath = master().server.config.cacert
    p = os.path.splitext(capath)[0] + "-cert.p12"
    return flask.Response(open(p).read(), mimetype='application/x-pkcs12')

@mapp.route("/scenario/")
@mapp.route("/scenario/<name>")
def scenario(name=None):
    if name:
        flow.Scenario = str(name)
    else: 
        flow.Scenario = flow.MAIN_SCENARIO
    return flask.render_template("scenario.html", scenario=flow.Scenario)
