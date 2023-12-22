$(call _assert_var,MAKEDIR)
$(call _conditional_include,$(MAKEDIR)/base.mk)
$(call _assert_var,CACHE_VERSIONS)
$(call _assert_var,CACHE_BIN)

MOCKGEN_VERSION ?= 0.4.0

MOCKGEN := $(CACHE_VERSIONS)/mockgen/$(MOCKGEN_VERSION)
$(MOCKGEN):
	rm -f $(CACHE_BIN)/mockgen
	mkdir -p $(CACHE_BIN)
	env GOBIN=$(CACHE_BIN) go install go.uber.org/mock/mockgen@v$(MOCKGEN_VERSION)
	chmod +x $(CACHE_BIN)/mockgen
	rm -rf $(dir $(MOCKGEN))
	mkdir -p $(dir $(MOCKGEN))
	touch $(MOCKGEN)
