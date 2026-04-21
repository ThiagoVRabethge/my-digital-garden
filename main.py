# -*- coding: utf-8 -*-
import io
import sys
import webbrowser

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import flet as ft
from sqlalchemy import JSON, Column, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import backref, declarative_base, relationship, sessionmaker

Base = declarative_base()
engine = create_engine("sqlite:///vault.db")
Session = sessionmaker(bind=engine)


class Item(Base):
    __tablename__ = "itens"
    id = Column(Integer, primary_key=True)
    titulo = Column(String(100), nullable=False)
    conteudo = Column(Text, nullable=True)
    tipo = Column(String(20))
    pai_id = Column(Integer, ForeignKey("itens.id"), nullable=True)
    ordem = Column(Integer, default=0)
    data_criacao = Column(Integer, default=0)  # timestamp unix
    filhos = relationship(
        "Item",
        backref=backref("pai", remote_side=[id]),
        cascade="all, delete-orphan",
    )
    tags = Column(JSON, default=[])  # Lista de tags para cada item


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
TEXT = "#E8E8F0"
TEXT_SUB = "#6B6B80"
TEXT_DIM = "#3D3D50"
WHITE = "#FFFFFF"
RED = "#C0392B"
TOOLBAR = "#18181D"


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


# ─── DRAG & DROP LIST ITEM ────────────────────────────────────────────────────


def build_list_item(
    item, on_click, on_edit, on_delete, on_drag_complete, all_items_ref
):
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

    # Visualização das tags
    tags_row = ft.Container(height=0)
    if item.tags:
        tags_row = ft.Row(
            [
                ft.Container(
                    content=ft.Text(f"#{tag}", size=10, color=TEXT_SUB),
                    bgcolor=CARD_HOV,
                    border_radius=6,
                    padding=ft.Padding(4, 2, 4, 2),
                )
                for tag in item.tags
            ],
            spacing=4,
            wrap=True,
        )

    card_content = ft.Column(
        [
            ft.Row(
                [
                    # Handle de drag
                    ft.Container(
                        content=ft.Icon(
                            ft.Icons.DRAG_INDICATOR_ROUNDED, size=18, color=TEXT_DIM
                        ),
                        padding=pad(r=4),
                    ),
                    ft.Container(
                        content=ft.Icon(icone, size=20, color=cor),
                        bgcolor=bg,
                        border_radius=10,
                        padding=10,
                        width=44,
                        height=44,
                    ),
                    ft.Container(width=12),
                    ft.Column(
                        [
                            ft.Text(
                                item.titulo,
                                size=15,
                                weight="w600",
                                color=TEXT,
                                max_lines=1,
                                overflow="ellipsis",
                            ),
                            ft.Text(
                                preview,
                                size=12,
                                color=TEXT_SUB,
                                max_lines=1,
                                overflow="ellipsis",
                            )
                            if preview
                            else ft.Container(height=0),
                            tags_row,  # Adiciona as tags aqui
                        ],
                        spacing=2,
                        expand=True,
                        alignment="center",
                    ),
                    ft.Container(width=4),
                    menu,
                ],
                vertical_alignment="center",
            ),
        ],
        spacing=0,
    )

    card = ft.Container(
        content=card_content,
        bgcolor=CARD,
        border_radius=14,
        padding=pad(h=12, v=12),
        on_click=lambda e, i=item: on_click(i),
    )

    # Drop target: quando outro item é solto em cima deste
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
        tgt_id = item.id
        if src_id != tgt_id:
            on_drag_complete(src_id, tgt_id)

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

    draggable = ft.Draggable(
        group="items",
        data=str(item.id),
        content=drop_target,
        content_when_dragging=ft.Container(
            content=ft.Row(
                [
                    ft.Icon(icone, size=18, color=cor),
                    ft.Text(item.titulo, size=14, color=TEXT_SUB, max_lines=1),
                ],
                spacing=10,
            ),
            bgcolor=CARD_DRG,
            border_radius=14,
            padding=pad(h=16, v=12),
            border=ft.Border.all(1, ACCENT),
            opacity=0.85,
        ),
        content_feedback=ft.Container(
            content=ft.Row(
                [
                    ft.Icon(icone, size=18, color=cor),
                    ft.Text(item.titulo, size=14, color=TEXT, max_lines=1),
                ],
                spacing=10,
            ),
            bgcolor=CARD_DRG,
            border_radius=14,
            padding=pad(h=16, v=12),
            border=ft.Border.all(1, ACCENT),
            shadow=ft.BoxShadow(blur_radius=20, color="#44000000"),
        ),
    )

    return draggable


def section_title(text):
    return ft.Text(text, size=11, weight="w700", color=TEXT_DIM)


# ─── EDITOR DE NOTAS COM TOOLBAR ─────────────────────────────────────────────


def build_note_editor(initial_value="", on_save=None, on_cancel=None):
    """
    Editor estilo markdown com toolbar de formatação e preview ao vivo.
    """
    content_field = ft.TextField(
        value=initial_value,
        multiline=True,
        min_lines=16,
        max_lines=None,
        border_color=BORDER,
        focused_border_color=ACCENT,
        color=TEXT,
        bgcolor=SURFACE,
        border_radius=ft.BorderRadius(0, 0, 12, 12),
        text_style=ft.TextStyle(size=14, font_family="monospace"),
        cursor_color=ACCENT,
        expand=True,
        content_padding=pad(h=16, v=14),
    )

    preview_col = ft.Column(
        [
            ft.Markdown(
                initial_value or "_Comece a escrever..._",
                selectable=True,
                extension_set="gitHubFlavored",
                code_theme="atom-one-dark",
            )
        ],
        scroll="auto",
        expand=True,
    )

    preview_container = ft.Container(
        content=preview_col,
        expand=True,
        padding=pad(h=16, v=14),
        bgcolor=SURFACE,
        border_radius=ft.BorderRadius(0, 0, 12, 12),
        border=ft.Border.all(1, BORDER),
        visible=False,
    )

    mode = {"preview": False}

    def atualizar_preview():
        md = preview_col.controls[0]
        md.value = content_field.value or "_Comece a escrever..._"
        preview_col.update()

    def toggle_preview(e):
        mode["preview"] = not mode["preview"]
        content_field.visible = not mode["preview"]
        preview_container.visible = mode["preview"]
        preview_btn.icon = (
            ft.Icons.EDIT_ROUNDED if mode["preview"] else ft.Icons.VISIBILITY_ROUNDED
        )
        preview_btn.tooltip = "Editar" if mode["preview"] else "Preview"
        if mode["preview"]:
            atualizar_preview()
        content_field.update()
        preview_container.update()
        preview_btn.update()

    def inserir(antes, depois="", placeholder="texto"):
        """Insere sintaxe markdown na posição do cursor."""
        v = content_field.value or ""
        sel_start = content_field.selection_start or len(v)
        sel_end = content_field.selection_end or sel_start
        selecionado = v[sel_start:sel_end] if sel_start != sel_end else placeholder
        novo = v[:sel_start] + antes + selecionado + depois + v[sel_end:]
        content_field.value = novo
        content_field.update()
        content_field.focus()

    def _tbtn_text(label, tooltip, fn):
        return ft.TextButton(
            label,
            tooltip=tooltip,
            on_click=fn,
            style=ft.ButtonStyle(
                color=TEXT_SUB,
                padding=ft.Padding(6, 4, 6, 4),
                shape=ft.RoundedRectangleBorder(radius=6),
            ),
        )

    def toolbar_btn(icon, tooltip, fn, color=TEXT_SUB):
        return ft.IconButton(
            icon=icon,
            icon_color=color,
            icon_size=18,
            tooltip=tooltip,
            on_click=fn,
            style=ft.ButtonStyle(
                padding=ft.Padding(6, 6, 6, 6),
                shape=ft.RoundedRectangleBorder(radius=6),
            ),
        )

    def toolbar_divider():
        return ft.Container(width=1, height=20, bgcolor=BORDER, margin=pad(h=2))

    preview_btn = ft.IconButton(
        icon=ft.Icons.VISIBILITY_ROUNDED,
        icon_color=TEXT_SUB,
        icon_size=18,
        tooltip="Preview",
        on_click=toggle_preview,
        style=ft.ButtonStyle(
            padding=ft.Padding(6, 6, 6, 6),
            shape=ft.RoundedRectangleBorder(radius=6),
        ),
    )

    toolbar = ft.Container(
        content=ft.Row(
            [
                toolbar_btn(
                    ft.Icons.FORMAT_BOLD,
                    "Negrito (** **)",
                    lambda _: inserir("**", "**", "negrito"),
                ),
                toolbar_btn(
                    ft.Icons.FORMAT_ITALIC,
                    "Itálico (* *)",
                    lambda _: inserir("*", "*", "itálico"),
                ),
                toolbar_btn(
                    ft.Icons.FORMAT_STRIKETHROUGH,
                    "Tachado (~~ ~~)",
                    lambda _: inserir("~~", "~~", "texto"),
                ),
                toolbar_divider(),
                _tbtn_text("H1", "Título 1", lambda _: inserir("# ", "", "Título")),
                _tbtn_text("H2", "Título 2", lambda _: inserir("## ", "", "Título")),
                _tbtn_text("H3", "Título 3", lambda _: inserir("### ", "", "Título")),
                toolbar_divider(),
                toolbar_btn(
                    ft.Icons.FORMAT_LIST_BULLETED,
                    "Lista",
                    lambda _: inserir("- ", "", "item"),
                ),
                toolbar_btn(
                    ft.Icons.FORMAT_LIST_NUMBERED,
                    "Lista numerada",
                    lambda _: inserir("1. ", "", "item"),
                ),
                toolbar_btn(
                    ft.Icons.CHECK_BOX_OUTLINED,
                    "Checkbox",
                    lambda _: inserir("- [ ] ", "", "tarefa"),
                ),
                toolbar_divider(),
                toolbar_btn(
                    ft.Icons.CODE,
                    "Código inline",
                    lambda _: inserir("`", "`", "código"),
                ),
                toolbar_btn(
                    ft.Icons.CODE_ROUNDED,
                    "Bloco de código",
                    lambda _: inserir("```\n", "\n```", "código"),
                ),
                toolbar_btn(
                    ft.Icons.FORMAT_QUOTE,
                    "Citação",
                    lambda _: inserir("> ", "", "citação"),
                ),
                toolbar_divider(),
                toolbar_btn(
                    ft.Icons.HORIZONTAL_RULE,
                    "Separador",
                    lambda _: inserir("\n---\n", "", ""),
                ),
                toolbar_btn(
                    ft.Icons.LINK_ROUNDED,
                    "Link",
                    lambda _: inserir("[", "](url)", "texto"),
                ),
                ft.Container(expand=True),
                preview_btn,
            ],
            scroll="auto",
            spacing=0,
            vertical_alignment="center",
        ),
        bgcolor=TOOLBAR,
        border_radius=ft.BorderRadius(12, 12, 0, 0),
        border=ft.Border.all(1, BORDER),
        padding=pad(h=8, v=4),
        height=44,
    )

    editor_stack = ft.Stack(
        [
            ft.Column([content_field], expand=True),
            ft.Column([preview_container], expand=True),
        ],
        expand=True,
    )

    # Conta palavras e caracteres
    word_count = ft.Text("0 palavras", size=10, color=TEXT_DIM)

    def on_change(e):
        v = content_field.value or ""
        words = len(v.split()) if v.strip() else 0
        word_count.value = (
            f"{words} palavra{'s' if words != 1 else ''} · {len(v)} chars"
        )
        word_count.update()

    content_field.on_change = on_change

    save_row = ft.Row(
        [
            word_count,
            ft.Container(expand=True),
            ft.OutlinedButton(
                "Cancelar",
                style=ft.ButtonStyle(color=TEXT_SUB),
                on_click=lambda _: on_cancel() if on_cancel else None,
            ),
            ft.Container(width=8),
            ft.FilledButton(
                "Guardar",
                icon=ft.Icons.SAVE_ROUNDED,
                style=ft.ButtonStyle(bgcolor=ACCENT, color=WHITE),
                on_click=lambda _: on_save(content_field.value) if on_save else None,
            ),
        ],
        vertical_alignment="center",
    )

    return ft.Column(
        [
            toolbar,
            ft.Container(
                content=ft.Stack(
                    [
                        ft.Column([content_field], expand=True),
                        preview_container,
                    ],
                    expand=True,
                ),
                expand=True,
                border=ft.Border.all(1, BORDER),
                border_radius=ft.BorderRadius(0, 0, 12, 12),
            ),
            ft.Container(height=12),
            save_row,
            ft.Container(height=24),
        ],
        expand=True,
        spacing=0,
    ), content_field


# ─── APP ─────────────────────────────────────────────────────────────────────


def main(page: ft.Page):
    page.title = "My Digital Garden"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BG
    page.padding = 0
    page.scroll = None

    session = Session()
    stack_nav = []
    view_state = {"atual": "grid"}
    _modo_salvo = pref_get(session, "sort_modo", "criacao")
    sort_state = {"modo": _modo_salvo}

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

    # ── AppBar com Pesquisa ────────────────────────────────────────────────────
    main_content = ft.Container(expand=True)
    appbar_title = ft.Text(
        "My Digital Garden",
        size=17,
        weight="w700",
        color=TEXT,
        overflow="ellipsis",
        expand=True,
    )
    back_btn = ft.IconButton(
        ft.Icons.ARROW_BACK_ROUNDED,
        icon_color=TEXT_SUB,
        on_click=lambda _: voltar(),
        visible=False,
    )

    # Campo de pesquisa
    search_field = ft.TextField(
        hint_text="Pesquisar por título ou tags...",
        border_color=BORDER,
        focused_border_color=ACCENT,
        color=TEXT,
        hint_style=ft.TextStyle(color=TEXT_DIM),
        bgcolor=SURFACE,
        border_radius=10,
        expand=True,
        on_change=lambda e: filtrar_itens(e.control.value),
        prefix_icon=ft.Icon(ft.Icons.SEARCH_ROUNDED, size=18, color=TEXT_SUB),
    )

    sort_btn = ft.PopupMenuButton(
        icon=ft.Icons.SORT_ROUNDED,
        icon_color=TEXT_SUB,
        icon_size=20,
        tooltip="Ordenar",
        visible=True,
        items=[
            ft.PopupMenuItem(
                content=ft.Row(
                    [
                        ft.Icon(
                            ft.Icons.SORT_BY_ALPHA_ROUNDED, size=16, color=TEXT_SUB
                        ),
                        ft.Text("A → Z", size=13, color=TEXT),
                    ],
                    spacing=10,
                ),
                on_click=lambda _: set_sort("az"),
            ),
            ft.PopupMenuItem(
                content=ft.Row(
                    [
                        ft.Icon(
                            ft.Icons.SORT_BY_ALPHA_ROUNDED, size=16, color=TEXT_SUB
                        ),
                        ft.Text("Z → A", size=13, color=TEXT),
                    ],
                    spacing=10,
                ),
                on_click=lambda _: set_sort("za"),
            ),
            ft.PopupMenuItem(),
            ft.PopupMenuItem(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.SCHEDULE_ROUNDED, size=16, color=TEXT_SUB),
                        ft.Text("Mais recente", size=13, color=TEXT),
                    ],
                    spacing=10,
                ),
                on_click=lambda _: set_sort("recente"),
            ),
            ft.PopupMenuItem(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.HISTORY_ROUNDED, size=16, color=TEXT_SUB),
                        ft.Text("Mais antigo", size=13, color=TEXT),
                    ],
                    spacing=10,
                ),
                on_click=lambda _: set_sort("criacao"),
            ),
        ],
    )

    appbar = ft.Container(
        content=ft.Row(
            [back_btn, appbar_title, search_field, sort_btn],
            vertical_alignment="center",
            spacing=4,
        ),
        bgcolor=SURFACE,
        border=ft.Border(bottom=ft.BorderSide(1, BORDER)),
        padding=pad(h=8, v=12),
        height=56,
    )

    def set_appbar(title, show_back=False, show_sort=True):
        appbar_title.value = title
        back_btn.visible = show_back
        sort_btn.visible = show_sort
        appbar.update()

    def set_sort(modo):
        sort_state["modo"] = modo
        pref_set(session, "sort_modo", modo)
        renderizar()

    # ── Função de Filtragem ───────────────────────────────────────────────────
    def filtrar_itens(texto):
        if not texto:
            renderizar()
            return

        itens = session.query(Item).filter_by(pai_id=pai_id()).all()
        itens_filtrados = [
            item
            for item in itens
            if texto.lower() in item.titulo.lower()
            or any(texto.lower() in tag.lower() for tag in (item.tags or []))
        ]
        renderizar_grid(itens_filtrados)

    # ── DRAG & DROP ───────────────────────────────────────────────────────────
    def on_drag_complete(src_id, tgt_id):
        """Move src para a posição de tgt, deslocando os demais."""
        src = session.get(Item, src_id)
        tgt = session.get(Item, tgt_id)
        if not src or not tgt or src.id == tgt.id:
            return
        # Reordena todos os itens do mesmo nível
        itens = (
            session.query(Item)
            .filter_by(pai_id=src.pai_id)
            .order_by(Item.ordem, Item.id)
            .all()
        )
        ids = [i.id for i in itens]
        if src.id not in ids or tgt.id not in ids:
            return
        ids.remove(src.id)
        tgt_pos = ids.index(tgt.id)
        ids.insert(tgt_pos, src.id)
        for nova_ordem, iid in enumerate(ids):
            item = session.get(Item, iid)
            if item:
                item.ordem = nova_ordem
        session.commit()
        renderizar()

    # ── GRID ──────────────────────────────────────────────────────────────────
    def renderizar_grid(itens=None):
        set_appbar(pasta_atual_nome(), show_back=bool(stack_nav))
        page.floating_action_button.visible = True

        itens = itens or session.query(Item).filter_by(pai_id=pai_id()).all()
        modo = sort_state["modo"]
        if modo == "az":
            itens = sorted(itens, key=lambda x: x.titulo)
        elif modo == "za":
            itens = sorted(itens, key=lambda x: x.titulo, reverse=True)
        elif modo == "recente":
            itens = sorted(itens, key=lambda x: x.data_criacao, reverse=True)
        else:  # criacao (mais antigo)
            itens = sorted(itens, key=lambda x: x.data_criacao)

        pastas = [i for i in itens if i.tipo == "Pasta"]
        links = [i for i in itens if i.tipo == "Link"]
        notas = [i for i in itens if i.tipo == "Nota"]

        sections = []

        def make_list(items):
            col = ft.Column(spacing=8)
            for it in items:
                col.controls.append(
                    build_list_item(
                        it, _click_item, _editar, _excluir, on_drag_complete, items
                    )
                )
            return col

        if pastas:
            sections += [
                section_title("PASTAS"),
                ft.Container(height=6),
                make_list(pastas),
                ft.Container(height=16),
            ]
        if links:
            sections += [
                section_title("LINKS"),
                ft.Container(height=6),
                make_list(links),
                ft.Container(height=16),
            ]
        if notas:
            sections += [
                section_title("NOTAS"),
                ft.Container(height=6),
                make_list(notas),
            ]

        if not itens:
            sections = [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Container(height=60),
                            ft.Icon(ft.Icons.YARD_ROUNDED, size=64, color=TEXT_DIM),
                            ft.Container(height=16),
                            ft.Text(
                                "Jardim vazio",
                                size=18,
                                color=TEXT_SUB,
                                weight="w600",
                                text_align="center",
                            ),
                            ft.Text(
                                "Toque em + para adicionar\npastas, links ou notas.",
                                size=13,
                                color=TEXT_DIM,
                                text_align="center",
                            ),
                        ],
                        horizontal_alignment="center",
                    ),
                )
            ]

        main_content.content = ft.Column(
            sections,
            scroll="auto",
            expand=True,
            spacing=0,
        )
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
        set_appbar(item.titulo, show_back=True, show_sort=False)
        page.floating_action_button.visible = False

        main_content.content = ft.Column(
            [
                ft.Row(
                    [
                        ft.Container(expand=True),
                        ft.IconButton(
                            ft.Icons.EDIT_ROUNDED,
                            icon_color=TEXT_SUB,
                            on_click=lambda _: mostrar_editor(item, "Nota"),
                            tooltip="Editar",
                        ),
                    ]
                ),
                ft.Column(
                    [
                        ft.Markdown(
                            item.conteudo or "_Nota vazia._",
                            selectable=True,
                            extension_set="gitHubFlavored",
                            code_theme="atom-one-dark",
                        )
                    ],
                    scroll="auto",
                    expand=True,
                ),
            ],
            expand=True,
            spacing=0,
        )
        page.update()

    # ── EDITOR ────────────────────────────────────────────────────────────────
    def mostrar_editor(item_existente=None, tipo="Nota"):
        view_state["atual"] = "editor"
        is_nota = tipo == "Nota"
        header = ("Editar" if item_existente else "Novo") + f" {tipo}"
        set_appbar(header, show_back=True, show_sort=False)
        page.floating_action_button.visible = False

        titulo_input = ft.TextField(
            label="Titulo",
            value=item_existente.titulo if item_existente else "",
            autofocus=not is_nota,
            border_color=BORDER,
            focused_border_color=ACCENT,
            color=TEXT,
            label_style=ft.TextStyle(color=TEXT_SUB),
            bgcolor=SURFACE,
            border_radius=10,
        )

        # Campo de tags
        tags_input = ft.TextField(
            label="Tags (separadas por vírgula)",
            value=", ".join(item_existente.tags)
            if item_existente and item_existente.tags
            else "",
            border_color=BORDER,
            focused_border_color=ACCENT,
            color=TEXT,
            label_style=ft.TextStyle(color=TEXT_SUB),
            bgcolor=SURFACE,
            border_radius=10,
        )

        if is_nota:
            # Editor markdown completo
            def on_save(content):
                if not titulo_input.value.strip():
                    titulo_input.error_text = "Campo obrigatorio"
                    titulo_input.update()
                    return
                tags = (
                    [tag.strip() for tag in tags_input.value.split(",")]
                    if tags_input.value
                    else []
                )
                if item_existente:
                    item_existente.titulo = titulo_input.value.strip()
                    item_existente.conteudo = content
                    item_existente.tags = tags
                else:
                    import time

                    session.add(
                        Item(
                            titulo=titulo_input.value.strip(),
                            conteudo=content,
                            tipo=tipo,
                            pai_id=pai_id(),
                            data_criacao=int(time.time()),
                            tags=tags,
                        )
                    )
                session.commit()
                view_state["atual"] = "grid"
                renderizar()

            editor_widget, _ = build_note_editor(
                initial_value=item_existente.conteudo if item_existente else "",
                on_save=on_save,
                on_cancel=voltar,
            )

            main_content.content = ft.Column(
                [
                    ft.Container(height=8),
                    titulo_input,
                    ft.Container(height=8),
                    tags_input,
                    ft.Container(height=12),
                    editor_widget,
                ],
                expand=True,
                spacing=0,
                scroll="auto",
            )

        else:
            # Editor simples para Link
            conteudo_input = ft.TextField(
                label="URL",
                value=item_existente.conteudo if item_existente else "",
                border_color=BORDER,
                focused_border_color=ACCENT,
                color=TEXT,
                label_style=ft.TextStyle(color=TEXT_SUB),
                bgcolor=SURFACE,
                border_radius=10,
                keyboard_type=ft.KeyboardType.URL,
            )

            def salvar(e):
                if not titulo_input.value.strip():
                    titulo_input.error_text = "Campo obrigatorio"
                    titulo_input.update()
                    return
                tags = (
                    [tag.strip() for tag in tags_input.value.split(",")]
                    if tags_input.value
                    else []
                )
                if item_existente:
                    item_existente.titulo = titulo_input.value.strip()
                    item_existente.conteudo = conteudo_input.value
                    item_existente.tags = tags
                else:
                    import time

                    session.add(
                        Item(
                            titulo=titulo_input.value.strip(),
                            conteudo=conteudo_input.value,
                            tipo=tipo,
                            pai_id=pai_id(),
                            data_criacao=int(time.time()),
                            tags=tags,
                        )
                    )
                session.commit()
                view_state["atual"] = "grid"
                renderizar()

            cor_btn, cor_bg = chip_cor(tipo)
            main_content.content = ft.Column(
                [
                    ft.Container(height=8),
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Container(
                                    content=ft.Icon(
                                        icone_tipo(tipo), size=16, color=cor_btn
                                    ),
                                    bgcolor=cor_bg,
                                    border_radius=8,
                                    padding=8,
                                ),
                                ft.Text(header, size=15, weight="w600", color=TEXT_SUB),
                            ],
                            spacing=10,
                        ),
                        padding=pad(b=4),
                    ),
                    divider(),
                    ft.Container(height=16),
                    titulo_input,
                    ft.Container(height=8),
                    tags_input,
                    ft.Container(height=12),
                    conteudo_input,
                    ft.Container(height=24),
                    ft.Row(
                        [
                            ft.Container(expand=True),
                            ft.OutlinedButton(
                                "Cancelar",
                                style=ft.ButtonStyle(color=TEXT_SUB),
                                on_click=lambda _: voltar(),
                            ),
                            ft.Container(width=8),
                            ft.FilledButton(
                                "Guardar",
                                icon=ft.Icons.SAVE_ROUNDED,
                                style=ft.ButtonStyle(bgcolor=ACCENT, color=WHITE),
                                on_click=salvar,
                            ),
                        ]
                    ),
                    ft.Container(height=32),
                ],
                scroll="auto",
                expand=True,
                spacing=0,
            )

        page.update()

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
            content=ft.Text(
                f'"{item.titulo}" sera removido permanentemente.', color=TEXT_SUB
            ),
            bgcolor=SURFACE,
            actions=[
                ft.TextButton("Cancelar", on_click=fechar),
                ft.FilledButton(
                    "Excluir",
                    style=ft.ButtonStyle(bgcolor=RED, color=WHITE),
                    on_click=confirmar,
                ),
            ],
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def _editar(item):
        mostrar_editor(item, item.tipo)

    # ── NOVA PASTA ────────────────────────────────────────────────────────────
    def nova_pasta():
        tf = ft.TextField(
            label="Nome da pasta",
            autofocus=True,
            border_color=BORDER,
            focused_border_color=ACCENT,
            color=TEXT,
            label_style=ft.TextStyle(color=TEXT_SUB),
            bgcolor=SURFACE,
            border_radius=10,
        )

        def criar(e):
            if tf.value.strip():
                total = session.query(Item).filter_by(pai_id=pai_id()).count()
                import time

                session.add(
                    Item(
                        titulo=tf.value.strip(),
                        tipo="Pasta",
                        pai_id=pai_id(),
                        ordem=total,
                        data_criacao=int(time.time()),
                        tags=[],
                    )
                )
                session.commit()
                dlg.open = False
                renderizar()

        def fechar(e):
            dlg.open = False
            page.update()

        dlg = ft.AlertDialog(
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.FOLDER_ROUNDED, color=ACCENT, size=20),
                    ft.Text("Nova Pasta", color=TEXT, weight="w600"),
                ],
                spacing=8,
            ),
            content=ft.Container(tf, width=400),
            bgcolor=SURFACE,
            actions=[
                ft.TextButton("Cancelar", on_click=fechar),
                ft.FilledButton(
                    "Criar",
                    style=ft.ButtonStyle(bgcolor=ACCENT, color=WHITE),
                    on_click=criar,
                ),
            ],
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
            content=ft.Row(
                [
                    ft.Container(
                        content=ft.Icon(icon, size=20, color=cor),
                        bgcolor=chip_cor(label)[1],
                        border_radius=10,
                        padding=10,
                        width=44,
                        height=44,
                    ),
                    ft.Text(label, size=15, weight="w500", color=TEXT),
                ],
                spacing=16,
                vertical_alignment="center",
            ),
            on_click=fn,
            border_radius=12,
            padding=pad(h=8, v=10),
            on_hover=hover,
        )

    def _bs_fechar(fn):
        bs.open = False
        page.update()
        fn()

    bs = ft.BottomSheet(
        ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Container(
                            width=40, height=4, bgcolor=BORDER, border_radius=2
                        ),
                        alignment=ft.alignment.Alignment(0, 0),
                        padding=pad(t=14, b=10),
                    ),
                    ft.Text(
                        "Adicionar",
                        size=14,
                        color=TEXT_SUB,
                        weight="w700",
                        text_align="center",
                    ),
                    ft.Container(height=8),
                    _menu_tile(
                        ft.Icons.FOLDER_ROUNDED,
                        "Pasta",
                        ACCENT,
                        lambda _: _bs_fechar(nova_pasta),
                    ),
                    _menu_tile(
                        ft.Icons.OPEN_IN_NEW_ROUNDED,
                        "Link",
                        ACCENT2,
                        lambda _: _bs_fechar(lambda: mostrar_editor(tipo="Link")),
                    ),
                    _menu_tile(
                        ft.Icons.ARTICLE_ROUNDED,
                        "Nota",
                        GREEN,
                        lambda _: _bs_fechar(lambda: mostrar_editor(tipo="Nota")),
                    ),
                    ft.Container(height=20),
                ],
                tight=True,
                spacing=2,
                horizontal_alignment="stretch",
            ),
            bgcolor=SURFACE,
            border_radius=ft.BorderRadius(
                top_left=20, top_right=20, bottom_left=0, bottom_right=0
            ),
            padding=pad(h=20),
        )
    )
    page.overlay.append(bs)

    page.floating_action_button = ft.FloatingActionButton(
        content=ft.Icon(ft.Icons.ADD_ROUNDED, color=WHITE, size=24),
        bgcolor=ACCENT,
        shape=ft.StadiumBorder(),
        on_click=lambda _: [setattr(bs, "open", True), page.update()],
    )

    page.add(
        ft.Column(
            [
                appbar,
                ft.Container(
                    content=main_content,
                    expand=True,
                    padding=pad(h=16, t=16, b=80),
                ),
            ],
            expand=True,
            spacing=0,
        )
    )

    def renderizar():
        if view_state["atual"] == "grid":
            renderizar_grid()

    renderizar()


if __name__ == "__main__":
    ft.run(main)
