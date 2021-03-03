FROM ubuntu:18.04
ARG VERSION=master
ARG TARGET=esp32

ARG DEBIAN_FRONTEND=noninteractive

ENV AMPY_PORT=/dev/ttyUSB0
ENV LANG='en_US.UTF-8' LANGUAGE='en_US:en' LC_ALL='en_US.UTF-8'
ENV IDF_PATH=/${TARGET}/ESP-IDF

RUN apt-get update \
  && apt-get install -y python-pip python2.7 \
  && apt-get install -y nano gcc git wget zip make libncurses-dev flex bison gperf libffi-dev python3 python3-venv python3-pip python3-pyparsing python3-setuptools mc libtool-bin esptool usbutils cmake \
  && update-alternatives --install /usr/bin/python python /usr/bin/python3 10 && alias pip=pip3 \
  && pip3 install pyparsing==2.3.1 pyelftools virtualenv==16.7.10 adafruit-ampy

# Avoid ascii errors when reading files in Python
RUN apt-get install -y locales && locale-gen en_US.UTF-8
  
WORKDIR /${TARGET}/micropython
#RUN git clone --progress --verbose https://github.com/micropython/micropython.git .
RUN git clone -b tve --progress --verbose https://github.com/tve/micropython.git .
RUN git submodule update --init --recursive
  
WORKDIR /${TARGET}/ESP-IDF
RUN git clone --progress --verbose https://github.com/espressif/esp-idf.git .
RUN git checkout 463a9d8b7f9af8205222b80707f9bdbba7c530e1
RUN git submodule update --init --recursive
RUN ./install.sh

WORKDIR /${TARGET}/micropython/ports/${TARGET}
RUN python3 -m venv build-venv
RUN /bin/bash -c "source build-venv/bin/activate"
RUN pip3 install -r ${IDF_PATH}/requirements.txt

WORKDIR /${TARGET}/micropython
RUN make ${MAKEOPTS} -j$(nproc) -C mpy-cross

WORKDIR /${TARGET}/micropython/ports/${TARGET}
RUN /bin/bash -c "source ${IDF_PATH}/export.sh && make submodules && make V=1 -j$(nproc)"
  
# WORKDIR /${TARGET}/micropython/ports/${TARGET}/build-GENERIC
# RUN zip -r -j ${TARGET}_v.${TAG}_$(date +%d%m%Y).zip *.bin *.elf

# Copy my code into container
WORKDIR /${TARGET}
COPY imlib /${TARGET}/imlib

WORKDIR /${TARGET}/imlib/cc1101
RUN /bin/bash -c "source ${IDF_PATH}/export.sh && make -j$(nproc) V=1"