$(call _assert_var,MAKEDIR)
$(call _conditional_include,$(MAKEDIR)/base.mk)
$(call _assert_var,UNAME_OS)
$(call _assert_var,UNAME_ARCH)
$(call _assert_var,CACHE_VERSIONS)
$(call _assert_var,CACHE_BIN)

GOENUM_VERSION ?= 0.6.0

GOENUM := $(CACHE_VERSIONS)/go-enum/$(GOENUM_VERSION)
$(GOENUM):
	rm -f $(CACHE_BIN)/go-enum
	mkdir -p $(CACHE_BIN)
	curl -sSL \
		https://github.com/abice/go-enum/releases/download/v$(GOENUM_VERSION)/go-enum_$(UNAME_OS)_$(UNAME_ARCH) \
		> $(CACHE_BIN)/go-enum
	chmod +x $(CACHE_BIN)/go-enum
	rm -rf $(dir $(GOENUM))
	mkdir -p $(dir $(GOENUM))
	touch $(GOENUM)
