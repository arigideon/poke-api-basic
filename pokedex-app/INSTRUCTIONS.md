# Pokédex — Instruções de Deploy

## Rodando localmente

### Pré-requisitos
- Docker Desktop instalado e rodando

### 1. Configuração inicial

```bash
cd pokedex-app
cp .env.example .env
```

Edite o `.env` e troque o `SECRET_KEY` por uma string aleatória segura:

```bash
# gere uma chave segura (rode no terminal):
python -c "import secrets; print(secrets.token_hex(32))"
```

`.env` final:

```
SECRET_KEY=cole_aqui_a_chave_gerada
ACCESS_TOKEN_EXPIRE_MINUTES=60
CACHE_TTL_SECONDS=3600
```

### 2. Build e subida

```bash
docker compose up --build
```

Aguarde até ver as 4 linhas de `INFO: Application startup complete` (uma por serviço). Leva ~2 min no primeiro build.

### 3. Criar o primeiro usuário

Acesse `http://localhost/register` e crie sua conta. Depois faça login em `http://localhost/login`.

### 4. Comandos úteis

```bash
docker compose logs -f frontend      # ver logs do frontend
docker compose logs -f auth-service  # ver logs de auth
docker compose down                  # parar tudo
docker compose up -d                 # subir em background
docker compose restart backend       # reiniciar só o backend
```

---

## Deploy na Railway

Railway não usa docker-compose em produção — cada serviço é deployado separadamente apontando para seu próprio Dockerfile.

### Estrutura no Railway

Você criará **1 projeto** com **3 services** (nginx não é necessário — Railway tem seu próprio proxy HTTPS).

### 1. Crie um projeto no Railway

Acesse [railway.app](https://railway.app) → **New Project** → **Empty Project**.

### 2. Deploy do `auth-service`

1. No projeto → **Add Service** → **GitHub Repo**
2. Selecione o repositório → em **Root Directory** coloque: `auth-service`
3. Railway detecta o Dockerfile automaticamente
4. Vá em **Variables** e adicione:
   ```
   SECRET_KEY=sua_chave_secreta_longa_aqui
   ACCESS_TOKEN_EXPIRE_MINUTES=60
   DATABASE_URL=sqlite:////app/data/auth.db
   ```
5. Em **Settings → Networking**, marque **Private** (não precisa de URL pública)
6. Anote o **Private Domain** gerado, ex: `auth-service.railway.internal`

### 3. Deploy do `backend`

1. **Add Service** → **GitHub Repo** → Root Directory: `backend`
2. Variáveis:
   ```
   POKEAPI_BASE_URL=https://pokeapi.co/api/v2
   CACHE_TTL_SECONDS=3600
   ```
3. Também deixe **Private** (sem URL pública)
4. Anote o Private Domain, ex: `backend.railway.internal`

### 4. Deploy do `frontend`

1. **Add Service** → **GitHub Repo** → Root Directory: `frontend`
2. Variáveis (substitua pelos Private Domains reais dos outros serviços):
   ```
   SECRET_KEY=sua_chave_secreta_longa_aqui   ← MESMA do auth-service
   AUTH_SERVICE_URL=http://auth-service.railway.internal:8000
   BACKEND_URL=http://backend.railway.internal:8000
   ```
3. Em **Settings → Networking** → **Generate Domain** (este precisa de URL pública)
4. Como o Railway usa HTTPS, edite `frontend/app/main.py` e mude `secure=False` para `secure=True` antes de fazer push

### 5. Volume persistente para o banco (auth-service)

1. No auth-service no Railway → **Add Volume**
2. Mount path: `/app/data`
3. Isso garante que o banco SQLite persista entre deploys

### 6. Acesso

A URL pública do frontend (gerada pelo Railway) é o único ponto de entrada. Backend e auth-service são acessíveis só internamente.

> **Importante:** antes do primeiro push ao Railway, edite `frontend/app/main.py` linha ~101:
> ```python
> secure=True,  # mude de False para True
> ```
> Isso garante que o cookie JWT só seja enviado em conexões HTTPS.

---

## Bugs corrigidos na validação

| # | Problema | Arquivo | Solução |
|---|----------|---------|---------|
| 1 | `__init__.py` faltando nos 3 serviços | `*/app/__init__.py` | Arquivos criados |
| 2 | Healthcheck usava `httpx` que não está nas dependências do `auth-service` | `docker-compose.yml` | Trocado para `urllib.request` (stdlib) |
| 3 | Parâmetro nomeado `type` sombrava o built-in Python | `backend/app/router.py` | Renomeado para `type_filter` com `alias="type"` |
| 4 | Contador de resultados de busca ficava oculto dentro da div de paginação escondida | `frontend/app/static/js/app.js` | Botões ficam invisíveis, contador permanece visível |
