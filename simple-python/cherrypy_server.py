#!/usr/bin/python

import requests
import cherrypy
import prometheus_client as prom
import socket
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--urls', nargs='*', dest='urls', action='append')
parser.add_argument('--service', dest='service', action=argparse.BooleanOptionalAction)
options = parser.parse_args()

# These urls can be used if arguments aren't passed in by the container
# GLOBAL_URLS = ['http://homer-simpson.apps.ocp.stratus.lab/demo', 'http://marge-simpson.apps.ocp.stratus.lab/demo', 'http://selma-bouvier.apps.ocp.stratus.lab/demo', 'http://patty-bouvier.apps.ocp.stratus.lab/demo']


def add_to_dictionary(dictionary, endpoint, component, value=1, overwrite=True):
    if endpoint in dictionary:
        if overwrite:
            dictionary[endpoint][component] = value
        else:
            dictionary[endpoint][component] +=1
    else:
        dictionary[endpoint] = {component: value}


def test_endpoint(incoming_url, port=8080):
    if options.service:
        final_endpoint = incoming_url + ":" + port
    else:
        final_endpoint = incoming_url
    response = requests.request(method='GET', url=final_endpoint)
    
    if response.status_code != 200:
        return ("FAILED", response.elapsed.total_seconds())
    else:
        return ("OK", response.elapsed.total_seconds())


class StartWebserver(object):
    fail_metric = prom.Counter('failed_attempts', 'Number of failed attempts', ['failed_attempts'])
    success_metric = prom.Counter('success_attempts', 'Number of successful attempts', ['success_attempts'])
    @cherrypy.expose
    def index(self):
        return "Hello world!"

    @cherrypy.expose
    def demo(self):
        testing_results = ''
        hostname = socket.gethostname()#.split('-')[0]
        for single_url in options.urls:
            gauge_variable_name = "%s_to_%s_response_time" % (hostname.split('-')[0], single_url[0].split("//")[1].split('.')[0].replace('-','_'))
            # This is a gnarly work around to set a dynamic name for the response time    
            exec(f'{gauge_variable_name}=prom.Gauge(gauge_variable_name, "Response time in seconds")')
            single_url = single_url[0]
            if not hostname in single_url:
                status, response_time = test_endpoint(single_url)
                # The same gnarly hack which enables you to call the dynamically created variable name without
                # having to know it in advance
                exec(f'{gauge_variable_name}.set(response_time)')
                if status == "FAILED":
                    self.fail_metric.labels(failed_attempts=single_url).inc()
                else:
                    self.success_metric.labels(success_attempts=single_url).inc()
                single_result = "%s --> %s : %s" %(hostname, single_url, status)
                testing_results += single_result + '\n'
        return testing_results

    @cherrypy.expose
    def metrics(self):
        return prom.generate_latest()

if __name__ == '__main__':
    cherrypy.config.update({'server.socket_host': '0.0.0.0'})
    cherrypy.quickstart(StartWebserver())
