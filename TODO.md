- [ ] Optional Dockerization for deployment (Priority: Low)
	- Goal: Add Dockerfile for Python app (optional, for production deployment only). Keep current hybrid setup for development.
	- Add docker-compose.prod.yml with app + db for production
	- Document two modes: local dev (current) vs Docker (production)
	- Rationale: Current hybrid setup (Python on host + Dockerized Postgres) is optimal for active development. Dockerization makes sense later for deployment, CI/CD, or onboarding. Interactive Telegram sessions and debugging are easier with native Python.

