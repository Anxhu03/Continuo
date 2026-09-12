# Contributing to Continuo

Thank you for your interest in contributing to Continuo! We welcome contributions to the Context Engine, provider adapters, frontend design system, and browser companions.

## Development Workflow

1. Fork the repository and clone your fork locally.
2. Create a virtual environment with Python 3.12+ and install dependencies:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Create a feature branch:
   ```bash
   git checkout -b feat/your-feature-name
   ```
4. Run tests before submitting:
   ```bash
   pytest -v
   ```
5. Follow conventional commit messages:
   - `feat: add new provider adapter`
   - `fix: resolve contradiction detector regex edge case`
   - `docs: update setup guide`

## Code Guidelines

- **Zero Fake Integrations**: We are transparent about cross-model automation capabilities. Do not simulate automated browser control where only clipboard or direct navigation is provided.
- **Provider Neutrality**: New AI providers must adhere to the standardized `ContextPackage` schema and implement a dedicated formatter in `backend/services/handoff_generator.py`.
- **Aesthetic Consistency**: Frontend updates must preserve the iOS 26 translucent glass language and living ambient background system.
