$(call _assert_var,MAKEDIR)
$(call _conditional_include,$(MAKEDIR)/base.mk)
$(call _assert_var,UNAME_OS2)
$(call _assert_var,UNAME_ARCH)
$(call _assert_var,CACHE_VERSIONS)
$(call _assert_var,CACHE_BIN)

TPARSE_VERSION ?= 0.13.1

TPARSE := $(CACHE_VERSIONS)/tparse/$(TPARSE_VERSION)
$(TPARSE):
	rm -f $(CACHE_BIN)/tparse
	mkdir -p $(CACHE_BIN)
	$(eval TMP := $(shell mktemp -d))
	curl -sSL https://github.com/mfridman/tparse/releases/download/v$(TPARSE_VERSION)/tparse_$(UNAME_OS2)_$(UNAME_ARCH) > $(CACHE_BIN)/tparse
	chmod +x $(CACHE_BIN)/tparse
	rm -rf $(dir $(TPARSE))
	mkdir -p $(dir $(TPARSE))
	touch $(TPARSE)
