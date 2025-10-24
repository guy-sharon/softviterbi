CC = gcc

#if debug dont optimize
ifeq ($(DEBUG), 1)
	CFLAGS += -march=native -O0 -g
else
	CFLAGS += -Wall -march=native -Ofast -Wfatal-errors 
endif

TARGET = softviterbi
PYTHON = python3
WHEEL_TEST_ENV = wheel_test_venv
UNITTEST_VENV = tests/venv

ifeq ($(OS),Windows_NT)
	SHELL := cmd.exe
	RM = del /Q
	RMDIR = rmdir /S /Q
	MOVE = move /y
	DEVNULL = nul
	LIBRARY_TARGET = $(TARGET).dll
	ACTIVATE_TEST_VENV = .\$(WHEEL_TEST_ENV)\Scripts\activate
	ACTIVATE_UNITTEST_GENERATION_VENV = .\$(UNITTEST_VENV)\Scripts\activate
	EXE = .exe
	SEP=\\
	PYTHON_FROM_VENV = $(SEP)Scripts$(SEP)python$(EXE)
	PYTHON := call $(shell where python3 2>nul || where py -3 2>nul || where python 2>nul || where py 2>nul)
else
	RM = rm -f
	RMDIR = rm -rf
	MOVE = mv
	DEVNULL = /dev/null
	LIBRARY_TARGET = lib$(TARGET).so
	ACTIVATE_TEST_VENV = . $(WHEEL_TEST_ENV)/bin/activate
	ACTIVATE_UNITTEST_GENERATION_VENV = . $(UNITTEST_VENV)/bin/activate
	EXE =
	SEP=/
	PYTHON_FROM_VENV = $(SEP)bin$(SEP)python$(EXE)
endif

PYTHON_PACKAGE_DIR = python_package
PYTHON_PACKAGE_LIB = $(PYTHON_PACKAGE_DIR)$(SEP)$(TARGET)$(SEP)$(LIBRARY_TARGET)
SETUP_PY = $(PYTHON_PACKAGE_DIR)$(SEP)setup.py
UNITTEST_TARGET = $(TARGET)_unittest$(EXE)

BOLD_TEXT := \033[1m
RESET_TEXT := \033[0m

all: $(TARGET)

$(TARGET): main.c
	$(CC) $(CFLAGS) -o $@ $^

lib: main.c
	$(CC) $(CFLAGS) -Wno-unused-function -shared -fPIC -DASLIB -o $(LIBRARY_TARGET) $^

generate_unittest:
	-$(RMDIR) $(UNITTEST_VENV)
	$(PYTHON) -m venv $(UNITTEST_VENV)
	$(ACTIVATE_UNITTEST_GENERATION_VENV) && pip install -r tests/requirements.txt
	$(UNITTEST_VENV)$(PYTHON_FROM_VENV) tests/generate_unittest.py

unittest:
	$(CC) $(CFLAGS) -DUNITTEST -o $(UNITTEST_TARGET) main.c

test: unittest
	./$(UNITTEST_TARGET)

wheel: lib
	$(MOVE) $(LIBRARY_TARGET) $(PYTHON_PACKAGE_LIB)
	$(PYTHON) -m pip show setuptools >$(DEVNULL) 2>&1 || $(PYTHON) -m pip install setuptools >$(DEVNULL)
	cd $(PYTHON_PACKAGE_DIR) && $(PYTHON) setup.py bdist_wheel -d . >$(DEVNULL)
	-$(RMDIR) build $(TARGET).egg-info
	$(MOVE) $(PYTHON_PACKAGE_DIR)$(SEP)*.whl .
	cd $(PYTHON_PACKAGE_DIR) && rm -rf dist build *.egg-info

test_python: wheel
	-$(RMDIR) $(WHEEL_TEST_ENV)
	$(PYTHON) -m venv $(WHEEL_TEST_ENV)
	$(ACTIVATE_TEST_VENV) && \
	$(WHEEL_TEST_ENV)$(PYTHON_FROM_VENV) -m pip install --find-links=. $(TARGET) && \
	$(WHEEL_TEST_ENV)$(PYTHON_FROM_VENV) tests$(SEP)unittest.py

test_all: test test_python
	@$(MAKE) -s clean >$(DEVNULL) 2>&1


help:
	@echo "softviterbi make commands:"
	@echo "\tmake\t\t\t\tmakes $(BOLD_TEXT)$(TARGET)$(RESET_TEXT) executable"
	@echo "\tmake lib\t\t\tmakes $(BOLD_TEXT)$(LIBRARY_TARGET)$(RESET_TEXT)"
	@echo "\tmake generate_unittest\t\tmakes $(BOLD_TEXT)unittest.c$(RESET_TEXT) and $(BOLD_TEXT)unittest.py$(RESET_TEXT) (may take a few minutes)"
	@echo "\tmake unittest\t\t\tcompiles $(BOLD_TEXT)unittest.c$(RESET_TEXT)"
	@echo "\tmake test\t\t\truns $(BOLD_TEXT)$(UNITTEST_TARGET)$(RESET_TEXT)"
	@echo "\tmake wheel\t\t\tmakes $(TARGET) python package's $(BOLD_TEXT)wheel file$(RESET_TEXT)"
	@echo "\tmake test_python\t\ttests the python package"
	@echo "\tmake test_all\t\t\truns all available tests"
	@echo "\tmake clean\t\t\tcleans extra files"
	@echo "\tmake help\t\t\tdisplays this message"

clean:
	-$(RM) $(TARGET) $(TARGET).exe $(TARGET)_unittest* $(LIBRARY_TARGET)
	-$(RMDIR) dist build *.egg-info tests$(SEP)venv $(WHEEL_TEST_ENV)
	-$(RM) $(TARGET)*.whl $(LIBRARY_TARGET) $(PYTHON_PACKAGE_LIB)
	-$(RMDIR) $(PYTHON_PACKAGE_DIR)$(SEP)$(TARGET).egg-info
	-$(RM) $(PYTHON_PACKAGE_DIR)$(SEP)*.whl 
	-$(RMDIR) $(PYTHON_PACKAGE_DIR)$(SEP)$(TARGET)$(SEP)__pycache__