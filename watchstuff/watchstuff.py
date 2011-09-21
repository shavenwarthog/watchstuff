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
ignore_proc: postfix CRON ntpd apid_stat.py pdns_recursor

# ignore lines with this regular expression pattern:
ignore_proc_pat: elasticd.+

# colorize words:
colori: error,white,on_red
colori: warning,red

# colorize patterns:
color_pat:
 client,bold
 Message.+as dev\S+,underline

# can repeat:
color_pat:
 smtp_reply.+?]]],bold

# Munin timestamp
color_pat:
 ..../../..-..:..:..,underline
 INFO,bold
 ERROR,red
 entropy,black,on_yellow
'''


def parseconfig(configstr):
    par = ConfigParser.SafeConfigParser()
    par.readfp( StringIO.StringIO(configstr) )
    return dict(par.items('default'))


def should_ignore_proc(config, procname):
    m = re.search(
        r'('
        + r'|'.join(config.get('ignore_proc','').split())
        + r')\b',
        procname)
    if m:
        return True
    pats = '|'.join(config.get('ignore_proc_pat','').split())
    m = re.search(r'(' + pats + r')\b', procname)
    if m:
        return True
    return False


def should_ignore(config, msg):
    ignore_str = config.get('ignore')
    if not ignore_str:
        return False
    ignore_pat = re.compile(r'('+ignore_str+r')')
    return ignore_pat.search(msg) != False


def do_color(config, msg):
    color, on_color = None, None
    args = config.get('colori').split(',')
    word = args.pop(0)
    if args:
        color = args.pop(0)
    if args:
        on_color = args.pop(0)

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
    if should_ignore(config, msg):
        return
    msg = do_color(config, msg)
    msg = do_colorpat(config, msg)
    return msg



# ::::::::::::::::::::::::::::::::::::::::::::::::::

logging.basicConfig(
    filename='/tmp/watchstuff.log',
    level=logging.DEBUG,
    )

def watchstuff(opts, args):
    cmd = ['tail']
    if opts.follow:
        cmd.append('-f')

    # WARNING: os.popen() is deprecated.  However, it works.
    proc = os.popen(' '.join(cmd + args))

    # 
    config = parseconfig(CONFIG)
    config.update( dict(
            ignore=opts.ignore,
            ) )
    
    # Sep 13 13:13:54 hostname procname 123:
    linepat = re.compile('(... .. \S+) (\S+) (.+?:) (.+)')
    try:
        last = None
        pause_secs = 5
        while 1:
            line = proc.readline()
            if not line:
                break
            info = linepat.match(line)
            rest = line.strip()
            if info:
                rest = info.group(4)
                if should_ignore_proc(config, info.group(3)):
                    continue
            if last and time.time()-last > pause_secs:
                print
                print '-'*20, int(time.time()-last), 'sec'
                print
            last = time.time()
            # print colored(timestamp,attrs=['underline']),
            # print colored(procname,'yellow'),
            msg = annotate(config, rest)
            if msg:
                print msg

    except KeyboardInterrupt:
        pass


def main():
    parser = optparse.OptionParser()
    parser.add_option("-f", dest="follow", action="store_const",
                      const=True, help="follow file")
    parser.add_option('--ignore', dest="ignore", default='',
                      help="ignore lines with pattern")
    (options, args) = parser.parse_args()
    return watchstuff(options, args)

if __name__=='__main__':
    main()
    
