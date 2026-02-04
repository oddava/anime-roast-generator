restart:
	docker compose restart

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs