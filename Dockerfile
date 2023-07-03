FROM docker.io/library/python:3.10 AS poetry-exporter

WORKDIR /work

RUN python -m pip install poetry

COPY pyproject.toml pyproject.toml
COPY poetry.lock poetry.lock

RUN poetry export -o requirements.txt

# adapted from https://github.com/stereolabs/zed-docker/blob/master/3.X/l4t/py-runtime/Dockerfile
# https://hub.docker.com/r/stereolabs/zed

# https://ngc.nvidia.com/catalog/containers/nvidia:l4t-base
FROM nvcr.io/nvidia/l4t-base:r32.6.1

# I have had issues with the camera not connecting on newer JetPack versions
ENV L4T_MAJOR_VERSION=32
ENV L4T_MINOR_VERSION=6
ENV L4T_PATCH_VERSION=1
ENV ZED_SDK_MAJOR=3
ENV ZED_SDK_MINOR=7

# Latest supported version by the ZED SDK
ENV PYTHON_VERSION=3.10

ENV DEBIAN_FRONTEND=noninteractive

# Fix numpy issues
ENV OPENBLAS_CORETYPE=AARCH64

# Install Python newer than 3.6
# https://github.com/deadsnakes/issues/issues/251
WORKDIR /work/
RUN apt-get update -y
RUN apt-get install -y tzdata curl ca-certificates
RUN curl -L -O https://github.com/bellflight/AVR-Python-arm-deb/releases/download/release/libpython3.10-minimal_3.10.11-1+bionic1_arm64.deb \
 && curl -L -O https://github.com/bellflight/AVR-Python-arm-deb/releases/download/release/libpython3.10-stdlib_3.10.11-1+bionic1_arm64.deb \
 && curl -L -O https://github.com/bellflight/AVR-Python-arm-deb/releases/download/release/python3.10-distutils_3.10.11-1+bionic1_all.deb \
 && curl -L -O https://github.com/bellflight/AVR-Python-arm-deb/releases/download/release/python3.10-lib2to3_3.10.11-1+bionic1_all.deb \
 && curl -L -O https://github.com/bellflight/AVR-Python-arm-deb/releases/download/release/python3.10-minimal_3.10.11-1+bionic1_arm64.deb \
 && curl -L -O https://github.com/bellflight/AVR-Python-arm-deb/releases/download/release/python3.10_3.10.11-1+bionic1_arm64.deb
RUN dpkg -i libpython3.10-minimal_3.10.11-1+bionic1_arm64.deb \
 && dpkg -i libpython3.10-stdlib_3.10.11-1+bionic1_arm64.deb \
 && dpkg -i python3.10-lib2to3_3.10.11-1+bionic1_all.deb \
 && dpkg -i python3.10-distutils_3.10.11-1+bionic1_all.deb \
 && dpkg -i python3.10-minimal_3.10.11-1+bionic1_arm64.deb \
 && dpkg -i python3.10_3.10.11-1+bionic1_arm64.deb \
 && rm *.deb
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python${PYTHON_VERSION} \
 && python${PYTHON_VERSION} -m pip install pip wheel setuptools --upgrade
# I understand this is bad to do, but the ZEDSDK installs a bunch of
# packages into `python3`, so setting this to our desired version reduces
# duplicate installs
RUN rm /usr/bin/python3 && ln -s /usr/bin/python${PYTHON_VERSION} /usr/bin/python3

# This environment variable is needed to use the streaming features on Jetson inside a container
ENV LOGNAME root

RUN apt-get install --no-install-recommends lsb-release wget less udev sudo apt-transport-https zstd -y \
 && echo "# R${L4T_MAJOR_VERSION} (release), REVISION: ${L4T_MINOR_VERSION}.${L4T_PATCH_VERSION}" > /etc/nv_tegra_release ; \
 wget -q https://download.stereolabs.com/zedsdk/${ZED_SDK_MAJOR}.${ZED_SDK_MINOR}/l4t${L4T_MAJOR_VERSION}.${L4T_MINOR_VERSION}/jetsons -O ZED_SDK_Linux.run \
 && chmod +x ZED_SDK_Linux.run ; ./ZED_SDK_Linux.run silent runtime_only \
 && rm -rf /usr/local/zed/resources/* \
 && rm -rf ZED_SDK_Linux.run \
 && apt-get remove --purge build-essential -y \
 && apt-get autoremove -y \
 && rm -rf /var/lib/apt/lists/*

# This symbolic link is needed to use the streaming features on Jetson inside a container
RUN ln -sf /usr/lib/aarch64-linux-gnu/tegra/libv4l2.so.0 /usr/lib/aarch64-linux-gnu/libv4l2.so

WORKDIR /app

COPY --from=poetry-exporter /work/requirements.txt requirements.txt

RUN python3 -m pip install -r requirements.txt

COPY src .

CMD ["python3", "vio.py"]