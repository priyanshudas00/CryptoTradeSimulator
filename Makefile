# CryptoTradeSimulator Build Commands

.PHONY: help install run-frontend run-backend clean

help:
	@echo "Available commands:"
	@echo "  make install     - Install Python dependencies"
	@echo "  make run-frontend - Start the frontend development server"
	@echo "  make run-backend  - Start the backend PyQt5 application"
	@echo "  make clean       - Clean up generated files"

install:
	@echo "Installing Python dependencies..."
	cd src && pip install -r requirements.txt

run-frontend:
	@echo "Starting frontend server..."
	cd frontend && npm start

run-backend:
	@echo "Starting backend application..."
	cd src && python main.py

clean:
	@echo "Cleaning up..."
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete
	@echo "Clean complete"
