ENUMS = \
	internal/store/enums/package_status_enum.go \
	internal/store/enums/package_type_enum.go \

$(ENUMS): GOENUM_FLAGS=--marshal --nocase --names --ptr --flag --sql

%_enum.go: %.go $(GOENUM) hack/make/enums.mk
	go-enum -f $*.go $(GOENUM_FLAGS)
