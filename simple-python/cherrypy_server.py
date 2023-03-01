#!/usr/bin/python

import requests
import cherrypy
import prometheus_client as prom
import socket
import argparse
from opentelemetry import trace
from opentelemetry import metrics
tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)



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

@tracer.start_as_current_span("endpoint_test")
def test_endpoint(incoming_url, port='8080'):   
    current_span = trace.get_current_span()
    retry_strategy = requests.adapters.Retry(
    total=0,
    status_forcelist=[429, 500, 502, 503, 504],
    method_whitelist=["HEAD", "GET", "OPTIONS"]
    )
    adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("https://", adapter)
    http.mount("http://", adapter)
    final_endpoint = incoming_url
    if options.service:
        if not "http://" in incoming_url:
            final_endpoint = "http://" + incoming_url + ":" + port
    current_span.set_attribute("url.name", final_endpoint)
    try:
        response = http.get(url=final_endpoint, timeout=0.1)

        if response.status_code != 200:
            return ("FAILED", response.elapsed.total_seconds())
        else:
            return ("OK", response.elapsed.total_seconds())
    # It's ok if the request fails
    except:
        return ("FAILED", 0)


class StartWebserver(object):
    def __init__(self) -> None:  
        def _process_urls(self):
            url_list = []
            metric_name_list = []
            for single_url in options.urls:
                single_url = single_url[0]
                # metric names cannot use '-' or '/' in the name so we need to remove them
                if "http" in single_url:
                    metric_name = single_url.split("//")[1].split('.')[0].replace('-','_')
                else:
                    metric_name = single_url.replace('-','_').replace(".", "_")
                metric_name_list.append(metric_name)
                url_list.append(single_url)
            return (metric_name_list, url_list)
        self.fail_metric = prom.Counter('failed_attempts', 'Number of failed attempts', ['failed_attempts'])
        self.success_metric = prom.Counter('success_attempts', 'Number of successful attempts', ['success_attempts'])
        self.gauge_metric = prom.Gauge("response_time", "Response time in seconds", labelnames=["from", "to"])   
        self.list_of_metric_names, self.list_of_urls = _process_urls(self)
        otel_success_metric = meter.create_counter("success")
    
    

    @cherrypy.expose
    def index(self):
        return "Hello world!"

    @cherrypy.expose
    def demo(self):
        testing_results = ''
        hostname = socket.gethostname().split('-')[0]
        index = 0
        for single_url in self.list_of_urls:
            if not hostname in single_url:
                status, response_time = test_endpoint(single_url)
                # The same gnarly hack which enables you to call the dynamically created variable name without
                # having to know it in advance
                self.gauge_metric.labels(hostname, single_url).set(response_time)
                if status == "FAILED":
                    self.fail_metric.labels(failed_attempts=self.list_of_metric_names[index]).inc()
                else:
                    self.success_metric.labels(success_attempts=self.list_of_metric_names[index]).inc()
                single_result = "%s --> %s : %s" %(hostname, single_url, status)
                testing_results += single_result + '\n'
                index +=1
        return testing_results

    @cherrypy.expose
    def metrics(self):
        return prom.generate_latest()

if __name__ == '__main__':
    cherrypy.config.update({'server.socket_host': '0.0.0.0'})
    cherrypy.quickstart(StartWebserver())
