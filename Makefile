all:

test:
	egrep json json.log | ./watchstuff.py -

ltest:
	./watchstuff.py 

install:
	test -d env || virtualenv --distribute env
	env/bin/python setup.py install
	env/bin/watchstuff test.log

clean:
	-$(RM) -rf env/ *.egg-info


