# -*- coding: utf-8 -*-
import sys
import io
import webbrowser

# Fix Windows terminal encoding (resolve UnicodeEncodeError no CI/build)
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import flet as ft
from sqlalchemy import Column, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import backref, declarative_base, relationship, sessionmaker

# --- DATABASE ---
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
    filhos = relationship(
        "Item",
        backref=backref("pai", remote_side=[id]),
        cascade="all, delete-orphan",
    )


Base.metadata.create_all(engine)

# --- Paleta ---
BG       = "#0D0D0F"
SURFACE  = "#141417"
CARD     = "#1A1A1F"
CARD_HOV = "#222228"
BORDER   = "#2A2A35"
ACCENT   = "#7C6AF7"
ACCENT2  = "#4FC3F7"
GREEN    = "#56D6A0"
TEXT     = "#E8E8F0"
TEXT_SUB = "#6B6B80"
TEXT_DIM = "#3D3D50"
WHITE    = "#FFFFFF"
RED      = "#C0392B"


def chip_cor(tipo):
    return {
        "Pasta": (ACCENT,  "#1E1B3A"),
        "Link":  (ACCENT2, "#112230"),
        "Nota":  (GREEN,   "#0F2820"),
    }.get(tipo, (TEXT_SUB, CARD))


def icone_tipo(tipo):
    return {
        "Pasta": ft.Icons.FOLDER_ROUNDED,
        "Link":  ft.Icons.OPEN_IN_NEW_ROUNDED,
        "Nota":  ft.Icons.ARTICLE_ROUNDED,
    }.get(tipo, ft.Icons.CIRCLE)


def pad(a=0, t=None, r=None, b=None, h=None, v=None):
    left   = h if h is not None else a
    right  = h if h is not None else (r if r is not None else a)
    top    = v if v is not None else (t if t is not None else a)
    bottom = v if v is not None else (b if b is not None else a)
    return ft.Padding(left=left, top=top, right=right, bottom=bottom)


def divider():
    return ft.Container(height=1, bgcolor=BORDER)


def label_chip(tipo: str):
    cor, bg = chip_cor(tipo)
    return ft.Container(
        content=ft.Text(tipo.upper(), size=9, weight="w700", color=cor),
        bgcolor=bg, border_radius=4, padding=pad(h=8, v=3),
    )


# --- Item em lista (mobile-first: linha inteira, toque fácil) ---
def build_list_item(item, on_click, on_edit, on_delete):
    cor, bg = chip_cor(item.tipo)
    icone   = icone_tipo(item.tipo)

    preview = ""
    if item.tipo == "Nota" and item.conteudo:
        preview = item.conteudo[:60].replace("\n", " ") + ("..." if len(item.conteudo) > 60 else "")
    elif item.tipo == "Link" and item.conteudo:
        preview = item.conteudo[:50]

    def popup_item(label, icon_name, handler):
        return ft.PopupMenuItem(
            content=ft.Row([ft.Icon(icon_name, size=14, color=TEXT_SUB),
                            ft.Text(label, size=13, color=TEXT)], spacing=10),
            on_click=handler,
        )

    menu = ft.PopupMenuButton(
        icon=ft.Icons.MORE_VERT_ROUNDED,
        icon_color=TEXT_DIM,
        icon_size=20,
        items=[
            popup_item("Editar",  ft.Icons.EDIT_ROUNDED,          lambda e, i=item: on_edit(i)),
            ft.PopupMenuItem(),
            popup_item("Excluir", ft.Icons.DELETE_OUTLINE_ROUNDED, lambda e, i=item: on_delete(i)),
        ],
    )

    def hover(e):
        e.control.bgcolor = CARD_HOV if e.data == "true" else CARD
        e.control.update()

    return ft.Container(
        content=ft.Row(
            [
                # Ícone
                ft.Container(
                    content=ft.Icon(icone, size=20, color=cor),
                    bgcolor=bg, border_radius=10, padding=10,
                    width=44, height=44,
                ),
                ft.Container(width=14),
                # Texto
                ft.Column(
                    [
                        ft.Text(item.titulo, size=15, weight="w600", color=TEXT,
                                max_lines=1, overflow="ellipsis"),
                        ft.Text(preview, size=12, color=TEXT_SUB,
                                max_lines=1, overflow="ellipsis") if preview
                        else ft.Container(height=0),
                    ],
                    spacing=2, expand=True,
                    alignment="center",
                ),
                ft.Container(width=4),
                menu,
            ],
            vertical_alignment="center",
        ),
        bgcolor=CARD,
        border_radius=14,
        padding=pad(h=16, v=12),
        on_click=lambda e, i=item: on_click(i),
        on_hover=hover,
        animate=ft.Animation(120, ft.AnimationCurve.EASE_OUT),
    )


def section_title(text):
    return ft.Text(text, size=11, weight="w700", color=TEXT_DIM)


# --- APP ---
def main(page: ft.Page):
    page.title       = "My Digital Garden"
    page.theme_mode  = ft.ThemeMode.DARK
    page.bgcolor     = BG
    page.padding     = 0
    page.scroll      = None

    session   = Session()
    stack_nav = []  # stack de pastas abertas

    # ── estado da view atual ──────────────────────────────────────────────────
    # "grid" | "editor" | "nota"
    view_state = {"atual": "grid"}

    # ── helpers de navegação ──────────────────────────────────────────────────
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

    # ── área principal ────────────────────────────────────────────────────────
    main_content = ft.Container(expand=True)
    appbar_title  = ft.Text("My Digital Garden", size=17, weight="w700", color=TEXT,
                            overflow="ellipsis", expand=True)
    back_btn = ft.IconButton(ft.Icons.ARROW_BACK_ROUNDED, icon_color=TEXT_SUB,
                             on_click=lambda _: voltar(), visible=False)

    appbar = ft.Container(
        content=ft.Row(
            [back_btn, appbar_title],
            vertical_alignment="center", spacing=4,
        ),
        bgcolor=SURFACE,
        border=ft.Border(bottom=ft.BorderSide(1, BORDER)),
        padding=pad(h=8, v=12),
        height=56,
    )

    def set_appbar(title, show_back=False):
        appbar_title.value = title
        back_btn.visible   = show_back
        appbar.update()

    # ── GRID ──────────────────────────────────────────────────────────────────
    def renderizar_grid():
        set_appbar(pasta_atual_nome(), show_back=bool(stack_nav))
        page.floating_action_button.visible = True

        itens  = session.query(Item).filter_by(pai_id=pai_id()).all()
        pastas = [i for i in itens if i.tipo == "Pasta"]
        links  = [i for i in itens if i.tipo == "Link"]
        notas  = [i for i in itens if i.tipo == "Nota"]

        sections = []

        def make_list(items):
            col = ft.Column(spacing=8)
            for it in items:
                col.controls.append(build_list_item(it, _click_item, _editar, _excluir))
            return col

        if pastas:
            sections += [section_title("PASTAS"), ft.Container(height=6),
                         make_list(pastas), ft.Container(height=16)]
        if links:
            sections += [section_title("LINKS"),  ft.Container(height=6),
                         make_list(links),  ft.Container(height=16)]
        if notas:
            sections += [section_title("NOTAS"),  ft.Container(height=6),
                         make_list(notas)]

        if not itens:
            sections = [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Container(height=60),
                            ft.Icon(ft.Icons.YARD_ROUNDED, size=64, color=TEXT_DIM),
                            ft.Container(height=16),
                            ft.Text("Jardim vazio", size=18, color=TEXT_SUB,
                                    weight="w600", text_align="center"),
                            ft.Text("Toque em + para adicionar\npastas, links ou notas.",
                                    size=13, color=TEXT_DIM, text_align="center"),
                        ],
                        horizontal_alignment="center",
                    ),
                )
            ]

        main_content.content = ft.Column(
            sections, scroll="auto", expand=True,
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
        set_appbar(item.titulo, show_back=True)
        page.floating_action_button.visible = False

        main_content.content = ft.Column(
            [
                ft.Row(
                    [ft.Container(expand=True),
                     ft.IconButton(ft.Icons.EDIT_ROUNDED, icon_color=TEXT_SUB,
                                   on_click=lambda _: mostrar_editor(item, "Nota"),
                                   tooltip="Editar")],
                ),
                ft.Column(
                    [ft.Markdown(
                        item.conteudo or "_Nota vazia._",
                        selectable=True,
                        extension_set="gitHubFlavored",
                        code_theme="atom-one-dark",
                    )],
                    scroll="auto", expand=True,
                ),
            ],
            expand=True, spacing=0,
        )
        page.update()

    # ── EDITOR ────────────────────────────────────────────────────────────────
    def mostrar_editor(item_existente=None, tipo="Nota"):
        view_state["atual"] = "editor"
        is_nota = tipo == "Nota"
        header  = ("Editar" if item_existente else "Novo") + f" {tipo}"
        set_appbar(header, show_back=True)
        page.floating_action_button.visible = False

        titulo_input = ft.TextField(
            label="Titulo",
            value=item_existente.titulo if item_existente else "",
            autofocus=True,
            border_color=BORDER, focused_border_color=ACCENT,
            color=TEXT, label_style=ft.TextStyle(color=TEXT_SUB),
            bgcolor=SURFACE, border_radius=10,
        )
        conteudo_input = ft.TextField(
            label="URL" if tipo == "Link" else "Conteudo (Markdown)",
            value=item_existente.conteudo if item_existente else "",
            multiline=is_nota,
            min_lines=6 if is_nota else 1,
            max_lines=None if is_nota else 3,
            border_color=BORDER, focused_border_color=ACCENT,
            color=TEXT, label_style=ft.TextStyle(color=TEXT_SUB),
            bgcolor=SURFACE, border_radius=10,
            expand=is_nota,
        )

        def salvar(e):
            if not titulo_input.value.strip():
                titulo_input.error_text = "Campo obrigatorio"
                titulo_input.update()
                return
            if item_existente:
                item_existente.titulo   = titulo_input.value.strip()
                item_existente.conteudo = conteudo_input.value
            else:
                session.add(Item(
                    titulo=titulo_input.value.strip(),
                    conteudo=conteudo_input.value,
                    tipo=tipo, pai_id=pai_id(),
                ))
            session.commit()
            view_state["atual"] = "grid"
            renderizar()

        cor_btn, cor_bg = chip_cor(tipo)

        main_content.content = ft.Column(
            [
                ft.Container(height=8),
                ft.Container(
                    content=ft.Row([
                        ft.Container(content=ft.Icon(icone_tipo(tipo), size=16, color=cor_btn),
                                     bgcolor=cor_bg, border_radius=8, padding=8),
                        ft.Text(header, size=15, weight="w600", color=TEXT_SUB),
                    ], spacing=10),
                    padding=pad(b=4),
                ),
                divider(),
                ft.Container(height=16),
                titulo_input,
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
            scroll="auto", expand=True, spacing=0,
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
            content=ft.Text(f'"{item.titulo}" sera removido permanentemente.', color=TEXT_SUB),
            bgcolor=SURFACE,
            actions=[
                ft.TextButton("Cancelar", on_click=fechar),
                ft.FilledButton("Excluir", style=ft.ButtonStyle(bgcolor=RED, color=WHITE),
                                on_click=confirmar),
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
            label="Nome da pasta", autofocus=True,
            border_color=BORDER, focused_border_color=ACCENT,
            color=TEXT, label_style=ft.TextStyle(color=TEXT_SUB),
            bgcolor=SURFACE, border_radius=10,
        )

        def criar(e):
            if tf.value.strip():
                session.add(Item(titulo=tf.value.strip(), tipo="Pasta", pai_id=pai_id()))
                session.commit()
                dlg.open = False
                renderizar()

        def fechar(e):
            dlg.open = False
            page.update()

        dlg = ft.AlertDialog(
            title=ft.Row([ft.Icon(ft.Icons.FOLDER_ROUNDED, color=ACCENT, size=20),
                          ft.Text("Nova Pasta", color=TEXT, weight="w600")], spacing=8),
            content=ft.Container(tf, width=400),
            bgcolor=SURFACE,
            actions=[
                ft.TextButton("Cancelar", on_click=fechar),
                ft.FilledButton("Criar", style=ft.ButtonStyle(bgcolor=ACCENT, color=WHITE),
                                on_click=criar),
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
                    ft.Container(content=ft.Icon(icon, size=20, color=cor),
                                 bgcolor=chip_cor(label)[1], border_radius=10, padding=10,
                                 width=44, height=44),
                    ft.Text(label, size=15, weight="w500", color=TEXT),
                ],
                spacing=16, vertical_alignment="center",
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
                        content=ft.Container(width=40, height=4, bgcolor=BORDER, border_radius=2),
                        alignment=ft.alignment.Alignment(0, 0),
                        padding=pad(t=14, b=10),
                    ),
                    ft.Text("Adicionar", size=14, color=TEXT_SUB, weight="w700",
                            text_align="center"),
                    ft.Container(height=8),
                    _menu_tile(ft.Icons.FOLDER_ROUNDED,      "Pasta", ACCENT,
                               lambda _: _bs_fechar(nova_pasta)),
                    _menu_tile(ft.Icons.OPEN_IN_NEW_ROUNDED, "Link",  ACCENT2,
                               lambda _: _bs_fechar(lambda: mostrar_editor(tipo="Link"))),
                    _menu_tile(ft.Icons.ARTICLE_ROUNDED,     "Nota",  GREEN,
                               lambda _: _bs_fechar(lambda: mostrar_editor(tipo="Nota"))),
                    ft.Container(height=20),
                ],
                tight=True, spacing=2, horizontal_alignment="stretch",
            ),
            bgcolor=SURFACE,
            border_radius=ft.BorderRadius(top_left=20, top_right=20,
                                          bottom_left=0, bottom_right=0),
            padding=pad(h=20),
        )
    )
    page.overlay.append(bs)

    # ── FAB ───────────────────────────────────────────────────────────────────
    page.floating_action_button = ft.FloatingActionButton(
        content=ft.Icon(ft.Icons.ADD_ROUNDED, color=WHITE, size=24),
        bgcolor=ACCENT,
        shape=ft.StadiumBorder(),
        on_click=lambda _: [setattr(bs, "open", True), page.update()],
    )

    # ── LAYOUT PRINCIPAL ──────────────────────────────────────────────────────
    # Mobile-first: sem sidebar. Tudo empilhado verticalmente.
    page.add(
        ft.Column(
            [
                appbar,
                ft.Container(
                    content=main_content,
                    expand=True,
                    padding=pad(h=16, t=16, b=80),  # b=80 evita FAB cobrir conteúdo
                ),
            ],
            expand=True, spacing=0,
        )
    )

    renderizar_grid()

    def renderizar():
        if view_state["atual"] == "grid":
            renderizar_grid()


if __name__ == "__main__":
    ft.run(main)