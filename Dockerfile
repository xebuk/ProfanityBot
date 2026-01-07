from python:3.13-slim as builder

run apt-get update && apt-get install -y --no-install-recommends \
    build-essential nasm yasm pkg-config curl \
    && rm -rf /var/lib/apt/lists/*

run curl -fsSL https://ffmpeg.org/releases/ffmpeg-8.0.tar.gz | tar -xz && \
    cd ffmpeg-8.0 && \
    ./configure \
        --prefix=/opt/ffmpeg \
        --disable-everything \
        --enable-demuxer=mov,mp4,matroska,avi,ogg \
        --enable-decoder=aac,mp3,ac3,pcm_s16le,pcm_f32le,vorbis,opus \
        --enable-muxer=wav \
        --enable-encoder=pcm_s16le \
        --enable-protocol=file,pipe \
        --enable-filter=aresample,anull \
        --enable-parser=aac,mpegaudio,vorbis,opus \
        --disable-doc \
        --enable-small \
        --enable-static \
        --disable-shared \
    && make -j$(nproc) \
    && make install \
    && cd / \
    && rm -rf /ffmpeg-8.0 \
    && apt-get purge -y --auto-remove build-essential nasm yasm pkg-config curl \
    && apt-get clean

copy requirements.txt .
run --mount=type=cache,target=/root/.cache/pip \
    pip install --prefix=/opt/pip -r requirements.txt

from python:3.13-slim

copy --from=builder /opt/ffmpeg /usr/local
copy --from=builder /opt/pip /usr/local
run ldconfig

workdir /app

copy . .

cmd ["python", "core/main.py"]