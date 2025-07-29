FROM nvidia/cuda:12.9.1-base-ubuntu24.04

COPY . /app

RUN apt-get update && \
    apt-get install -y --allow-unauthenticated --no-install-recommends \
    wget \
    git \
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

ENV HOME="/root"
ENV CONDA_DIR="${HOME}/miniconda"
ENV PATH="$CONDA_DIR/bin":$PATH
ENV CONDA_AUTO_UPDATE_CONDA=false
ENV PIP_DOWNLOAD_CACHE="$HOME/.pip/cache"
ENV TORTOISE_MODELS_DIR="$HOME/tortoise-tts/build/lib/tortoise/models"

RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda3.sh \
    && bash /tmp/miniconda3.sh -b -p "${CONDA_DIR}" -f -u \
    && "${CONDA_DIR}/bin/conda" init bash \
    && rm -f /tmp/miniconda3.sh \
    && echo ". '${CONDA_DIR}/etc/profile.d/conda.sh'" >> "${HOME}/.profile"

# --login option used to source bashrc (thus activating conda env) at every RUN statement
SHELL ["/bin/bash", "--login", "-c"]

RUN conda tos accept \
    && conda create --name tortoise python=3.13.5 numba inflect -y \ 
    && conda activate tortoise \
    && conda install --yes conda-forge::pytorch==2.7.1 conda-forge::torchaudio=2.7.1 pytorch-cuda -c pytorch -c nvidia \
    && conda install --yes conda-forge::torchvision=0.22.0 \
    && conda install --yes conda-forge::transformers=4.53.3 \
    && cd /app \
    && python setup.py install
