SHELL = /bin/bash

project_dependencies ?= $(addprefix $(project_root)/, cltl-requirements \
    cltl-combot \
    cltl-face-recognition \
    cltl-mention-detection \
    cltl-emissor-data \
    emissor)

git_remote ?= https://github.com/leolani

include util/make/makefile.base.mk
include util/make/makefile.py.base.mk
include util/make/makefile.git.mk
include util/make/makefile.component.mk
