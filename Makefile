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

ifeq ($(OS),Windows_NT)
	SHELL := cmd.exe
	RM = del /Q
	RMDIR = rmdir /S /Q
	COPY = copy
	DEVNULL = nul
	LIBRARY_TARGET = $(TARGET).dll
	ACTIVATE_TEST_VENV = .\$(WHEEL_TEST_ENV)\Scripts\activate
	EXE = .exe
	SEP=\\
	PYTHON := call $(shell where python3 2>nul || where py -3 2>nul || where python 2>nul || where py 2>nul)
else
	RM = rm -f
	RMDIR = rm -rf
	COPY = cp
	DEVNULL = /dev/null
	LIBRARY_TARGET = lib$(TARGET).so
	EXE =
	ACTIVATE_TEST_VENV = . $(WHEEL_TEST_ENV)/bin/activate
	SEP=/
endif

PYTHON_PACKAGE_DIR = python_package
DIST_DIR = $(PYTHON_PACKAGE_DIR)$(SEP)dist
BUILD_DIR = $(PYTHON_PACKAGE_DIR)$(SEP)build
EGG_INFO_DIR = $(PYTHON_PACKAGE_DIR)$(SEP)$(TARGET).egg-info
PYTHON_PACKAGE_LIB = $(PYTHON_PACKAGE_DIR)$(SEP)$(TARGET)$(SEP)$(LIBRARY_TARGET)
SETUP_PY = $(PYTHON_PACKAGE_DIR)$(SEP)setup.py
UNITTEST_TARGET = $(TARGET)_unittest$(EXE)

all: $(TARGET)

$(TARGET): main.c
	$(CC) $(CFLAGS) -o $@ $^

lib: main.c
	$(CC) $(CFLAGS) -Wno-unused-function -shared -fPIC -DASLIB -o $(LIBRARY_TARGET) $^

generate_unittest:
	
	$(PYTHON) tests/generate_unittest.py

unittest:
	$(CC) $(CFLAGS) -DUNITTEST -o $(UNITTEST_TARGET) main.c

test: unittest
	./$(UNITTEST_TARGET)

test_all: test test_python_pkg
	@$(MAKE) -s clean >$(DEVNULL) 2>&1

wheel: lib
	$(COPY) $(LIBRARY_TARGET) $(PYTHON_PACKAGE_LIB)
	$(PYTHON) -m pip show setuptools >$(DEVNULL) 2>&1 || $(PYTHON) -m pip install setuptools >$(DEVNULL)
	$(PYTHON) $(SETUP_PY) bdist_wheel -d . >$(DEVNULL)
	$(RMDIR) build $(TARGET).egg-info
	cd $(PYTHON_PACKAGE_DIR) && rm -rf dist build *.egg-info

test_python_pkg: wheel
	$(PYTHON) -m venv $(WHEEL_TEST_ENV)
	$(ACTIVATE_TEST_VENV) && \
	$(PYTHON) -m pip install --find-links=. $(TARGET) --quiet && \
	$(PYTHON) $(PYTHON_PACKAGE_DIR)$(SEP)example.py
	$(RMDIR) $(WHEEL_TEST_ENV)

clean:
	-$(RM) $(TARGET) $(TARGET).exe $(TARGET)_unittest* $(LIBRARY_TARGET)
	-$(RMDIR) $(DIST_DIR) $(BUILD_DIR) $(EGG_INFO_DIR) tests$(SEP)venv
	-$(RM) $(TARGET)*.whl $(LIBRARY_TARGET) $(PYTHON_PACKAGE_LIB)