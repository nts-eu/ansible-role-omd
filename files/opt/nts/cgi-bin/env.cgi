#!/usr/bin/perl -w


use strict;

use CGI qw(:standard);


my $key;
my ($r_addr, $r_port);

print header();

print start_html('ENV.pl');

print h1('ENV') . localtime();

print hr() . h3('QUERY_STRING');

my $f=1;
foreach $key (param()) {
   print b($key) . " => " . param($key) . "<br>\n";
   $f=0;
}

print "empty $key<br>\n" if ($f);

print hr() . h3('ENV');

foreach $key ( sort keys %ENV) {
   print b($key) . " => ", $ENV{$key}, "<br>\n";
}


$r_addr=$ENV{'REMOTE_ADDR'};
$r_port=$ENV{'REMOTE_PORT'};
print hr() . h3("netstat | egrep \'$r_addr|$r_port\'");

open (NETSTAT,"netstat -an |");
while (<NETSTAT>)
{
        if (/ $r_addr:|:$r_port /)
        {
                s# ($r_addr):# <b>$1</b>:#g;
                s#:($r_port) #:<b>$1</b> #g;
                print $_ ."<br>\n";
        }
}
close(NETSTAT);

print hr() . h3('System');

system ("id -a");

print "<br>Working directory: " . `pwd`;

print "<br>ps alfx: <pre><code>";
open (PS,"ps alfx |");
while (<PS>)
{
        s#<#&lt;#g;
        s#>#&gt;#g;
        print;
}
close(PS);
print "</code></pre>";

print end_html;

