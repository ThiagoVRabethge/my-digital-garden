# 🌱 My Digital Garden

Um organizador pessoal de conhecimento construído com **Flet** e **SQLite**, focado em mobile-first. Organize links, notas em Markdown e pastas hierárquicas — tudo num app leve que roda no celular, no desktop e pode ser exportado como APK ou EXE.

---

## Tecnologias

| | |
|---|---|
| **Framework** | [Flet](https://flet.dev) 0.80+ |
| **Banco de dados** | SQLite via [SQLAlchemy](https://www.sqlalchemy.org) |
| **Gerenciador de pacotes** | [uv](https://docs.astral.sh/uv) |
| **Build** | `flet build` (APK Android + EXE Windows) |
| **CI/CD** | GitHub Actions |

---

## Pré-requisitos

- Python 3.12+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) instalado

---

## Instalação e execução

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/my-digital-garden.git
cd my-digital-garden

# Instale as dependências
uv sync

# Rode o app no desktop
uv run flet run main.py

# Rode no navegador (para testar no celular via Wi-Fi)
uv run flet run main.py --web --port 8080
# Acesse: http://SEU_IP_LOCAL:8080
```

---

## Build

```bash
# APK para Android
uv run flet build apk --yes

# Executável para Windows
uv run flet build windows --yes
```

Os artefatos de build também são gerados automaticamente pelo GitHub Actions a cada push na branch `main`.

---

## Estrutura do projeto

```
my-digital-garden/
├── main.py                  # Código principal do app
├── pyproject.toml           # Dependências e configuração do projeto
├── uv.lock                  # Lock file do uv
├── vault.db                 # Banco SQLite (gerado automaticamente)
├── .github/
│   └── workflows/
│       └── build.yml        # CI/CD: build APK + EXE
└── README.md
```

---

## Licença

MIT