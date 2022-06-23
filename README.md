# Department News Board
## Features
- Create, read, update, and delete news items.
- Register and log in as a user.
- Get news and download files (without auth)
- Automatic archival for news older than 30 days.

## Tech Stack
- Python 3.10 or higher.
- Nameko framework
- Docker
- PostgreSQL
- Redis
- RabbitMQ
- Python schedule library

## Architecture:
I use Nameko microservices framework in Python. Thus, the architecture follows the RPC over AMQP that Nameko enforces by default.  
<br>
![Diagram](/diagram/diagram.png)
<br>

### 1. Gateway Service  
API Gateway Service will serve as the main handler of external requests coming in to the application. It also handles authentication as the authentication system is quite simple. 

The gateway service communicates to other services and receives the reply via RPC over AMQP using RabbitMQ. This is enabled by default using Nameko.

### 2. User Service
User service handles user registration and login. After a successful login or registration, the gateway will generate the JWT token and sends it back to the client.

### 3. News Service
News service handles news data management (CRUD).

### 4. Storage Service
Storage service handles the uploaded and downloaded files and stores them in the container's filesystem (mounted to host filesystem for debugging).

### 5. Archival Service
Runs every day at 00:00 to update all news data which are older than 30 days from the current day and labels them as archived.