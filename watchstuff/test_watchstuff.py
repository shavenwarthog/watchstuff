def test_parseconfig():
    conf = parseconfig('''
[default]
colori: a,b
colori: c,d
''')
    eq_(conf, {'colori':'c,d'})            # latest
    conf = parseconfig('''
[default]
colori:
  a,b
  c,d
''')
    eq_(conf, {'colori': '\na,b\nc,d'}) # all, with newlines


def test_ignore():
    conf = dict(ignore='bogus')
    eq_( should_ignore(conf, 'tasty'), (False,False) )
    eq_( should_ignore(conf, 'this bogus line'), (True,False) )


def test_ignore_pat():
    conf = dict(ignore_pat='g.+s')
    eq_( should_ignore(conf, 'tasty'), (False,False) )
    eq_( should_ignore(conf, 'this bogus line'), (True,False) )
    eq_( should_ignore(conf, 'squishbogus'), (True,False) )
    eq_( should_ignore(conf, 'guff'), (False,False) )


def test_ignore_twoline():
    conf = dict(ignore_twoline='python')
    eq_( should_ignore(conf, 'beer'), (False,False) )
    eq_( should_ignore(conf, '/python2'), (True,True) )

                      
def test_do_color():    
    conf = {'color': '\na,white\nc,red,on_yellow'} # all, with newlines
    eq_( do_color(conf, 'apple beer cider'),
         '\x1b[37ma\x1b[0mpple beer \x1b[43m\x1b[31mc\x1b[0mider',
         )


