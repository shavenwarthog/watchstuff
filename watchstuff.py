#!/usr/bin/env python

'''
watchstuff.py -- "tail -f" files, add tasteful color, ignore boring stuff
'''

import ConfigParser, logging, optparse, os, re, StringIO, time

# http://pypi.python.org/pypi/termcolor
from termcolor import colored 

CONFIG = '''
[default]
ignore: postfix CRON ntpd apid_stat.py pdns_recursor
ignore_pat: elasticd.+
colori: error,white,on_red
'''


def is_dull(config, procname):
    return re.search(
        r'('
        + r'|'.join(config.get('ignore','').split())
        + r')\b',
        procname)

def annotate(msg):
    def makered(match):
        return colored(match.group(0), 'white','on_red')
    makebold = lambda m: colored(m.group(0), attrs=['bold'])
    msg = re.compile(r'error', re.IGNORECASE).sub(makered, msg)
    msg = re.compile(r'(email relayed|smtp_reply)', re.IGNORECASE).sub(
        makebold, msg)
    # 'Message queued by dev6-md2.sendgrid.net as dev6-md2.9262.4E6FDF801',
    msg = re.sub(r'Message.+as dev\S+', makebold, msg)
    msg = re.sub(r'smtp_reply.+?]]]', makebold, msg)
    return msg

logging.basicConfig(
    filename='/tmp/watchstuff.log',
    level=logging.DEBUG,
    )

def parseconfig(configstr):
    par = ConfigParser.SafeConfigParser()
    par.readfp( StringIO.StringIO(configstr) )
    return dict(par.items('default'))

def watchstuff(opts, args):
    if args:
        proc = os.popen('cat {0}'.format(' '.join(args)))
    else:
        proc = os.popen('tail -f /var/log/syslog')

    config = parseconfig(CONFIG)
    
    # Sep 13 13:13:54 dev6-md2 apid_stat.py 123:
    linepat = re.compile('(... .. \S+) (\S+) (.+?:) (.+)')
    try:
        last = None
        pause_secs = 5
        while 1:
            line = proc.readline()
            if not line:
                break
            info = linepat.match(line)
            if not info:
                print '??',info
                continue
            timestamp, _host, procname, rest = info.groups()
            if is_dull(config, procname):
                if 0:
                    print '(ignoring: {0} {1})'.format(procname,rest)
                continue
            if last and time.time()-last > pause_secs:
                print '\n\n' + '-'*20 + str(int(time.time()-last)), 'sec\n'
            last = time.time()
            print colored(timestamp,attrs=['underline']),
            print colored(procname,'yellow'),
            print annotate(rest)

    except KeyboardInterrupt:
        pass

def main():
    parser = optparse.OptionParser()
    # parser.add_option("-f", "--file", dest="filename",
    #                   help="write report to FILE", metavar="FILE")
    # parser.add_option("-q", "--quiet",
    #                   action="store_false", dest="verbose", default=True,
    #                   help="don't print status messages to stdout")
    (options, args) = parser.parse_args()
    return watchstuff(options, args)

if __name__=='__main__':
    main()
    
