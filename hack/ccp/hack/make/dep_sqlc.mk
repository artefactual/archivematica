$(call _assert_var,MAKEDIR)
$(call _conditional_include,$(MAKEDIR)/base.mk)
$(call _assert_var,UNAME_OS)
$(call _assert_var,UNAME_ARCH)
$(call _assert_var,CACHE_VERSIONS)
$(call _assert_var,CACHE_BIN)

SQLC_VERSION ?= 1.24.0

ARCH := $(UNAME_ARCH)
ifeq ($(UNAME_ARCH),x86_64)
ARCH := amd64
endif

SQLC := $(CACHE_VERSIONS)/sqlc/$(SQLC_VERSION)
$(SQLC):
	rm -f $(CACHE_BIN)/sqlc
	mkdir -p $(CACHE_BIN)
	$(eval TMP := $(shell mktemp -d))
	$(eval OS := $(shell echo $(UNAME_OS) | tr A-Z a-z))
	curl -sSL \
		https://github.com/sqlc-dev/sqlc/releases/download/v$(SQLC_VERSION)/sqlc_$(SQLC_VERSION)_$(OS)_$(ARCH).tar.gz \
		| tar xvz -C $(TMP)
	ls -lha $(TMP)
	mv $(TMP)/sqlc $(CACHE_BIN)/
	chmod +x $(CACHE_BIN)/sqlc
	rm -rf $(dir $(SQLC))
	mkdir -p $(dir $(SQLC))
	touch $(SQLC)
