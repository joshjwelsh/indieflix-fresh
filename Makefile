.PHONY: setup install-uv git-config venv env install clean
.PHONY: db-create db-init seed-fake scrape-real
.PHONY: backend frontend test-frontend test-api
.PHONY: quickstart help

help:
	@echo "Indieflix Makefile Commands"
	@echo "============================"
	@echo ""
	@echo "🚀 Quick Start:"
	@echo "  make quickstart       - Complete setup with fake data (recommended for testing)"
	@echo ""
	@echo "⚙️  Setup Commands:"
	@echo "  make setup            - Install uv and configure git"
	@echo "  make install-uv       - Install uv package manager"
	@echo "  make git-config       - Configure git user settings"
	@echo "  make venv             - Create virtual environment"
	@echo "  make install          - Install Python dependencies"
	@echo ""
	@echo "🗄️  Database Commands:"
	@echo "  make db-create        - Create PostgreSQL database and user"
	@echo "  make db-init          - Initialize database tables"
	@echo "  make seed-fake        - Seed database with fake data (16 movies)"
	@echo "  make scrape-real      - Scrape real data from theaters"
	@echo ""
	@echo "🎬 TMDB Enrichment Commands:"
	@echo "  make enrich-all       - Enrich all unenriched movies with TMDB data"
	@echo "  make enrich-recent    - Enrich movies from last 24 hours"
	@echo "  make enrich-stale     - Re-enrich movies older than 30 days"
	@echo ""
	@echo "🖥️  Server Commands:"
	@echo "  make backend          - Start backend API server (port 5000)"
	@echo "  make frontend         - Start frontend server (port 8000)"
	@echo ""
	@echo "🧪 Testing Commands:"
	@echo "  make test-frontend    - Quick frontend test with fake data"
	@echo "  make test-api         - Test API endpoints"
	@echo ""
	@echo "🧹 Utility Commands:"
	@echo "  make env              - Show environment variables"
	@echo "  make clean            - Clean Python cache files"
	@echo ""

setup: install-uv git-config
	@echo "✅ Setup complete! Run 'make quickstart' to get started"

install-uv:
	@if ! command -v uv &> /dev/null; then \
		echo "📦 Installing uv..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
		. $$HOME/.local/bin/env; \
	else \
		echo "✅ uv already installed"; \
	fi

git-config:
	@echo "🔧 Configuring git..."
	@git config --global user.name "Joshua Welsh"
	@git config --global user.email "joshua.welsh.1001@gmail.com"
	@git config --global init.defaultBranch main
	@echo "✅ Git configured"

venv:
	@echo "🐍 Creating virtual environment..."
	@cd backend && uv venv
	@echo "✅ Virtual environment created"
	@echo "💡 Activate with: source backend/.venv/bin/activate"

install:
	@echo "📚 Installing Python packages..."
	@if [ -f backend/requirements.txt ]; then \
		cd backend && uv pip install -r requirements.txt; \
	else \
		cd backend && uv pip install -e .; \
	fi
	@echo "✅ Dependencies installed"

env:
	@echo "🌍 Environment variables:"
	@echo "export DATABASE_URL='postgresql://indieflix:mypassword@indieflix-db:5432/indieflix'"
	@echo "export DEBUG=True"
	@echo "export SECRET_KEY='your-secret-key-here'"
	@echo ""
	@echo "💡 To set these variables, run: source <(make env)"

db-create:
	@echo "🗄️  Creating PostgreSQL database..."
	@sudo -u postgres psql -c "CREATE DATABASE indieflix;" 2>/dev/null || echo "Database already exists"
	@sudo -u postgres psql -c "CREATE USER indieflix WITH PASSWORD 'mypassword';" 2>/dev/null || echo "User already exists"
	@sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE indieflix TO indieflix;" 2>/dev/null || true
	@echo "✅ Database created"

db-init:
	@echo "📋 Initializing database tables..."
	@cd deng/utils/storage && python postgres.py
	@echo "✅ Database tables created"

seed-fake:
	@echo "🎬 Seeding fake data (16 movies)..."
	@cd deng && python seed_fake_data.py
	@echo "✅ Fake data seeded"

scrape-real:
	@echo "🌐 Scraping real data from theaters..."
	@cd deng/ingestion && python ifc_center.py
	@cd deng/ingestion && python metrograph.py
	@cd deng/ingestion && python syndicatedbk.py
	@echo "✅ Real data scraped"

enrich-all:
	@echo "🎬 Enriching all unenriched movies with TMDB data..."
	@cd deng/enrichment && python tmdb_enricher.py --all
	@echo "✅ Enrichment complete"

enrich-recent:
	@echo "🎬 Enriching movies from last 24 hours..."
	@cd deng/enrichment && python tmdb_enricher.py --recent 24
	@echo "✅ Recent enrichment complete"

enrich-stale:
	@echo "🎬 Re-enriching movies older than 30 days..."
	@cd deng/enrichment && python tmdb_enricher.py --stale 30
	@echo "✅ Stale data re-enriched"

backend:
	@echo "🚀 Starting backend API server..."
	@echo "💡 API will be available at http://localhost:5000"
	@cd backend/api && python app.py

frontend:
	@echo "🌐 Starting frontend server..."
	@echo "💡 Frontend will be available at http://localhost:8000"
	@cd frontend && python -m http.server 8000

test-frontend:
	@echo "🧪 Quick Frontend Test Setup"
	@echo "============================"
	@echo ""
	@echo "This will:"
	@echo "  1. Create database"
	@echo "  2. Initialize tables"
	@echo "  3. Seed fake data (16 movies)"
	@echo ""
	@read -p "Continue? [y/N] " response; \
	if [ "$$response" = "y" ] || [ "$$response" = "Y" ]; then \
		make db-create && \
		make db-init && \
		make seed-fake && \
		echo "" && \
		echo "✅ Test setup complete!" && \
		echo "" && \
		echo "Next steps:" && \
		echo "  1. Terminal 1: make backend" && \
		echo "  2. Terminal 2: make frontend" && \
		echo "  3. Browser: http://localhost:8000"; \
	fi

test-api:
	@echo "🧪 Testing API endpoints..."
	@echo ""
	@echo "Health Check:"
	@curl -s http://localhost:5000/api/health || echo "❌ Backend not running"
	@echo ""
	@echo ""
	@echo "Stats:"
	@curl -s http://localhost:5000/api/stats || echo "❌ Backend not running"
	@echo ""

quickstart:
	@echo "🚀 Indieflix Quickstart"
	@echo "======================="
	@echo ""
	@make setup
	@echo ""
	@make venv
	@echo ""
	@make install
	@echo ""
	@make db-create
	@echo ""
	@make db-init
	@echo ""
	@make seed-fake
	@echo ""
	@echo "✅ Quickstart complete!"
	@echo ""
	@echo "🎉 Ready to go! Run these commands:"
	@echo "  1. Terminal 1: make backend"
	@echo "  2. Terminal 2: make frontend"
	@echo "  3. Browser: http://localhost:8000"
	@echo ""

clean:
	@echo "🧹 Cleaning up..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleaned"
