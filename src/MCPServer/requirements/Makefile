.PHONY: all check clean

upgrade_flag = #-U

objects = $(wildcard *.in)
outputs := $(objects:.in=.txt)

all: $(outputs)

%.txt: %.in
	pip-compile -v $(upgrade_flag) --output-file $@ $<

test.txt: base.txt

dev.txt: test.txt

production.txt: base.txt

check:
	@which pip-compile > /dev/null

clean: check
	- rm *.txt
