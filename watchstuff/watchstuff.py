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
# ignore: postfix CRON ntpd apid_stat.py pdns_recursor

# ignore lines with this regular expression pattern:
#ignore_pat: elasticd.+
# ignore_pat: lib/python
ignore_pat: py

# colorize words:
colori: error,white,on_red
colori: warning,red

# colorize patterns:
# color_pat:
#  client,bold
#  Message.+as dev\S+,underline

# can repeat:
# color_pat:
#  smtp_reply.+?]]],bold

# Munin timestamp
# color_pat:
#  ..../../..-..:..:..,underline
#  INFO,bold
#  ERROR,red
#  entropy,black,on_yellow
'''


def parseconfig(configstr):
    par = ConfigParser.SafeConfigParser()
    par.readfp( StringIO.StringIO(configstr) )
    return dict(par.items('default'))


def should_ignore(config, line):
    ignore_str = config.get('ignore', None)
    if ignore_str:
        ignore = re.compile(
            r'\b('
            + r'|'.join(ignore_str.split())
            + r')\b')
        m = ignore.search(line)
        if m is not None:
            return True
    ignore_str = config.get('ignore_pat', None)
    if ignore_str:
        pats = '|'.join(ignore_str.split())
        return bool( re.search(r'(' + pats + r')\b', line) )
    return False

from nose.tools import eq_
def test_should_ignore():
    conf = dict(ignore='bogus')
    eq_( should_ignore(conf, 'tasty'), False )
    eq_( should_ignore(conf, 'this bogus line'), True )

    conf = dict(ignore_pat='g.+s')
    eq_( should_ignore(conf, 'tasty'), False )
    eq_( should_ignore(conf, 'this bogus line'), True )
    eq_( should_ignore(conf, 'squishbogus'), True )
    eq_( should_ignore(conf, 'guff'), False )

                      
    

# def should_ignore(config, msg):
#     ignore_str = config.get('ignore')
#     if not ignore_str:
#         return False
#     ignore_pat = re.compile(r'('+ignore_str+r')')
#     return ignore_pat.search(msg) != False


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
    for colorpat in filter(None, config.get('color_pat','').split('\n')):
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

    # TODO: move to external config file
    config = parseconfig(CONFIG)
    config.update( dict(
            ignore=opts.ignore,
            ) )
    
    # Sep 13 13:13:54 hostname procname 123:
    # date_pat = '(... .. \S+) (\S+) (.+?:) (.+)'
    # [12/Nov/2012 09:55:35] WARNING [django.request:142 get_response] ...
    date_pat = re.compile(
        '\['
        '(?P<timestamp>	\S+ [0-9:]{8})\] \s+'
        '(?P<rest>	.+)',
        re.VERBOSE)
    

    try:
        last = None
        pause_secs = 5
        while 1:
            line = proc.readline()
            if not line:
                break
            info = date_pat.match(line)
            rest = line.strip()
            if info:
                rest = info.group('rest')
                # if should_ignore_proc(config, info.group(3)):
                #     continue
            else:
                if opts.verbose:
                    print '?',line.rstrip()
                    continue
            if last and time.time()-last > pause_secs:
                print
                print '-'*20, int(time.time()-last), 'sec'
                print
            last = time.time()
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
    parser.add_option('-v', '--verbose', dest="verbose", action='store_true',
                      help="output nonmatched lines")
    (options, args) = parser.parse_args()
    return watchstuff(options, args)

if __name__=='__main__':
    main()
    
