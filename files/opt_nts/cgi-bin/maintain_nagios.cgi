#!/bin/bash
################################

deploy="true"
#deploy="false"    # deploy global sperren

# deploy fuer Kunden sperren
doNotDeployRegex="false"
#doNotDeployRegex="aag|bhb|alfe"
#doNotDeployRegex="loacker|sappi"
doNotDeployRegex="bhb"

restart="true"
#restart="false"  # restart nagios sperren

################################

FrontEndSrv=194.50.28.40
DbSrv=mmdb01.nts.eu

FrontEndRestUrl="http://$FrontEndSrv:28080/monitor/REST/nagios"
FrontEndUrl="$FrontEndRestUrl/workerconfig?id="

Core=naemon
export LD_LIBRARY_PATH=/omd/sites/central/local/lib:/omd/sites/central/lib

NagiosCfgDir=/omd/sites/central/etc/$Core/conf.d
NagiosCheck="/omd/sites/central/bin/$Core -v /omd/sites/central/tmp/$Core/$Core.cfg"
NagiosRetention=/omd/sites/central/var/$Core/retention.dat

NagiosSavePre=save_
NagiosSaveTs=$(date +%Y%m%d_%H%M%S)
NagiosSave=$NagiosSavePre$NagiosSaveTs

StateFile=/tmp/maintain_nagios_state_
NagiosFile=/tmp/maintain_nagios_file_
NagiosOutFile=/tmp/maintain_nagios_out

LogFile=/tmp/maintain_nagios_log
LockFile=/tmp/maintain_nagios_lock
ActionFile=$NagiosCfgDir/maintain.log

md5tag="#MD5SUM="

##################
worker_id=0
worker_name=""
worker_cmd=""
timestamp=""


_exit()
{
    echo 
    echo "EXIT=$1"
    echo 
    echo -e "$2"

    case "$1" in
    0)  s="OK"
        echo -e "$(date +%Y%m%d_%H%M%S) $s: $2" >$StateFile$worker_id

        case "$worker_cmd" in
        poll|show_backup|statistics)
            ;;
        upload*|delete*|reload|restore|monitoring_worker)
            echo "$NagiosSaveTs exit $1 ( $(echo "$2"|egrep  "config:|(^| )configuration | workergroups" | sed 's#$#  #g; s#<pre>##g; s#\\n##g;'| tr -d '\n' )  )" >> $ActionFile
            ;;
        *)
            echo "$NagiosSaveTs exit $1 ( $2 )" >> $ActionFile
            ;;
        esac
        ;;
    *)  s="ERROR"
        echo -e "$(date +%Y%m%d_%H%M%S) $s: $2" >$StateFile$worker_id
        echo "<pre>
         _
        (_ _ _ _  _
        (_| | (_)| 
        </pre>
        "  | tee -a $StateFile$worker_id

        echo "$NagiosSaveTs exit $1 ( $2 )" >> $ActionFile
        ;;
    esac


    echo -e "$(date +%Y%m%d_%H%M%S) done"
    
    if [ "$1" != 92 ]
    then
        rm $LockFile
    fi

    exit $1
}
#
_echo()
{
    echo
    echo -e "## $1"
    echo -e "$(date +%Y%m%d_%H%M%S) INFO: $1" >$StateFile$worker_id
}

################
trap 'echo "trap: signal ignored"'  1 2 3 4 5 6 7 8  10 11 12 13 14 15


if [ "x$HTTP_X_FORWARDED_FOR" != x ]
then    # via proxy
        REMOTE_ADDR="$HTTP_X_FORWARDED_FOR"
fi

echo 'Content-type: text/plain
'


QUERY_STRING="$QUERY_STRING&$(cat)"     # html-get+post
# --> worker_id; worker_name; worker_cmd
eval $(echo "$QUERY_STRING"| tr -s '&' '\012'|egrep "worker|timestamp")

case "$worker_cmd" in
poll|show_backup|statistics)
    # echo "no lock for $worker_cmd"
    :
    ;;
*)
    if [ -f $LockFile ]
    then
        # putzen
        _echo "lockfile $LockFile found!\n$(cat $LockFile)"
        find $LockFile -mmin +20 -exec rm {} \;

        if [ -f $LockFile ]
        then
            echo 
            _exit 92 "an other Nagios job is running - please wait .. \n$(cat $LockFile) "
        else
            echo "... deleted"
        fi
    fi

    rm $LogFile.9 2>/dev/null
    mv $LogFile.8   $LogFile.9  2>/dev/null
    mv $LogFile.7   $LogFile.8  2>/dev/null
    mv $LogFile.6   $LogFile.7  2>/dev/null
    mv $LogFile.5   $LogFile.6  2>/dev/null
    mv $LogFile.4   $LogFile.5  2>/dev/null
    mv $LogFile.3   $LogFile.4  2>/dev/null
    mv $LogFile.2   $LogFile.3  2>/dev/null
    mv $LogFile.1   $LogFile.2  2>/dev/null
    mv $LogFile     $LogFile.1  2>/dev/null

    exec &> >(tee $LogFile)

    echo -e "requested at $(date) from $REMOTE_ADDR\n  worker_id=$worker_id; worker_name=$worker_name; worker_cmd=$worker_cmd"
    echo -e "requested at $(date) from $REMOTE_ADDR\n  worker_id=$worker_id; worker_name=$worker_name; worker_cmd=$worker_cmd">$LockFile

    echo "$NagiosSaveTs $worker_cmd ( $worker_name $worker_id $timestamp )" >> $ActionFile
    #sed -n -i '1,200p' $ActionFile
    tail -200 $ActionFile >$ActionFile.tmp && mv $ActionFile.tmp $ActionFile

    ;;
esac

case "$worker_cmd" in
poll)   
    case "$worker_id" in
    0|"")
        _exit 99 "missing worker_id "
        ;;
    esac

    cat $StateFile$worker_id

    if [ "$worker_id" = all ]
    then
        echo "######################################################################"
        echo "Logfile:"
        cat $ActionFile
    fi

    exit
    ;;
upload)

    case "$worker_id" in
    0|"")
        _exit 99 "missing worker_id "
        ;;
    esac

    if [ "$worker_name" = "" ]
    then
        _exit 97 "missing worker_name "
    fi

    if [ "$deploy" != true ]
    then
        _exit 87 "Wartungsarbeiten!! Derzeit kein deploy Nagios!"
    fi

    if echo "$worker_name" | egrep "$doNotDeployRegex" >/dev/null
    then
        _exit 86 "Wartungsarbeiten!! Derzeit kein deploy der worker $doNotDeployRegex !"
    fi


    ###
    _echo "uploading configuration $worker_name ..." 
    echo "$(date +%Y%m%d_%H%M%S) wget: $FrontEndUrl$worker_id"

    # achtung: timeout im apache /opt/omd/sites/central/etc/apache/conf.d/nts_maintain.conf  und /etc/apache2/apache2.conf   Timeout 900
    # wildfly timout 900

    wget -t 1 -O - -T 830 -q $FrontEndUrl$worker_id > $NagiosFile$worker_name
    e=$?
    if [ $e != 0 ]
    then
        _exit 90 "error getting $worker_name-configuration (wget error $e) "
    fi

    hosts=$(egrep 'define host *{'  $NagiosFile$worker_name | wc -l)
    svcs=$(egrep 'define service *{'  $NagiosFile$worker_name | wc -l)
    echo -e "\ngot configurationfile for worker $worker_name:\n\t\t$hosts hosts\n\t\t$svcs services"

    accCred=$(grep "_XS_description" $NagiosFile$worker_name | wc -l)
    if [ "$hosts" != "$accCred" ]
    then
        _exit 84 "host access credentials missing! ($hosts != $accCred) "
    fi


    ###
    _echo "bulding md5sum ..." 
   
    soll_md5="$(grep $md5tag $NagiosFile$worker_name)"
    sum_soll="$(echo $soll_md5 | sed 's@'$md5tag'@@')"
    if [ "$soll_md5" = "$md5tag" ]
    then
        _exit 91 "got empty file for $worker_name "
    else

        sum_ist="$(grep -v $md5tag $NagiosFile$worker_name | md5sum | cut -f 1 -d' ')"

        if [ "$sum_soll" != "$sum_ist" ]
        then
            _exit 96 "checksum mismatch! ($sum_soll != $sum_ist) "
        fi

        running_md5="$(grep $md5tag $NagiosCfgDir/worker_$worker_name.cfg)"
        sum_running="$(echo $running_md5 | sed 's@'$md5tag'@@')"

        if [ "$sum_soll" = "$sum_running" ]
        then
            _exit 0 "nothing to do - monitoring configuration $worker_name ready "
        fi
    fi

    ###
    if false
    then
       _echo "fix bug in service-aggregat configuration ..." 
       mv $NagiosFile$worker_name $NagiosFile$worker_name.ori
       sed ' s#\(service_description.*intf-.*port\)-#\1_#; s#\(service_description.*intf-.*\)san-port#\1san_port#; s#\(check_aggr.*intf-.*port\)-#\1_#; s#\(check_aggr.*intf-.*\)san-port#\1san_port#;   s#\(check_command.*nc_if.*-n  \)\(\S* \S*\)#\1"\2"#; ' <$NagiosFile$worker_name.ori >$NagiosFile$worker_name    
       echo "  fixed $(sdiff -sbB $NagiosFile$worker_name.ori $NagiosFile$worker_name|wc -l) lines"
      #sdiff -sbBsw 150 $NagiosFile$worker_name.ori $NagiosFile$worker_name
    fi

    ###
    _echo "checking running configuration ..." 

    $NagiosCheck >$NagiosOutFile 2>&1 
    e=$?
    if [ $e != 0 ]
    then
        echo "#----------- $core out ---"
        echo "<pre>"
        cat $NagiosOutFile
        echo "</pre>"
        echo "#--------------------------"
        _exit 95 "running monitoring configuration is not valid! (error $e)\n$(egrep -i '^(error:|warning:)' $NagiosOutFile | egrep -v 'is deprecated and will be removed|is obsoleted and no longer' ) "
    else
        egrep '^(Total |Things)' $NagiosOutFile
    fi

    ###
    _echo "saveing running configuration ..." 
    ( cd $NagiosCfgDir; tar czf $NagiosSave.tgz *.cfg )
    echo $NagiosCfgDir/$NagiosSave.tgz
    if [ ! -f $NagiosCfgDir/worker_$worker_name.cfg ]
    then
        echo "old configuration for $worker_name missing - no delta" 
        touch $NagiosCfgDir/worker_$worker_name.cfg
    fi

    cp -p $NagiosCfgDir/worker_$worker_name.cfg /tmp
    # cleanup
    ( cd $NagiosCfgDir; find ./$NagiosSavePre*tgz -mtime +3 -exec rm {} \; )
    
    ###
    _echo "building delta configuration ..." 
    grep "host_name" $NagiosCfgDir/worker_$worker_name.cfg | awk '{print $2}' | sort -u >/tmp/maintain_nagios_hosts_old
    grep "host_name" $NagiosFile$worker_name | awk '{print $2}' | sort -u >/tmp/maintain_nagios_hosts_new

    
    grep "service_description" $NagiosCfgDir/worker_$worker_name.cfg | sort | awk '{print $2}' >/tmp/maintain_nagios_svcs_old
    grep "service_description" $NagiosFile$worker_name | sort | awk '{print $2}' >/tmp/maintain_nagios_svcs_new

    /opt/nts/bin/view_nagios_config_file < $NagiosCfgDir/worker_$worker_name.cfg >/tmp/maintain_nagios_all_old
    /opt/nts/bin/view_nagios_config_file < $NagiosFile$worker_name  >/tmp/maintain_nagios_all_new

    stat="$(
    echo "#==== $(comm -23 /tmp/maintain_nagios_hosts_new /tmp/maintain_nagios_hosts_old | wc -l) Hosts new:"
    comm -23 /tmp/maintain_nagios_hosts_new /tmp/maintain_nagios_hosts_old
    echo "#==== $(comm -13 /tmp/maintain_nagios_hosts_new /tmp/maintain_nagios_hosts_old | wc -l) Hosts deleted:"
    comm -13 /tmp/maintain_nagios_hosts_new /tmp/maintain_nagios_hosts_old
    echo
    echo "#==== $(comm -23 /tmp/maintain_nagios_svcs_new /tmp/maintain_nagios_svcs_old | wc -l) Services new:"
    comm -23 /tmp/maintain_nagios_svcs_new /tmp/maintain_nagios_svcs_old | sort | uniq -c
    echo "#==== $(comm -13 /tmp/maintain_nagios_svcs_new /tmp/maintain_nagios_svcs_old | wc -l) Services deleted:"
    comm -13 /tmp/maintain_nagios_svcs_new /tmp/maintain_nagios_svcs_old | sort | uniq -c
    echo
    echo "-----------------------------------------------------------------"
    echo "#==== Checks on $worker_name:"
    #grep -v '#' $NagiosCfgDir/worker_$worker_name.cfg | grep "\scheck_command\s" |  awk '{gsub("!.*","",$2); print $2}'| sort  | uniq -c | sort -nr 2>/dev/null
    grep -v '#' $NagiosCfgDir/worker_$worker_name.cfg | grep "\scheck_command\s" |  awk '{gsub("!"," ",$2); print $2}'| sort  | uniq -c | sort -nr 2>/dev/null
    echo )"

    echo "  $NagiosCfgDir/worker_$worker_name.cfg"
    #echo "#================== delta total ===================="
    #echo "<pre><font size=-2>$( sdiff -bBEsw 150 $NagiosFile$worker_name $NagiosCfgDir/worker_$worker_name.cfg) </font></pre>"
    echo "#================== delta total ===================="
    echo "<pre><font size=-2>$( sdiff -bBEsw 150 /tmp/maintain_nagios_all_new /tmp/maintain_nagios_all_old) </font></pre>"
    echo "#==================================================="

    # echo "$stat"

    ###
    _echo "checking new configuration ..." 

    cp $NagiosFile$worker_name $NagiosCfgDir/worker_$worker_name.cfg
    $NagiosCheck >$NagiosOutFile 2>&1 
    e=$?
    if [ $e != 0 ]
    then
        echo "#----------- $core out ---"
        echo "<pre>"
        cat $NagiosOutFile
        echo "</pre>"
        echo "#--------------------------"
        # recover
        _echo "recover previos configuration ..." 
        rm  $NagiosCfgDir/worker_$worker_name.cfg
        ( cd $NagiosCfgDir; tar xzf $NagiosSave.tgz )
        
        _exit 94 "new monitoring configuration is not valid! (error $e) - $(egrep -i '^(error:|warning:)' $NagiosOutFile | egrep -v 'is deprecated and will be removed|is obsoleted and no longer' ) "
    else
        egrep '^(Total |Things)' $NagiosOutFile
    fi


    if [ "$worker_name" = "ntsgraz" ]
    then
        _echo "copy configuration to dev.system ..." 

        sed 's#nts_#ntsprod_#g; s#hostgroup_ntsgraz#hostgroup_devnts#g;' < $NagiosCfgDir/worker_$worker_name.cfg >/tmp/worker_$worker_name.cfg_for_devnts
        scp /tmp/worker_$worker_name.cfg_for_devnts 172.21.200.11:/omd/sites/central/etc/naemon/conf.d/worker_ntsgraz_prod.cfg

        sed 's#194.50.28.42#172.21.200.11#g;' <  $NagiosCfgDir/mm_cmd.cfg >/tmp/mm_cmd.cfg_for_devnts
        scp /tmp/mm_cmd.cfg_for_devnts  172.21.200.11:/omd/sites/central/etc/naemon/conf.d/mm_cmd.cfg

        sed 's#https://mmpnp01.nts.eu#http://172.21.200.11#g;' <  $NagiosCfgDir/mm_templates.cfg >/tmp/mm_templates.cfg_for_devnts
        scp /tmp/mm_templates.cfg_for_devnts  172.21.200.11:/omd/sites/central/etc/naemon/conf.d/mm_templates.cfg

        ssh 172.21.200.11 omd restart core
    fi

    _exit 0 "configuration $worker_name ready
<pre>
#==== config: $hosts hosts, $svcs services

please dont forget to
 _ _  __|_ _  __|_  |\ | _  _ . _  _ 
| (/__\ | (_||  |   | \|(_|(_||(_)_\ 
                            _|       

$stat
</pre>
"
    ;;
monitoring_worker)
    worker_name=monitoring_worker

    ###
    _echo "getting workers from db ..." 

    mysql --batch --silent --raw -h $DbSrv -D MonConf -u max --password="gruen1" -e '
select concat("define host {\n  host_name     manmon_w_",w.name,"_",wn.identifier,
                           "\n  alias         Worker",wn.identifier," ",w.description,
                           "\n  use           worker",
                           "\n  __WORKER_NANMEID ",w.name,"_",wn.identifier,
                           "\n  __WORKER_QUEUE   hostgroup_",w.name,"_",wn.identifier,
                           "\n  __WORKER_NAME ",w.name,
                           "\n  _WORKER_HASH  ",wn.nodehash,
                           "\n  _HOSTID       ",ifnull(h.id,""),
                           "\n  _MS           [",ifnull( group_concat(ms.nts_managedservice SEPARATOR ",") ,"hostid_missing"),"]",
                           if(h.comment is null,"","\n  notes_url     /central/nts_maintain/show_notes.cgi?hostid=$_HOSTHOSTID$") , 
                           "\n  check_command nc_business_logic!-N manmon -H ",w.name,"_",wn.identifier, " -S \"appliance|disk|load|uptime|vmstat\" --freshness",
               "\n}\n",
               "define service {\n     service_description appliance",
                              "\n     host_name           manmon_w_",w.name,"_",wn.identifier,
                              "\n     _WORKER             hostgroup_",w.name,"_",wn.identifier,
                              "\n     use                 worker_appliance \n}\n",
               "define service {\n     service_description gearman",
                              "\n     host_name           manmon_w_",w.name,"_",wn.identifier,
                              "\n     use                 worker_gearman \n}\n",
               "define service {\n     service_description disk",
                              "\n     host_name           manmon_w_",w.name,"_",wn.identifier,
                              "\n     _WORKER             hostgroup_",w.name,"_",wn.identifier,
                              "\n     use                 worker_disk \n}\n",
               "define service {\n     service_description vmstat",
                              "\n     host_name           manmon_w_",w.name,"_",wn.identifier,
                              "\n     _WORKER             hostgroup_",w.name,"_",wn.identifier,
                              "\n     use                 worker_vmstat \n}\n",
               "define service {\n     service_description uptime",
                              "\n     host_name           manmon_w_",w.name,"_",wn.identifier,
                              "\n     _WORKER             hostgroup_",w.name,"_",wn.identifier,
                              "\n     use                 worker_uptime \n}\n",
               "define service {\n     service_description timediff2nagios",
                              "\n     host_name           manmon_w_",w.name,"_",wn.identifier,
                              "\n     _WORKER             hostgroup_",w.name,"_",wn.identifier,
                              "\n     use                 worker_timediff2nagios \n}\n",
               "define service {\n     service_description closed_sessions",
                              "\n     host_name           manmon_w_",w.name,"_",wn.identifier,
                              "\n     _WORKER             hostgroup_",w.name,"_",wn.identifier,
                              "\n     use                 worker_closed_sessions \n}\n",
               "define service {\n     service_description intf_bandwidth",
                              "\n     host_name           manmon_w_",w.name,"_",wn.identifier,
                              "\n     _WORKER             hostgroup_",w.name,"_",wn.identifier,
                              "\n     use                 worker_intf_bandwidth \n}\n",

               "define service {\n     service_description load",
                              "\n     host_name           manmon_w_",w.name,"_",wn.identifier,
                              "\n     _WORKER             hostgroup_",w.name,"_",wn.identifier,
                              "\n     use                 ",ifnull(wn.hostgroup,"esx_worker"),"_load \n}\n",
                            
               if ( wn.hostgroup = "raspi_worker", concat(
                   "define service {\n     service_description sensorW1",
                              "\n     host_name           manmon_w_",w.name,"_",wn.identifier,
                              "\n     _WORKER             hostgroup_",w.name,"_",wn.identifier,
                              "\n     use                 raspi_worker_sensorW1 \n}\n"
                  ), "" ),
               "\n\n"
               )
  from MonConf.worker w
       join MonConf.workernode wn on w.id = wn.idWorker
       left join MonConf.host h on  h.name = concat("w_",w.name,"_",wn.identifier ) 
       left join MonConf.hostmanagedservice hm on h.id = hm.idHost
       left join MonConf.managedservicelocal ms on hm.idManagedService = ms.id
    group by w.name,wn.identifier
    order by w.name,wn.identifier;
    ' > $NagiosFile$worker_name
    e=$?
    if [ $e != 0 ]
    then
        _exit 89 "error getting $worker_name-configuration (mysql error $e) "
    fi

    hosts=$(egrep 'define host *{'  $NagiosFile$worker_name | wc -l)
    echo -e "\ngot $hosts hosts for $worker_name\n"

    if [ $hosts = 0 ]
    then
        _exit 88 "got no workers (empty file) "
    fi


    ###
    _echo "checking running configuration ..." 

    $NagiosCheck >$NagiosOutFile 2>&1 
    e=$?
    if [ $e != 0 ]
    then
        echo "#----------- $core out ---"
        echo "<pre>"
        cat $NagiosOutFile
        echo "</pre>"
        echo "#--------------------------"
        _exit 95 "running monitoring configuration is not valid! (error $e)\n$(egrep -i '^(error:|warning:)' $NagiosOutFile | egrep -v 'is deprecated and will be removed|is obsoleted and no longer' ) "
    else
        egrep '^(Total |Things)' $NagiosOutFile
    fi

    ###
    _echo "saveing running configuration ..." 
    ( cd $NagiosCfgDir; tar czf $NagiosSave.tgz *.cfg )
    echo $NagiosCfgDir/$NagiosSave.tgz
    # cleanup
    ( cd $NagiosCfgDir; find ./$NagiosSavePre*tgz -mtime +3 -exec rm {} \; )
    
    ###
    _echo "building delta configuration ..." 
    grep "host_name" $NagiosCfgDir/mm_$worker_name.cfg | awk '{print $2}' | sort -u >/tmp/maintain_nagios_hosts_old
    grep "host_name" $NagiosFile$worker_name | awk '{print $2}' | sort -u >/tmp/maintain_nagios_hosts_new

    stat="$(
    echo "#==== Worker new:"
    comm -23 /tmp/maintain_nagios_hosts_new /tmp/maintain_nagios_hosts_old
    echo "#==== Worker deleted:"
    comm -13 /tmp/maintain_nagios_hosts_new /tmp/maintain_nagios_hosts_old
    echo )"

    echo "$stat"

    echo "  $NagiosCfgDir/mm_$worker_name.cfg"
    echo "#================== delta total ===================="
    echo "<pre><font size=-2>$( sdiff -bBEsw 150 $NagiosFile$worker_name $NagiosCfgDir/mm_$worker_name.cfg) </font></pre>"
    echo "#==================================================="

    ###
    _echo "checking new configuration ..." 

    cp $NagiosFile$worker_name $NagiosCfgDir/mm_$worker_name.cfg
    $NagiosCheck >$NagiosOutFile 2>&1 
    e=$?
    if [ $e != 0 ]
    then
        echo "#----------- $core out ---"
        echo "<pre>"
        cat $NagiosOutFile
        echo "</pre>"
        echo "#--------------------------"
        # recover
        _echo "recover previos configuration ..." 
        rm  $NagiosCfgDir/mm_$worker_name.cfg
        ( cd $NagiosCfgDir; tar xzf $NagiosSave.tgz )
        
        _exit 94 "new monitoring configuration is not valid! (error $e)\n$(egrep -i '^(error:|warning:)' $NagiosOutFile | egrep -v 'is deprecated and will be removed|is obsoleted and no longer' ) "
    else
        egrep '^(Total |Things)' $NagiosOutFile
    fi

    _exit 0 "configuration $worker_name ready
<pre>
#==== config: $hosts worker

$stat

please dont forget to
 _ _  __|_ _  __|_  |\ | _  _ . _  _ 
| (/__\ | (_||  |   | \|(_|(_||(_)_\ 
                            _|       
</pre>
"
    ;;
#upload_backupconfig|delete_backupconfig|upload_uomconfig|delete_uomconfig)
#
#    
#    case "$worker_cmd" in 
#    upload_*)
#        todo=$(echo $worker_cmd| sed 's#upload_##')
#        cmd=upload
#        ;;
#    delete_*)
#        todo=$(echo $worker_cmd| sed 's#delete_##')
#        cmd=delete
#        ;;
#    esac
#
#    if [ "$deploy" != true ]
#    then
#        _exit 87 "Wartungsarbeiten!! Derzeit kein deploy Nagios!"
#    fi
#
#    if echo "$todo" | egrep "$doNotDeployRegex" >/dev/null
#    then
#        _exit 86 "Wartungsarbeiten!! Derzeit kein deploy der worker $doNotDeployRegex !"
#    fi
#
#
#    ###
#    if [ "$cmd" = upload ]
#    then
#        _echo "uploading configuration $todo ..." 
#        echo "$(date +%Y%m%d_%H%M%S) wget: $FrontEndRestUrl/$todo"
#
#        # achtung: timeout im apache /opt/omd/sites/central/etc/apache/conf.d/nts_maintain.conf Timeout 600
#
#        wget -t 1 -O - -T 200 -q $FrontEndRestUrl/$todo > $NagiosFile$todo
#        e=$?
#        if [ $e != 0 ]
#        then
#            _exit 90 "error getting $todo-configuration (wget error $e) "
#        fi
#
#        hosts=$(egrep 'define host *{'  $NagiosFile$todo | wc -l)
#        svcs=$(egrep 'define service *{'  $NagiosFile$todo | wc -l)
#        echo -e "\ngot configurationfile for $todo:\n\t\t$hosts hosts\n\t\t$svcs services"
#
#        ###
#        _echo "bulding md5sum ..." 
#       
#        soll_md5="$(grep $md5tag $NagiosFile$todo)"
#        sum_soll="$(echo $soll_md5 | sed 's@'$md5tag'@@')"
#        if [ "$soll_md5" = "$md5tag" ]
#        then
#            _exit 91 "got empty file for $todo "
#        else
#
#            sum_ist="$(grep -v $md5tag $NagiosFile$todo | md5sum | cut -f 1 -d' ')"
#
#            if [ "$sum_soll" != "$sum_ist" ]
#            then
#                _exit 96 "checksum mismatch! ($sum_soll != $sum_ist) "
#            fi
#
#            running_md5="$(grep $md5tag $NagiosCfgDir/mm_$todo.cfg)"
#            sum_running="$(echo $running_md5 | sed 's@'$md5tag'@@')"
#
#            if [ "$sum_soll" = "$sum_running" ]
#            then
#                _exit 0 "nothing to do - monitoring configuration $todo ready "
#            fi
#        fi
#    fi
#
#    if [ "$cmd" = delete ]
#    then
#        _echo "deleting configuration $todo ..." 
#
#        hosts=1
#        svcs=0
#
#        echo '
#                define host {
#                    host_name       manmon_'$todo'_config_deleted
#                    alias           config missing
#                    address         127.0.0.1
#                    action_url
#                    check_command       echo_crit!"please deploy nagiosconfig '$todo'"
#                    use         host-24x7-5
#                    _WORKER         
#                }
#                define service{
#                        service_description     config_deleted
#                        use             service-24x7-5
#                        host_name       manmon_'$todo'_config_deleted
#                        action_url
#                        check_command   echo_crit!"please deploy nagiosconfig '$todo'"
#                }
#
#        ' > $NagiosFile$todo 
#    fi
#
#    ###
#    _echo "checking running configuration ..." 
#
#    $NagiosCheck >$NagiosOutFile 2>&1 
#    e=$?
#    if [ $e != 0 ]
#    then
#        echo "#----------- $core out ---"
#        echo "<pre>"
#        cat $NagiosOutFile
#        echo "</pre>"
#        echo "#--------------------------"
#        _exit 95 "running monitoring configuration is not valid! (error $e)\n$(egrep -i '^(error:|warning:)' $NagiosOutFile | egrep -v 'is deprecated and will be removed|is obsoleted and no longer' ) "
#    else
#        egrep '^(Total |Things)' $NagiosOutFile
#    fi
#
#    ###
#    _echo "saveing running configuration ..." 
#    ( cd $NagiosCfgDir; tar czf $NagiosSave.tgz *.cfg )
#    echo $NagiosCfgDir/$NagiosSave.tgz
#    cp -p $NagiosCfgDir/mm_$todo.cfg /tmp
#    # cleanup
#    ( cd $NagiosCfgDir; find ./$NagiosSavePre*tgz -mtime +3 -exec rm {} \; )
#    
#    ###
#    _echo "building delta configuration ..." 
#    grep "host_name" $NagiosCfgDir/mm_$todo.cfg | awk '{print $2}' | sort -u >/tmp/maintain_nagios_hosts_old
#    grep "host_name" $NagiosFile$todo | awk '{print $2}' | sort -u >/tmp/maintain_nagios_hosts_new
#    
#    grep "service_description" $NagiosCfgDir/mm_$todo.cfg | sort | awk '{print $2}' >/tmp/maintain_nagios_svcs_old
#    grep "service_description" $NagiosFile$todo | sort | awk '{print $2}' >/tmp/maintain_nagios_svcs_new
#
#    stat="$(
#    echo "#==== $(comm -23 /tmp/maintain_nagios_hosts_new /tmp/maintain_nagios_hosts_old | wc -l) Hosts new:"
#    comm -23 /tmp/maintain_nagios_hosts_new /tmp/maintain_nagios_hosts_old
#    echo "#==== $(comm -13 /tmp/maintain_nagios_hosts_new /tmp/maintain_nagios_hosts_old | wc -l) Hosts deleted:"
#    comm -13 /tmp/maintain_nagios_hosts_new /tmp/maintain_nagios_hosts_old
#    echo
#    echo "#==== $(comm -23 /tmp/maintain_nagios_svcs_new /tmp/maintain_nagios_svcs_old | wc -l) Services new:"
#    comm -23 /tmp/maintain_nagios_svcs_new /tmp/maintain_nagios_svcs_old | sort | uniq -c
#    echo "#==== $(comm -13 /tmp/maintain_nagios_svcs_new /tmp/maintain_nagios_svcs_old | wc -l) Services deleted:"
#    comm -13 /tmp/maintain_nagios_svcs_new /tmp/maintain_nagios_svcs_old | sort | uniq -c
#    echo )"
#
#    echo "$stat"
#
#    echo "  $NagiosCfgDir/mm_$todo.cfg"
#    #echo "#================== delta total ===================="
#    #echo "<pre><font size=-2>$( sdiff -bBEsw 150 $NagiosFile$todo $NagiosCfgDir/mm_$todo.cfg) </font></pre>"
#    echo "#==================================================="
#
#    ###
#    _echo "checking new configuration ..." 
#
#    cp $NagiosFile$todo $NagiosCfgDir/mm_$todo.cfg
#    $NagiosCheck >$NagiosOutFile 2>&1 
#    e=$?
#    if [ $e != 0 ]
#    then
#        echo "#----------- $core out ---"
#        echo "<pre>"
#        cat $NagiosOutFile
#        echo "</pre>"
#        echo "#--------------------------"
#        # recover
#        _echo "recover previos configuration ..." 
#        rm  $NagiosCfgDir/mm_$todo.cfg
#        ( cd $NagiosCfgDir; tar xzf $NagiosSave.tgz )
#        
#        _exit 94 "new monitoring configuration is not valid! (error $e)\n$(egrep -i '^(error:|warning:)' $NagiosOutFile | egrep -v 'is deprecated and will be removed|is obsoleted and no longer' ) "
#    else
#        egrep '^(Total |Things)' $NagiosOutFile
#    fi
#
#    if [ "$cmd" = delete ]
#    then
#        _exit 0 "monitoring configuration $todo ready"
#    fi
#
#    _exit 0 "monitoring configuration $todo ready
#<pre>
##==== config: $hosts hosts, $svcs services
#
#$stat
#
#please dont forget to
# _ _  __|_ _  __|_  |\ | _  _ . _  _ 
#| (/__\ | (_||  |   | \|(_|(_||(_)_\ 
#                            _|       
#</pre>
#"
#    ;;

reload)

    worker_id=all

    if [ "$restart" != true ]
    then
        _exit 88 "Wartungsarbeiten!! Derzeit kein restart Nagios!"
    fi

    _echo "previous $Core reload: $(cat ${StateFile}last_nagios_reload 2>/dev/null) "

    # if [ "$(find  ${StateFile}last_nagios_reload -mmin -60)" =  ${StateFile}last_nagios_reload ]
    #then
    #    _echo "previous $Core reload was less then 1 hour ago !!!"
    #    # _exit 83 "previous $Core reload was less then 1 hour ago! please wait (in case of emergency delete file ${StateFile}last_nagios_reload on host $(uname -n))"
    #fi
 
    _echo "checking running configuration ..." 

    $NagiosCheck >$NagiosOutFile 2>&1 
    e=$?
    if [ $e != 0 ]
    then
        echo "#----------- $core out ---"
        echo "<pre>"
        cat $NagiosOutFile
        echo "</pre>"
        echo "#--------------------------"
        _exit 95 "running monitoring configuration is not valid! (error $e)\n$(egrep -i '^(error:|warning:)' $NagiosOutFile | egrep -v 'is deprecated and will be removed|is obsoleted and no longer' ) "
    else
        egrep '^(Total |Things)' $NagiosOutFile
    fi


    ###
    _echo "activating configuration ..." 

    
    info=$(
    echo "<pre>"
    hosts=$(egrep 'define host *{'  $NagiosCfgDir/worker_*.cfg | wc -l)
    svcs=$(egrep 'define service *{'  $NagiosCfgDir/worker_*.cfg | wc -l)
    hostsesx=$(  egrep 'use\s*esx_worker' $NagiosCfgDir/mm_monitoring_worker.cfg | wc -l )
    hostsraspi=$(  egrep 'use\s*raspi_worker' $NagiosCfgDir/mm_monitoring_worker.cfg | wc -l )
    svcsesx=$( egrep 'hostgroup_name.*esx_worker' $NagiosCfgDir/mm_monitoring_checks_on_worker.cfg| wc -l )
    (( svcsesx = svcsesx * hostsesx ))
    svcsraspi=$( egrep 'hostgroup_name.*raspi_worker' $NagiosCfgDir/mm_monitoring_checks_on_worker.cfg| wc -l )
    (( svcsraspi = svcsraspi * hostsraspi ))

    a=$(ls  $NagiosCfgDir/worker_*.cfg| wc -l)
    #echo -e "\ngot $a configurationfiles for workers:\n\t\t$hosts hosts\n\t\t$svcs services"

    printf "%20s %10s %10s %10s %10s %6s\n" Workergroup Hosts int.Hosts Services int.Scv Svc/Hst
    echo "------------------------------------------------------------------------"
    for w in $(ls $NagiosCfgDir/worker_*.cfg)
    do
        wn=$(echo "$w" | sed 's#.*worker_\(.*\)\.cfg#\1#')
        h=$(egrep 'define host *{' $w| wc -l)
        hi=$(egrep 'use\s+no_mon\s*$' $w| wc -l)
        s=$(egrep 'define service *{' $w| wc -l)
        si=$(egrep 'use\s+(inventory|backup)\s*$' $w| wc -l)
        #printf "%25s %10s %10s\n" $wn $h $s
        echo $h $s $wn   $hi $si 
    done |awk '
        {    h=$1+0; s=$2+0; hi=$4+0; si=$5+0; 
             th+=h;  ts+=s;  thi+=hi; tsi+=si;
             printf "%20s %10s %10s %10s %10s %7.1f\n",$3,h,hi,s,si,s/h 
        }
        END {print "------------------------------------------------------------------------"
             printf "%20s %10s %10s %10s %10s %7.1f\n","Total ("NR" groups)",th,thi,ts,tsi,ts/th ;
        }
    '


    #echo
    #for f in $NagiosCfgDir/mm_*config.cfg 
    #do
    #    c=$(echo $f | sed 's#.*mm_##; s#config.cfg$##')
    #    echo "$c:"
    #    echo "  Hosts:             $(  egrep 'define host\s*\{' $f | wc -l ) Hosts"
    #    echo "  Services:          $(  egrep 'define service\s*\{' $f | wc -l ) Services"
    #done
    
    echo
    echo "Monitoring:" 
    echo "  Central:           $(  egrep 'define host\s*\{' $NagiosCfgDir/mm_monitoring_central.cfg | wc -l ) Hosts"
    echo "  ESX-Workernodes:   $hostsesx Hosts $svcsesx Services "
    echo "  Raspi-Workernodes: $hostsraspi Hosts $svcsraspi Services "
    echo "</pre>"
    )
    
    echo "[$(date +%s)] SAVE_STATE_INFORMATION" > /opt/omd/sites/central/tmp/run/$Core.cmd
    sleep 15

    rm -f $NagiosRetention.save.2 
    mv $NagiosRetention.save.1 $NagiosRetention.save.2 2>/dev/null
    cp -p $NagiosRetention     $NagiosRetention.save.1 

    #omd reload core  >$NagiosOutFile 2>&1 
    omd restart core  >$NagiosOutFile 2>&1 
 
    e=$?
    echo "#----------- $core out ---"
    echo "<pre>"
    cat $NagiosOutFile
    echo "</pre>"
    echo "#--------------------------"
    if [ $e != 0 ]
    then
        _exit 93 "activating monitoring configuration failed! (error $e) $(egrep -i 'error:|warning:' $NagiosOutFile) "
    fi

    # debug
    ls -l  --time-style=full-iso $NagiosRetention     $NagiosRetention.save.1

    date  +%Y%m%d_%H%M%S > ${StateFile}last_nagios_reload

    _exit 0 "new monitoring configuration activated\n$info
<pre>
 _ 
/ \ |/ 
\_/ |\ 
</pre>
"
    for i in {1..36}
    do 
         sleep 5
         [ "$( find /omd/sites/central/tmp/$Core/status.dat -newer /omd/sites/central/var/$Core/objects.precache )" = "/omd/sites/central/tmp/$Core/status.dat" ] && break
         echo -n "."
    done

    echo
    
    ;;
show_backup)
    _echo "showing configuration backups from filesystem ..." 

    backups=$(cd $NagiosCfgDir; ls -r ${NagiosSavePre}*.tgz | sed 's#'${NagiosSavePre}'##; s#\.tgz##;')

    _echo "found $(echo $backups|wc -w) backups:\n"

    echo "backup_timestamp action comment"
    echo "------------------------------------------------------------------------"
    for b in $backups
    do
        egrep -v " exit " $ActionFile | egrep "^$b " || echo $b
    done
    _echo "to restore a backup,  run \"$SCRIPT_URI?worker_cmd=restore&amp;timestamp=backup_timestamp\""    

    _exit 0 ""
    ;;
restore)

    cd $NagiosCfgDir
    backup=${NagiosSavePre}$timestamp.tgz
    if [ ! -s $backup ]
    then
        _exit 85 "backup $backup not found!"
    fi

    ###
    _echo "saveing running configuration ..." 
    ( cd $NagiosCfgDir; tar czf $NagiosSave.tgz *.cfg )
    echo $NagiosCfgDir/$NagiosSave.tgz

    _echo "recover backup configuration from $backup ..." 
    ( cd $NagiosCfgDir; tar xzf $backup )
        
    _echo "checking configuration ..." 

    $NagiosCheck >$NagiosOutFile 2>&1 
    e=$?
    if [ $e != 0 ]
    then
        echo "#----------- $core out ---"
        echo "<pre>"
        cat $NagiosOutFile
        echo "</pre>"
        echo "#--------------------------"
        # recover
        _echo "recover previos configuration ..." 
        ( cd $NagiosCfgDir; tar xzf $NagiosSave.tgz )
        
        _exit 94 "new monitoring configuration is not valid! (error $e)\n$(egrep -i '^(error:|warning:)' $NagiosOutFile | egrep -v 'is deprecated and will be removed|is obsoleted and no longer' ) "
    else
        egrep '^(Total |Things)' $NagiosOutFile
    fi

    _exit 0 "monitoring configuration $timestamp ready
<pre>

please dont forget to
 _ _  __|_ _  __|_  |\ | _  _ . _  _ 
| (/__\ | (_||  |   | \|(_|(_||(_)_\ 
                            _|       
</pre>
"
    ;;
statistics)
    echo " <pre>"
    _echo "workergroups ..." 
    echo
    printf "%20s %10s %10s %10s %10s %6s\n" Workergroup Hosts int.Hosts Services int.Scv Svc/Hst
    echo "------------------------------------------------------------------------"
    for w in $(ls $NagiosCfgDir/worker_*.cfg)
    do
        wn=$(echo "$w" | sed 's#.*worker_\(.*\)\.cfg#\1#')
        h=$(egrep 'define host *{' $w| wc -l)
        hi=$(egrep 'use\s+no_mon\s*$' $w| wc -l)
        s=$(egrep 'define service *{' $w| wc -l)
        si=$(egrep 'use\s+(inventory|backup)\s*$' $w| wc -l)
        #printf "%25s %10s %10s\n" $wn $h $s
        echo $h $s $wn   $hi $si 
    done |awk '
        {    h=$1+0; s=$2+0; hi=$4+0; si=$5+0; 
             th+=h;  ts+=s;  thi+=hi; tsi+=si;
             printf "%20s %10s %10s %10s %10s %7.1f\n",$3,h,hi,s,si,s/h 
        }
        END {print "------------------------------------------------------------------------"
             printf "%20s %10s %10s %10s %10s %7.1f\n","Total ("NR" groups)",th,thi,ts,tsi,ts/th ;
        }
    '

    _echo "configuration statistics ..." 

    top=50

    cmds=$(cd $NagiosCfgDir; cat *.cfg | grep -v '#' | grep "\scheck_command\s" |  awk '{gsub("!.*","",$2); print $2}'| sort  | uniq -c | sort -nr 2>/dev/null | head -$top)
    _echo "top $top check-commands:\n$cmds\n\n"

    hosts=$(cd $NagiosCfgDir; cat *.cfg | grep -v '#' | grep "\shost_name\s" |  awk '{print $2}'| sort  | uniq -c | sort -nr 2>/dev/null | head -$top)
    _echo "top $top checks per host:\n$hosts\n\n"

    svcs=$(cd $NagiosCfgDir; cat *.cfg | grep -v '#' | grep "\sservice_description\s" |  awk '{print $2}'| sort  | uniq -c | sort -nr 2>/dev/null | head -$top)
    _echo "top $top service-names:\n$svcs\n\n"

    templates=$(cd $NagiosCfgDir; cat *.cfg | grep -v '#' | grep "\suse\s" |  awk '{print $2}'| sort  | uniq -c | sort -nr 2>/dev/null | head -$top)
    _echo "top $top used templates:\n$templates\n\n"

    echo " </pre>"
    _exit 0 ""
    ;;
*)
    echo
    echo "available commands: poll upload monitoring_worker reload show_backup restore statistics  .."
    _exit 98 "wrong cmd \"$worker_cmd\" "
    ;;
esac




