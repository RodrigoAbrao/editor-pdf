# 🚀 Guia de Deploy — PDF Editor

## Frontend (Vercel) ✅

### Status: **DEPLOYADO**
- URL: https://editor-pdf-enganonimo.vercel.app
- Atualizações automáticas a cada push

---

## Backend (Fly.io) 🚁

### Pré-requisitos
- Conta no [Fly.io](https://fly.io) (grátis)
- Fly CLI instalado: `choco install flyctl` (Windows) ou `brew install flyctl` (Mac)
- GitHub conectado (já tem)

### Passos

#### 1. **Instalar e Login**
```bash
flyctl auth login
# Abre navegador para autenticar
```

#### 2. **Criar Aplicação**
```bash
cd c:\Users\PHOENIX\editor-pdf
flyctl launch
```

**Respostas do wizard:**
- **App name**: `pdf-editor-api` (Fly vai sugerir um ID único)
- **Region**: Escolha `sao` (São Paulo) ou `gig` (mais próximo)
- **Create database**: `N` (não precisa)
- **Deploy**: `N` (vamos configurar antes)

#### 3. **Configurar fly.toml** (gerado automaticamente)
Vai parecer assim:
```toml
app = "pdf-editor-api-xxxx"
primary_region = "sao"

[env]
  OPENAI_API_KEY = "sk-xxxxx"
  CORS_ORIGINS = "https://editor-pdf-enganonimo.vercel.app"

[build]
  dockerfile = "Dockerfile"
  dockerfile_path = "backend/Dockerfile"
```

Editar linhas importantes:
```toml
[env]
  OPENAI_API_KEY = "sk-xxxxx"  # ← Sua chave OpenAI
  CORS_ORIGINS = "https://editor-pdf-enganonimo.vercel.app"
  DATA_DIR = "/app/data"

[[services]]
  protocol = "tcp"
  internal_port = 8000  # ← Port do uvicorn
  processes = ["app"]

  [[services.ports]]
    port = 80  # HTTP
    handlers = ["http"]

  [[services.ports]]
    port = 443  # HTTPS
    handlers = ["tls", "http"]
```

#### 4. **Volumes (Armazenamento Persistente)**
```bash
flyctl volumes create pdf_data --size 1
```

Adicionar ao `fly.toml`:
```toml
[[mounts]]
  source = "pdf_data"
  destination = "/app/data"
```

#### 5. **Deploy!**
```bash
flyctl deploy
```

Fly faz tudo: build Docker, push, e roda na nuvem ☁️

#### 6. **Ver Status**
```bash
flyctl status
flyctl logs
```

### Resultado
- URL: `https://pdf-editor-api-xxxx.fly.dev` (Fly gera automaticamente)
- Sempre ligado (grátis, sempre)
- Logs em tempo real via `flyctl logs`

---

## Integração Final

### Atualizar Vercel com URL do Backend

1. **Pegar URL do backend**:
```bash
flyctl info
# Procura por "HTTPS URLs"
```

2. **No Vercel Dashboard**:
   - Settings → Environment Variables
   - Atualize `VITE_API_URL`:
   ```
   https://pdf-editor-api-xxxx.fly.dev
   ```
   - Trigger redeploy: Settings → Deployments → Redeploy

### Testar
```bash
# Verificar backend
curl https://pdf-editor-api-xxxx.fly.dev/health

# Frontend automaticamente conecta via VITE_API_URL
```

---

## Troubleshooting

### CORS Error
- Verifique `CORS_ORIGINS` no `fly.toml` (sem trailing slash)
- Deploy novamente: `flyctl deploy`

### OpenAI Vision não funciona
- Verifique se `OPENAI_API_KEY` está em `fly.toml` e é válida
- Teste endpoint: `https://seu-app.fly.dev/api/documents/{doc_id}/quality-check`

### Upload lento / timeout
- Fly.io tem timeouts de ~60s (melhor que Render!)
- Se ainda lento, implementar upload em chunks (feature futura)

### Volume cheio
```bash
flyctl ssh console
# Dentro do shell:
du -sh /app/data
rm -rf /app/data/uploads/old-files
```

### App não sobe
```bash
flyctl logs  # Ver erro
flyctl deploy --no-cache  # Rebuild tudo
```

---

## Próximas Steps (Opcional)

- [ ] Custom domain (ex: api.seu-dominio.com) via `flyctl certs add`
- [ ] Auto-scaling se traffic crescer
- [ ] Backup automático do volume
- [ ] Monitoring com Datadog/NewRelic
- [ ] Rate limiting para API pública

---

## Links Úteis

- [Fly.io Docs — FastAPI](https://fly.io/docs/languages-and-frameworks/python/)
- [Fly.io CLI Reference](https://fly.io/docs/flyctl/)
- [Vercel Docs](https://vercel.com/docs)
- [OpenAI API Keys](https://platform.openai.com/api-keys)
