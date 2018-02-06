#!/bin/bash

mv /tmp/new_worker.cgi.out.3  /tmp/new_worker.cgi.out.4 2>/dev/null
mv /tmp/new_worker.cgi.out.2  /tmp/new_worker.cgi.out.3 2>/dev/null
mv /tmp/new_worker.cgi.out.1  /tmp/new_worker.cgi.out.2 2>/dev/null
mv /tmp/new_worker.cgi.out    /tmp/new_worker.cgi.out.1 2>/dev/null

exec 2>/tmp/new_worker.cgi.out
set -x

################

trap 'echo "trap: signal ignored"'  1 2 3 4 5 6 7 8 9 10 11 12 13 14 15
#disown

if [ "x$HTTP_X_FORWARDED_FOR" != x ]
then    # via proxy
        REMOTE_ADDR="$HTTP_X_FORWARDED_FOR"
fi

echo 'Content-type: text/plain
'

clu=""
descr=""
id=1
type=e
j1=y
j2=y
j3=y
j4=y
j5=y
loc=""
snmp="public"
custMS=""


QUERY_STRING="$QUERY_STRING&$(cat)"     # html-get+post
eval $(echo "$QUERY_STRING"| tr -s '&' '\012'|egrep "wn_"| sed 's#wn_##g')

if [ "$loc" = "" ]
then
    loc="$descr"
fi

case "$clu" in
"")
    echo "usage: $SCRIPT_URI?wn_PARAM=value[&wn_PARAM=value[..]]

    wn_PARAM    Description
 --------------------------------
    wn_clu      clustername
    wn_descr    Description
    wn_id       NodeId
    wn_type     ESX/Raspberry [e/r] 
    wn_j1       Job: Inventory [y/n]
    wn_j2       Job: Rsync [y/n]
    wn_j3       Job: Counter [y/n]
    wn_j4       Job: Backup [y/n]
    wn_j5       Job: Macaddresses [y/n]
    wn_loc      Root Location
    wn_snmp     snmp RO community
    wn_custMS   custom managed_service_name to join worker (worker is always joined to NTS:MS-4900009.07)
        
example:  $SCRIPT_URI?wn_clu=dev-test-raspi&wn_descr=NtsTestRaspi&wn_id=1&wn_type=r&wn_j1=y&wn_j2=y&wn_j3=y&wn_j4=y&wn_j5=y&wn_loc=NTS&wn_snmp=public&wn_custMS=MS-4900009.01
"
    ;;
*)  
    descr=$(echo $descr|/opt/nts/cgi-bin/html_conv)
    loc=$(echo $loc|/opt/nts/cgi-bin/html_conv)
    . /opt/nts/bin/new_worker ;;
esac



