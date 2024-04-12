$(call _assert_var,MAKEDIR)
$(call _conditional_include,$(MAKEDIR)/base.mk)
$(call _assert_var,CACHE_VERSIONS)
$(call _assert_var,CACHE_BIN)

SQLC_VERSION ?= 1.26.0

SQLC := $(CACHE_VERSIONS)/sqlc/$(SQLC_VERSION)
$(SQLC):
	rm -f $(CACHE_BIN)/sqlc
	mkdir -p $(CACHE_BIN)
	env GOBIN=$(CACHE_BIN) go install github.com/sqlc-dev/sqlc/cmd/sqlc@v$(SQLC_VERSION)
	chmod +x $(CACHE_BIN)/sqlc
	rm -rf $(dir $(SQLC))
	mkdir -p $(dir $(SQLC))
	touch $(SQLC)
