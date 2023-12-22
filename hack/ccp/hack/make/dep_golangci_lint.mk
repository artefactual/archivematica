$(call _assert_var,MAKEDIR)
$(call _conditional_include,$(MAKEDIR)/base.mk)
$(call _assert_var,UNAME_OS)
$(call _assert_var,UNAME_ARCH)
$(call _assert_var,CACHE_VERSIONS)
$(call _assert_var,CACHE_BIN)

GOLANGCI_LINT_VERSION ?= 1.54.2

ARCH := $(UNAME_ARCH)
ifeq ($(UNAME_ARCH),x86_64)
ARCH := amd64
endif

GOLANGCI_LINT := $(CACHE_VERSIONS)/golangci-lint/$(GOLANGCI_LINT_VERSION)
$(GOLANGCI_LINT):
	rm -f $(CACHE_BIN)/golangci-lint
	mkdir -p $(CACHE_BIN)
	$(eval TMP := $(shell mktemp -d))
	$(eval OS := $(shell echo $(UNAME_OS) | tr A-Z a-z))
	curl -sSL \
		https://github.com/golangci/golangci-lint/releases/download/v$(GOLANGCI_LINT_VERSION)/golangci-lint-$(GOLANGCI_LINT_VERSION)-$(OS)-$(ARCH).tar.gz \
		| tar xz --strip-components=1 -C $(TMP)
	mv $(TMP)/golangci-lint $(CACHE_BIN)/
	chmod +x $(CACHE_BIN)/golangci-lint
	rm -rf $(dir $(GOLANGCI_LINT))
	mkdir -p $(dir $(GOLANGCI_LINT))
	touch $(GOLANGCI_LINT)
