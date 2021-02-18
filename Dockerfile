FROM ubuntu:18.04
ARG VERSION=master
ARG TARGET=esp32
ARG TAG=1.13

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
  && apt-get install -y nano gcc git wget zip make libncurses-dev flex bison gperf libffi-dev python-dev python3 python3-venv python3-pip python-pip python-serial python3-pyparsing mc libtool-bin esptool usbutils \
  && pip install --upgrade pip \
  && pip install pyparsing==2.3.1 ecdsa==0.16 esptool pyelftools>=0.25 virtualenv==16.7.10 \
  && pip3 install pyparsing==2.3.1 pyelftools virtualenv==16.7.10 adafruit-ampy

# Avoid ascii errors when reading files in Python
RUN apt-get install -y locales && locale-gen en_US.UTF-8
ENV LANG='en_US.UTF-8' LANGUAGE='en_US:en' LC_ALL='en_US.UTF-8'
  
WORKDIR /esp32/micropython
#RUN git clone --progress --verbose https://github.com/micropython/micropython.git .
RUN git clone -b tve --progress --verbose https://github.com/tve/micropython.git .
RUN git submodule update --init --recursive
  
WORKDIR /esp32/ESP-IDF
RUN git clone --progress --verbose https://github.com/espressif/esp-idf.git . \
    && git checkout 463a9d8b7f9af8205222b80707f9bdbba7c530e1 \
    && git submodule update --init --recursive
ENV ESPIDF=/esp32/ESP-IDF

WORKDIR /esp32/micropython/ports/esp32
RUN python3 -m venv build-venv
RUN /bin/bash -c "source build-venv/bin/activate"
RUN pip install --upgrade pip
RUN pip install -r ${ESPIDF}/requirements.txt

WORKDIR /esp32/ESP-IDF
RUN ./install.sh

WORKDIR /esp32/micropython
RUN make ${MAKEOPTS} -j8 -C mpy-cross

WORKDIR /esp32/micropython/ports/esp32
RUN /bin/bash -c "source ${ESPIDF}/export.sh && make submodules && make V=1 -j8"
  
# WORKDIR /esp32/micropython/ports/${TARGET}/build-GENERIC
# RUN zip -r -j ${TARGET}_v.${TAG}_$(date +%d%m%Y).zip *.bin *.elf

# Copy my code into container
WORKDIR /esp32
COPY imlib /esp32/imlib

WORKDIR /esp32/imlib
RUN /bin/bash -c "source ${ESPIDF}/export.sh"
RUN make V=1 -C cc1101
ENV AMPY_PORT=/dev/ttyUSB0