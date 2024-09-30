<!-- Fast Api -->

- Please check your python version with the following command. The result should be 3.11 or higher.

python3 --version

fastapi==0.115.0
uvicorn==0.30.6
SQLAlchemy==2.0.35
pydantic==2.9.2

pip3 install -r requirements.txt

 Launch server:
 uvicorn main:app --reload

Open project in the web browser:
http://127.0.0.1:8000/docs

