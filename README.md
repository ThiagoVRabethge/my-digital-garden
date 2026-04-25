# 🌱 Meu Jardim Digital

Organizador pessoal de conhecimento construído com [Flet](https://flet.dev) e Python. Guarde pastas, links e notas em Markdown em um único lugar, com suporte a tags, busca e arrastar para reordenar.

---

## Funcionalidades

- **Pastas** — organize seus itens em hierarquias
- **Links** — salve URLs com título, abre direto no navegador
- **Notas** — editor Markdown completo com toolbar, preview e contagem de palavras
- **Tags** — crie e filtre notas por tags coloridas
- **Busca** — pesquisa global por título, conteúdo ou tag
- **Ordenação** — A→Z, Z→A, mais recente ou mais antigo
- **Arrastar para reordenar** — reordene itens dentro de uma pasta
- **Compartilhamento** — receba links direto do menu "Compartilhar" do Android
- **Links no Markdown** — links em notas abrem no navegador ao tocar

---

## Tecnologias

| Tecnologia | Uso |
|---|---|
| [Flet](https://flet.dev) | Interface (Flutter via Python) |
| [SQLAlchemy](https://www.sqlalchemy.org) | Banco de dados local (SQLite) |
| SQLite | Armazenamento persistente em `vault.db` |

---

## Instalação e execução local

### Pré-requisitos

- Python 3.12+
- [uv](https://github.com/astral-sh/uv)

### Passos

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/meu-jardim-digital.git
cd meu-jardim-digital

# Instale as dependências
uv sync

# Execute o app
uv run python main.py
```

---

## Build

O projeto usa GitHub Actions para gerar automaticamente os binários a cada push na branch `main`.

### Android (APK)

O build gera **três APKs separados por arquitetura**, o que reduz significativamente o tamanho do arquivo em comparação com um APK universal:

| Arquivo | Uso |
|---|---|
| `app-arm64-v8a-release.apk` | Android moderno (2016+) — **recomendado** |
| `app-armeabi-v7a-release.apk` | Android antigo (32-bit) |
| `app-x86_64-release.apk` | Emuladores |

Para instalar no celular, baixe o artifact `android-apk` na aba **Actions** do GitHub e instale o arquivo `arm64-v8a`.

> **Atenção:** pode ser necessário habilitar "Instalar de fontes desconhecidas" nas configurações do Android.

### Windows (EXE)

O build gera a pasta do aplicativo compactada em um arquivo `.zip` para facilitar o download. Para usar:

1. Baixe o artifact `windows-exe` na aba **Actions** do GitHub
2. Extraia o `.zip`
3. Execute o `.exe` dentro da pasta extraída

### Rodando o build manualmente

Acesse a aba **Actions** no GitHub, selecione o workflow **Build APK & EXE** e clique em **Run workflow**.

---

## Estrutura do projeto

```
meu-jardim-digital/
├── main.py                  # Código principal do app
├── pyproject.toml           # Dependências e configuração do Flet
├── vault.db                 # Banco de dados local (gerado ao rodar)
├── assets/                  # Ícones e recursos estáticos
├── flutter/
│   └── android/
│       └── app/src/main/
│           └── AndroidManifest.xml  # Configuração do share intent
└── .github/
    └── workflows/
        └── build.yml        # Pipeline de build automático
```

---

## Compartilhar links pelo Android

O app está registrado como destino no menu **Compartilhar** do Android. Para salvar um link direto de outro app (YouTube, navegador, etc.):

1. Toque em **Compartilhar** no app de origem
2. Selecione **Meu Jardim Digital** na lista
3. O editor de Link abrirá com a URL já preenchida
4. Digite o título e toque em **Guardar**

---

## Licença

MIT