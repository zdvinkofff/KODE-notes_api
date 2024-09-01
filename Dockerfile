# ���������� ����������� ����� Python � �������� ��������
FROM python: 3.10.8

# ������������� ������� ���������� � ����������
WORKDIR /app

# �������� ����� requirements.txt � ������������� �����������
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# �������� ��� ����� ���������� � ������� ����������
COPY . .

# ������� ������� Uvicorn �������
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]