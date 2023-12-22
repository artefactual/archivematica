$(call _assert_var,PROJECT)

UNAME_OS := $(shell uname -s)
UNAME_OS2 := $(shell echo $(UNAME_OS) | tr A-Z a-z)

UNAME_ARCH := $(shell uname -m)
UNAME_ARCH2 := $(UNAME_ARCH)
ifeq ($(UNAME_ARCH),x86_64)
UNAME_ARCH2 := amd64
endif

CACHE_BASE ?= $(HOME)/.cache/$(PROJECT)
CACHE := $(CACHE_BASE)/$(UNAME_OS)/$(UNAME_ARCH)
CACHE_BIN := $(CACHE)/bin
CACHE_VERSIONS := $(CACHE)/versions
CACHE_GOBIN := $(CACHE)/gobin
CACHE_GOCACHE := $(CACHE)/gocache

export PATH := $(abspath $(CACHE_BIN)):$(PATH)
