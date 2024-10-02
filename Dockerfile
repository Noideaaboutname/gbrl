##############################################################################
# Copyright (c) 2024, NVIDIA Corporation. All rights reserved.
#
# This work is made available under the Nvidia Source Code License-NC.
# To view a copy of this license, visit
# https://nvlabs.github.io/gbrl_sb3/license.html
#
##############################################################################
# FROM nvcr.io/nvidian/pytorch:23.11-py3 as base
FROM nvcr.io/nvidia/cuda:12.5.1-devel-ubuntu20.04 as base
# FROM nvcr.io/nvidia/cuda:12.5.1-devel-rockylinux8 as base
RUN apt-get update
RUN DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get -y install tzdata
RUN apt-get install ffmpeg libsm6 libxext6 libxrender-dev -y
RUN apt-get install libosmesa6-dev libgl1-mesa-glx libglfw3 -y

# Install wget and other dependencies
RUN apt-get update && \
    apt-get install -y wget && \
    apt-get install -y unzip && \
    apt-get install -y swig && \
    apt-get install -y curl && \
    apt-get install -y patchelf && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update 

RUN apt-get install python3.9 python3.9-dev -y && \
    apt-get install python3.10 python3.10-dev -y && \
    apt-get install python3.11 python3.11-dev -y && \
    apt-get install -y python3.9-distutils python3.10-distutils python3.11-distutils && \ 
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \ 
    python3.9 get-pip.py && \ 
    python3.10 get-pip.py && \ 
    python3.11 get-pip.py 

RUN apt install git-all -y

WORKDIR /
RUN git clone https://github.com/NVlabs/gbrl.git
WORKDIR /gbrl





