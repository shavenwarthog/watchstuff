all:	reinstall

reinstall: install

test:
	egrep json json.log | ./watchstuff.py -

ltest:
	./watchstuff.py 

install:
	test -d env || virtualenv --distribute env
	env/bin/python setup.py install
	@echo
	env/bin/watchstuff test.log

clean:
	-$(RM) -rf env/ *.egg-info build/
distclean: clean
	-$(RM) -rf dist/

DEVHOST := dev6-md2.sendgrid.net
sync:
	rsync -av --exclude=.git --exclude=env --exclude=build \
	--exclude=*.egg-info \
	. $(DEVHOST):checkout/watchstuff

rinstall: sync
	ssh $(DEVHOST) make -C checkout/watchstuff reinstall

clean:
	-$(RM) fn_[0-9]*.py

