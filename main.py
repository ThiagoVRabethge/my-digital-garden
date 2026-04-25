# -*- coding: utf-8 -*-
import io
import os
import sys
import webbrowser

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import flet as ft
from sqlalchemy import Column, ForeignKey, Integer, String, Table, Text, create_engine
from sqlalchemy.orm import backref, declarative_base, relationship, sessionmaker

Base = declarative_base()
engine = create_engine("sqlite:///vault.db")
Session = sessionmaker(bind=engine)

# Tabela de associação Item <-> Tag
item_tag = Table(
    "item_tag",
    Base.metadata,
    Column(
        "item_id", Integer, ForeignKey("itens.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    ),
)


class Item(Base):
    __tablename__ = "itens"
    id = Column(Integer, primary_key=True)
    titulo = Column(String(100), nullable=False)
    conteudo = Column(Text, nullable=True)
    tipo = Column(String(20))
    pai_id = Column(Integer, ForeignKey("itens.id"), nullable=True)
    ordem = Column(Integer, default=0)
    data_criacao = Column(Integer, default=0)
    filhos = relationship(
        "Item",
        backref=backref("pai", remote_side=[id]),
        cascade="all, delete-orphan",
    )
    tags = relationship("Tag", secondary=item_tag, back_populates="tags")


class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True)
    nome = Column(String(50), nullable=False, unique=True)
    cor = Column(String(10), default="#7C6AF7")
    itens = relationship("Item", secondary=item_tag, back_populates="tags")


class Preferencia(Base):
    __tablename__ = "preferencias"
    chave = Column(String(50), primary_key=True)
    valor = Column(String(100), nullable=False)


Base.metadata.create_all(engine)


def pref_get(session, chave, default=""):
    p = session.get(Preferencia, chave)
    return p.valor if p else default


def pref_set(session, chave, valor):
    p = session.get(Preferencia, chave)
    if p:
        p.valor = valor
    else:
        session.add(Preferencia(chave=chave, valor=valor))
    session.commit()


# ─── SHARE INTENT (Android) ───────────────────────────────────────────────────

def _get_shared_intent_file() -> str | None:
    """
    Determina o caminho de flet_shared.txt escrito pela MainActivity.
    Usa /proc/self/cmdline para descobrir o package name dinamicamente,
    sem hardcode — funciona em qualquer build do Flet.
    """
    try:
        with open("/proc/self/cmdline", "rb") as f:
            pkg = f.read().split(b"\x00")[0].decode().strip()
        if not pkg:
            return None
        for base in (
            f"/data/user/0/{pkg}/files",
            f"/data/data/{pkg}/files",
        ):
            if os.path.isdir(base):
                return os.path.join(base, "flet_shared.txt")
    except Exception:
        pass
    return None


def consume_shared_intent() -> str | None:
    """
    Lê e apaga o arquivo de compartilhamento.
    Retorna o texto compartilhado ou None.
    """
    path = _get_shared_intent_file()
    if not path or not os.path.isfile(path):
        return None
    try:
        text = open(path, "r", encoding="utf-8").read().strip()
        os.remove(path)
        return text or None
    except Exception:
        return None


# --- Paleta ---
BG = "#0D0D0F"
SURFACE = "#141417"
CARD = "#1A1A1F"
CARD_HOV = "#222228"
CARD_DRG = "#2A2A40"
BORDER = "#2A2A35"
ACCENT = "#7C6AF7"
ACCENT2 = "#4FC3F7"
GREEN = "#56D6A0"
YELLOW = "#F7C86A"
PINK = "#F76A9E"
TEXT = "#E8E8F0"
TEXT_SUB = "#6B6B80"
TEXT_DIM = "#3D3D50"
WHITE = "#FFFFFF"
RED = "#C0392B"
TOOLBAR = "#18181D"

TAG_CORES = [ACCENT, ACCENT2, GREEN, YELLOW, PINK, "#F7956A", "#A0F76A", "#6AF7E8"]


def chip_cor(tipo):
    return {
        "Pasta": (ACCENT, "#1E1B3A"),
        "Link": (ACCENT2, "#112230"),
        "Nota": (GREEN, "#0F2820"),
    }.get(tipo, (TEXT_SUB, CARD))


def icone_tipo(tipo):
    return {
        "Pasta": ft.Icons.FOLDER_ROUNDED,
        "Link": ft.Icons.OPEN_IN_NEW_ROUNDED,
        "Nota": ft.Icons.ARTICLE_ROUNDED,
    }.get(tipo, ft.Icons.CIRCLE)


def pad(a=0, t=None, r=None, b=None, h=None, v=None):
    left = h if h is not None else a
    right = h if h is not None else (r if r is not None else a)
    top = v if v is not None else (t if t is not None else a)
    bottom = v if v is not None else (b if b is not None else a)
    return ft.Padding(left=left, top=top, right=right, bottom=bottom)


def divider():
    return ft.Container(height=1, bgcolor=BORDER)


def _tag_bg(hex_color):
    h = hex_color.lstrip("#")
    try:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"#{20:02x}{r:02x}{g:02x}{b:02x}"
    except Exception:
        return "#1E1B3A"


def tag_chip(tag, on_remove=None, small=False):
    size = 10 if small else 12
    cor = tag.cor or ACCENT
    bg = _tag_bg(cor)
    children = [ft.Text(f"#{tag.nome}", size=size, color=cor, weight="w600")]
    if on_remove:
        children.append(
            ft.GestureDetector(
                content=ft.Icon(ft.Icons.CLOSE_ROUNDED, size=12, color=cor),
                on_tap=lambda e, t=tag: on_remove(t),
            )
        )
    return ft.Container(
        content=ft.Row(children, spacing=3, tight=True),
        bgcolor=bg,
        border_radius=20,
        padding=pad(h=8, v=3),
    )


def build_list_item(item, on_click, on_edit, on_delete, on_drag_complete, all_items_ref):
    cor, bg = chip_cor(item.tipo)
    icone = icone_tipo(item.tipo)

    preview = ""
    if item.tipo == "Nota" and item.conteudo:
        preview = item.conteudo[:60].replace("\n", " ") + (
            "..." if len(item.conteudo) > 60 else ""
        )
    elif item.tipo == "Link" and item.conteudo:
        preview = item.conteudo[:50]

    def popup_item(label, icon_name, handler):
        return ft.PopupMenuItem(
            content=ft.Row(
                [
                    ft.Icon(icon_name, size=14, color=TEXT_SUB),
                    ft.Text(label, size=13, color=TEXT),
                ],
                spacing=10,
            ),
            on_click=handler,
        )

    menu = ft.PopupMenuButton(
        icon=ft.Icons.MORE_VERT_ROUNDED,
        icon_color=TEXT_DIM,
        icon_size=20,
        items=[
            popup_item("Editar", ft.Icons.EDIT_ROUNDED, lambda e, i=item: on_edit(i)),
            ft.PopupMenuItem(),
            popup_item(
                "Excluir",
                ft.Icons.DELETE_OUTLINE_ROUNDED,
                lambda e, i=item: on_delete(i),
            ),
        ],
    )

    text_col_children = [
        ft.Text(item.titulo, size=15, weight="w600", color=TEXT, max_lines=1, overflow="ellipsis"),
    ]
    if preview:
        text_col_children.append(
            ft.Text(preview, size=12, color=TEXT_SUB, max_lines=1, overflow="ellipsis")
        )
    if item.tipo == "Nota" and item.tags:
        text_col_children.append(ft.Container(height=4))
        text_col_children.append(ft.Row([tag_chip(t, small=True) for t in item.tags[:4]], spacing=4))

    card_content = ft.Row(
        [
            ft.Container(content=ft.Icon(ft.Icons.DRAG_INDICATOR_ROUNDED, size=18, color=TEXT_DIM), padding=pad(r=4)),
            ft.Container(content=ft.Icon(icone, size=20, color=cor), bgcolor=bg, border_radius=10, padding=10, width=44, height=44),
            ft.Container(width=12),
            ft.Column(text_col_children, spacing=2, expand=True, alignment="center"),
            ft.Container(width=4),
            menu,
        ],
        vertical_alignment="center",
    )

    card = ft.Container(
        content=card_content,
        bgcolor=CARD,
        border_radius=14,
        padding=pad(h=12, v=12),
        on_click=lambda e, i=item: on_click(i),
    )

    def will_accept(e):
        e.control.content.border = ft.Border.all(2, ACCENT)
        e.control.update()

    def on_accept(e):
        e.control.content.border = None
        e.control.update()
        try:
            src_id = int(e.data)
        except (AttributeError, ValueError, TypeError):
            return
        if src_id != item.id:
            on_drag_complete(src_id, item.id)

    def on_leave(e):
        e.control.content.border = None
        e.control.update()

    drop_target = ft.DragTarget(
        group="items",
        content=ft.Container(content=card, border_radius=14),
        on_will_accept=will_accept,
        on_accept=on_accept,
        on_leave=on_leave,
    )

    return ft.Draggable(
        group="items",
        data=str(item.id),
        content=drop_target,
        content_when_dragging=ft.Container(
            content=ft.Row([ft.Icon(icone, size=18, color=cor), ft.Text(item.titulo, size=14, color=TEXT_SUB, max_lines=1)], spacing=10),
            bgcolor=CARD_DRG, border_radius=14, padding=pad(h=16, v=12),
            border=ft.Border.all(1, ACCENT), opacity=0.85,
        ),
        content_feedback=ft.Container(
            content=ft.Row([ft.Icon(icone, size=18, color=cor), ft.Text(item.titulo, size=14, color=TEXT, max_lines=1)], spacing=10),
            bgcolor=CARD_DRG, border_radius=14, padding=pad(h=16, v=12),
            border=ft.Border.all(1, ACCENT),
            shadow=ft.BoxShadow(blur_radius=20, color="#44000000"),
        ),
    )


def section_title(text):
    return ft.Text(text, size=11, weight="w700", color=TEXT_DIM)


def build_note_editor(initial_value="", on_save=None, on_cancel=None, on_tap_link=None):
    content_field = ft.TextField(
        value=initial_value, multiline=True, min_lines=16, max_lines=None,
        border_color=BORDER, focused_border_color=ACCENT, color=TEXT, bgcolor=SURFACE,
        border_radius=ft.BorderRadius(0, 0, 12, 12),
        text_style=ft.TextStyle(size=14, font_family="monospace"),
        cursor_color=ACCENT, expand=True, content_padding=pad(h=16, v=14),
    )

    preview_col = ft.Column(
        [ft.Markdown(initial_value or "_Comece a escrever..._", selectable=True, extension_set="gitHubFlavored", code_theme="atom-one-dark", on_tap_link=on_tap_link)],
        scroll="auto", expand=True,
    )

    preview_container = ft.Container(
        content=preview_col, expand=True, padding=pad(h=16, v=14), bgcolor=SURFACE,
        border_radius=ft.BorderRadius(0, 0, 12, 12), border=ft.Border.all(1, BORDER), visible=False,
    )

    mode = {"preview": False}

    def atualizar_preview():
        preview_col.controls[0].value = content_field.value or "_Comece a escrever..._"
        preview_col.update()

    def toggle_preview(e):
        mode["preview"] = not mode["preview"]
        content_field.visible = not mode["preview"]
        preview_container.visible = mode["preview"]
        preview_btn.icon = ft.Icons.EDIT_ROUNDED if mode["preview"] else ft.Icons.VISIBILITY_ROUNDED
        preview_btn.tooltip = "Editar" if mode["preview"] else "Preview"
        if mode["preview"]:
            atualizar_preview()
        content_field.update()
        preview_container.update()
        preview_btn.update()

    def inserir(antes, depois="", placeholder="texto"):
        v = content_field.value or ""
        s = content_field.selection_start or len(v)
        e = content_field.selection_end or s
        sel = v[s:e] if s != e else placeholder
        content_field.value = v[:s] + antes + sel + depois + v[e:]
        content_field.update()
        content_field.focus()

    def tbtn(label, tooltip, fn):
        return ft.TextButton(label, tooltip=tooltip, on_click=fn, style=ft.ButtonStyle(color=TEXT_SUB, padding=ft.Padding(6, 4, 6, 4), shape=ft.RoundedRectangleBorder(radius=6)))

    def ibtn(icon, tooltip, fn):
        return ft.IconButton(icon=icon, icon_color=TEXT_SUB, icon_size=18, tooltip=tooltip, on_click=fn, style=ft.ButtonStyle(padding=ft.Padding(6, 6, 6, 6), shape=ft.RoundedRectangleBorder(radius=6)))

    def tdiv():
        return ft.Container(width=1, height=20, bgcolor=BORDER, margin=pad(h=2))

    preview_btn = ft.IconButton(icon=ft.Icons.VISIBILITY_ROUNDED, icon_color=TEXT_SUB, icon_size=18, tooltip="Preview", on_click=toggle_preview, style=ft.ButtonStyle(padding=ft.Padding(6, 6, 6, 6), shape=ft.RoundedRectangleBorder(radius=6)))

    toolbar = ft.Container(
        content=ft.Row(
            [
                ibtn(ft.Icons.FORMAT_BOLD, "Negrito", lambda _: inserir("**", "**", "negrito")),
                ibtn(ft.Icons.FORMAT_ITALIC, "Itálico", lambda _: inserir("*", "*", "itálico")),
                ibtn(ft.Icons.FORMAT_STRIKETHROUGH, "Tachado", lambda _: inserir("~~", "~~", "texto")),
                tdiv(),
                tbtn("H1", "Título 1", lambda _: inserir("# ", "", "Título")),
                tbtn("H2", "Título 2", lambda _: inserir("## ", "", "Título")),
                tbtn("H3", "Título 3", lambda _: inserir("### ", "", "Título")),
                tdiv(),
                ibtn(ft.Icons.FORMAT_LIST_BULLETED, "Lista", lambda _: inserir("- ", "", "item")),
                ibtn(ft.Icons.FORMAT_LIST_NUMBERED, "Lista numerada", lambda _: inserir("1. ", "", "item")),
                ibtn(ft.Icons.CHECK_BOX_OUTLINED, "Checkbox", lambda _: inserir("- [ ] ", "", "tarefa")),
                tdiv(),
                ibtn(ft.Icons.CODE, "Código inline", lambda _: inserir("`", "`", "código")),
                ibtn(ft.Icons.CODE_ROUNDED, "Bloco de código", lambda _: inserir("```\n", "\n```", "código")),
                ibtn(ft.Icons.FORMAT_QUOTE, "Citação", lambda _: inserir("> ", "", "citação")),
                tdiv(),
                ibtn(ft.Icons.HORIZONTAL_RULE, "Separador", lambda _: inserir("\n---\n", "")),
                ibtn(ft.Icons.LINK_ROUNDED, "Link", lambda _: inserir("[", "](url)", "texto")),
                ft.Container(expand=True),
                preview_btn,
            ],
            scroll="auto", spacing=0, vertical_alignment="center",
        ),
        bgcolor=TOOLBAR, border_radius=ft.BorderRadius(12, 12, 0, 0),
        border=ft.Border.all(1, BORDER), padding=pad(h=8, v=4), height=44,
    )

    word_count = ft.Text("0 palavras", size=10, color=TEXT_DIM)

    def on_change(e):
        v = content_field.value or ""
        w = len(v.split()) if v.strip() else 0
        word_count.value = f"{w} palavra{'s' if w != 1 else ''} · {len(v)} chars"
        word_count.update()

    content_field.on_change = on_change

    save_row = ft.Row(
        [
            word_count,
            ft.Container(expand=True),
            ft.OutlinedButton("Cancelar", style=ft.ButtonStyle(color=TEXT_SUB), on_click=lambda _: on_cancel() if on_cancel else None),
            ft.Container(width=8),
            ft.FilledButton("Guardar", icon=ft.Icons.SAVE_ROUNDED, style=ft.ButtonStyle(bgcolor=ACCENT, color=WHITE), on_click=lambda _: on_save(content_field.value) if on_save else None),
        ],
        vertical_alignment="center",
    )

    return ft.Column(
        [
            toolbar,
            ft.Container(
                content=ft.Stack([ft.Column([content_field], expand=True), preview_container], expand=True),
                expand=True, border=ft.Border.all(1, BORDER), border_radius=ft.BorderRadius(0, 0, 12, 12),
            ),
            ft.Container(height=12),
            save_row,
            ft.Container(height=24),
        ],
        expand=True, spacing=0,
    ), content_field


# ─── APP ─────────────────────────────────────────────────────────────────────


def main(page: ft.Page):
    page.title = "My Digital Garden"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BG
    page.padding = 0
    page.scroll = None
    page.window.maximized = True

    session = Session()
    stack_nav = []
    view_state = {"atual": "grid"}
    sort_state = {"modo": pref_get(session, "sort_modo", "criacao")}
    search_state = {"ativo": False, "query": ""}

    # Guarda referência ao editor de link para poder chamar após renderizar
    _pending_share: dict = {"texto": None}

    def pai_id():
        return stack_nav[-1].id if stack_nav else None

    def pasta_atual_nome():
        return stack_nav[-1].titulo if stack_nav else "My Digital Garden"

    def navegar(pasta=None):
        if pasta is None:
            stack_nav.clear()
        elif pasta not in stack_nav:
            stack_nav.append(pasta)
        view_state["atual"] = "grid"
        _fechar_busca(update=False)
        renderizar()

    def voltar():
        if view_state["atual"] in ("editor", "nota"):
            view_state["atual"] = "grid"
            renderizar()
        elif stack_nav:
            stack_nav.pop()
            renderizar()

    def abrir_link(url):
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        webbrowser.open(url)

    # ── Controles principais ──────────────────────────────────────────────────
    main_content = ft.Container(expand=True)

    # ── AppBar ────────────────────────────────────────────────────────────────
    appbar_title = ft.Text("My Digital Garden", size=17, weight="w700", color=TEXT, overflow="ellipsis", expand=True)

    search_field = ft.TextField(
        hint_text="Buscar notas, links, tags...", hint_style=ft.TextStyle(color=TEXT_DIM, size=14),
        border=ft.InputBorder.NONE, color=TEXT, bgcolor="transparent", cursor_color=ACCENT,
        text_style=ft.TextStyle(size=14), expand=True, content_padding=pad(h=4, v=0),
        autofocus=True, on_change=lambda e: _on_search_change(e.control.value),
    )

    search_row = ft.Row(
        [
            ft.Icon(ft.Icons.SEARCH_ROUNDED, color=TEXT_SUB, size=20),
            search_field,
            ft.IconButton(ft.Icons.CLOSE_ROUNDED, icon_color=TEXT_SUB, icon_size=18, on_click=lambda _: _fechar_busca(), style=ft.ButtonStyle(padding=ft.Padding(4, 4, 4, 4))),
        ],
        vertical_alignment="center", spacing=8, expand=True, visible=False,
    )

    sort_btn = ft.PopupMenuButton(
        icon=ft.Icons.SORT_ROUNDED, icon_color=TEXT_SUB, icon_size=20, tooltip="Ordenar", visible=True,
        items=[
            ft.PopupMenuItem(content=ft.Row([ft.Icon(ft.Icons.SORT_BY_ALPHA_ROUNDED, size=16, color=TEXT_SUB), ft.Text("A → Z", size=13, color=TEXT)], spacing=10), on_click=lambda _: set_sort("az")),
            ft.PopupMenuItem(content=ft.Row([ft.Icon(ft.Icons.SORT_BY_ALPHA_ROUNDED, size=16, color=TEXT_SUB), ft.Text("Z → A", size=13, color=TEXT)], spacing=10), on_click=lambda _: set_sort("za")),
            ft.PopupMenuItem(),
            ft.PopupMenuItem(content=ft.Row([ft.Icon(ft.Icons.SCHEDULE_ROUNDED, size=16, color=TEXT_SUB), ft.Text("Mais recente", size=13, color=TEXT)], spacing=10), on_click=lambda _: set_sort("recente")),
            ft.PopupMenuItem(content=ft.Row([ft.Icon(ft.Icons.HISTORY_ROUNDED, size=16, color=TEXT_SUB), ft.Text("Mais antigo", size=13, color=TEXT)], spacing=10), on_click=lambda _: set_sort("criacao")),
        ],
    )

    search_btn = ft.IconButton(ft.Icons.SEARCH_ROUNDED, icon_color=TEXT_SUB, icon_size=20, tooltip="Buscar", on_click=lambda _: _abrir_busca(), style=ft.ButtonStyle(padding=ft.Padding(8, 8, 8, 8)))

    appbar_normal = ft.Row([appbar_title, search_btn, sort_btn], vertical_alignment="center", spacing=4, expand=True)
    appbar_search_wrap = ft.Container(content=search_row, expand=True, visible=False)

    appbar = ft.Container(
        content=ft.Stack([ft.Container(content=appbar_normal, expand=True), appbar_search_wrap]),
        bgcolor=SURFACE, border=ft.Border(bottom=ft.BorderSide(1, BORDER)),
        padding=pad(h=16, v=12), height=56,
    )

    def _abrir_busca():
        search_state["ativo"] = True
        search_state["query"] = ""
        search_field.value = ""
        appbar_normal.visible = False
        appbar_search_wrap.visible = True
        search_row.visible = True
        appbar.update()
        renderizar_grid()

    def _fechar_busca(update=True):
        search_state["ativo"] = False
        search_state["query"] = ""
        search_field.value = ""
        appbar_normal.visible = True
        appbar_search_wrap.visible = False
        search_row.visible = False
        if update:
            try:
                appbar.update()
                renderizar_grid()
            except Exception:
                pass

    def _on_search_change(query):
        search_state["query"] = query.lower().strip()
        renderizar_grid()

    # ── Bottom Bar ────────────────────────────────────────────────────────────
    fab_btn = ft.Container(
        content=ft.Icon(ft.Icons.ADD_ROUNDED, color=WHITE, size=28),
        bgcolor=ACCENT, width=56, height=56, border_radius=28,
        alignment=ft.alignment.Alignment(0, 0),
        shadow=ft.BoxShadow(blur_radius=16, color="#557C6AF7", offset=ft.Offset(0, 4)),
        on_click=None,
    )

    back_btn = ft.Container(
        content=ft.Column(
            [ft.Icon(ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED, size=20, color=TEXT_SUB), ft.Text("Voltar", size=11, color=TEXT_SUB)],
            horizontal_alignment="center", spacing=2,
        ),
        on_click=lambda _: voltar(), padding=pad(h=16, v=8), border_radius=12, visible=False,
    )

    bottom_bar = ft.Container(
        content=ft.Row(
            [
                ft.Container(content=back_btn, width=80, alignment=ft.alignment.Alignment(0, 0)),
                ft.Container(expand=True),
                ft.Container(content=fab_btn, alignment=ft.alignment.Alignment(0, 0)),
                ft.Container(expand=True),
                ft.Container(width=80),
            ],
            vertical_alignment="center",
        ),
        bgcolor=SURFACE, border=ft.Border(top=ft.BorderSide(1, BORDER)), padding=pad(h=16, t=8, b=16),
    )

    def set_appbar(title, show_back=False, show_sort=True, show_search_btn=True):
        appbar_title.value = title
        back_btn.visible = show_back
        sort_btn.visible = show_sort
        search_btn.visible = show_search_btn
        if not show_search_btn:
            _fechar_busca(update=False)
        appbar.update()
        bottom_bar.update()

    def set_sort(modo):
        sort_state["modo"] = modo
        pref_set(session, "sort_modo", modo)
        renderizar_grid()

    # ── DRAG & DROP ───────────────────────────────────────────────────────────
    def on_drag_complete(src_id, tgt_id):
        src = session.get(Item, src_id)
        tgt = session.get(Item, tgt_id)
        if not src or not tgt or src.id == tgt.id:
            return
        itens = session.query(Item).filter_by(pai_id=src.pai_id).order_by(Item.ordem, Item.id).all()
        ids = [i.id for i in itens]
        if src.id not in ids or tgt.id not in ids:
            return
        ids.remove(src.id)
        ids.insert(ids.index(tgt.id), src.id)
        for nova_ordem, iid in enumerate(ids):
            it = session.get(Item, iid)
            if it:
                it.ordem = nova_ordem
        session.commit()
        renderizar()

    # ── GRID ──────────────────────────────────────────────────────────────────
    def renderizar_grid():
        set_appbar(pasta_atual_nome(), show_back=bool(stack_nav))
        fab_btn.visible = True
        fab_btn.update()

        from sqlalchemy import asc, desc, or_

        modo = sort_state["modo"]
        query = search_state["query"]
        q = session.query(Item)

        if query:
            q = q.filter(Item.tipo != "Pasta")
            q = q.filter(or_(Item.titulo.ilike(f"%{query}%"), Item.conteudo.ilike(f"%{query}%"), Item.tags.any(Tag.nome.ilike(f"%{query}%"))))
        else:
            q = q.filter(Item.pai_id == pai_id())

        if modo == "az":
            q = q.order_by(asc(Item.titulo))
        elif modo == "za":
            q = q.order_by(desc(Item.titulo))
        elif modo == "recente":
            q = q.order_by(desc(Item.data_criacao), desc(Item.id))
        else:
            q = q.order_by(asc(Item.data_criacao), asc(Item.id))

        itens = q.all()
        pastas = [i for i in itens if i.tipo == "Pasta"]
        links = [i for i in itens if i.tipo == "Link"]
        notas = [i for i in itens if i.tipo == "Nota"]
        sections = []

        def make_list(items):
            col = ft.Column(spacing=8)
            for it in items:
                col.controls.append(build_list_item(it, _click_item, _editar, _excluir, on_drag_complete, items))
            return col

        if query:
            resultados = links + notas
            if resultados:
                sections += [section_title(f'RESULTADOS PARA "{query}"'), ft.Container(height=6), make_list(resultados)]
            else:
                sections = [ft.Container(content=ft.Column([ft.Container(height=60), ft.Icon(ft.Icons.SEARCH_OFF_ROUNDED, size=64, color=TEXT_DIM), ft.Container(height=16), ft.Text("Nenhum resultado", size=18, color=TEXT_SUB, weight="w600", text_align="center"), ft.Text(f'Nada encontrado para "{query}".', size=13, color=TEXT_DIM, text_align="center")], horizontal_alignment="center"))]
        else:
            if pastas:
                sections += [section_title("PASTAS"), ft.Container(height=6), make_list(pastas), ft.Container(height=16)]
            if links:
                sections += [section_title("LINKS"), ft.Container(height=6), make_list(links), ft.Container(height=16)]
            if notas:
                sections += [section_title("NOTAS"), ft.Container(height=6), make_list(notas)]
            if not itens:
                sections = [ft.Container(content=ft.Column([ft.Container(height=60), ft.Icon(ft.Icons.YARD_ROUNDED, size=64, color=TEXT_DIM), ft.Container(height=16), ft.Text("Jardim vazio", size=18, color=TEXT_SUB, weight="w600", text_align="center"), ft.Text("Toque em + para adicionar\npastas, links ou notas.", size=13, color=TEXT_DIM, text_align="center")], horizontal_alignment="center"))]

        main_content.content = ft.Column(sections, scroll="auto", expand=True, spacing=0)
        page.update()

    def _click_item(item):
        if item.tipo == "Pasta":
            navegar(item)
        elif item.tipo == "Link":
            abrir_link(item.conteudo or "")
        else:
            ver_nota(item)

    # ── VER NOTA ──────────────────────────────────────────────────────────────
    def ver_nota(item):
        view_state["atual"] = "nota"
        set_appbar(item.titulo, show_back=True, show_sort=False, show_search_btn=False)
        fab_btn.visible = False
        fab_btn.update()

        cabecalho = [ft.Row([ft.Container(expand=True), ft.IconButton(ft.Icons.EDIT_ROUNDED, icon_color=TEXT_SUB, on_click=lambda _: mostrar_editor(item, "Nota"), tooltip="Editar")])]
        if item.tags:
            cabecalho.append(ft.Row([tag_chip(t) for t in item.tags], spacing=6, wrap=True))
            cabecalho.append(ft.Container(height=8))

        main_content.content = ft.Column(
            cabecalho + [ft.Column([ft.Markdown(item.conteudo or "_Nota vazia._", selectable=True, extension_set="gitHubFlavored", code_theme="atom-one-dark", on_tap_link=lambda e: abrir_link(e.data))], scroll="auto", expand=True)],
            expand=True, spacing=0,
        )
        page.update()

    # ── EDITOR DE TAGS ────────────────────────────────────────────────────────
    def build_tag_editor(tags_state):
        chips_row = ft.Row(spacing=6, wrap=True)
        sugest_row = ft.Row(spacing=6, wrap=True)
        nova_field = ft.TextField(
            hint_text="Nova tag...", hint_style=ft.TextStyle(color=TEXT_DIM, size=12),
            border_color=BORDER, focused_border_color=ACCENT, color=TEXT, bgcolor=SURFACE,
            border_radius=20, content_padding=pad(h=12, v=6), text_style=ft.TextStyle(size=12), width=130,
        )

        def refresh():
            chips_row.controls = [tag_chip(t, on_remove=remover) for t in tags_state["selecionadas"]]
            ids_sel = {t.id for t in tags_state["selecionadas"]}
            todas = session.query(Tag).order_by(Tag.nome).all()
            sugest_row.controls = [
                ft.GestureDetector(
                    content=ft.Container(content=ft.Text(f"#{t.nome}", size=11, color=t.cor or ACCENT, weight="w600"), bgcolor=CARD_HOV, border_radius=20, padding=pad(h=10, v=4), border=ft.Border.all(1, BORDER)),
                    on_tap=lambda e, tag=t: adicionar(tag),
                )
                for t in todas if t.id not in ids_sel
            ]
            try:
                chips_row.update()
                sugest_row.update()
            except Exception:
                pass

        def adicionar(tag):
            if tag not in tags_state["selecionadas"]:
                tags_state["selecionadas"].append(tag)
            refresh()

        def remover(tag):
            tags_state["selecionadas"] = [t for t in tags_state["selecionadas"] if t.id != tag.id]
            refresh()

        def criar_tag(e):
            import random
            nome = nova_field.value.strip().lower().replace(" ", "-")
            if not nome:
                return
            existente = session.query(Tag).filter_by(nome=nome).first()
            if existente:
                adicionar(existente)
            else:
                nova = Tag(nome=nome, cor=random.choice(TAG_CORES))
                session.add(nova)
                session.commit()
                adicionar(nova)
            nova_field.value = ""
            try:
                nova_field.update()
            except Exception:
                pass

        nova_field.on_submit = criar_tag
        refresh()

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("Tags", size=12, color=TEXT_SUB, weight="w600"),
                    ft.Container(height=6),
                    ft.Row([chips_row, nova_field, ft.IconButton(ft.Icons.ADD_ROUNDED, icon_color=ACCENT, icon_size=18, tooltip="Adicionar tag", on_click=criar_tag, style=ft.ButtonStyle(padding=ft.Padding(4, 4, 4, 4)))], vertical_alignment="center", wrap=True, spacing=6),
                    ft.Container(height=6),
                    sugest_row,
                ],
                spacing=0,
            ),
            bgcolor=CARD, border_radius=12, padding=pad(h=14, v=12), border=ft.Border.all(1, BORDER),
        )

    # ── EDITOR ────────────────────────────────────────────────────────────────
    def mostrar_editor(item_existente=None, tipo="Nota"):
        view_state["atual"] = "editor"
        is_nota = tipo == "Nota"
        header = ("Editar" if item_existente else "Novo") + f" {tipo}"
        set_appbar(header, show_back=True, show_sort=False, show_search_btn=False)
        fab_btn.visible = False
        fab_btn.update()

        titulo_input = ft.TextField(
            label="Titulo", value=item_existente.titulo if item_existente else "",
            autofocus=not is_nota, border_color=BORDER, focused_border_color=ACCENT,
            color=TEXT, label_style=ft.TextStyle(color=TEXT_SUB), bgcolor=SURFACE, border_radius=10,
        )

        if is_nota:
            tags_state = {"selecionadas": list(item_existente.tags) if item_existente else []}
            tag_editor = build_tag_editor(tags_state)

            def on_save(content):
                if not titulo_input.value.strip():
                    titulo_input.error_text = "Campo obrigatorio"
                    titulo_input.update()
                    return
                import time
                if item_existente and item_existente.id if hasattr(item_existente, "id") else False:
                    item_existente.titulo = titulo_input.value.strip()
                    item_existente.conteudo = content
                    item_existente.tags = tags_state["selecionadas"]
                else:
                    novo = Item(titulo=titulo_input.value.strip(), conteudo=content, tipo=tipo, pai_id=pai_id(), data_criacao=int(time.time()))
                    novo.tags = tags_state["selecionadas"]
                    session.add(novo)
                session.commit()
                view_state["atual"] = "grid"
                renderizar()

            editor_widget, _ = build_note_editor(
                initial_value=item_existente.conteudo if item_existente else "",
                on_save=on_save, on_cancel=voltar, on_tap_link=lambda e: abrir_link(e.data),
            )

            main_content.content = ft.Column(
                [ft.Container(height=8), titulo_input, ft.Container(height=12), tag_editor, ft.Container(height=12), editor_widget],
                expand=True, spacing=0, scroll="auto",
            )

        else:
            conteudo_input = ft.TextField(
                label="URL", value=item_existente.conteudo if item_existente else "",
                border_color=BORDER, focused_border_color=ACCENT, color=TEXT,
                label_style=ft.TextStyle(color=TEXT_SUB), bgcolor=SURFACE, border_radius=10,
                keyboard_type=ft.KeyboardType.URL,
            )

            def salvar(e):
                if not titulo_input.value.strip():
                    titulo_input.error_text = "Campo obrigatorio"
                    titulo_input.update()
                    return
                import time
                if item_existente and hasattr(item_existente, "id") and item_existente.id:
                    item_existente.titulo = titulo_input.value.strip()
                    item_existente.conteudo = conteudo_input.value
                else:
                    session.add(Item(titulo=titulo_input.value.strip(), conteudo=conteudo_input.value, tipo=tipo, pai_id=pai_id(), data_criacao=int(time.time())))
                session.commit()
                view_state["atual"] = "grid"
                renderizar()

            cor_btn, cor_bg = chip_cor(tipo)
            main_content.content = ft.Column(
                [
                    ft.Container(height=8),
                    ft.Container(content=ft.Row([ft.Container(content=ft.Icon(icone_tipo(tipo), size=16, color=cor_btn), bgcolor=cor_bg, border_radius=8, padding=8), ft.Text(header, size=15, weight="w600", color=TEXT_SUB)], spacing=10), padding=pad(b=4)),
                    divider(),
                    ft.Container(height=16),
                    titulo_input,
                    ft.Container(height=12),
                    conteudo_input,
                    ft.Container(height=24),
                    ft.Row([ft.Container(expand=True), ft.OutlinedButton("Cancelar", style=ft.ButtonStyle(color=TEXT_SUB), on_click=lambda _: voltar()), ft.Container(width=8), ft.FilledButton("Guardar", icon=ft.Icons.SAVE_ROUNDED, style=ft.ButtonStyle(bgcolor=ACCENT, color=WHITE), on_click=salvar)]),
                    ft.Container(height=32),
                ],
                scroll="auto", expand=True, spacing=0,
            )

        page.update()

    # ── SHARE INTENT ─────────────────────────────────────────────────────────

    def processar_share(texto: str):
        """
        Recebe texto/URL compartilhado e abre o editor correto.
        - URL  → editor de Link com URL pré-preenchida
        - Texto → editor de Nota com conteúdo pré-preenchido
        """
        is_url = texto.startswith("http://") or texto.startswith("https://")

        class _FakeItem:
            id = None
            titulo = ""
            conteudo = None
            tipo = ""
            tags = []

        fake = _FakeItem()

        if is_url:
            fake.tipo = "Link"
            fake.conteudo = texto
            mostrar_editor(fake, "Link")
        else:
            fake.tipo = "Nota"
            fake.conteudo = texto
            mostrar_editor(fake, "Nota")

    def verificar_share_intent():
        """Verifica se há conteúdo compartilhado pendente e processa."""
        texto = consume_shared_intent()
        if texto:
            processar_share(texto)

    # on_app_link: recebe URLs vindas de ACTION_VIEW ou de shares que o Flet
    # detecta como deep link (fallback para o caminho via arquivo)
    def handle_app_link(e):
        url = (e.data or "").strip()
        if url.startswith("http"):
            processar_share(url)

    page.on_app_link = handle_app_link

    # on_app_lifecycle_state_change: disparado quando o app volta ao foreground.
    # É o momento em que o arquivo escrito pela MainActivity já está disponível.
    def handle_lifecycle(e):
        if e.data == "resume":
            verificar_share_intent()

    page.on_app_lifecycle_state_change = handle_lifecycle

    # ── EXCLUIR ───────────────────────────────────────────────────────────────
    def _excluir(item):
        def confirmar(e):
            session.delete(item)
            session.commit()
            dlg.open = False
            renderizar()

        def fechar(e):
            dlg.open = False
            page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Excluir item?", color=TEXT),
            content=ft.Text(f'"{item.titulo}" sera removido permanentemente.', color=TEXT_SUB),
            bgcolor=SURFACE,
            actions=[ft.TextButton("Cancelar", on_click=fechar), ft.FilledButton("Excluir", style=ft.ButtonStyle(bgcolor=RED, color=WHITE), on_click=confirmar)],
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def _editar(item):
        mostrar_editor(item, item.tipo)

    # ── NOVA PASTA ────────────────────────────────────────────────────────────
    def nova_pasta():
        tf = ft.TextField(label="Nome da pasta", autofocus=True, border_color=BORDER, focused_border_color=ACCENT, color=TEXT, label_style=ft.TextStyle(color=TEXT_SUB), bgcolor=SURFACE, border_radius=10)

        def criar(e):
            if tf.value.strip():
                import time
                total = session.query(Item).filter_by(pai_id=pai_id()).count()
                session.add(Item(titulo=tf.value.strip(), tipo="Pasta", pai_id=pai_id(), ordem=total, data_criacao=int(time.time())))
                session.commit()
                dlg.open = False
                renderizar()

        def fechar(e):
            dlg.open = False
            page.update()

        dlg = ft.AlertDialog(
            title=ft.Row([ft.Icon(ft.Icons.FOLDER_ROUNDED, color=ACCENT, size=20), ft.Text("Nova Pasta", color=TEXT, weight="w600")], spacing=8),
            content=ft.Container(tf, width=400), bgcolor=SURFACE,
            actions=[ft.TextButton("Cancelar", on_click=fechar), ft.FilledButton("Criar", style=ft.ButtonStyle(bgcolor=ACCENT, color=WHITE), on_click=criar)],
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    # ── BOTTOM SHEET ──────────────────────────────────────────────────────────
    def _menu_tile(icon, label, cor, fn):
        def hover(e):
            e.control.bgcolor = CARD_HOV if e.data == "true" else "transparent"
            e.control.update()

        return ft.Container(
            content=ft.Row([ft.Container(content=ft.Icon(icon, size=20, color=cor), bgcolor=chip_cor(label)[1], border_radius=10, padding=10, width=44, height=44), ft.Text(label, size=15, weight="w500", color=TEXT)], spacing=16, vertical_alignment="center"),
            on_click=fn, border_radius=12, padding=pad(h=8, v=10), on_hover=hover,
        )

    bs = ft.BottomSheet(
        ft.Container(
            content=ft.Column(
                [
                    ft.Container(content=ft.Container(width=40, height=4, bgcolor=BORDER, border_radius=2), alignment=ft.alignment.Alignment(0, 0), padding=pad(t=14, b=10)),
                    ft.Text("Adicionar", size=14, color=TEXT_SUB, weight="w700", text_align="center"),
                    ft.Container(height=8),
                    _menu_tile(ft.Icons.FOLDER_ROUNDED, "Pasta", ACCENT, lambda _: _bs_fechar(nova_pasta)),
                    _menu_tile(ft.Icons.OPEN_IN_NEW_ROUNDED, "Link", ACCENT2, lambda _: _bs_fechar(lambda: mostrar_editor(tipo="Link"))),
                    _menu_tile(ft.Icons.ARTICLE_ROUNDED, "Nota", GREEN, lambda _: _bs_fechar(lambda: mostrar_editor(tipo="Nota"))),
                    ft.Container(height=20),
                ],
                tight=True, spacing=2, horizontal_alignment="stretch",
            ),
            bgcolor=SURFACE, border_radius=ft.BorderRadius(top_left=20, top_right=20, bottom_left=0, bottom_right=0), padding=pad(h=20),
        )
    )
    page.overlay.append(bs)

    def _bs_fechar(fn):
        bs.open = False
        page.update()
        fn()

    fab_btn.on_click = lambda _: [setattr(bs, "open", True), page.update()]

    # ── LAYOUT PRINCIPAL ──────────────────────────────────────────────────────
    page.add(
        ft.SafeArea(
            content=ft.Column(
                [appbar, ft.Container(content=main_content, expand=True, padding=pad(h=16, t=16, b=8)), bottom_bar],
                expand=True, spacing=0,
            ),
            expand=True,
        )
    )

    # Renderiza a grid e só então verifica share intent pendente
    renderizar_grid()
    verificar_share_intent()

    def renderizar():
        if view_state["atual"] == "grid":
            renderizar_grid()


if __name__ == "__main__":
    ft.run(main)