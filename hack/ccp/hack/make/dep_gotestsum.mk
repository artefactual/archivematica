$(call _assert_var,MAKEDIR)
$(call _conditional_include,$(MAKEDIR)/base.mk)
$(call _assert_var,UNAME_OS2)
$(call _assert_var,UNAME_ARCH2)
$(call _assert_var,CACHE_VERSIONS)
$(call _assert_var,CACHE_BIN)

GOTESTSUM_VERSION ?= 1.11.0

GOTESTSUM := $(CACHE_VERSIONS)/gotestsum/$(GOTESTSUM_VERSION)
$(GOTESTSUM):
	rm -f $(CACHE_BIN)/gotestsum
	mkdir -p $(CACHE_BIN)
	$(eval TMP := $(shell mktemp -d))
	curl -sSL \
		https://github.com/gotestyourself/gotestsum/releases/download/v$(GOTESTSUM_VERSION)/gotestsum_$(GOTESTSUM_VERSION)_$(UNAME_OS2)_$(UNAME_ARCH2).tar.gz \
		| tar xz -C $(TMP)
	mv $(TMP)/gotestsum $(CACHE_BIN)/
	chmod +x $(CACHE_BIN)/gotestsum
	rm -rf $(dir $(GOTESTSUM))
	mkdir -p $(dir $(GOTESTSUM))
	touch $(GOTESTSUM)
