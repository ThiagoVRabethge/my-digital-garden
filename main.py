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
    tipo = Column(String(20))  # Pasta, Nota, Link
    pai_id = Column(Integer, ForeignKey("itens.id"), nullable=True)
    filhos = relationship(
        "Item",
        backref=backref("pai", remote_side=[id]),
        cascade="all, delete-orphan",
    )


Base.metadata.create_all(engine)


# Paleta
BG = "#0D0D0F"
SURFACE = "#141417"
CARD = "#1A1A1F"
CARD_HOV = "#1F1F26"
BORDER = "#2A2A35"
ACCENT = "#7C6AF7"
ACCENT2 = "#4FC3F7"
GREEN = "#56D6A0"
TEXT = "#E8E8F0"
TEXT_SUB = "#6B6B80"
TEXT_DIM = "#3D3D50"
WHITE = "#FFFFFF"
RED = "#C0392B"


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


# Helpers de padding/border sem usar APIs deprecated
def pad(a=0, t=None, r=None, b=None, h=None, v=None):
    left = h if h is not None else a
    right = h if h is not None else r if r is not None else a
    top = v if v is not None else t if t is not None else a
    bottom = v if v is not None else b if b is not None else a
    return ft.Padding(left=left, top=top, right=right, bottom=bottom)


def border_right(color, width=1):
    return ft.Border(right=ft.BorderSide(width, color))


def border_bottom(color, width=1):
    return ft.Border(bottom=ft.BorderSide(width, color))


def border_all_sides(color, width=1):
    s = ft.BorderSide(width, color)
    return ft.Border(left=s, top=s, right=s, bottom=s)


def border_radius_top(r):
    return ft.BorderRadius(top_left=r, top_right=r, bottom_left=0, bottom_right=0)


# Componentes
def divider():
    return ft.Container(height=1, bgcolor=BORDER)


def label_chip(tipo: str):
    cor, bg = chip_cor(tipo)
    return ft.Container(
        content=ft.Text(
            tipo.upper(), size=9, weight="w700", color=cor, font_family="monospace"
        ),
        bgcolor=bg,
        border_radius=4,
        padding=pad(h=8, v=3),
    )


def _hover_card(e):
    e.control.bgcolor = CARD_HOV if e.data == "true" else CARD
    e.control.update()


def build_card(item, on_click, on_edit, on_delete):
    cor, bg = chip_cor(item.tipo)
    icone = icone_tipo(item.tipo)

    preview = ""
    if item.tipo == "Nota" and item.conteudo:
        preview = item.conteudo[:80].replace("\n", " ") + (
            "..." if len(item.conteudo) > 80 else ""
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
        icon_size=16,
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

    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Icon(icone, size=18, color=cor),
                            bgcolor=bg,
                            border_radius=8,
                            padding=8,
                        ),
                        ft.Container(expand=True),
                        menu,
                    ],
                    vertical_alignment="center",
                ),
                ft.Container(height=12),
                ft.Text(
                    item.titulo,
                    size=14,
                    weight="w600",
                    color=TEXT,
                    max_lines=2,
                    overflow="ellipsis",
                ),
                ft.Container(height=4),
                ft.Text(
                    preview, size=11, color=TEXT_SUB, max_lines=2, overflow="ellipsis"
                )
                if preview
                else ft.Container(height=0),
                ft.Container(expand=True),
                label_chip(item.tipo),
            ],
            spacing=0,
        ),
        bgcolor=CARD,
        border_radius=14,
        padding=pad(a=16),
        border=border_all_sides(BORDER),
        on_click=lambda e, i=item: on_click(i),
        on_hover=_hover_card,
        animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
    )


def section_title(text):
    return ft.Text(
        text, size=11, weight="w700", color=TEXT_DIM, font_family="monospace"
    )


def _menu_tile(icon, label, cor, on_click_fn):
    def hover(e):
        e.control.bgcolor = CARD_HOV if e.data == "true" else "transparent"
        e.control.update()

    return ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.Icon(icon, size=16, color=cor),
                    bgcolor=chip_cor(label)[1],
                    border_radius=8,
                    padding=8,
                ),
                ft.Text(label, size=14, weight="w500", color=TEXT),
            ],
            spacing=12,
            vertical_alignment="center",
        ),
        on_click=on_click_fn,
        border_radius=10,
        padding=pad(h=8, v=10),
        on_hover=hover,
    )


def _nav_btn(icon, label, on_click_fn):
    def hover(e):
        e.control.bgcolor = CARD if e.data == "true" else "transparent"
        e.control.update()

    return ft.Container(
        content=ft.Row(
            [
                ft.Icon(icon, size=16, color=TEXT_SUB),
                ft.Text(label, size=13, color=TEXT_SUB, weight="w500"),
            ],
            spacing=10,
            vertical_alignment="center",
        ),
        on_click=on_click_fn,
        border_radius=8,
        padding=pad(h=10, v=8),
        on_hover=hover,
    )


# APP
def main(page: ft.Page):
    page.title = "My Digital Garden"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BG
    page.padding = 0

    session = Session()
    stack_nav = []

    breadcrumb_row = ft.Row(spacing=4, vertical_alignment="center", scroll="auto")
    content_area = ft.Container(expand=True)
    status_text = ft.Text("", size=11, color=TEXT_DIM, font_family="monospace")

    def pai_id():
        return stack_nav[-1].id if stack_nav else None

    def navegar(pasta=None):
        if pasta is None:
            stack_nav.clear()
        elif pasta not in stack_nav:
            stack_nav.append(pasta)
        renderizar_grid()

    def voltar_para(pasta):
        idx = stack_nav.index(pasta)
        del stack_nav[idx + 1 :]
        renderizar_grid()

    def abrir_link(url):
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        import webbrowser

        webbrowser.open(url)

    def atualizar_breadcrumb():
        breadcrumb_row.controls = [
            ft.TextButton(
                "Vault",
                style=ft.ButtonStyle(
                    color=ACCENT if not stack_nav else TEXT_SUB, padding=pad(h=4)
                ),
                on_click=lambda _: navegar(None),
            )
        ]
        for i, pasta in enumerate(stack_nav):
            is_last = i == len(stack_nav) - 1
            breadcrumb_row.controls.append(ft.Text("›", color=TEXT_DIM, size=16))
            breadcrumb_row.controls.append(
                ft.TextButton(
                    pasta.titulo,
                    style=ft.ButtonStyle(
                        color=ACCENT if is_last else TEXT_SUB, padding=pad(h=4)
                    ),
                    on_click=lambda e, p=pasta: voltar_para(p),
                )
            )

    def renderizar_grid():
        page.floating_action_button.visible = True
        atualizar_breadcrumb()
        itens = session.query(Item).filter_by(pai_id=pai_id()).all()
        pastas = [i for i in itens if i.tipo == "Pasta"]
        links = [i for i in itens if i.tipo == "Link"]
        notas = [i for i in itens if i.tipo == "Nota"]
        status_text.value = f"{len(itens)} item{'s' if len(itens) != 1 else ''}"

        def make_grid(items):
            return ft.ResponsiveRow(
                controls=[
                    ft.Column(
                        [build_card(it, _click_item, _editar, _excluir)],
                        col={"xs": 12, "sm": 6, "md": 4, "lg": 3},
                    )
                    for it in items
                ],
                spacing=16,
                run_spacing=16,
            )

        sections = []
        if pastas:
            sections += [
                section_title("PASTAS"),
                ft.Container(height=8),
                make_grid(pastas),
                ft.Container(height=24),
            ]
        if links:
            sections += [
                section_title("LINKS"),
                ft.Container(height=8),
                make_grid(links),
                ft.Container(height=24),
            ]
        if notas:
            sections += [
                section_title("NOTAS"),
                ft.Container(height=8),
                make_grid(notas),
            ]

        if not itens:
            sections = [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(ft.Icons.INBOX_ROUNDED, size=56, color=TEXT_DIM),
                            ft.Container(height=16),
                            ft.Text(
                                "Este espaco esta vazio",
                                size=16,
                                color=TEXT_SUB,
                                weight="w500",
                            ),
                            ft.Text(
                                "Use o botao + para adicionar pastas, links ou notas.",
                                size=12,
                                color=TEXT_DIM,
                                text_align="center",
                            ),
                        ],
                        horizontal_alignment="center",
                        alignment="center",
                    ),
                    expand=True,
                    padding=pad(t=80),
                )
            ]

        content_area.content = ft.Column(
            sections, scroll="auto", expand=True, spacing=0
        )
        page.update()

    def _click_item(item):
        if item.tipo == "Pasta":
            navegar(item)
        elif item.tipo == "Link":
            abrir_link(item.conteudo or "")
        else:
            ver_nota(item)

    def ver_nota(item):
        content_area.content = ft.Column(
            [
                ft.Row(
                    [
                        ft.IconButton(
                            ft.Icons.ARROW_BACK_ROUNDED,
                            icon_color=TEXT_SUB,
                            on_click=lambda _: renderizar_grid(),
                            tooltip="Voltar",
                        ),
                        ft.Text(
                            item.titulo, size=20, weight="w700", color=TEXT, expand=True
                        ),
                        ft.IconButton(
                            ft.Icons.EDIT_ROUNDED,
                            icon_color=TEXT_SUB,
                            on_click=lambda _: mostrar_editor(item, "Nota"),
                            tooltip="Editar",
                        ),
                    ],
                    vertical_alignment="center",
                ),
                divider(),
                ft.Container(height=16),
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

    def mostrar_editor(item_existente=None, tipo="Nota"):
        is_nota = tipo == "Nota"

        titulo_input = ft.TextField(
            label="Titulo",
            value=item_existente.titulo if item_existente else "",
            autofocus=True,
            border_color=BORDER,
            focused_border_color=ACCENT,
            color=TEXT,
            label_style=ft.TextStyle(color=TEXT_SUB),
            bgcolor=SURFACE,
            border_radius=10,
        )
        conteudo_input = ft.TextField(
            label="URL" if tipo == "Link" else "Conteudo (Markdown)",
            value=item_existente.conteudo if item_existente else "",
            multiline=is_nota,
            min_lines=8 if is_nota else 1,
            max_lines=20 if is_nota else 3,
            border_color=BORDER,
            focused_border_color=ACCENT,
            color=TEXT,
            label_style=ft.TextStyle(color=TEXT_SUB),
            bgcolor=SURFACE,
            border_radius=10,
            expand=is_nota,
        )

        def salvar(e):
            if not titulo_input.value.strip():
                titulo_input.error_text = "Campo obrigatorio"
                titulo_input.update()
                return
            if item_existente:
                item_existente.titulo = titulo_input.value.strip()
                item_existente.conteudo = conteudo_input.value
            else:
                session.add(
                    Item(
                        titulo=titulo_input.value.strip(),
                        conteudo=conteudo_input.value,
                        tipo=tipo,
                        pai_id=pai_id(),
                    )
                )
            session.commit()
            renderizar_grid()

        cor_btn, cor_bg = chip_cor(tipo)
        header_label = ("Editar" if item_existente else "Novo") + f" {tipo}"

        # Esconde o FAB para o botao Guardar nao ficar atras dele
        page.floating_action_button.visible = False
        page.update()

        def _cancelar(_):
            page.floating_action_button.visible = True
            renderizar_grid()

        content_area.content = ft.Column(
            [
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Icon(icone_tipo(tipo), size=18, color=cor_btn),
                            bgcolor=cor_bg,
                            border_radius=8,
                            padding=8,
                        ),
                        ft.Text(header_label, size=18, weight="w700", color=TEXT),
                        ft.Container(expand=True),
                        ft.IconButton(
                            ft.Icons.CLOSE_ROUNDED,
                            icon_color=TEXT_SUB,
                            on_click=_cancelar,
                        ),
                    ],
                    vertical_alignment="center",
                    spacing=12,
                ),
                ft.Container(height=8),
                divider(),
                ft.Container(height=20),
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
                            on_click=_cancelar,
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
                ft.Container(height=16),
            ],
            scroll="auto",
            expand=True,
            spacing=0,
        )
        page.update()

    def _excluir(item):
        def confirmar(e):
            session.delete(item)
            session.commit()
            dlg.open = False
            renderizar_grid()

        def fechar(e):
            dlg.open = False
            page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Excluir item?", color=TEXT),
            content=ft.Text(
                f'"{item.titulo}" sera permanentemente removido.', color=TEXT_SUB
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
                session.add(
                    Item(titulo=tf.value.strip(), tipo="Pasta", pai_id=pai_id())
                )
                session.commit()
                dlg.open = False
                renderizar_grid()

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
            content=ft.Container(tf, width=320),
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
                            width=36, height=4, bgcolor=BORDER, border_radius=2
                        ),
                        alignment=ft.alignment.Alignment(0, 0),
                        padding=pad(t=12, b=8),
                    ),
                    ft.Text(
                        "Adicionar",
                        size=13,
                        color=TEXT_SUB,
                        weight="w600",
                        font_family="monospace",
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
                    ft.Container(height=16),
                ],
                tight=True,
                spacing=2,
                horizontal_alignment="stretch",
            ),
            bgcolor=SURFACE,
            border_radius=border_radius_top(20),
            padding=pad(h=16),
        )
    )
    page.overlay.append(bs)

    sidebar = ft.Container(
        content=ft.Column(
            [
                ft.Container(height=8),
                ft.Row(
                    [
                        ft.Icon(ft.Icons.HEXAGON_ROUNDED, color=ACCENT, size=22),
                        ft.Text(
                            "MY DIGITAL GARDEN",
                            size=13,
                            weight="w900",
                            color=TEXT,
                            font_family="monospace",
                        ),
                    ],
                    spacing=8,
                ),
                ft.Container(height=32),
                ft.Column(
                    [_nav_btn(ft.Icons.HOME_ROUNDED, "Inicio", lambda _: navegar(None))]
                ),
                ft.Container(expand=True),
                ft.Text("v2.0", size=10, color=TEXT_DIM, font_family="monospace"),
                ft.Container(height=8),
            ],
            spacing=0,
        ),
        width=200,
        bgcolor=SURFACE,
        border=border_right(BORDER),
        padding=pad(h=20, v=20),
    )

    topbar = ft.Container(
        content=ft.Row(
            [ft.Row([breadcrumb_row], expand=True, scroll="auto"), status_text],
            vertical_alignment="center",
        ),
        bgcolor=SURFACE,
        border=border_bottom(BORDER),
        padding=pad(h=24, v=14),
        height=52,
    )

    page.floating_action_button = ft.FloatingActionButton(
        content=ft.Icon(ft.Icons.ADD_ROUNDED, color=WHITE, size=22),
        bgcolor=ACCENT,
        shape=ft.StadiumBorder(),
        on_click=lambda _: [setattr(bs, "open", True), page.update()],
    )

    page.add(
        ft.Row(
            [
                sidebar,
                ft.Column(
                    [
                        topbar,
                        ft.Container(
                            content=content_area, expand=True, padding=pad(a=24)
                        ),
                    ],
                    expand=True,
                    spacing=0,
                ),
            ],
            expand=True,
            spacing=0,
            vertical_alignment="start",
        )
    )

    renderizar_grid()


if __name__ == "__main__":
    ft.run(main)
