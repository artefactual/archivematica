$(call _assert_var,MAKEDIR)
$(call _conditional_include,$(MAKEDIR)/base.mk)
$(call _assert_var,UNAME_OS)
$(call _assert_var,UNAME_ARCH)
$(call _assert_var,CACHE_VERSIONS)
$(call _assert_var,CACHE_BIN)

BUF_VERSION ?= 1.31.0

BUF := $(CACHE_VERSIONS)/buf/$(BUF_VERSION)
$(BUF):
	rm -f $(CACHE_BIN)/buf
	mkdir -p $(CACHE_BIN)
	$(eval TMP := $(shell mktemp -d))
	curl -sSL \
		https://github.com/bufbuild/buf/releases/download/v$(BUF_VERSION)/buf-$(UNAME_OS)-$(UNAME_ARCH).tar.gz \
			| tar xz --strip-components=1 -C $(TMP)
	mv $(TMP)/bin/buf $(CACHE_BIN)/
	mv $(TMP)/bin/protoc-gen-buf-lint $(CACHE_BIN)/
	mv $(TMP)/bin/protoc-gen-buf-breaking $(CACHE_BIN)/
	rm -rf $(dir $(BUF))
	mkdir -p $(dir $(BUF))
	touch $(BUF)
