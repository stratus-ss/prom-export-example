#!/bin/sh
read request
url="${request#GET }"
url="${url% HTTP/*}"
query="${url#*\?}"
url="${url%%\?*}"
export metrics_file="/metrics/app.prom"

source /www/exporter_lib.sh

echo -e "HTTP/1.1 200 OK\r"
echo -e "Content-Type: text/plain\r"
echo -e "X-ENV-HOSTNAME: $HOSTNAME\r"
echo -e "\r"

if [ "$query" == "/demo" ] ; then
  echo "# Connection test from $HOSTNAME"
  DEMO_FROM="$(echo $HOSTNAME | cut -f1 -d'-').$(cat /var/run/secrets/kubernetes.io/serviceaccount/namespace)"
  # Skip connection to yourself, because of https://gist.github.com/rbo/4aa7840ebabf11aad3bf7961619e18e3
  # for i in marge.simpson homer.simpson selma.bouvier patty.bouvier ; do
  echo "marge.simpson homer.simpson selma.bouvier patty.bouvier" | tr " " "\n" | grep -v "$(echo $HOSTNAME | cut -f1 -d'-')" | while read i ; do
    need_export=False
    echo -n "$DEMO_FROM -> $i : "
    # in theory metric should look like simpson_connect_to_blah 1
    # some metrics may have comments so skip those
    if [ -f "${metrics_file}" ];
      then
        current_success=$(grep simpson_connect_to_${i} ${metrics_file} 2>/dev/null|grep -v "#" |awk '{print $2}')
        current_failure=$(grep simpson_failed_connection_to_${i} ${metrics_file} 2>/dev/null|grep -v "#" |awk '{print $2}')
        if [ -z ${current_failure} ] && [ -z ${current_success} ]; 
           then
              need_export=True
        fi
      else 
        need_export=True
    fi
    
    # If the variables are empty, set the counter to 1
    if [ -z ${current_success} ]; 
       then 
           current_success=1;
       else current_success=$((current_success+1)) 
    fi
    if [ -z ${current_failure} ]; 
       then 
           current_failure=1;
       else current_failure=$((current_failure+1)) 
    fi
    # If both the variables are empty we need to update the file

    
    # Run the curl test
    curl -I -s --connect-timeout 1 $i:8080  >/dev/null && success="OK"  || success="FAIL"
    echo ${success}
    
    # If the curl is successful
    if [ ${success} == "OK" ]; 
      then 
           # and if the file exists
           if [ -f "${metrics_file}" ];
             then
               # if we need to actually update the file
               if [ "${need_export}" == "True" ]; 
                then
                # run the export commands and dump the results to a file
                 exporter_add_metric simpson_connect_to_${i} counter "Successful connections to ${i}" ${current_success};
                 exporter_show_metrics > ${metrics_file}
               else
                 # otherwise, replace the line so that the count has incremented by 1
                 sed -i "s/simpson_connect_to_${i} [0-9]\+/simpson_connect_to_${i} ${current_success}/g" "${metrics_file}"
               fi
           # If we have no file in the first place, we need to create it
           else
               exporter_add_metric simpson_connect_to_${i} counter "Successful connections to ${i}" ${current_success};
               exporter_show_metrics > ${metrics_file}
           fi
      else
           if [ -f "${metrics_file}" ];
             then
               if [ "${need_export}" == "True" ]; 
                then
                 exporter_add_metric simpson_failed_connection_to_${i} counter "Unscuccessful connections to ${i}" ${current_failure};
                 exporter_show_metrics > ${metrics_file}
               else
                 sed -i "s/simpson_failed_connection_to_${i} [0-9]\+/simpson_failed_connection_to_${i} ${current_failure}/g" "${metrics_file}"
              fi
           else
               exporter_add_metric simpson_failed_connection_to_${i} counter "Unsuccessful connections to ${i}" ${current_failure}; 
               exporter_show_metrics > ${metrics_file}
           fi
 
      fi 
    sleep 1
    done; 
  exit;
fi;

echo -e "\n## request"
echo $request
