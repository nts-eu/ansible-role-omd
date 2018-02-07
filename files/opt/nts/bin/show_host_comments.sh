#!/bin/bash
#

#echo under construction $1; exit 3 
#echo $* ; exit 

hid=$1

log=/tmp/show_host_comments.log

rm        $log.9 2>/dev/null
mv $log.8 $log.9 2>/dev/null
mv $log.7 $log.8 2>/dev/null
mv $log.6 $log.7 2>/dev/null
mv $log.5 $log.6 2>/dev/null
mv $log.4 $log.5 2>/dev/null
mv $log.3 $log.4 2>/dev/null
mv $log.2 $log.3 2>/dev/null
mv $log.1 $log.2 2>/dev/null
mv $log   $log.1 2>/dev/null
echo "$(date) $0 hid=$hid" >$log

exec 2>>$log



case "$hid" in
[0-9]*)
    o="$( wget http://mmfrontend01.nts.eu:28080/monitor/REST/thruk/hostComments/$hid -O - 2>$log.err )" 
    e=$?
    err=$(cat $log.err; rm $log.err)

       echo "exit: $e" >>$log
       echo "out: $o" >>$log

    case $e in
    0)  
        if [ "$(echo $o | sed 's#<[^>]*>##g')" = "" ]
        then
            echo "no comments and instructions stored for this host"
            exit 0
        else
            echo "<div style=\"text-align:left\"><style>.comments .comment {text-align:left}</style> $o </div>"
        fi
        exit 1  # 1, damit das Message-Fenster nicht aus-timed
        ;;
    *)
        echo "error getting data from mmfrontend01.nts.eu for hostid $hid !" >>$log
        echo "<h1> ERROR </h1><h3>error (wget: $e) getting data from mmfrontend01.nts.eu for hostid $hid !</h3><hr><pre>"
        echo
        echo "err: $err" 
        echo
        echo "out: $o" 
        echo "</pre>"
        exit 2
        ;;
    esac
    ;;
*)
    echo "Hostid missing!" >>$log
    echo "Hostid missing!"
    exit 3
    ;;
esac
