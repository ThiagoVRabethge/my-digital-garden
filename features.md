# 📋 Funcionalidades — My Digital Garden

## ✅ Implementado

### Estrutura e navegação

- **Pastas hierárquicas** — crie pastas dentro de pastas sem limite de profundidade
- **Navegação em pilha** — entre e saia de pastas com o botão voltar na AppBar
- **AppBar dinâmica** — título muda conforme a pasta atual; botão voltar aparece contextualmente
- **Estado vazio** — tela com ícone e instrução quando não há itens na pasta

### Tipos de item

- **Pasta** — agrupa outros itens (pastas, links e notas); identificada por ícone e chip roxo
- **Link** — salva uma URL com nome; abre no navegador padrão do sistema ao tocar
- **Nota** — texto livre em formato Markdown; identificada por chip verde

### Editor de Notas

- **Toolbar de formatação Markdown** com os seguintes botões:
  - Negrito, Itálico, Tachado
  - Títulos H1, H2, H3
  - Lista com marcadores, Lista numerada, Checkbox
  - Código inline, Bloco de código
  - Citação, Separador horizontal, Link
- **Preview ao vivo** — alterna entre modo edição e renderização Markdown com um clique
- **Contador** de palavras e caracteres em tempo real
- **Campo monospace** para edição confortável de Markdown
- **Renderização completa** de Markdown na leitura (GitHub Flavored Markdown + syntax highlighting)

### Organização

- **Ordenação persistente** — a preferência de ordenação é salva no banco e restaurada ao reabrir o app
- Quatro modos de ordenação disponíveis:
  - **A → Z** — alfabética crescente
  - **Z → A** — alfabética decrescente
  - **Mais recente** — por data de criação, do mais novo ao mais antigo
  - **Mais antigo** — por data de criação, ordem cronológica (padrão)

### Gerenciamento de itens

- **Criar** pasta via dialog; link e nota via editor dedicado
- **Editar** qualquer item pelo menu `⋮` do card
- **Excluir** com confirmação via dialog (exclusão em cascata: apaga subpastas e itens filhos)
- **Menu contextual** por item com opções Editar e Excluir

### Interface

- **Design mobile-first** — layout em lista vertical, áreas de toque generosas
- **Tema escuro** com paleta de cores consistente
- **Bottom Sheet** para adicionar novos itens (Pasta / Link / Nota)
- **FAB** (botão +) oculto automaticamente no editor para não sobrepor o botão Guardar
- **Seções separadas** por tipo (PASTAS, LINKS, NOTAS) dentro de cada pasta
- **Preview de conteúdo** nos cards (primeiros 60 caracteres da nota ou URL do link)
- **Chips coloridos** por tipo de item (roxo = Pasta, ciano = Link, verde = Nota)

### Técnico

- Banco de dados **SQLite local** via SQLAlchemy (sem servidor, sem internet)
- **Preferências persistidas** em tabela chave-valor no mesmo banco
- Correção de **encoding UTF-8** no Windows para compatibilidade com build e CI
- **GitHub Actions** com build automático de APK (Android) e EXE (Windows) a cada push

---

## 🔮 Sugestões para implementação futura

### Busca e descoberta
- [ ] **Busca global** — campo de pesquisa que filtra títulos e conteúdo de notas em tempo real
- [ ] **Tags/etiquetas** — adicionar tags aos itens e filtrar por elas
- [ ] **Vista recentes** — seção especial com os últimos itens acessados ou editados

### Editor de notas
- [ ] **Auto-save** — salvar automaticamente enquanto o usuário digita (com debounce)
- [ ] **Histórico de versões** — manter as últimas N versões de cada nota
- [ ] **Modo foco** — editor em tela cheia sem distrações
- [ ] **Inserção de imagens** — da galeria ou câmera, incorporadas na nota
- [ ] **Templates** — modelos pré-definidos para notas (diário, reunião, tarefa, etc.)
- [ ] **Exportar nota** — como arquivo `.md` ou `.pdf`

### Links
- [ ] **Favicon automático** — buscar e exibir o ícone do site salvo
- [ ] **Preview de URL** — miniatura ou metadados (título, descrição) ao salvar um link
- [ ] **Verificar links quebrados** — checar quais URLs salvas estão inacessíveis
- [ ] **Abrir link dentro do app** — WebView embutida para não sair do app

### Organização
- [ ] **Drag & drop funcional** — reordenação manual por arrastar e soltar (bloqueado por limitação do Flet)
- [ ] **Mover item entre pastas** — opção no menu contextual para mover para outra pasta
- [ ] **Duplicar item** — criar cópia de uma nota ou link
- [ ] **Seleção múltipla** — selecionar vários itens para mover, excluir ou etiquetar em lote

### Sincronização e backup
- [ ] **Exportar/importar banco** — backup do `vault.db` para o armazenamento do dispositivo
- [ ] **Sincronização via nuvem** — Google Drive, Dropbox ou servidor próprio
- [ ] **Compartilhar nota** — exportar como texto e enviar via apps do sistema

### Experiência do usuário
- [ ] **Tema claro** — alternativa ao tema escuro, com opção de seguir o sistema
- [ ] **Tamanho de fonte configurável** — acessibilidade para leitura
- [ ] **Animações de transição** — entre telas e ao criar/excluir itens
- [ ] **Widget Android** — acesso rápido às últimas notas na tela inicial
- [ ] **Atalhos de teclado** — para uso no desktop (Ctrl+S salvar, Ctrl+N nova nota, etc.)
- [ ] **Onboarding** — tela de boas-vindas com tutorial rápido para novos usuários

### Segurança
- [ ] **Senha / biometria** — bloquear o app com PIN, senha ou impressão digital
- [ ] **Pastas protegidas** — bloquear pastas específicas individualmente
- [ ] **Criptografia do banco** — SQLCipher para criptografar o arquivo `vault.db`