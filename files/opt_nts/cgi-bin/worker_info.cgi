#!/bin/bash


################

trap 'echo "trap: signal ignored"'  1 2 3 4 5 6 7 8 9 10 11 12 13 14 15
#disown

if [ "x$HTTP_X_FORWARDED_FOR" != x ]
then    # via proxy
        REMOTE_ADDR="$HTTP_X_FORWARDED_FOR"
fi

echo 'Content-type: text/plain
'


QUERY_STRING="$QUERY_STRING&$(cat)"     # html-get+post
eval $(echo "$QUERY_STRING"| tr -s '&' '\012'|egrep "info")


case "$info" in
config)
    echo "Worker;Description;Nodes"
    mysql -B -N --delimiter=";" -h mmdb01.nts.eu -D MonConf -u max --password="gruen1" -e "
    select concat_ws(';',w.name, w.description, max(wn.identifier)) from MonConf.worker w
       join MonConf.workernode wn on w.id = wn.idWorker
      group by w.name, w.description  order by 1 ;
    "
    ;;
id)
    echo "Worker;Description;Id"
    mysql -B -N --delimiter=";" -h mmdb01.nts.eu -D MonConf -u max --password="gruen1" -e "
    select concat_ws(';',w.name, w.description, w.id) from MonConf.worker w 
    order by w.name;
    "
    ;;
statistics)
    NagiosCfgDir=/omd/sites/central/etc/nagios/conf.d

    hosts=$(egrep 'define host *{'  $NagiosCfgDir/worker_*.cfg | wc -l)
    svcs=$(egrep 'define service *{'  $NagiosCfgDir/worker_*.cfg | wc -l)
    a=$(ls  $NagiosCfgDir/worker_*.cfg| wc -l)
    printf "Worker;Hosts;Services;Svc/Hst\n"
    for w in $(ls $NagiosCfgDir/worker_*.cfg)
    do
        wn=$(echo "$w" | sed 's#.*worker_\(.*\)\.cfg#\1#')
        h=$(egrep 'define host *{' $w| wc -l)
        s=$(egrep 'define service *{' $w| wc -l)
        echo $h $s "$wn" |awk '{h=$1+0; s=$2+0; print $3 ";" h ";" s ";" s/h }'
    done
    echo $hosts $svcs "Total ($a worker)" |awk '{h=$1+0; s=$2+0; print $3" "$4" "$5 ";" h ";" s ";" s/h }'

    ;;
running)
    gm_srv=194.50.28.80
    gm_port=4730
    all_queues="$( (echo status; sleep 1) | telnet $gm_srv $gm_port 2>/dev/null )"
    queues="$( echo "$all_queues" | egrep '_ma\s' | sort )"
    #all_workers="$( echo "$queues"| cut -f1 | sed 's#_ma$##' )"
    #all_active_workers="$( echo "$queues"| egrep -v '[^0-9]0$' | cut -f1 | sed 's#_ma$##' )"
    echo "Worker;Nodes"
    echo "$queues"| cut -f1 | sed 's#_[0-9][0-9]*_ma$##' | sort |uniq -c|awk '{ print $2 ";" $1 }'
    ;;
*)
    echo "unknown argument
    usage:
        info=config ..... configured workers in DB
        info=running .... workers connected
        info=statistics . Nagios hosts/services per worker
        info=id ......... worker IDs from DB
"
    ;;
esac



