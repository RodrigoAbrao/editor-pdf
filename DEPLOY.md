# 🚀 Guia de Deploy — PDF Editor

## Frontend (Vercel)

### Pré-requisitos
- Conta no [Vercel](https://vercel.com)
- GitHub conectado ao Vercel

### Passos

1. **Push para GitHub**
   ```bash
   git push origin master
   ```

2. **No Vercel Dashboard**
   - Clique em "New Project"
   - Selecione este repositório
   - Framework: **Vite** (Vercel detecta automaticamente)
   - Root Directory: `./frontend`
   - Build Command: `npm run build`
   - Output Directory: `dist`

3. **Variáveis de Ambiente**
   Adicione na aba "Environment Variables":
   - `VITE_API_URL` = `https://seu-backend-encore-url` (sem trailing slash)

4. **Deploy**
   - Vercel faz deploy automaticamente

### Resultado
- URL: `https://seu-app.vercel.app`
- Atualiza automaticamente a cada push

---

## Backend (Encore.dev)

### Pré-requisitos
- Conta no [Encore.dev](https://encore.dev)
- Encore CLI instalado: `npm install -g encore`

### Passos

1. **Autenticar no Encore**
   ```bash
   encore auth login
   ```

2. **Deploy**
   ```bash
   encore deploy
   ```
   
   Encore automaticamente:
   - Detecta Python 3.12 via `encore.json`
   - Instala `requirements.txt`
   - Roda Dockerfile (se existir)
   - Configura variáveis de ambiente

3. **Variáveis de Ambiente**
   - No dashboard Encore, defina:
     - `OPENAI_API_KEY` = sua chave OpenAI (importante para validação de qualidade!)
     - `CORS_ORIGINS` = `https://seu-app.vercel.app`

4. **Resultado**
   - URL: `https://seu-app-staging.encoreapi.com` (ou produção)
   - Logs automáticos no dashboard

---

## Integração

### Após Deploy

1. **Atualizar Vercel**
   - Se a URL do Encore mudou, atualize a variável `VITE_API_URL`

2. **Atualizar Encore**
   - Se a URL do Vercel mudou, atualize `CORS_ORIGINS`

### Testar
```bash
curl https://seu-app-staging.encoreapi.com/health
# Deve retornar: {"status":"ok"}
```

---

## Troubleshooting

### CORS Error
- Verifique se `CORS_ORIGINS` no backend contém a URL do Vercel
- Deve ser exatamente: `https://seu-app.vercel.app` (sem trailing slash)

### OpenAI Vision não funciona
- Verifique se `OPENAI_API_KEY` está setada no Encore
- Verifique se a chave é válida em https://platform.openai.com/api-keys

### Upload lento
- Vercel limita requisições a ~10s
- Se upload > 10s, pode dar timeout
- Solução: aumentar limite ou usar upload em chunks (feature futura)

---

## Links Úteis

- [Vercel Docs](https://vercel.com/docs)
- [Encore.dev Docs](https://encore.dev/docs)
- [Vite Deploy Guide](https://vitejs.dev/guide/static-deploy.html)
