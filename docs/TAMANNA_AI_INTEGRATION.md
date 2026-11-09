# Tamanna AI integration

The full Tamanna AI source is linked into this repository as a Git submodule at `vendor/tamanna-ai`.

- Upstream: https://github.com/tamanna456760-it/Tamanna-
- Pinned upstream revision: `e96dc0505690cbc21a06ab534a0fec2d5a996001`
- Source entry point: `Main.py` / `run_server.py`
- Local model path: Ollama (no hosted GPT/Gemini provider required)
- Existing Central Server remains Flask and is not overwritten.

## Clone with the AI source
```sh
git clone --recurse-submodules https://github.com/tamanna456760-it/Tamanna-server.git
cd Tamanna-server
git submodule update --init --recursive
```

## Run the AI service separately
The upstream project contains its own FastAPI entry point and runtime requirements. Install and launch from the submodule directory, using its documented environment configuration:
```sh
cd vendor/tamanna-ai
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-server.txt
cp .env.example .env
python run_server.py
```

Configure a private `.env`; never commit session secrets, admin credentials, user databases, memory exports, or model data. Use a random `TAMANNA_SESSION_SECRET` of at least 32 characters and set the authorized `TAMANNA_ADMIN_EMAIL`. The model provider defaults to local Ollama.

## Integration status
This adds the complete upstream source as a pinned submodule without copying private runtime data or overwriting existing server files. It does **not** yet mean the AI service is reverse-proxied, started by Docker Compose, or live in production. Those steps require dependency/build tests and explicit deployment validation. The existing Flask API, website, DNS and Nginx configuration remain unchanged.
