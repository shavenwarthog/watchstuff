#!/usr/bin/env python

'''
watchstuff.py -- "tail -f" files, add tasteful color, ignore boring stuff
'''

import ConfigParser, logging, optparse, os, re, StringIO, time

# http://pypi.python.org/pypi/termcolor
from termcolor import colored 

CONFIG = '''
[default]

# ignore lines with any of these words:
ignore: postfix CRON ntpd apid_stat.py pdns_recursor

# ignore lines with this regular expression pattern:
ignore_pat: elasticd.+

# colorize words:
colori: error,white,on_red

# colorize patterns:
color_pat:
 client,bold
 Message.+as dev\S+,underline

# can repeat:
color_pat:
 smtp_reply.+?]]],bold
'''


def parseconfig(configstr):
    par = ConfigParser.SafeConfigParser()
    par.readfp( StringIO.StringIO(configstr) )
    return dict(par.items('default'))


def should_ignore(config, procname):
    m = re.search(
        r'('
        + r'|'.join(config.get('ignore','').split())
        + r')\b',
        procname)
    if m:
        return True
    pats = '|'.join(config.get('ignore_pat','').split())
    m = re.search(r'(' + pats + r')\b', procname)
    if m:
        return True
    return False


def do_color(config, msg):
    word,color,on_color = config.get('colori').split(',')
    pat = re.compile(word, re.IGNORECASE)
    return pat.sub(lambda match: colored(match.group(0), color, on_color), msg)
    

def do_colorpat(config, msg):
    for colorpat in filter(None, config.get('color_pat').split('\n')):
        args = colorpat.split(',')
        word = args.pop(0)
        attrs = []
        for aname in ('bold','underline'):
            if aname in args:
                args.remove(aname)
                attrs.append(aname)
        pat = re.compile(word)
        msg = pat.sub(lambda match: colored(match.group(0), attrs=attrs), msg)
    return msg


def annotate(config, msg):
    msg = do_color(config, msg)
    msg = do_colorpat(config, msg)
    return msg



# ::::::::::::::::::::::::::::::::::::::::::::::::::

logging.basicConfig(
    filename='/tmp/watchstuff.log',
    level=logging.DEBUG,
    )

def watchstuff(_opts, args):
    if args:
        proc = os.popen('cat {0}'.format(' '.join(args)))
    else:
        proc = os.popen('tail -10 /var/log/syslog; tail -f /var/log/syslog')

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
                print '??',line
                continue
            timestamp, _host, procname, rest = info.groups()
            if should_ignore(config, procname):
                continue
            if last and time.time()-last > pause_secs:
                print
                print '-'*20, int(time.time()-last), 'sec'
                print
            last = time.time()
            print colored(timestamp,attrs=['underline']),
            print colored(procname,'yellow'),
            print annotate(config, rest)

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
    
