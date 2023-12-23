FROM python:3.12-bookworm

USER root

# [Optional] Uncomment this section to install additional OS packages.
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends sudo libgl1-mesa-dev ghostscript python3-tk

RUN groupadd -g 1000 developer && \
    useradd -u 1000 -g developer -G sudo -m -s /bin/bash vscode && \
    echo 'vscode:password' | chpasswd && \
    echo 'Defaults visiblepw'               >> /etc/sudoers && \
    echo 'vscode ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

RUN \
    mkdir -p /workspace/.venv \

USER vscode

ENV PATH /home/vscode/.local/bin:$PATH

WORKDIR /home/vscode

RUN pip3 --disable-pip-version-check --no-cache-dir install poetry

# 現在のプロジェクトディレクトリのしたにvenv環境を作る。.venvの下に作られる。
RUN poetry config virtualenvs.in-project true
