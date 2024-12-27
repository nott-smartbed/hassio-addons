FROM python:3.10-slim

# Cài đặt các thư viện Python cần thiết
RUN pip install --no-cache-dir \
    requests
RUN pip install pyserial

# Sao chép mã ứng dụng vào container
COPY main.py /main.py
COPY src /src
#COPY options.json /data/options.json
# Chạy script Python
CMD ["python", "/run.py"]