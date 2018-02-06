
read -p year: year
read -p month: mon
read -p day_from: sday
read -p day_to: eday
echo
read -p domain_user: user
read -p passwd: -s pw
echo

mon=$(echo "00$mon" | sed 's#.*\([0-9][0-9]\)$#\1#')
d=$( echo $sday| awk '{print $1+0}')
e=$( echo $eday| awk '{print $1+0}')

while [ $d -le $e ]
do
    day=$(echo "00$d" | sed 's#.*\([0-9][0-9]\)$#\1#')
    echo "$year$mon$day ...."

    # achtung: limit in thruk.conf: report_max_objects = xxxxx

    wget "https://127.0.0.1:5443/central/thruk/cgi-bin/avail.cgi?eday=$day&eyear=$year&timeperiod=custom&ssec=0&sday=$day&smin=0&emon=$mon&ehour=24&syear=$year&assumestatesduringnotrunning=yes&initialassumedservicestate=0&show_log_entries=&shour=0&initialassumedhoststate=0&assumestateretention=yes&esec=0&host=all&assumeinitialstates=yes&rpttimeperiod=&emin=0&includesoftstates=yes&smon=$mon&view_mode=csv" --no-check-certificate -O  /tmp/nagios_availability_tmp.csv --http-user=$user --http-password="$pw"  -q

    if egrep 'DOCTYPE HTML PUBLIC|<html>|Ethan Galstad' /tmp/nagios_availability_tmp.csv >/dev/null  
    then
        echo "###################################################"
        echo "## failed !! see /tmp/nagios_availability_$year$mon$day.err /omd/sites/central/var/thruk/jobs/.. !!!! )" 
        echo "###################################################"
        mv /tmp/nagios_availability_tmp.csv /tmp/nagios_availability_$year$mon$day.err
    elif egrep HOST_NAME /tmp/nagios_availability_tmp.csv >/dev/null
    then
        awk '{ print "'$year$mon$day', " $0 } ' < /tmp/nagios_availability_tmp.csv >/tmp/nagios_availability_$year$mon$day.csv
        echo "  ... file stored: $(wc -l < /tmp/nagios_availability_$year$mon$day.csv) hosts # $(ls -l /tmp/nagios_availability_$year$mon$day.csv)"
        echo >>/tmp/nagios_availability_$year$mon$day.csv
    else
        echo "###################################################"
        echo "## failed !!  got corrupt file !!! -  see /tmp/nagios_availability_$year$mon$day.err "
        echo "###################################################"
        mv /tmp/nagios_availability_tmp.csv /tmp/nagios_availability_$year$mon$day.err
    fi
    echo

    (( d = d + 1 ))
done

echo
cat  /tmp/nagios_availability_$year$mon??.csv | sed '1p; /HOST_NAME/d; /^$/d;' >/tmp/nagios_availability_$year$mon.csv
echo "  ... month-file stored: $(ls -l /tmp/nagios_availability_$year$mon.csv)"

