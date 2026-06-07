# library-service

How to run library-service

Assuming you have Docker Desktop installed (if not, download it from docker.com), here are the steps:

1. Make sure Docker Desktop is running
Open Docker Desktop and wait for it to say "Engine running".
2. Unzip the project
Check out the library-service

4. Open a terminal in that folder
 cmd  ~/Desktop/library-service
5. Start everything
   docker compose up --build

This will take 2–3 minutes the first time (downloading images, installing dependencies). You'll see logs from three services: db, backend, and frontend.
5. Wait for this line in the logs
library_backend  | INFO:     Application startup complete.
That means the API is ready.
6. Open the app

Frontend UI → http://localhost:3000
API docs (Swagger) → http://localhost:8000/docs

7. To stop everything
Press Ctrl + C in the terminal, then:
bashdocker compose down
