import os
import random
import tkinter as tk
import tkinter.font as tkfont
from tkinter import messagebox

# pill para redimensionar as imagens
try:
    from PIL import Image, ImageTk
    TEM_PIL = True
except ImportError:
    TEM_PIL = False

# configurações do jogo
NUM_ROWS = 6             # número de linhas na grade de cards
NUM_COLS = 6             # número de colunas na grade de cards
CARD_PX = 110            # tamanho do card em pixels
IMG_PX = 90              # tamanho da imagem dentro do card
MAX_ATTEMPTS = 50        # número máximo de tentativas antes de perder
DELAY_MS = 800           # tempo que as cartas erradas ficam à mostra

# configurações de responsividade
TELA_PERC_ALTURA = 0.85  # a janela abre ocupando esse percentual da altura da tela
MIN_CARD = 40            # menor tamanho permitido para um card em pixels
MIN_LARGURA = 600        # largura mínima da janela
MIN_ALTURA = 600         # altura mínima da janela

# pastas com as imagens dos personagens dos cards
PASTA_IMAGENS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'personagens')

# paleta estilo DBZ
BG_COLOR = '#0b1d4d'
PANEL_COLOR = '#12307a'
ORANGE = '#f7871c'
ORANGE_DARK = '#b8500a'
YELLOW = '#ffd400'
RED = '#d62828'
WHITE = '#ffffff'
# fontes
TITLE_FONT = ('Impact', 34)
SUB_FONT = ('Arial', 12, 'bold')
CARD_FONT = ('Arial', 10, 'bold')
HIDDEN_FONT = ('Arial', 40, 'bold')

# uma lista de personagens do dbz com seus nomes, arquivos de imagem e cores
PERSONAGENS = [
    ('Goku',          'goku',         '#f7871c', 'black'),
    ('Vegeta',        'vegeta',       '#2b50c8', 'white'),
    ('Gohan',         'gohan',        '#7b3fa0', 'white'),
    ('Piccolo',       'piccolo',      '#3fa34d', 'white'),
    ('Kuririn',       'kuririn',      '#e8a33d', 'black'),
    ('Trunks',        'trunks',       '#8a63d2', 'white'),
    ('Goten',         'goten',        '#e85d04', 'white'),
    ('Freeza',        'freeza',       '#c9b6e4', 'black'),
    ('Cell',          'cell',         '#5cb85c', 'black'),
    ('Majin Boo',     'majin_boo',    '#ff8fab', 'black'),
    ('Mestre Kame',   'mestre_kame',  '#f4d35e', 'black'),
    ('Yamcha',        'yamcha',       '#d97706', 'white'),
    ('Tenshinhan',    'tenshinhan',   '#16a085', 'white'),
    ('Bulma',         'bulma',        '#00b4d8', 'black'),
    ('Gotenks',       'gotenks',      '#9d4edd', 'white'),
    ('Broly',         'broly',        '#2d6a4f', 'white'),
    ('Bardock',       'bardock',      '#9c2f2f', 'white'),
    ('Shenlong',      'shenlong',     '#2a9d8f', 'white'),
]

# cria a janela principal
window = tk.Tk()
window.title('Dragon Ball Z - Jogo da Memória')
window.configure(bg=BG_COLOR)
# define um ícone para a janela, se existir
pixel_vazio = tk.PhotoImage(width=1, height=1)
imagens = {}
grid = []
cards = []
matched = set()
selected = []
attempts = 0
bloqueado = False

# fontes
fonte_titulo = tkfont.Font(font=TITLE_FONT)
fonte_sub = tkfont.Font(font=SUB_FONT)
fonte_card = tkfont.Font(font=CARD_FONT)
fonte_oculta = tkfont.Font(font=HIDDEN_FONT)

#  estado de cada card 
estados = {}
tam_card = CARD_PX
img_px = IMG_PX
ajuste_id = None


# função para carregar imagens dos personagens, com cache para não recarregar várias vezes
def carregar_imagem(arquivo):
    chave = (arquivo, img_px)  # o cache agora também considera o tamanho da imagem
    if chave in imagens:
        return imagens[chave]
    img = None
    for ext in ('.png', '.gif', '.jpg', '.jpeg'):
        caminho = os.path.join(PASTA_IMAGENS, arquivo + ext)
        if os.path.exists(caminho):
            try:
                if TEM_PIL:
                    pil = Image.open(caminho).convert('RGBA').resize((img_px, img_px))
                    img = ImageTk.PhotoImage(pil)
                elif ext in ('.png', '.gif'):
                    img = tk.PhotoImage(file=caminho)
            except Exception:
                img = None
            break
    imagens[chave] = img
    return img

# função para criar a grade de cards embaralhados
def create_card_grid():
    indices = list(range(len(PERSONAGENS))) * 2
    random.shuffle(indices)
    return [[indices.pop() for _ in range(NUM_COLS)] for _ in range(NUM_ROWS)]

# funções para esconder, revelar e marcar cards combinados
def esconder(r, c):
    estados[(r, c)] = 'oculto'
    cards[r][c].config(
        text='★', font=fonte_oculta, image=pixel_vazio, compound='center',
        bg=ORANGE, fg=RED, activebackground=YELLOW, relief=tk.RAISED, state=tk.NORMAL,
    )

# função para revelar o card com o personagem correspondente
def revelar(r, c, combinado=False):
    nome, arquivo, cor, cor_texto = PERSONAGENS[grid[r][c]]
    img = carregar_imagem(arquivo)
    # sem pillow não dá para reduzir a imagem: se ela não couber no card, mostra só o nome
    if img and not TEM_PIL and img.width() > tam_card * 0.7:
        img = None
    estados[(r, c)] = 'combinado' if combinado else 'revelado'
    cards[r][c].config(
        text=nome, font=fonte_card, fg=YELLOW if combinado else cor_texto,
        bg=PANEL_COLOR if combinado else cor, activebackground=cor,
        image=img if img else pixel_vazio,
        compound='top' if img else 'center',
        relief=tk.FLAT if combinado else tk.SUNKEN,
        state=tk.DISABLED if combinado else tk.NORMAL,
        disabledforeground=YELLOW,
    )

# função para marcar os cards combinados
def marcar_combinado(r, c):
    revelar(r, c, combinado=True)

# função chamada quando um card é clicado
def card_clicked(r, c):
    global bloqueado, attempts
    if bloqueado or (r, c) in matched or (r, c) in selected:
        return
    revelar(r, c)
    selected.append((r, c))
    if len(selected) == 2:
        bloqueado = True
        attempts += 1
        update_score()
        window.after(DELAY_MS, check_match)

# função ppra verificar se os dois cards selecionados são iguais
def check_match():
    global bloqueado
    (r1, c1), (r2, c2) = selected
    if grid[r1][c1] == grid[r2][c2]:
        matched.update([(r1, c1), (r2, c2)])
        marcar_combinado(r1, c1)
        marcar_combinado(r2, c2)
    else:
        esconder(r1, c1)
        esconder(r2, c2)
    selected.clear()
    bloqueado = False
    update_score()
    check_end()

# função pra verificar se o jogo terminou
def check_end():
    if len(matched) == NUM_ROWS * NUM_COLS:
        messagebox.showinfo('PARABÉNS!', 'A terra foi salva, pois você reuniu todos os guerreiros Z e venceu!')
        reiniciar()
    elif attempts >= MAX_ATTEMPTS:
        messagebox.showinfo('Fim de Jogo', 'Seu ki acabou! Você perdeu o jogo.')
        reiniciar()

# função para atualizar o placar e a barra de ki
def update_score(event=None):
    attempts_label.config(text=f'Tentativas: {attempts}/{MAX_ATTEMPTS}')
    pairs_label.config(text=f'Pares: {len(matched) // 2}/{len(PERSONAGENS)}')
    # barra de ki: verde se >50%, laranja se >25%, vermelho se <=25%
    largura = max(ki_bar.winfo_width(), 60) 
    restante = max(0, MAX_ATTEMPTS - attempts) / MAX_ATTEMPTS
    ki_bar.delete('all')
    cor = YELLOW if restante > 0.5 else ORANGE if restante > 0.25 else RED
    ki_bar.create_rectangle(0, 0, (largura - 1) * restante, 16, fill=cor, outline='')
    ki_bar.create_rectangle(0, 0, largura - 1, 15, outline=WHITE)

# função para reiniciar o jogo
def reiniciar():
    global grid, attempts, bloqueado
    grid = create_card_grid()
    matched.clear()
    selected.clear()
    attempts = 0
    bloqueado = False
    for r in range(NUM_ROWS):
        for c in range(NUM_COLS):
            esconder(r, c)
    update_score()


# função para redesenhar um card de acordo com o estado atual, usada após redimensionar
def aplicar_estado(r, c):
    estado = estados.get((r, c), 'oculto')
    if estado == 'oculto':
        esconder(r, c)
    else:
        revelar(r, c, combinado=(estado == 'combinado'))

# função que recalcula o tamanho dos cards, imagens e fontes conforme o espaço disponível
def ajustar_tamanho():
    global tam_card, img_px, ajuste_id
    ajuste_id = None

    w = tabuleiro.winfo_width()
    h = tabuleiro.winfo_height()
    if w < 50 or h < 50:
        return

    # fontes do título e do rodapé acompanham a altura da janela (tamanho negativo = pixels)
    alt = window.winfo_height()
    fonte_titulo.configure(size=-max(20, min(64, alt // 20)))
    fonte_sub.configure(size=-max(11, min(18, alt // 55)))

    # espaço de cada célula, descontando o padding do tabuleiro (8*2) e dos botões (4*2)
    cel_w = (w - 16) // NUM_COLS - 8
    cel_h = (h - 16) // NUM_ROWS - 8
    novo = max(MIN_CARD, min(cel_w, cel_h))
    if abs(novo - tam_card) < 3:
        return

    tam_card = novo
    img_px = int(tam_card * 0.60)
    fonte_card.configure(size=-max(8, int(tam_card * 0.115)))
    fonte_oculta.configure(size=-max(16, int(tam_card * 0.40)))
    imagens.clear()

    for r in range(NUM_ROWS):
        for c in range(NUM_COLS):
            cards[r][c].config(wraplength=tam_card - 8)
            aplicar_estado(r, c)

# função chamada quando o tabuleiro muda de tamanho, espera parar de arrastar antes de recalcular
def ao_redimensionar(event=None):
    global ajuste_id
    if ajuste_id is not None:
        window.after_cancel(ajuste_id)
    ajuste_id = window.after(80, ajustar_tamanho)

#  funções para entrar e sair da tela cheia
def alternar_tela_cheia(event=None):
    window.attributes('-fullscreen', not window.attributes('-fullscreen'))

def sair_tela_cheia(event=None):
    window.attributes('-fullscreen', False)

# tamanho inicial da janela baseado na tela onde ela abre
sw = window.winfo_screenwidth()
sh = window.winfo_screenheight()
alt_inicial = min(int(sh * TELA_PERC_ALTURA), sh - 80)
larg_inicial = min(int(sw * 0.9), alt_inicial - 120)
larg_inicial = max(larg_inicial, MIN_LARGURA)
alt_inicial = max(alt_inicial, MIN_ALTURA)
pos_x = max(0, (sw - larg_inicial) // 2)
pos_y = max(0, (sh - alt_inicial) // 2 - 20)
window.geometry(f'{larg_inicial}x{alt_inicial}+{pos_x}+{pos_y}')
window.minsize(MIN_LARGURA, MIN_ALTURA)

# a coluna e a linha do tabuleiro esticam junto com a janela
window.columnconfigure(0, weight=1)
window.rowconfigure(1, weight=1)


# layout da interface
# cabeçalho com título e subtítulo
header = tk.Frame(window, bg=BG_COLOR)
header.grid(row=0, column=0, pady=(10, 2))

tk.Label(header, text='DRAGON BALL Z', font=fonte_titulo, fg=YELLOW, bg=BG_COLOR).pack()
tk.Label(header, text='★  JOGO DA MEMÓRIA DOS GUERREIROS Z  ★', font=fonte_sub,
         fg=ORANGE, bg=BG_COLOR).pack()

# card grid
moldura = tk.Frame(window, bg=ORANGE, padx=6, pady=6)
moldura.grid(row=1, column=0, sticky='nsew', padx=16, pady=8)
tabuleiro = tk.Frame(moldura, bg=PANEL_COLOR, padx=8, pady=8)
tabuleiro.pack(fill='both', expand=True)

# configurar as colunas e linhas para expandir com a janela
for c in range(NUM_COLS):
    tabuleiro.columnconfigure(c, weight=1, uniform='col')
for r in range(NUM_ROWS):
    tabuleiro.rowconfigure(r, weight=1, uniform='row')

# cria os botões dos cards na grade
for r in range(NUM_ROWS):
    linha = []
    for c in range(NUM_COLS):
        btn = tk.Button(
            tabuleiro, width=10, height=10, image=pixel_vazio, compound='center',
            bd=4, cursor='hand2',
            command=lambda rr=r, cc=c: card_clicked(rr, cc),
        )
        btn.grid(row=r, column=c, padx=4, pady=4, sticky='nsew')
        linha.append(btn)
    cards.append(linha)

# rodapé com placar, barra de ki e botão de reiniciar
footer = tk.Frame(window, bg=BG_COLOR)
footer.grid(row=2, column=0, sticky='ew', padx=16, pady=(4, 12))
footer.columnconfigure(3, weight=1)  
# labels e barra de ki
attempts_label = tk.Label(footer, font=fonte_sub, fg=WHITE, bg=BG_COLOR)
attempts_label.grid(row=0, column=0, padx=(0, 14))
# label para mostrar o número de pares encontrados
pairs_label = tk.Label(footer, font=fonte_sub, fg=YELLOW, bg=BG_COLOR)
pairs_label.grid(row=0, column=1, padx=(0, 14))
# label e barra de ki
tk.Label(footer, text='KI:', font=fonte_sub, fg=ORANGE, bg=BG_COLOR).grid(row=0, column=2)
ki_bar = tk.Canvas(footer, width=60, height=16, bg=BG_COLOR, highlightthickness=0)
ki_bar.grid(row=0, column=3, padx=(4, 14), sticky='ew')
ki_bar.bind('<Configure>', update_score)
# botão de reiniciar
tk.Button(footer, text='REINICIAR', font=fonte_sub, bg=RED, fg=WHITE,
          activebackground=ORANGE, activeforeground=BG_COLOR, bd=3, cursor='hand2',
          command=reiniciar).grid(row=0, column=4)

# redimensionar os cards e imagens
tabuleiro.bind('<Configure>', ao_redimensionar)
window.bind('<F11>', alternar_tela_cheia)
window.bind('<Escape>', sair_tela_cheia)

# inicia o jogo
reiniciar()
window.mainloop()