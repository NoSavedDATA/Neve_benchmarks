CXX := clang++-21
LLVM_CONFIG ?= llvm-config-21
NEVE_ROOT ?= $(abspath $(NEVE_LIBS)/..)
CXXFLAGS := -std=c++17 -O2 -fPIC -I$(NEVE_ROOT)/src $(shell $(LLVM_CONFIG) --cxxflags)
SOURCES := $(shell find src -name '*.cpp')
OBJECTS := $(SOURCES:src/%.cpp=obj/%.o)
.PHONY: all
all: lib.so
obj/%.o: src/%.cpp
	@mkdir -p $(dir $@)
	$(CXX) $(CXXFLAGS) -MMD -MP -c $< -o $@
lib.so: $(OBJECTS)
	$(CXX) -shared $(OBJECTS) -o $@
-include $(OBJECTS:.o=.d)
