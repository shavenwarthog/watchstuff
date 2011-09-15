all:

test:
	egrep json json.log | ./watchstuff.py -

ltest:
	./watchstuff.py 

install:
	test -d env || virtualenv --distribute env
	env/bin/python setup.py install

