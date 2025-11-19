from python:3.11-slim as builder

run apt-get update && apt-get install -y \
    build-essential nasm yasm pkg-config curl
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
    && make install

from python:3.11-slim

copy --from=builder /opt/ffmpeg /usr/local
run ldconfig

workdir /app

run mkdir -p data media media_nightly core/IO core/data_access core/analysis wheelhouse
copy . .

run --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir --find-links wheelhouse \
    --no-index -r requirements.txt \
    && rm -rf wheelhouse \
    && rm requirements.txt

cmd ["python", "core/IO/main.py"]