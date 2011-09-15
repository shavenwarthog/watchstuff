all:

sync:
	rsync -av --exclude=.git \
	. dev6-md2.sendgrid.net:checkout/watchstuff

test:
	egrep json json.log | ./watchstuff.py -

ltest:
	./watchstuff.py 

rtest: sync
	ssh $(HOST) make -C checkout/watchstuff ltest

install:
	virtualenv --distribute env
	. env/bin/activate ; python setup.py install

