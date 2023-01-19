# prom-export-example

The respository holds a few sample applications that will generate prometheus style metrics.

**simple-python** is an app based on a Sysdig example from some time ago. It simply publishes random stats in prometheus format so that you can confirm that you know how to scrape an endpoint

**simple-http-server** was forked from Robert Bohne's OpenShift Examples. It was extended so that it now produces prometheus metrics for number of success/failures as well as stats that curl gathers

**helm-chart-sample** is a helm chart (that needs a bit of smoothing of rough edges) that can be used to deploy 4 copies of the _simple-http-server_ in a Simpsons layout adapted from the OpenShift Examples author as cited above. It currently does not create a namespace/project and should probably be extended to use persistant storage for the metrics it gathers
