#!/usr/bin/env python

'''
watchstuff.py -- "tail -f" files, add tasteful color, ignore boring stuff
'''

import ConfigParser, logging, optparse, os, re, StringIO, time
# from nose.tools import eq_

# http://pypi.python.org/pypi/termcolor
from termcolor import colored 


CONFIG = r'''
[default]

# ignore lines with any of these words:
# ignore: postfix CRON ntpd apid_stat.py pdns_recursor

# ignore lines with this regular expression pattern:
#ignore_pat: elasticd.+
ignore_pat:
  raise.JSONDecodeError
ignore_pat:
  (GET|POST)
  GET.+/static/
  WARNING.+Not.Found
ignore_twoline:
  lib/python2
  /tastypie/

# colorize words:
# - colors: black red green yellow blue magenta cyan white
#
color: 
  detail,red
  INFO,yellow
  ERROR,white,on_red
  WARNING,red
  DEBUG,white,on_blue
  BEER,white,on_red
  GET,yellow,on_grey
  POST,yellow,on_grey

# colorize patterns:
# - options: bold underscore
#
color_pat:
   INFO,bold
   /views.py.+,underline
   /v1/[^?\s]+,underline
   POST,underline
   detail,bold
   error,underline
   \s4\d\d\s,red
   \s5\d\d\s,red
# can repeat:
# color_pat:
#  smtp_reply.+?]]],bold

# Munin timestamp
# color_pat:
#  ..../../..-..:..:..,underline
#  INFO,bold
#  ERROR,red
#  entropy,black,on_yellow

# shortname:
#  enterpriseapp.log=ENT
'''


logging.basicConfig(
    filename='/tmp/watchstuff.log',
    level=logging.DEBUG,
    )


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
            return True, False
    ignore_str = config.get('ignore_pat', None)
    if ignore_str:
        pats = '|'.join(ignore_str.split())
        if re.search(r'(' + pats + r')', line):
            return True, False
    ignore_str = config.get('ignore_twoline', None)
    if ignore_str:
        pats = '|'.join(ignore_str.split())
        if re.search(r'(' + pats + r')', line):
            return True, True
    return False, False


def do_color(config, msg):
    for colorpat in filter(None, config.get('color','').split('\n')):
        word,color,on_color = ( colorpat.split(',')+[None,None] )[:3]
        # pat = re.compile(word, re.IGNORECASE)
        pat = re.compile(word)
        msg = pat.sub(
            lambda match: colored(match.group(0), color, on_color),
            msg,
            )
    return msg


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
    """
    Return fixed message, and whether to ignore the next line or not
    """
    thisline,twoline = should_ignore(config, msg)
    if thisline:
        return None,twoline
    msg = do_color(config, msg)
    msg = do_colorpat(config, msg)
    return msg,False



# ::::::::::::::::::::::::::::::::::::::::::::::::::

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
    name_pat = re.compile('==>.(.+).<==')
    ignore_next = False
    try:
        last = None
        name = None
        pause_secs = 5
        while 1:
            line = proc.readline()
            if not line:
                break
            if ignore_next:
                ignore_next = False
                continue
            m = name_pat.match(line)
            if m:
                name = os.path.basename(m.group(1))
                continue
            info = date_pat.match(line)
            rest = line.rstrip()
            if info:
                rest = info.group('rest')
            else:
                if opts.verbose:
                    print '?',name,line.rstrip()
                    continue
            if last and time.time()-last > pause_secs:
                print
                print '-'*20, int(time.time()-last), 'sec'
                print
            last = time.time()
            msg,ignore_next = annotate(config, rest)
            if msg:
                if name:
                    print '{0}: {1}'.format(name,msg)
                else:
                    print msg

    except KeyboardInterrupt:
        pass


def main():
    parser = optparse.OptionParser()
    parser.add_option("--auto", action="store_true")
    parser.add_option("-f", dest="follow", action="store_const",
                      const=True, help="follow file")
    parser.add_option('--ignore', dest="ignore", default='',
                      help="ignore lines with pattern")
    parser.add_option('-v', '--verbose', dest="verbose", action='store_true',
                      help="output nonmatched lines")
    (options, args) = parser.parse_args()

    if options.auto:
        args += ['/var/log/yourevent/enterpriseapp-dev.log',
                 '/var/log/yourevent/enterpriseapp-trace.log',
                 ]

    return watchstuff(options, args)


if __name__=='__main__':
    main()
    
