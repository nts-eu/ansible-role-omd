#! /bin/bash

# 20170308jd
#
# params:       host,service
#

NagLog=/omd/sites/central/var/naemon/naemon.log
NagLogArch=/omd/sites/central/var/naemon/archive/naemon.log-


################
trap 'echo "trap: signal ignored"'  1 2 3 4 5 6 7 8  10 11 12 13 14 15

tmpFile=/tmp/search_log

set -x
exec 2> $tmpFile.err

if [ "x$HTTP_X_FORWARDED_FOR" != x ]
then    # via proxy
        REMOTE_ADDR="$HTTP_X_FORWARDED_FOR"
fi

echo 'Content-type: text/plain
'

host=""
service=""
ts=""

QUERY_STRING="$QUERY_STRING&$(cat)"     # html-get+post
eval $(echo "$QUERY_STRING"| tr -s '&' '\012'|egrep "usage|host|service|ts|all|hard"|sed '/=/ '\!'s#$#=y#;')

#if [ "$host" = "" -o "${!usage*}" = "usage" -o "$ts" = "" ]
if [ "$host" = "" -o "$usage" = "y" -o "$ts" = "" ]
then
    echo "$0 

    parameter:
        host ..... nagios-hostname (or part)
        service .. nagios-servicename (or part or empty)

        ts ....... timestamp (format: yyyymm or yyyymmdd)
                    achtung: timestamp vom logfile - die events sind vom tag davor

        all ...... show all entry-types
        hard ..... show only hard states

    example: $SCRIPT_URI?hard&host=nts_grzsw01&service=ping&ts=$(date +%Y%m%d -d "2 days ago")
    "
    exit 99
fi

param="-h $host"

if [ "$service" != "" ]
then
    param="$param -s $service"
fi

if [ "$all" = y ]
then
    param="$param -a"
fi

if [ "$hard" = y ]
then
    param="$param -t hard"
fi


#echo $param

case "$ts" in
201???|201?????)
    : ;;
*)
    echo "wrong timestamp ($ts)"
    exit 99
    ;;
esac

case "$ts" in
 $(date +%Y%m))
    cat $NagLogArch$ts* $NagLog
    ;;
$(date +%Y%m%d))
    cat $NagLogArch$ts* $NagLog
    #cat $NagLog
    ;;
*)
    cat $NagLogArch$ts* 
    ;;
esac |  /opt/nts/bin/log_viewer -f - $param


