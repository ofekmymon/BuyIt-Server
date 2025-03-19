Set-ExecutionPolicy Unrestricted -Scope Process
venv\Scripts\activate
uvicorn server:app --reload
 Set-ExecutionPolicy Default -Scope Process
