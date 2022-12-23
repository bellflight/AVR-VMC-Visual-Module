# adapted from https://github.com/stereolabs/zed-docker/blob/master/3.X/l4t/py-runtime/Dockerfile
# https://hub.docker.com/r/stereolabs/zed

# https://ngc.nvidia.com/catalog/containers/nvidia:l4t-base
FROM nvcr.io/nvidia/l4t-base:r35.1.0

ENV PYTHON_VERSION=3.11

ENV L4T_MAJOR_VERSION=35
ENV L4T_MINOR_VERSION=1
ENV L4T_PATCH_VERSION=0
ENV ZED_SDK_MAJOR=3
ENV ZED_SDK_MINOR=7

ENV DEBIAN_FRONTEND=noninteractive

# Fix numpy issues
ENV OPENBLAS_CORETYPE=AARCH64

# Install Python newer than 3.8
RUN apt-get update -y || true \
 && apt-get install -y ca-certificates software-properties-common && update-ca-certificates
RUN add-apt-repository ppa:deadsnakes/ppa \
 && apt-get update -y
RUN apt-get install -y \
    curl \
    python3-pip \
    python${PYTHON_VERSION} \
    python${PYTHON_VERSION}-dev \
    python${PYTHON_VERSION}-distutils \
 && curl -sS https://bootstrap.pypa.io/get-pip.py | python${PYTHON_VERSION} \
 && python${PYTHON_VERSION} -m pip install pip wheel setuptools --upgrade
# I understand this is bad to do, but the ZEDSDK installs a bunch of
# packages into `python3`, so setting this to our desired version reduces
# duplicate installs
RUN rm /usr/bin/python3 && ln -s /usr/bin/python${PYTHON_VERSION} /usr/bin/python3

# This environment variable is needed to use the streaming features on Jetson inside a container
ENV LOGNAME root

# This also installs the Python Zed package
RUN apt-get update -y && apt-get install --no-install-recommends lsb-release wget less udev sudo apt-transport-https -y \
 && echo "# R${L4T_MAJOR_VERSION} (release), REVISION: ${L4T_MINOR_VERSION}" > /etc/nv_tegra_release ; \
 wget -q -O ZED_SDK_Linux_JP.run https://download.stereolabs.com/zedsdk/${ZED_SDK_MAJOR}.${ZED_SDK_MINOR}/l4t${L4T_MAJOR_VERSION}.${L4T_MINOR_VERSION}/jetsons \
 && chmod +x ZED_SDK_Linux_JP.run ; ./ZED_SDK_Linux_JP.run silent runtime_only \
 && rm -rf /usr/local/zed/resources/* \
 && rm -rf ZED_SDK_Linux_JP.run \
 && apt-get remove --purge build-essential python${PYTHON_VERSION}-dev -y && apt-get autoremove -y \
 && rm -rf /var/lib/apt/lists/*

# This symbolic link is needed to use the streaming features on Jetson inside a container
RUN ln -sf /usr/lib/aarch64-linux-gnu/tegra/libv4l2.so.0 /usr/lib/aarch64-linux-gnu/libv4l2.so

WORKDIR /app

COPY requirements.txt requirements.txt

RUN python3 -m pip install -r requirements.txt

COPY . .

CMD ["python3", "vio.py"]
