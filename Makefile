# ---------- LOCAL TESTS ----------
#Use wait -n trick, to detect failure correctly
# Runs both tests in parallel
# Tracks each process
# Fails if ANY fails
test:
	@echo "Running tests in parallel..."
	( cd myapp && USE_TESTCONTAINERS=true poetry run pytest ) & \
	P1=$$!; \
	( cd mylearning && poetry run pytest ) & \
	P2=$$!; \
	wait $$P1 || exit 1; \
	wait $$P2 || exit 1;

# ---------- DOCKER BUILD ----------
docker-build:
	docker compose build

# ---------- DOCKER DB ----------
docker-db:
	docker compose up -d db

# ---------- DOCKER TEST ----------
#Parallel Docker Tests (Advanced)
test-docker:
	docker compose down -v --remove-orphans #remove any container created earlier those are orphan now
	docker compose up --build --abort-on-container-exit #--abort-on-container-exit = foreground mode (watch containers)
	sleep 10
	@echo "Running Docker tests in parallel..."
	(docker compose run --rm myapp poetry run pytest) & \
	P1=$$!; \
	(docker compose run --rm mylearning) & \
	P2=$$!; \
	wait $$P1 || exit 1; \
	wait $$P2 || exit 1;
	docker compose down -v

# ---------- FULL RUN ----------
run:
	docker compose down -v --remove-orphans # CI runners are reused sometimes → leftover containers can break builds, down -v ensures clean start
	docker compose up --build -d #Run DB in background, tests separately. -d = detached mode (run in background)

# ---------- API CHECK ----------
check-api:
	sleep 10
	curl -f http://localhost:8000/docs || exit 1

# ---------- CLEAN ----------
clean:
	docker compose down -v --remove-orphans
	docker system prune -f