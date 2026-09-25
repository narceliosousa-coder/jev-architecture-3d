# -*- coding: utf-8 -*-
"""Cena 3D interativa e detalhada da arquitetura do Jev (TypeSafe AI / System One Model).
Gera a descrição da cena (JSON) e um HTML autocontido renderizado com Three.js."""
import json
import os
import re
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from saber_mais import MORE   # textos 'Saber mais' (um por card)

# ---------- paleta (mesma familia do PDF) ----------
INK = "#1c2230"
MUTED = "#5b6472"
C_IN = "#3a7bd5"       # entrada
C_IN2 = "#7fb0ea"
C_TR = "#14365d"       # atencao
C_TRQ, C_TRK, C_TRV = "#2b4f7e", "#3d6597", "#5479ad"   # Q K V
C_TRO = "#1f4470"      # W_O
C_TR2 = "#476a94"      # ffn
C_TR2b = "#6f8db3"     # gate/up
C_TR3 = "#9fb3c8"      # norm
C_TR4 = "#6b7c93"      # add
C_RES = "#b7c4d6"      # fluxo residual
C_CHOICE = "#c8552b"
C_SCORE = "#2a9d8f"
C_NOUL = "#8e44ad"
C_CAL = "#d4a017"
C_OUT = "#1f7a4d"
C_GHOST = "#9aa3ad"
C_RED = "#c0392b"

PRIMS = []        # primitivas da cena (JSON)
GROUPS = []       # legenda: (nome, cor) na ordem de aparicao
_xoff = 0.0       # deslocamento em x aplicado por todos os helpers (muda apos a etapa 1)
_layer = "main"   # "main" ou "exp" (regiao do Bloco 1 expandido)
components = []   # para o painel lateral


def _grp(lname, color):
    if lname and lname not in [g[0] for g in GROUPS]:
        GROUPS.append((lname, color))


def box(x0, x1, y0, y1, z0, z1, color, name, hover, group, opacity=1.0, legend_label=None):
    lname = legend_label or group
    _grp(lname, color)
    PRIMS.append(dict(t="box", b=[x0 + _xoff, x1 + _xoff, y0, y1, z0, z1], c=color, o=opacity, n=name,
                  h=f"<b>{name}</b><br>{hover}", g=lname, L=_layer))


def label(x, y, z, text, size=11, color=INK, bold=False):
    PRIMS.append(dict(t="label", p=[x + _xoff, y, z], s=str(text), sz=size, c=color, b=bool(bold), L=_layer))


def line(pts, color=MUTED, width=4, dash=None, hover=None):
    PRIMS.append(dict(t="line", pts=[[float(p[0]) + _xoff, float(p[1]), float(p[2])] for p in pts], c=color, w=width,
                  d=bool(dash), h=hover, L=_layer))


def arrow(p0, p1, color=MUTED, width=4, hover=None, head=0.5):
    PRIMS.append(dict(t="arrow", p0=[float(p0[0]) + _xoff, float(p0[1]), float(p0[2])],
                  p1=[float(p1[0]) + _xoff, float(p1[1]), float(p1[2])], c=color, w=width, hd=head, h=hover, L=_layer))


def points(pts, color, size, hover=None, sym="sphere"):
    PRIMS.append(dict(t="points", pts=[[float(p[0]) + _xoff, float(p[1]), float(p[2])] for p in pts], c=color, sz=size,
                  sym=sym, h=hover, L=_layer))


def floor(x0, x1, y0, y1, color, title, z=-0.35):
    box(x0, x1, y0, y1, z - 0.08, z, color, title, "Piso da etapa", "Etapas", opacity=0.12, legend_label="Etapas (piso)")
    label((x0 + x1) / 2, y0 - 1.0, z, title, size=13, color=color, bold=True)


# ---------- cameras (coordenadas de dados; o visualizador Three.js posiciona a camera) ----------
XOFF2 = 14.0
ZE = 40.0    # deslocamento vertical da regiao 'Bloco 1 expandido' (acima da cena: o bloco sobe ate la)
XMIN, XMAX, YMIN, YMAX, ZMIN, ZMAX = -0.5, 37.5 + XOFF2, -17.5, 13.0, -0.5, ZE + 24.5
DUNIT = 23.8   # 1 unidade de distancia "plotly" ~ 23.8 unidades de dados (calibracao herdada)


def view(cx, cy, cz, dist, az_deg, el_deg):
    """Alvo (x,y,z) em dados + distancia em dados + azimute/elevacao em graus."""
    if dist < 1.0:
        dist *= 1.5   # vistas focadas: afastar um pouco
    return dict(tg=[float(cx + _xoff), float(cy), float(cz)], d=float(dist * DUNIT), az=float(az_deg), el=float(el_deg))


def comp(stage, cid, title, desc, cam, formula=None, exp=False):
    components.append(dict(stage=stage, id=cid, title=title, desc=desc, cam=cam, formula=formula, exp=exp))


# =====================================================================
# ETAPA 1 — ENTRADA E PRE-PROCESSAMENTO  (x 0 .. 23) — matrizes de frente (plano x-z)
# =====================================================================
def _hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def ramp(v, c0="#e8f0fa", c1="#2f6db5"):
    """valor em [0,1] -> cor entre c0 (claro) e c1 (escuro)."""
    a, b = _hex2rgb(c0), _hex2rgb(c1)
    v = float(min(max(v, 0.0), 1.0))
    return "#%02x%02x%02x" % tuple(int(round(a[i] + (b[i] - a[i]) * v)) for i in range(3))


def cubes(cells, group, legend_label=None, opacity=1.0):
    """Muitos cubinhos numa unica malha instanciada. cells = [(x0,x1,y0,y1,z0,z1,color,hover), ...]"""
    if not cells:
        return
    lname = legend_label or group
    _grp(lname, cells[0][6])
    PRIMS.append(dict(t="cubes", cells=[[float(x0) + _xoff, float(x1) + _xoff, float(y0), float(y1), float(z0), float(z1), col, hv]
                                    for (x0, x1, y0, y1, z0, z1, col, hv) in cells], g=lname, o=opacity, L=_layer))


CELL, GAP = 0.24, 0.06
PITCH = CELL + GAP


def wallx(x0, z0, y0, y1, ncols, nrows, color_fn, hover_fn, group, legend_label=None, cell=CELL, gap=GAP):
    """Matriz vertical de frente para o observador (plano x-z): ncols ao longo de x, nrows ao longo de z."""
    cells = []
    p = cell + gap
    for r in range(nrows):
        for c in range(ncols):
            xa = x0 + c * p
            za = z0 + r * p
            cells.append((xa, xa + cell, y0, y1, za, za + cell, color_fn(r, c), hover_fn(r, c)))
    cubes(cells, group, legend_label)
    return x0 + ncols * p - gap, z0 + nrows * p - gap   # extremos x, z


def plate(x0, x1, y0, y1, name, hover):
    box(x0, x1, y0, y1, 0.0, 0.05, "#d3e0f0", name, hover, "1 · Entrada", opacity=0.95)


rng1 = np.random.default_rng(11)
floor(-0.5, 23.3, -5.0, 2.2, C_IN, "1 · ENTRADA E PRÉ-PROCESSAMENTO")
YF0, YF1 = -0.25, 0.25          # espessura das matrizes (y)

# ---------- 1.1 state: "pagina" de linhas de texto, de frente ----------
state_cells = []
line_lengths = [11, 9, 10, 7, 11, 8, 5, 10, 9, 6]
kinds = ["texto", "texto", "texto", "JSON", "JSON", "JSON", "JSON", "telemetria", "telemetria", "texto"]
for r, (n, kind) in enumerate(zip(line_lengths, kinds)):
    z0 = 0.12 + (len(line_lengths) - 1 - r) * 0.26      # linha 1 no topo
    for c in range(n):
        x0 = 0.15 + c * PITCH
        shade = {"texto": 0.7, "JSON": 0.45, "telemetria": 0.95}[kind] + rng1.uniform(-0.1, 0.1)
        state_cells.append((x0, x0 + CELL, YF0, YF1, z0, z0 + 0.2, ramp(shade, "#bcd5f2", "#1f5aa6"),
                            f"<b>1.1 state</b> · linha {r + 1} ({kind})<br>Trecho de contexto: será tokenizado junto com os critérios.<br>"
                            "Contagens, datas e agregações precisam já vir calculadas aqui."))
cubes(state_cells, "1 · Entrada")
plate(0.0, 3.5, -0.4, 0.4, "1.1 state (contexto)", "Página de contexto: texto livre, JSON, telemetria.")
label(1.75, 0, 3.3, "state", size=12, bold=True)
label(1.75, 0, -0.5, "texto · JSON · telemetria", size=8, color=MUTED)
comp("1 · Entrada e pré-processamento", "1.1a", "1.1 state — bloco de contexto",
     "Representado como uma 'página' de frente: cada linha é uma sequência de cubinhos (palavras/campos). Tons diferentes "
     "marcam texto livre, JSON e telemetria — o Jev aceita tudo misturado, sem delimitação de formato. É a única fonte de "
     "evidência: contagens, datas calculadas e agregações precisam já estar aqui. Limite: state + interrogação mais longa ≤ 32k tokens.",
     view(1.75, 0, 1.4, 0.32, -85, 18))

# ---------- 1.1 M interrogacoes: cartoes na frente do state (y negativo), criterios como cubinhos ----------
YQ0, YQ1 = -3.2, -2.0
for idx, (nm, col, desc) in enumerate([
    ("Choice", C_CHOICE, "Conjunto fechado de 2 a 255 opções, cada uma com descrição semântica."),
    ("Score", C_SCORE, "Escala ordinal de 2 a 10 patamares descritos semanticamente."),
    ("Noul", C_NOUL, "Afirmação declarativa booleana unária."),
]):
    x0 = 0.1 + idx * 1.2
    box(x0, x0 + 1.0, YQ0, YQ1, 0, 0.3, col, f"1.1 Interrogação {nm} · instructions",
        f"Texto de instrução da pergunta ({nm}).<br>Hiper-literalismo: só o que está escrito aqui é considerado.",
        "1 · Entrada", legend_label=f"Primitiva {nm}", opacity=0.5)
    crit = []
    if nm == "Choice":
        for k2 in range(4):
            xa = x0 + 0.08 + k2 * 0.23
            crit.append((xa, xa + 0.18, YQ0 + 0.35, YQ1 - 0.35, 0.35, 0.7, col, f"<b>criteria Choice</b> · opção {k2 + 1} de K (2 ≤ K ≤ 255)<br>{desc}"))
    elif nm == "Score":
        for k2 in range(3):
            xa = x0 + 0.12 + k2 * 0.28
            crit.append((xa, xa + 0.22, YQ0 + 0.35, YQ1 - 0.35, 0.35, 0.5 + 0.2 * k2, col, f"<b>criteria Score</b> · patamar {k2} (ordenado)<br>{desc}"))
    else:
        crit.append((x0 + 0.3, x0 + 0.7, YQ0 + 0.35, YQ1 - 0.35, 0.35, 0.7, col, f"<b>criteria Noul</b> · asserção única<br>{desc}"))
    cubes(crit, "1 · Entrada", legend_label=f"Primitiva {nm}")
    label(x0 + 0.5, YQ0 - 0.15, 0.55, nm, size=9.5, color=col, bold=True)
label(1.75, YQ0 - 0.15, 1.35, "M interrogações (esquema fechado)", size=10, bold=True)
comp("1 · Entrada e pré-processamento", "1.1b", "1.1 Dicionário de M interrogações",
     "Três cartões translúcidos na frente do state: cada um é o texto de instructions de uma pergunta; os cubinhos em cima "
     "são os criteria, na forma de cada primitiva — Choice = K opções lado a lado; Score = patamares em escada (ordinal); "
     "Noul = uma única asserção. O esquema é fechado: o modelo não pode responder fora dele. As M perguntas não competem "
     "entre si nem dependem de respostas prévias.", view(1.75, -2.6, 0.5, 0.3, -80, 35))

# ---------- 1.2 tokenizer: esteira com duas fileiras (fragmentos -> IDs) ----------
T1 = 14
src_of = lambda t: "state" if t < 9 else ("Choice" if t < 11 else ("Score" if t < 13 else "Noul"))
col_of = {"state": C_IN, "Choice": C_CHOICE, "Score": C_SCORE, "Noul": C_NOUL}
frag = ["trans", "ação", "ip", "diverg", "valor", "12500", "hist", "reclam", "0", "aprovar", "bloq", "risco", "moder", "conten"]
ids = [1042, 77, 3301, 812, 2210, 9541, 605, 4419, 15, 720, 3388, 951, 2748, 6120]
TX0 = 4.3
tok_cells = []
for t in range(T1):
    xa = TX0 + t * PITCH
    s_ = src_of(t)
    tok_cells.append((xa, xa + CELL, YF0, YF1, 0.15, 0.15 + CELL, ramp(0.3, "#ffffff", col_of[s_]),
                      f"<b>1.2 fragmento</b> '{frag[t]}' (origem: {s_})<br>Pedaço de texto antes da tokenização."))
    tok_cells.append((xa, xa + CELL, YF0, YF1, 1.0, 1.0 + CELL, col_of[s_],
                      f"<b>1.2 token ID</b> {ids[t]} ← '{frag[t]}' (origem: {s_})<br>Posição t = {t + 1} de T na sequência única (≤ 64k)."))
cubes(tok_cells, "1 · Entrada")
TX1 = TX0 + T1 * PITCH - GAP
plate(TX0 - 0.15, TX1 + 0.15, -0.4, 0.4, "1.2 Tokenizer (esteira)", "Uma única sequência: state ⊕ instruções ⊕ critérios.")
for t in range(T1):
    xa = TX0 + t * PITCH + CELL / 2
    arrow((xa, 0, 0.42), (xa, 0, 0.97), color=MUTED, width=2, head=0.16)
    if t in (0, 4, 9, 11, 13):
        label(xa, 0, 1.55, str(ids[t]), size=7, color=MUTED)
label((TX0 + TX1) / 2, 0, 2.2, "Tokenizer", size=11, bold=True)
label((TX0 + TX1) / 2, 0, -0.5, "texto → IDs · T tokens · ≤ 64k por chamada", size=8, color=MUTED)
label(TX1 + 0.45, 0, 0.27, "fragmentos", size=7, color=MUTED)
label(TX1 + 0.35, 0, 1.12, "IDs", size=7, color=MUTED)
comp("1 · Entrada e pré-processamento", "1.2", "1.2 Tokenização e empacotamento unificado",
     "Esteira com duas fileiras: embaixo os fragmentos de texto, em cima o ID numérico de cada um (setinhas = lookup no "
     "vocabulário). A cor diz a origem — azul = state, laranja/verde/roxo = critérios de cada primitiva — mas todos vão na "
     "MESMA sequência de T posições. É isso que, mais adiante, deixa os critérios 'verem' o contexto na atenção. "
     "Teto: 64k tokens acumulados por chamada.", view((TX0 + TX1) / 2, 0, 1.0, 0.36, -88, 15))

# ---------- 1.3 embedding: matriz |V| x d_model com a linha consultada em destaque ----------
D = 12          # colunas (d_model)
VROWS = 11      # linhas visiveis (|V|)
E = rng1.random((VROWS, D))
for r in range(VROWS):
    E[r] = 0.5 * E[r] + 0.5 * np.convolve(E[r], np.ones(3) / 3, mode="same")
hl_row = 6      # linha do token consultado (id 1042)
EX0 = 9.3


def e_color(r, c):
    return ramp(E[r, c], "#f6d9cc", "#c8552b") if r == hl_row else ramp(E[r, c])


def e_hover(r, c):
    base = (f"<b>1.3 Embedding</b> E[v, j] · linha v = token {'1042 (consultado)' if r == hl_row else '…'} · "
            f"coluna j = dimensão {c + 1} de d_model<br>peso aprendido ≈ {E[r, c]:.2f}")
    if r == hl_row:
        base += "<br><b>Lookup:</b> o ID 1042 seleciona esta linha inteira → vetor de d_model."
    return base


EX1, EZ1 = wallx(EX0, 0.15, YF0, YF1, D, VROWS, e_color, e_hover, "1 · Entrada")
plate(EX0 - 0.15, EX1 + 0.15, -0.4, 0.4, "1.3 Matriz de incorporação", "|V| × d_model")
HLZ = 0.15 + hl_row * PITCH + CELL / 2
label((EX0 + EX1) / 2, 0, EZ1 + 0.95, "Embedding  |V| × d_model", size=11, bold=True)
label((EX0 + EX1) / 2, 0, EZ1 + 0.45, "⋮  |V| ≈ dezenas de milhares de linhas  ⋮", size=7, color=MUTED)
label(EX1 + 0.85, 0, HLZ, "← E[1042]", size=7.5, color=C_CHOICE, bold=True)
label(EX0 - 0.45, 0, EZ1 / 2, "|V|", size=8, color=MUTED)
label((EX0 + EX1) / 2, 0, -0.5, "d_model →", size=8, color=MUTED)
comp("1 · Entrada e pré-processamento", "1.3", "1.3 Matriz de incorporação (Token Embedding)",
     "Agora uma matriz de verdade: linhas = entradas do vocabulário (|V|, truncado com ⋮), colunas = dimensões d_model. "
     "Cada cubinho é um peso aprendido (tom = valor). A linha laranja é o lookup do ID 1042: o token seleciona a linha inteira, "
     "que vira o seu vetor. Repetindo para os T tokens obtém-se a matriz T × d_model da direita.",
     view((EX0 + EX1) / 2, 0, 1.9, 0.36, -88, 12))

# ---------- 1.4 RoPE: matriz T x d_model com padrao senoidal ----------
POS = T1
pe = np.zeros((D, POS))
for i in range(D):
    freq = 1.0 / (10000 ** (2 * (i // 2) / D))
    for p in range(POS):
        pe[i, p] = np.sin(p * freq) if i % 2 == 0 else np.cos(p * freq)
pe01 = 0.5 + 0.5 * pe
PX0 = 13.8


def pe_color(r, c):
    return ramp(pe01[r, c], "#ece4f5", "#6a3a9e")


def pe_hover(r, c):
    fn = "sin" if r % 2 == 0 else "cos"
    return (f"<b>1.4 Codificação posicional</b> · posição t = {c + 1} · dimensão {r + 1}<br>"
            f"{fn}(t · ω_{r // 2 + 1}) = {pe[r, c]:+.2f} — em RoPE o par (dim {2 * (r // 2) + 1}, {2 * (r // 2) + 2}) "
            f"é rotacionado pelo ângulo t·ω.<br>Bidirecional: dá ordem relativa sem impor causalidade.")


PX1, PZ1 = wallx(PX0, 0.15, YF0, YF1, POS, D, pe_color, pe_hover, "1 · Entrada")
plate(PX0 - 0.15, PX1 + 0.15, -0.4, 0.4, "1.4 Codificação posicional", "T × d_model")
label((PX0 + PX1) / 2, 0, PZ1 + 0.95, "RoPE bidirecional  (T × d_model)", size=11, bold=True)
label((PX0 + PX1) / 2, 0, PZ1 + 0.45, "linhas = pares (sin, cos) com frequência ω_i; ω alta embaixo, baixa em cima", size=7, color=MUTED)
label((PX0 + PX1) / 2, 0, -0.5, "posição t →", size=8, color=MUTED)
label(PX0 - 0.55, 0, PZ1 / 2, "d_model", size=8, color=MUTED)
comp("1 · Entrada e pré-processamento", "1.4", "1.4 Codificação posicional (RoPE)",
     "Matriz T × d_model com o padrão senoidal característico: colunas = posições t, linhas = dimensões, cada par de linhas com "
     "uma frequência ω_i diferente (rápidas embaixo, lentas em cima). Em RoPE esse ângulo t·ω gira pares de dimensões de Q e K; "
     "aqui está mostrado como a injeção de posição do passo 1.4. Dá ordem relativa sem impor 'antes/depois' obrigatório.",
     view((PX0 + PX1) / 2, 0, 1.9, 0.36, -88, 12))

# ---------- 1.5 matriz de saida X = E[ids] (+) pos  (T x d_model) ----------
OX0 = 18.9


def out_color(r, c):
    v = 0.6 * E[(c * 3 + r) % VROWS, r] + 0.4 * pe01[r, c]
    return ramp(v, "#e8f0fa", "#2b4f7e") if c < 9 else ramp(0.35 + 0.65 * v, "#ffffff", col_of[src_of(c)])


def out_hover(r, c):
    return (f"<b>Saída da etapa 1</b> · X[t={c + 1}, j={r + 1}] = E[id_t, j] ⊕ pos(t, j)<br>"
            f"Token '{frag[c]}' (origem: {src_of(c)}).<br>Matriz T × d_model que entra no Bloco 1.")


OX1, OZ1 = wallx(OX0, 0.15, YF0, YF1, POS, D, out_color, out_hover, "1 · Entrada")
plate(OX0 - 0.15, OX1 + 0.15, -0.4, 0.4, "Saída: T × d_model", "Entrada do Bloco 1")
label((OX0 + OX1) / 2, 0, OZ1 + 0.95, "X = E[ids] ⊕ pos   (T × d_model)", size=10.5, bold=True)
label((OX0 + OX1) / 2, 0, OZ1 + 0.45, "colunas coloridas à direita = tokens dos critérios", size=7, color=MUTED)
label((OX0 + OX1) / 2, 0, -0.5, "posição t →", size=8, color=MUTED)
label((PX1 + OX0) / 2, 0, OZ1 / 2, "⊕", size=18, color=INK, bold=True)
comp("1 · Entrada e pré-processamento", "1.5", "Saída da etapa 1 — matriz T × d_model",
     "Resultado da etapa: uma matriz com T colunas (uma por token; as últimas, coloridas, são os critérios) e d_model linhas. "
     "É o embedding de cada token combinado com sua posição. Essa matriz inteira entra no Bloco 1 de uma vez — não há "
     "'próximo token' a esperar.", view((OX0 + OX1) / 2, 0, 1.9, 0.36, -88, 12))

# ---------- fluxo ----------
arrow((3.55, 0, 1.3), (TX0 - 0.2, 0, 1.3), color=C_IN)
arrow((1.9, YQ1, 0.4), (TX0 - 0.2, -0.45, 0.7), color=C_IN, width=3)
arrow((TX1 + 0.2, 0, 1.12), (EX0 - 0.2, 0, 1.12), color=C_IN, hover="IDs → lookup na matriz E")
arrow((EX1 + 0.2, 0, HLZ), (PX0 - 0.2, 0, HLZ), color=C_CHOICE, width=3, hover="Linha E[1042] (vetor d_model) recebe a posição")
arrow((OX1 + 0.3, 0, 2.0), (XOFF2 + 10.3, 0, 0.3), color=C_TR, hover="Matriz T × d_model → Bloco 1")
label(OX1 + 1.1, 0.5, 2.4, "T × d_model", size=8, color=MUTED)

# =====================================================================
# ETAPA 2 — N BLOCOS TRANSFORMER  (x 10 .. 22)
# =====================================================================
_xoff = XOFF2
floor(9.7, 22.5, -3.8, 7.8, C_TR, "2 · N BLOCOS TRANSFORMER — PASSO EM FRENTE ÚNICO")

block_x = [10.5, 13.5, 16.5, 19.5]
for bi, xb in enumerate(block_x):
    b = f"Bloco {bi + 1} · "
    # 2.1 pre-norm
    box(xb, xb + 1.6, -2, 2, 0.0, 0.5, C_TR3, b + "2.1 Pre-Norm", "RMSNorm / LayerNorm aplicada ANTES da atenção (arquitetura pre-norm).", "2 · Transformer")
    # 2.2 atencao: Q K V (lado a lado) -> scores/softmax -> W_O
    box(xb, xb + 1.6, -2.0, -0.75, 0.6, 1.15, C_TRQ, b + "2.2 Projeção Q (W_Q)", "Query = x · W_Q  — h cabeças de atenção (MHA) ou grupos (GQA).", "2 · Transformer")
    box(xb, xb + 1.6, -0.6, 0.6, 0.6, 1.15, C_TRK, b + "2.2 Projeção K (W_K)", "Key = x · W_K  — em GQA, K/V são compartilhados entre grupos de cabeças.", "2 · Transformer")
    box(xb, xb + 1.6, 0.75, 2.0, 0.6, 1.15, C_TRV, b + "2.2 Projeção V (W_V)", "Value = x · W_V.", "2 · Transformer")
    box(xb, xb + 1.6, -2, 2, 1.25, 1.85, C_TR, b + "2.2 Scores + Softmax — SEM máscara causal",
        "A = softmax(Q·Kᵀ / √d_k) · V, sobre a matriz T×T <b>completa</b>.<br>"
        "Todos os tokens do state e dos critérios interagem mutuamente (bidirecional, denso).", "2 · Transformer")
    box(xb, xb + 1.6, -2, 2, 1.95, 2.35, C_TRO, b + "2.2 Projeção de saída W_O", "Concatena as h cabeças e projeta de volta a d_model.", "2 · Transformer")
    # 2.3 add
    box(xb, xb + 1.6, -2, 2, 2.45, 2.85, C_TR4, b + "2.3 Add (residual 1)", "x = x + Atenção(x)", "2 · Transformer")
    # 2.4 norm
    box(xb, xb + 1.6, -2, 2, 2.95, 3.45, C_TR3, b + "2.4 Norm", "RMSNorm / LayerNorm antes da FFN.", "2 · Transformer")
    # 2.5 ffn: gate + up -> ativacao -> down
    box(xb, xb + 1.6, -2.0, -0.1, 3.55, 4.25, C_TR2b, b + "2.5 FFN · W_gate", "Ramo de porta: g = x · W_gate  (SwiGLU).", "2 · Transformer")
    box(xb, xb + 1.6, 0.1, 2.0, 3.55, 4.25, C_TR2b, b + "2.5 FFN · W_up", "Ramo de expansão: u = x · W_up  (d_model → d_ff, ~4×).", "2 · Transformer")
    box(xb, xb + 1.6, -2, 2, 4.35, 4.7, C_TR2, b + "2.5 FFN · ativação SwiGLU / GeLU", "h = SiLU(g) ⊙ u  — não linearidade com porta.", "2 · Transformer")
    box(xb, xb + 1.6, -2, 2, 4.8, 5.3, C_TR2, b + "2.5 FFN · W_down", "Projeção de volta: h · W_down  (d_ff → d_model).", "2 · Transformer")
    # 2.6 add
    box(xb, xb + 1.6, -2, 2, 5.4, 5.8, C_TR4, b + "2.6 Add (residual 2)", "x = x + MLP(x)", "2 · Transformer")
    # fluxo residual (tubo lateral)
    box(xb + 1.75, xb + 2.05, -0.2, 0.2, 0.0, 5.8, C_RES, b + "Fluxo residual (d_model)",
        "Corrente residual que atravessa o bloco. Cada subcamada só <i>soma</i> sua contribuição.", "2 · Transformer",
        opacity=0.55, legend_label="Fluxo residual")
    line([(xb + 1.9, 0, 0.25), (xb + 1.9, 0, 2.65), (xb + 1.6, 0, 2.65)], color=C_TR4, width=3, dash="dash", hover="Residual 1 → Add")
    line([(xb + 1.9, 0, 2.9), (xb + 1.9, 0, 5.6), (xb + 1.6, 0, 5.6)], color=C_TR4, width=3, dash="dash", hover="Residual 2 → Add")
    label(xb + 0.8, -2.6, 6.4, f"Bloco {bi + 1}" if bi < 3 else "Bloco N", size=11, bold=True)
    if bi == 0:
        label(xb + 0.8, -2.6, 7.1, "passe o mouse: expandir em matrizes", size=7.5, color=C_CHOICE)
    if bi < 3:
        arrow((xb + 1.6, 0.9, 5.6), (block_x[bi + 1], 0.9, 0.25), color=C_TR, width=3)

# rótulos das subcamadas ao lado do bloco 1
for z, t in [(0.25, "2.1 Pre-Norm"), (0.9, "2.2 Q · K · V"), (1.55, "2.2 softmax(QKᵀ/√d)·V"), (2.15, "2.2 W_O"),
             (2.65, "2.3 Add"), (3.2, "2.4 Norm"), (3.9, "2.5 W_gate · W_up"), (4.5, "2.5 SwiGLU"),
             (5.05, "2.5 W_down"), (5.6, "2.6 Add")]:
    label(10.4, -3.4, z, t, size=8.5, color=MUTED)
label(16.0, 0, 7.4, "× N blocos · um único forward pass · sem loop de decodificação", size=11, color=C_TR, bold=True)

comp("2 · N blocos Transformer", "2.1", "2.1 Primeira normalização (Pre-Norm)",
     "RMSNorm ou LayerNorm aplicada à entrada do bloco, antes da atenção. O arranjo pre-norm estabiliza o treino "
     "e mantém o fluxo residual 'limpo' (as normalizações ficam nos ramos, não na corrente principal).",
     view(11.3, 0, 0.3, 0.3, -70, 20))
comp("2 · N blocos Transformer", "2.2", "2.2 Atenção bidirecional global (MHA / GQA)",
     "Três projeções lineares geram Q, K e V (h cabeças; em GQA, K/V compartilhados por grupo). Os scores "
     "Q·Kᵀ/√d_k passam pelo softmax SEM máscara causal: a matriz T×T é completa, então os tokens dos critérios das "
     "perguntas atendem ao state inteiro e vice-versa. O resultado das cabeças é concatenado e projetado por W_O. "
     "É aqui que a decisão é 'resolvida' em profundidade constante, em vez de token a token.",
     view(11.3, 0, 1.5, 0.3, -70, 15))
comp("2 · N blocos Transformer", "2.3", "2.3 Primeira ligação residual (Add)",
     "x ← x + Atenção(x). A linha tracejada ao lado do bloco mostra a corrente residual desviando a subcamada. "
     "Nada é sobrescrito: cada subcamada apenas soma sua contribuição ao vetor de cada token.",
     view(11.3, 0, 2.65, 0.3, -70, 15))
comp("2 · N blocos Transformer", "2.4", "2.4 Segunda normalização",
     "RMSNorm/LayerNorm antes da rede densa (FFN). Mesmo padrão pre-norm da subcamada anterior.",
     view(11.3, 0, 3.2, 0.3, -70, 15))
comp("2 · N blocos Transformer", "2.5", "2.5 MLP / FFN com porta (SwiGLU / GeLU)",
     "Dois ramos paralelos (W_gate e W_up) expandem d_model → d_ff (~4×); a ativação SiLU(g) ⊙ u aplica a porta; "
     "W_down projeta de volta a d_model. É onde ficam os 'mapeamentos semânticos' (conhecimento/associações) do modelo.",
     view(11.3, 0, 4.4, 0.3, -70, 15))
comp("2 · N blocos Transformer", "2.6", "2.6 Segunda ligação residual (Add)",
     "x ← x + MLP(x). Fecha o bloco. A saída (T × d_model) alimenta o bloco seguinte — N vezes — e ao final "
     "vai direto para a normalização final. Não há retorno para o início (sem loop autorregressivo).",
     view(11.3, 0, 5.6, 0.3, -70, 15))
comp("2 · N blocos Transformer", "2.R", "Fluxo residual (tubo lateral)",
     "Barra translúcida ao lado de cada bloco: a corrente residual de dimensão d_model que percorre todas as camadas. "
     "As subcamadas lêem dela e somam de volta (setas tracejadas).", view(12.4, 0, 3.0, 0.32, -50, 15))

# ---- inset: mascara causal vs atencao bidirecional ----
T = 10
rng = np.random.default_rng(3)
full_w = 0.35 + 0.65 * rng.random((T, T))
causal_w = np.tril(np.ones((T, T))) * (0.35 + 0.65 * rng.random((T, T)))
yy, xx = np.meshgrid(np.linspace(-2, 2, T), np.linspace(0, 4, T), indexing="ij")


def heat(x_off, z0, w, title, hover):
    PRIMS.append(dict(t="heat", x0=float(x_off + _xoff), x1=float(x_off + 4 + _xoff), y0=-2.0, y1=2.0, z=float(z0),
                  w=[[float(v) for v in row] for row in w], h=f"<b>{title}</b><br>{hover}", L=_layer))
    label(x_off + 2, 0, z0 + 0.9, title, size=10, color=C_TR, bold=True)
    label(x_off + 2, -2.5, z0, "keys →", size=8, color=MUTED)
    label(x_off - 0.5, 0, z0, "queries ↓", size=8, color=MUTED)


heat(10.3, 9.0, causal_w, "LLM decoder: máscara causal (só o passado)",
     "Matriz de atenção T×T triangular inferior.<br>Token t só vê 1..t. Força a geração sequencial, token a token.")
heat(17.2, 9.0, full_w, "Jev: atenção bidirecional densa",
     "Matriz T×T cheia: state ↔ critérios ↔ instruções.<br>Toda a decisão é resolvida num único passo.")
label(15.75, 0, 9.0, "→", size=22, color=C_CHOICE, bold=True)
label(15.75, 0, 9.9, "sem Causal Mask", size=10, color=C_CHOICE, bold=True)
comp("2 · N blocos Transformer", "2.M", "Inset: máscara causal vs. atenção bidirecional",
     "Duas matrizes T×T flutuando sobre os blocos. Esquerda: decoder tradicional — triângulo inferior, cada query só "
     "vê keys do passado, o que obriga a gerar um token por vez. Direita: Jev — matriz cheia, todo token vê todos; "
     "por isso o modelo é um encoder bidirecional (linhagem ModernBERT) e resolve tudo em um passo.",
     view(15.8, 0, 9.0, 0.55, -90, 75))

# =====================================================================
# ETAPA 3 — SAIDA E PROJECAO TIPADA  (x 24 .. 37)
# =====================================================================
floor(23.7, 37.3, -7.5, 7.5, C_OUT, "3 · SAÍDA E PROJEÇÃO TIPADA")

arrow((21.1, 0.9, 5.6), (24, 0, 2.6), color=C_TR, hover="Ativações finais (T × d_model) após N blocos")
box(24, 25, -2, 2, 0, 5.2, C_TR3, "3.1 Normalização final",
    "RMSNorm / LayerNorm nos vetores de saída dos N blocos.", "3 · Saída tipada")
label(24.5, 0, 5.9, "Norm final", size=11, bold=True)
comp("3 · Saída e projeção tipada", "3.1a", "3.1 Normalização final",
     "Última RMSNorm/LayerNorm sobre a matriz T × d_model que sai do bloco N.", view(24.5, 0, 2.6, 0.32, -70, 20))

label(26.1, 0, 6.8, "3.1 Pooling por interrogação", size=11, bold=True)
label(26.1, 0, 6.2, "separa M vetores latentes → M cabeças", size=9, color=MUTED)
heads = [("Choice", C_CHOICE, -5.0), ("Score", C_SCORE, 0.0), ("Noul", C_NOUL, 5.0)]
for nm, col, yh in heads:
    arrow((25, 0, 2.6), (27, yh, 1.0), color=col, width=5, hover=f"Vetor latente pooled da interrogação {nm}")
comp("3 · Saída e projeção tipada", "3.1b", "3.1 Agrupamento por interrogação (Pooling)",
     "Das T posições, o modelo extrai e separa o vetor de ativação correspondente a cada uma das M perguntas "
     "(por exemplo, a posição do token especial que abre cada interrogação). Cada vetor segue, em paralelo, para a "
     "cabeça da sua primitiva. As três setas coloridas são esse fan-out.", view(26, 0, 1.8, 0.45, -70, 25))

# --- CHOICE ---
box(27, 28, -6, -4, 0, 2, C_CHOICE, "3.2 Cabeça Choice — projeção restrita",
    "W_choice: d_model → K (2 ≤ K ≤ 255), <b>só</b> as opções cadastradas.<br>"
    "Softmax → .probabilities · argmax → .choice · concentração → .confidence", "3 · Saída tipada",
    legend_label="Primitiva Choice")
label(27.5, -5, 2.6, "Choice", size=11, color=C_CHOICE, bold=True)
label(27.5, -5, -0.5, "d_model → K", size=8, color=MUTED)
opts = [("bloquear", 0.72), ("solicitar_mfa", 0.15), ("aprovar", 0.09), ("insufficient_data", 0.04)]
for i2, (o, p) in enumerate(opts):
    y0 = -6.0 + i2 * 0.55
    box(29, 29.7, y0, y0 + 0.42, 0, p * 3.2, C_CHOICE if i2 == 0 else "#e6a58c",
        f"Softmax · opção '{o}'", f".probabilities['{o}'] = {p:.2f}" + ("<br><b>argmax → .choice = 'bloquear'</b><br>.confidence = 0.72" if i2 == 0 else ""),
        "3 · Saída tipada", legend_label="Primitiva Choice")
    label(31.0, y0 + 0.2, 0.12, f"{o}  {p:.2f}", size=8, color=MUTED)
points([(29.35, -5.79, 0.72 * 3.2 + 0.35)], C_CHOICE, 6, "<b>argmax</b> → .choice = 'bloquear' · .confidence = 0.72", "diamond")
label(29.35, -5.79, 0.72 * 3.2 + 0.9, ".choice = 'bloquear' · .confidence 0.72", size=9, color=C_CHOICE, bold=True)
label(29.4, -5, 3.4, "Softmax sobre K opções (K = 4)", size=9, color=MUTED)
comp("3 · Saída e projeção tipada", "3.2a", "3.2 Cabeça Choice",
     "Projeção linear restrita ao subespaço das K opções declaradas (2 ≤ K ≤ 255). Softmax dá .probabilities; "
     "argmax dá .choice; a concentração da distribuição vira .confidence. Como não há vocabulário aberto, é "
     "algebricamente impossível emitir uma opção fora das K — alucinação de formato eliminada por construção. "
     "Acima de 255 opções: filtrar antes com Score e escolher depois.", view(29, -5, 1.2, 0.4, -60, 25))

# --- SCORE ---
box(27, 28, -1, 1, 0, 2, C_SCORE, "3.2 Cabeça Score — escala ordinal",
    "W_score: d_model → L patamares (2 ≤ L ≤ 10), ordenados.<br>"
    "Regressão logística → centroide → <b>.score</b> contínuo (ex.: 1.035), + .probabilities por nível + .confidence",
    "3 · Saída tipada", legend_label="Primitiva Score")
label(27.5, 0, 2.6, "Score", size=11, color=C_SCORE, bold=True)
label(27.5, 0, -0.5, "d_model → L níveis", size=8, color=MUTED)
lv = [("negligível", 0.10), ("moderado", 0.75), ("crítico", 0.15)]
for i2, (o, p) in enumerate(lv):
    y0 = -0.9 + i2 * 0.7
    box(29, 29.7, y0, y0 + 0.5, 0, p * 3.2, C_SCORE if i2 == 1 else "#8fd0c8",
        f"Nível {i2} · '{o}'", f".probabilities[{i2}] = {p:.2f}", "3 · Saída tipada", legend_label="Primitiva Score")
    label(31.0, y0 + 0.25, 0.12, f"{i2} · {o}  {p:.2f}", size=8, color=MUTED)
sc = 0.10 * 0 + 0.75 * 1 + 0.15 * 2
yc = -0.9 + sc * 0.7 + 0.25
points([(29.35, yc, 3.0)], C_SCORE, 7, f"<b>.score</b> · Centroide: Σ p_i · i = 0.10·0 + 0.75·1 + 0.15·2 = {sc:.3f}<br>Contínuo, não truncado ao inteiro.", "diamond")
label(29.35, yc, 3.55, f".score = {sc:.3f} (centroide)", size=9, color=C_SCORE, bold=True)
line([(29.35, yc, 0), (29.35, yc, 2.9)], color=C_SCORE, width=2, dash="dot")
comp("3 · Saída e projeção tipada", "3.2b", "3.2 Cabeça Score",
     "Projeção sobre 2–10 patamares ordenados descritos semanticamente. Uma regressão logística multissegmento "
     "localiza o centroide da distribuição (Σ p_i · i), devolvendo .score como float interpolado — no exemplo 1.050, "
     "entre 'moderado' (1) e 'crítico' (2). Também retorna .probabilities por nível e .confidence.",
     view(29, 0, 1.2, 0.4, -60, 25))

# --- NOUL ---
box(27, 28, 4, 6, 0, 2, C_NOUL, "3.2 Cabeça Noul — sigmoide calibrada",
    "W_noul: d_model → 1 logit z. σ(z) = 1 / (1 + e^(−z)).<br>"
    "Saída direta em <b>.noul</b> ∈ [0,1] = P(asserção verdadeira).<br>Sem campo separado de confiança.",
    "3 · Saída tipada", legend_label="Primitiva Noul")
label(27.5, 5, 2.6, "Noul", size=11, color=C_NOUL, bold=True)
label(27.5, 5, -0.5, "d_model → 1", size=8, color=MUTED)
zz = np.linspace(-6, 6, 60)
sig = 1 / (1 + np.exp(-zz))
line([(29 + (z + 6) / 12 * 2.2, 5.0, sg * 3.0) for z, sg in zip(zz, sig)], color=C_NOUL, width=5,
     hover="<b>Sigmoide</b> σ(z) = 1 / (1 + e^(−z)) para z ∈ [−6, 6]")
line([(29, 5, 0), (31.2, 5, 0)], color=MUTED, width=2)
line([(29, 5, 1.5), (31.2, 5, 1.5)], color=MUTED, width=1, dash="dot", hover="σ = 0.5 (indiferença)")
z_ex = 1.2
s_ex = 1 / (1 + np.exp(-z_ex))
points([(29 + (z_ex + 6) / 12 * 2.2, 5.0, s_ex * 3.0)], C_NOUL, 7, f"<b>.noul</b> · logit z = {z_ex} → σ(z) = {s_ex:.2f}")
label(29 + (z_ex + 6) / 12 * 2.2, 5.0, s_ex * 3.0 + 0.55, f".noul = {s_ex:.2f}", size=9, color=C_NOUL, bold=True)
label(30.1, 5, -0.6, "σ(z) = 1 / (1 + e⁻ᶻ)    z ∈ [−6, 6]", size=9, color=MUTED)
comp("3 · Saída e projeção tipada", "3.2c", "3.2 Cabeça Noul",
     "Projeção unária para um único logit z, seguida da sigmoide σ(z) = 1/(1+e^−z). O valor é emitido direto em "
     ".noul ∈ [0,1] e já É a probabilidade calibrada de a asserção ser verdadeira, por isso não há .confidence "
     "separado. A curva roxa é a sigmoide; o ponto marca z = 1.2 → 0.77.", view(30, 5, 1.2, 0.4, -60, 25))

# --- 3.3 CALIBRACAO ---
box(32.2, 33.0, -6.5, 6.5, 0, 3.4, C_CAL, "3.3 Calibração pós-RLCD (Temperature Scaling)",
    "Logits z → z / T (T ajustado por L-BFGS num conjunto de validação).<br>"
    "Treino com <i>proper scoring rules</i>: L = L_CE + α·L_Brier.<br>"
    "Garante P(correto | confiança = p) ≈ p  (ECE ≈ 3,3–3,5% vs 15–35% em LLMs RLHF).", "3 · Saída tipada",
    opacity=0.33, legend_label="Calibração (RLCD)")
label(32.6, 0, 4.0, "z / T", size=13, color=C_CAL, bold=True)
label(32.6, 0, 4.7, "3.3 Calibração RLCD", size=10, color=INK, bold=True)
label(32.6, 0, -0.6, "L = L_CE + α·L_Brier", size=9, color=MUTED)
# mini diagrama de confiabilidade no topo da placa (confiança x acurácia)
cal_x = np.linspace(0, 1, 6)
acc_llm = np.clip(cal_x - 0.25 * cal_x, 0, 1)   # sobreconfiante
line([(32.2 + 0.8 * c, -6.2 + 4.0 * c, 3.5) for c in cal_x], color=INK, width=3, hover="Calibração perfeita: acc = conf")
line([(32.2 + 0.8 * c, -6.2 + 4.0 * c, 3.5 + 2.2 * (a - c)) for c, a in zip(cal_x, acc_llm)], color=C_RED, width=3, dash="dot",
     hover="<b>LLM RLHF</b>: sobreconfiante — a acurácia fica abaixo da confiança declarada")
points([(32.2 + 0.8 * c, -6.2 + 4.0 * c, 3.5 + 2.2 * (a - c)) for c, a in zip(cal_x, acc_llm)], C_RED, 3,
       "<b>LLM RLHF</b>: conf → acc menor (sobreconfiança)")
points([(32.2 + 0.8 * c, -6.2 + 4.0 * c, 3.5 + 0.12 * np.sin(c * 9)) for c in cal_x], C_CAL, 4,
       "<b>Jev</b>: conf ≈ acc (calibrado: P(correto | p) ≈ p)")
label(32.6, -4.2, 4.3, "diagrama de confiabilidade", size=8, color=MUTED)
label(32.6, -4.2, 3.9, "preto = perfeito · dourado = Jev · vermelho = LLM RLHF", size=7, color=MUTED)
for nm, col, yh in heads:
    arrow((31.4, yh, 1.0), (32.2, yh, 1.0), color=col, width=4)
    arrow((33.0, yh, 1.0), (34.4, 0, 1.5), color=col, width=4)
comp("3 · Saída e projeção tipada", "3.3", "3.3 Calibração de probabilidades pós-RLCD",
     "Placa dourada que todas as cabeças atravessam: os logits são divididos por uma temperatura T (ajustada por "
     "L-BFGS em validação), o que reordena nada mas espalha/concentra a distribuição. Durante o treino RLCD a perda "
     "combinou entropia cruzada com o termo quadrático de Brier (proper scoring rules), penalizando confiança "
     "descolada do acerto. Resultado: P(correto | p) ≈ p, ECE ≈ 3,3–3,5%. No topo da placa há um mini diagrama de "
     "confiabilidade comparando Jev (dourado) com um LLM RLHF sobreconfiante (vermelho).",
     view(32.6, 0, 2.0, 0.45, -55, 25))

# --- 3.4 OBJETO TIPADO ---
box(34.4, 36.4, -1.6, 1.6, 0, 3.2, C_OUT, "3.4 Emissão estruturada direta",
    "Sem loop autorregressivo · sem amostragem · sem destokenização.<br>"
    "Objeto estritamente tipado serializado em memória:<br>"
    "{ acao_imediata: {choice:'bloquear', confidence:0.72, probabilities:{…}},<br>"
    "&nbsp;&nbsp;risco_operacional: {score:1.05, probabilities:[…], confidence:…},<br>"
    "&nbsp;&nbsp;bloqueio_urgente: {noul:0.77} }<br>Consumido via SDK (Python, TypeScript, Java, Go).",
    "3 · Saída tipada", legend_label="Objeto tipado (saída)")
label(35.4, 0, 3.9, "Objeto tipado", size=12, color=C_OUT, bold=True)
label(35.4, 0, -0.6, "SDK: Python · TS · Java · Go", size=8, color=MUTED)
label(35.4, 0, 4.5, "70–500 ms · $0,042 / 1M tokens in · saída $0", size=8, color=MUTED)
comp("3 · Saída e projeção tipada", "3.4", "3.4 Emissão estruturada direta",
     "O processo termina aqui, ao fim da única passagem: não há amostragem (greedy/top-p/top-k), não há loop e não "
     "há destokenização. O retorno é montado em memória como objeto estritamente tipado — dicionário com uma entrada "
     "por interrogação, cada uma com os campos da sua primitiva — e consumido via SDK. Latência 70–500 ms; "
     "$0,042 por milhão de tokens de entrada, saída gratuita.", view(35.4, 0, 1.6, 0.35, -50, 25))

# --- lane fantasma: ELIMINADO ---
gy0, gy1 = 10.6, 12.6
ghost = [
    (24.0, 26.6, "LM Head / Unembedding |V|", "Projeção d_model → |V| (dezenas de milhares de tokens).<br><b>Não existe no Jev</b>: só cabeças tipadas restritas (K, L ou 1)."),
    (27.2, 29.8, "Amostragem (greedy · top-p · top-k)", "Escolha estocástica do próximo token sobre o vocabulário.<br><b>Não existe no Jev</b>: nada é amostrado."),
    (30.4, 33.0, "Loop autorregressivo × T", "Um forward pass por token gerado, T vezes (3–30 s).<br><b>Não existe no Jev</b>: termina após 1 passo (70–500 ms)."),
    (33.6, 36.4, "Destokenização", "IDs → caracteres / palavras / JSON a validar.<br><b>Não existe no Jev</b>: a saída já é objeto tipado."),
]
for x0, x1, nm, hv in ghost:
    box(x0, x1, gy0, gy1, 0, 1.6, C_GHOST, f"✕ {nm}", hv, "Eliminado no Jev", opacity=0.35)
    label((x0 + x1) / 2, gy0 + 1.0, 2.1, nm, size=8, color=MUTED)
    line([(x0 + 0.2, gy0 - 0.05, 0.1), (x1 - 0.2, gy0 - 0.05, 1.5)], color=C_RED, width=5)
    line([(x0 + 0.2, gy0 - 0.05, 1.5), (x1 - 0.2, gy0 - 0.05, 0.1)], color=C_RED, width=5)
# arco do loop autorregressivo
th = np.linspace(0, 1.75 * np.pi, 40)
line([(31.7 + 1.0 * np.cos(t_), 11.6 + 0.6 * np.sin(t_), 2.6) for t_ in th], color=C_RED, width=4,
     hover="<b>Loop autorregressivo</b>: y_t ~ P(· | x, y_1..y_{t−1}), repetido T vezes")
label(31.7, 11.6, 3.1, "× T", size=9, color=C_RED, bold=True)
label(30.2, 11.6, 3.9, "PIPELINE DE UM LLM GENERATIVO — ELIMINADO NO JEV", size=11, color=C_RED, bold=True)
line([(24, 10.2, 0), (36.4, 10.2, 0)], color=C_RED, width=2, dash="dot")
comp("✕ O que o Jev elimina", "X", "Pipeline autorregressivo eliminado",
     "Faixa cinza riscada ao fundo da etapa 3, alinhada com o ponto em que um decoder entraria em cada peça: "
     "(1) LM head para vocabulário aberto; (2) amostragem estocástica; (3) loop de T passos, um forward por token; "
     "(4) destokenização e parsing de JSON. É a ausência dessas quatro peças que dá O(1), custo zero de saída e "
     "impossibilidade estrutural de erro de formato.", view(30.2, 11.6, 1.2, 0.55, -95, 35))

# =====================================================================
# BLOCO 1 EXPANDIDO — matrizes reais, passo a passo (regiao oculta; botao "Expandir")
# =====================================================================
_xoff = 0.0
_layer = "exp"

C_W0, C_W1 = "#e9edf3", "#3b4d6b"       # pesos (cinza-azulado)
C_A0, C_A1 = "#e4f3ea", "#1f7a4d"       # ativacoes (verde)
C_S0, C_S1 = "#fbeee8", "#c8552b"       # atencao (laranja)
YW0, YW1 = -13.25, -12.75               # plano da "parede" (y)
YL = -13.6                              # y dos rotulos (um pouco a frente)
P = 0.3
CE = 0.24

Tn, Dm, Dk, Dff, Hh = 14, 12, 6, 16, 2
rngE = np.random.default_rng(7)


def silu(v):
    return v / (1 + np.exp(-v))


def lnorm(M):
    mu = M.mean(axis=1, keepdims=True)
    sd = M.std(axis=1, keepdims=True) + 1e-5
    return (M - mu) / sd


Xin = rngE.normal(0, 1, (Tn, Dm))
Xh = lnorm(Xin)
WQ = rngE.normal(0, 0.35, (Dm, Dk)); WK = rngE.normal(0, 0.35, (Dm, Dk)); WV = rngE.normal(0, 0.35, (Dm, Dk))
WQ2 = rngE.normal(0, 0.35, (Dm, Dk)); WK2 = rngE.normal(0, 0.35, (Dm, Dk)); WV2 = rngE.normal(0, 0.35, (Dm, Dk))
Q, Kmat, V = Xh @ WQ, Xh @ WK, Xh @ WV
S = Q @ Kmat.T / np.sqrt(Dk)
A = np.exp(S - S.max(axis=1, keepdims=True)); A = A / A.sum(axis=1, keepdims=True)
O1 = A @ V
Q2, K2, V2 = Xh @ WQ2, Xh @ WK2, Xh @ WV2
S2 = Q2 @ K2.T / np.sqrt(Dk); A2 = np.exp(S2 - S2.max(axis=1, keepdims=True)); A2 = A2 / A2.sum(axis=1, keepdims=True)
O2 = A2 @ V2
Ocat = np.concatenate([O1, O2], axis=1)          # T x d_model (h*d_k = d_model)
WO = rngE.normal(0, 0.3, (Dm, Dm))
Y = Ocat @ WO
X1 = Xin + Y
Xh1 = lnorm(X1)
Wg = rngE.normal(0, 0.3, (Dm, Dff)); Wu = rngE.normal(0, 0.3, (Dm, Dff)); Wd = rngE.normal(0, 0.25, (Dff, Dm))
G = Xh1 @ Wg; U = Xh1 @ Wu; Hm = silu(G) * U
F = Hm @ Wd
X2 = X1 + F


def norm01(M):
    lo, hi = float(M.min()), float(M.max())
    return (M - lo) / (hi - lo + 1e-9)


MATBOX = {}


def matrix(x0, z0, M, name, c0, c1, cell_hover, group="Bloco 1 expandido", col_color=None):
    """Matriz de frente (plano x-z). Linha 0 no topo. Retorna (x1, z1)."""
    nr, nc = M.shape
    MATBOX[name] = [float(x0), float(x0 + nc * P - (P - CE)), YW0, YW1, float(z0), float(z0 + nr * P - (P - CE))]
    N = norm01(M)
    cells = []
    for r in range(nr):
        for c in range(nc):
            xa = x0 + c * P
            za = z0 + (nr - 1 - r) * P
            col = col_color(r, c, N[r, c]) if col_color else ramp(N[r, c], c0, c1)
            cells.append((xa, xa + CE, YW0, YW1, za, za + CE, col, f"<b>{name}</b>[{r + 1},{c + 1}] = {M[r, c]:+.2f}<br>{cell_hover(r, c)}"))
    cubes(cells, group)
    x1, z1 = x0 + nc * P - (P - CE), z0 + nr * P - (P - CE)
    box(x0 - 0.1, x1 + 0.1, YW0 - 0.05, YW1 + 0.05, z0 - 0.12, z0 - 0.06, "#c9d3e0", name, "base", group, opacity=0.9)
    return x1, z1


def mlabel(x0, x1, z, text, size=9.5, color=INK, bold=True):
    label((x0 + x1) / 2, YL, z, text, size=size, color=color, bold=bold)


def dims(x0, x1, z0, text):
    label((x0 + x1) / 2, YL, z0 - 0.42, text, size=7.5, color=MUTED)


def harrow(x0, x1, z, color=MUTED, hover=None, width=4):
    arrow((x0, -13.0, z), (x1, -13.0, z), color=color, width=width, hover=hover, head=0.28)


tok = frag  # nomes dos 14 tokens (etapa 1)

# ---------------- piso e titulo ----------------
box(4.5, 47.5, -16.0, -10.4, ZE - 0.45, ZE - 0.37, C_TR, "Bloco 1 expandido", "Região de detalhe", "Bloco 1 expandido", opacity=0.10)
label(26.0, -16.6, ZE - 0.4, "BLOCO 1 EXPANDIDO — matrizes reais (T = 14 tokens · d_model = 12 · h = 2 cabeças · d_k = 6 · d_ff = 16)", size=13, color=C_TR, bold=True)
label(26.0, -16.6, ZE + 23.0, "leia da esquerda para a direita e de baixo para cima · passe o mouse em qualquer célula para ver o valor", size=9, color=MUTED)

# ---------------- TIER 1: X → LN → X̂ → W_Q W_K W_V → Q K V ----------------
Z1 = 0.3 + ZE
label(4.8, YL, Z1 + 5.6, "① Normalização + projeções", size=10, color=C_TR, bold=True)
x1, zt = matrix(6.0, Z1, Xin, "X", C_A0, C_A1, lambda r, c: f"entrada do bloco · token {r + 1} '{tok[r]}' · dimensão {c + 1}")
mlabel(6.0, x1, zt + 0.55, "X  (entrada do bloco)")
dims(6.0, x1, Z1, "T × d_model = 14 × 12")
harrow(x1 + 0.15, 11.45, Z1 + 1.8, hover="2.1 Pre-Norm")
label(11.0, YL, Z1 + 2.55, "LN", size=9, color=MUTED, bold=True)
x2, _ = matrix(11.6, Z1, Xh, "X̂", C_A0, C_A1, lambda r, c: f"após Pre-Norm · token {r + 1} '{tok[r]}' · dimensão {c + 1}")
mlabel(11.6, x2, zt + 0.55, "X̂ = (X − μ) / σ · γ + β")
dims(11.6, x2, Z1, "RMSNorm / LayerNorm por token (linha)")
# pesos Q K V
xw = 17.0
for W, nm, sub in [(WQ, "W_Q", "Q"), (WK, "W_K", "K"), (WV, "W_V", "V")]:
    xe, ze = matrix(xw, Z1, W, nm, C_W0, C_W1, lambda r, c, nm=nm: f"peso aprendido · linha = dimensão de entrada {r + 1} · coluna = dim. da cabeça {c + 1}")
    mlabel(xw, xe, ze + 0.55, nm, size=9)
    dims(xw, xe, Z1, "d_model × d_k = 12 × 6")
    xw = xe + 0.55
harrow(x2 + 0.15, 16.85, Z1 + 1.8, hover="X̂ multiplica cada matriz de pesos")
label(16.6, YL, Z1 + 2.55, "×", size=14, color=INK, bold=True)
label((17.0 + xw) / 2, YL, ze + 1.15, "cabeça 1 (de h = 2) · em GQA, W_K e W_V são compartilhados por grupo", size=7.5, color=MUTED)
# Q K V empilhados
xq = xw + 0.5
for M, nm, zo, form in [(V, "V", Z1, "V = X̂ · W_V"), (Kmat, "K", Z1 + 2.25, "K = X̂ · W_K"), (Q, "Q", Z1 + 4.5, "Q = X̂ · W_Q")]:
    xe, ze = matrix(xq, zo, M, nm, C_A0, C_A1, lambda r, c, nm=nm: f"{nm} do token {r + 1} '{tok[r]}' · dim. {c + 1} da cabeça")
    label(xe + 1.05, YL, zo + 0.9, form, size=9, color=INK, bold=True)
    harrow(xw - 0.35, xq - 0.15, zo + 0.9, hover=form, width=3)
dims(xq, xe, Z1, "cada um: T × d_k = 14 × 6")
XQ1 = xe
T1_END = (xq, xe, Z1 + 4.5 + 1.8)

# ---------------- TIER 2: S = QKᵀ/√d_k → A = softmax(S) → O = A·V → concat → W_O → Y ----------------
Z2 = 9.2 + ZE
label(4.8, YL, Z2 + 5.2, "② Atenção bidirecional (sem máscara causal)", size=10, color=C_TR, bold=True)
x1, zt = matrix(6.0, Z2, S, "S", C_S0, C_S1,
                lambda r, c: f"score bruto: query do token {r + 1} '{tok[r]}' × key do token {c + 1} '{tok[c]}'<br>Sem máscara: c &gt; r também é permitido (bidirecional).")
mlabel(6.0, x1, zt + 0.55, "S = Q · Kᵀ / √d_k")
dims(6.0, x1, Z2, "T × T = 14 × 14 · matriz cheia, sem triângulo mascarado")
harrow(x1 + 0.15, 11.45, Z2 + 2.0, hover="softmax por linha (cada query distribui peso 1 entre todas as keys)")
label(11.0, YL, Z2 + 2.75, "softmax", size=8.5, color=MUTED, bold=True)
x2, _ = matrix(11.6, Z2, A, "A", C_S0, C_S1,
               lambda r, c: f"peso de atenção: token {r + 1} '{tok[r]}' atende token {c + 1} '{tok[c]}'<br>linha soma 1,00")
mlabel(11.6, x2, zt + 0.55, "A = softmax(S)  (por linha)")
dims(11.6, x2, Z2, "T × T · cada linha soma 1")
harrow(x2 + 0.15, 17.05, Z2 + 2.0, hover="A · V: média ponderada dos values")
label(16.6, YL, Z2 + 2.75, "· V", size=11, color=INK, bold=True)
x3, z3 = matrix(17.2, Z2, O1, "O₁", C_A0, C_A1, lambda r, c: f"saída da cabeça 1 · token {r + 1} '{tok[r]}' · dim. {c + 1}")
mlabel(17.2, x3, z3 + 0.55, "O₁ = A · V")
dims(17.2, x3, Z2, "T × d_k = 14 × 6")
harrow(x3 + 0.15, 22.65, Z2 + 0.9, hover="concatena as h cabeças")
label(22.3, YL, Z2 + 1.6, "‖", size=13, color=INK, bold=True)
x4, z4 = matrix(22.8, Z2, Ocat, "concat", C_A0, C_A1,
                lambda r, c: f"cabeça {'1' if c < Dk else '2'} · token {r + 1} '{tok[r]}' · dim. {c % Dk + 1}",
                col_color=lambda r, c, v: ramp(v, C_A0, C_A1) if c < Dk else ramp(v, "#ececef", "#6b7c93"))
mlabel(22.8, x4, z4 + 0.55, "concat(O₁ ‖ O₂)")
dims(22.8, x4, Z2, "T × (h·d_k) = 14 × 12 · cinza = cabeça 2")
harrow(x4 + 0.15, 28.25, Z2 + 1.8, hover="× W_O")
label(27.9, YL, Z2 + 2.55, "×", size=14, color=INK, bold=True)
x5, z5 = matrix(28.4, Z2, WO, "W_O", C_W0, C_W1, lambda r, c: f"projeção de saída · linha {r + 1} · coluna {c + 1}")
mlabel(28.4, x5, z5 + 0.55, "W_O", size=9)
dims(28.4, x5, Z2, "d_model × d_model = 12 × 12")
harrow(x5 + 0.15, 33.25, Z2 + 1.8, hover="=")
label(32.9, YL, Z2 + 2.55, "=", size=14, color=INK, bold=True)
x6, z6 = matrix(33.4, Z2, Y, "Y", C_A0, C_A1, lambda r, c: f"saída da atenção · token {r + 1} '{tok[r]}' · dimensão {c + 1}")
mlabel(33.4, x6, z6 + 0.55, "Y = concat(O₁‖O₂) · W_O")
dims(33.4, x6, Z2, "T × d_model = 14 × 12 · segue para o Add")
# ligacao tier1 -> tier2 (Q,K,V subem para S)
arrow((XQ1 - 2.0, -13.0, Z1 + 6.6), (8.0, -13.0, Z2 - 0.3), color=C_TR, width=3, hover="Q e K entram em S = QKᵀ/√d_k; V entra em A·V", head=0.3)

# ---------------- TIER 3: X' = X + Y → LN → FFN (SwiGLU) → X'' ----------------
Z3 = 17.0 + ZE
label(4.8, YL, Z3 + 5.6, "③ Residual + FFN com porta (SwiGLU)", size=10, color=C_TR, bold=True)
x1, zt = matrix(6.0, Z3, X1, "X′", C_A0, C_A1, lambda r, c: f"após o Add: X + Y · token {r + 1} '{tok[r]}' · dimensão {c + 1}")
mlabel(6.0, x1, zt + 0.55, "X′ = X + Y   (2.3 Add)")
dims(6.0, x1, Z3, "T × d_model · residual soma, não substitui")
harrow(x1 + 0.15, 11.45, Z3 + 1.8, hover="2.4 Norm")
label(11.0, YL, Z3 + 2.55, "LN", size=9, color=MUTED, bold=True)
x2, _ = matrix(11.6, Z3, Xh1, "X̂′", C_A0, C_A1, lambda r, c: f"após a 2ª Norm · token {r + 1} '{tok[r]}' · dimensão {c + 1}")
mlabel(11.6, x2, zt + 0.55, "X̂′ = Norm(X′)")
dims(11.6, x2, Z3, "T × d_model")
harrow(x2 + 0.15, 17.05, Z3 + 1.8, hover="× W_gate e × W_up em paralelo")
label(16.6, YL, Z3 + 2.55, "×", size=14, color=INK, bold=True)
x3, z3 = matrix(17.2, Z3, Wg, "W_gate", C_W0, C_W1, lambda r, c: f"ramo da porta · linha {r + 1} · coluna {c + 1}")
mlabel(17.2, x3, z3 + 0.55, "W_gate", size=9)
dims(17.2, x3, Z3, "d_model × d_ff = 12 × 16 (d_ff truncado; real ≈ 4·d_model)")
x4, z4 = matrix(x3 + 0.6, Z3, Wu, "W_up", C_W0, C_W1, lambda r, c: f"ramo de expansão · linha {r + 1} · coluna {c + 1}")
mlabel(x3 + 0.6, x4, z4 + 0.55, "W_up", size=9)
harrow(x4 + 0.15, x4 + 1.35, Z3 + 2.0, hover="H = SiLU(X̂′W_gate) ⊙ (X̂′W_up)")
label(x4 + 0.75, YL, Z3 + 2.75, "⊙", size=13, color=INK, bold=True)
x5, z5 = matrix(x4 + 1.5, Z3, Hm, "H", C_A0, C_A1, lambda r, c: f"ativação oculta · token {r + 1} '{tok[r]}' · neurônio {c + 1} de d_ff")
mlabel(x4 + 1.5, x5, z5 + 0.55, "H = SiLU(X̂′·W_gate) ⊙ (X̂′·W_up)")
dims(x4 + 1.5, x5, Z3, "T × d_ff = 14 × 16")
harrow(x5 + 0.15, x5 + 1.35, Z3 + 2.0, hover="× W_down")
label(x5 + 0.75, YL, Z3 + 2.75, "×", size=14, color=INK, bold=True)
x6, z6 = matrix(x5 + 1.5, Z3, Wd, "W_down", C_W0, C_W1, lambda r, c: f"projeção de volta · linha {r + 1} · coluna {c + 1}")
mlabel(x5 + 1.5, x6, z6 + 0.55, "W_down", size=9)
dims(x5 + 1.5, x6, Z3, "d_ff × d_model = 16 × 12")
harrow(x6 + 0.15, x6 + 1.35, Z3 + 1.8, hover="F = H·W_down ; X″ = X′ + F")
label(x6 + 0.75, YL, Z3 + 2.55, "+X′", size=9, color=INK, bold=True)
x7, z7 = matrix(x6 + 1.5, Z3, X2, "X″", C_A0, C_A1, lambda r, c: f"saída do bloco · token {r + 1} '{tok[r]}' · dimensão {c + 1}<br>Entra no Bloco 2 (ou na Norm final, se for o bloco N).")
mlabel(x6 + 1.5, x7, z7 + 0.55, "X″ = X′ + H·W_down   (2.6 Add)")
dims(x6 + 1.5, x7, Z3, "T × d_model → próximo bloco")
# ligacao tier2 -> tier3
arrow((x6 - 6.0, -13.0, Z2 + 4.3), (8.0, -13.0, Z3 - 0.3), color=C_TR, width=3, hover="Y soma-se a X (residual) e segue para a FFN", head=0.3)

_layer = "main"

# cameras da regiao expandida
CAM_EXP_ALL = view(26.0, -13.0, 11.0 + ZE, 1.45, -90, 3)
CAM_T1 = view(17.0, -13.0, 3.5 + ZE, 0.60, -90, 2)
CAM_T2 = view(21.0, -13.0, 11.6 + ZE, 0.60, -90, 2)
CAM_T3 = view(24.0, -13.0, 19.5 + ZE, 0.60, -90, 2)
CAM_ATT = view(11.0, -13.0, 11.6 + ZE, 0.43, -90, 2)

def _mcam(names, dist=0.36, el=3):
    bs = [MATBOX[n] for n in names]
    cx_ = (min(b[0] for b in bs) + max(b[1] for b in bs)) / 2
    cz_ = (min(b[4] for b in bs) + max(b[5] for b in bs)) / 2
    return view(cx_, -13.0, cz_, dist, -90, el)


EST = "🔍 Bloco 1 expandido — um card por matriz"
JEVN = " <b>No Jev:</b> "
comp(EST, "E0", "Visão completa do bloco expandido",
     "Três fileiras, lidas da esquerda para a direita e de baixo para cima: ① normalização e projeções Q/K/V; ② atenção "
     "bidirecional (scores, softmax, A·V, concat, W_O); ③ residual e FFN com porta. Todos os números são calculados de "
     "verdade (numpy) para os T = 14 tokens da etapa 1, d_model = 12, h = 2 cabeças, d_k = 6, d_ff = 16. Verde = ativações "
     "(dependem da entrada), cinza-azul = pesos aprendidos (fixos após o treino), laranja = matrizes de atenção. Passe o mouse "
     "em qualquer célula para ver o valor; <b>clique numa matriz da cena para abrir o card dela aqui</b>.", CAM_EXP_ALL, exp=True)

# ---- fileira ① ----
comp(EST, "E-X", "① X — entrada do bloco",
     "Matriz T × d_model = 14 × 12. Cada linha é um token (os 14 da etapa 1, incluindo os dos critérios das perguntas) e cada "
     "coluna uma dimensão do vetor latente. No Bloco 1, X é a saída da etapa 1 (E[ids] ⊕ pos); nos blocos seguintes é a saída do "
     "bloco anterior. É também o que corre pelo 'fluxo residual' (tubo lateral dos blocos na cena principal)." + JEVN +
     "nada aqui distingue 'contexto' de 'pergunta' — state e critérios são apenas linhas da mesma matriz, e é isso que permite "
     "processá-los juntos, num único passo.", _mcam(["X"], 0.3), exp=True,
     formula="X ∈ ℝ<sup>T × d<sub>model</sub></sup> · linha t = vetor do token t · ativação (verde)")
comp(EST, "E-Xh", "① X̂ — saída da Pre-Norm (2.1)",
     "Matriz T × d_model. Cada linha (token) de X foi normalizada para média 0 e desvio 1 e reescalada com γ e β aprendidos; a "
     "variante RMSNorm dispensa a média e divide pela raiz da média dos quadrados. Isso estabiliza a escala do que entra na atenção: "
     "sem a normalização, tokens com vetores 'grandes' dominariam os scores. Aplicada antes da subcamada (pre-norm), deixa o fluxo "
     "residual intacto. Compare com X: o padrão de cores é parecido, mas os contrastes ficam uniformes linha a linha.",
     _mcam(["X̂"], 0.3), exp=True, formula="X̂ = (X − μ) / σ · γ + β &nbsp;·&nbsp; RMSNorm: X̂ = X / √(mean(X²) + ε) · γ")
comp(EST, "E-WQ", "① W_Q — pesos da projeção Query",
     "Matriz d_model × d_k = 12 × 6 de pesos aprendidos (cinza-azul), fixa após o treino. Aplicada a cada linha de X̂, produz a "
     "<i>query</i> do token: 'o que este token procura nos outros'. Há uma W_Q por cabeça (h = 2; aqui a da cabeça 1). Repare "
     "que a mesma matriz serve para todos os tokens — o que muda de uma chamada para outra é X, nunca W.",
     _mcam(["W_Q"], 0.26), exp=True, formula="Q = X̂ · W<sub>Q</sub>, &nbsp; W<sub>Q</sub> ∈ ℝ<sup>d<sub>model</sub> × d<sub>k</sub></sup>")
comp(EST, "E-WK", "① W_K — pesos da projeção Key",
     "Matriz d_model × d_k de pesos aprendidos. Produz a <i>key</i> de cada token: 'o que este token oferece para ser encontrado'. "
     "O produto escalar query·key é o que decide quem atende quem. Em GQA (Grouped-Query Attention), várias cabeças compartilham "
     "a mesma W_K, economizando memória de KV." + JEVN + "as keys dos tokens do state podem ser consultadas pelos tokens dos "
     "critérios (e vice-versa), porque não há máscara causal.",
     _mcam(["W_K"], 0.26), exp=True, formula="K = X̂ · W<sub>K</sub>, &nbsp; W<sub>K</sub> ∈ ℝ<sup>d<sub>model</sub> × d<sub>k</sub></sup>")
comp(EST, "E-WV", "① W_V — pesos da projeção Value",
     "Matriz d_model × d_k de pesos aprendidos. Produz o <i>value</i> de cada token: o conteúdo que ele entrega quando é atendido. "
     "Ao contrário de Q e K, os values não recebem rotação posicional (RoPE): carregam só conteúdo. Também compartilhada por grupo "
     "em GQA.", _mcam(["W_V"], 0.26), exp=True,
     formula="V = X̂ · W<sub>V</sub>, &nbsp; W<sub>V</sub> ∈ ℝ<sup>d<sub>model</sub> × d<sub>k</sub></sup>")
comp(EST, "E-Q", "① Q — queries (T × d_k)",
     "Matriz 14 × 6 (a de cima na pilha). Cada linha é a consulta do token t, um vetor curto de d_k = 6 dimensões. Em modelos com "
     "RoPE, é aqui que a posição entra: o vetor é girado por um ângulo proporcional a t, de modo que q_i·k_j passe a depender da "
     "distância relativa i − j. A linha do token 'bloq' (critério) pergunta, em essência, 'quais tokens do contexto me dizem se devo "
     "bloquear?'.", _mcam(["Q"], 0.3), exp=True, formula="Q = X̂ · W<sub>Q</sub> ∈ ℝ<sup>T × d<sub>k</sub></sup> &nbsp;·&nbsp; q<sub>i</sub> = linha i")
comp(EST, "E-K", "① K — keys (T × d_k)",
     "Matriz 14 × 6 (a do meio). Cada linha é a chave do token t, também rotacionada pelo RoPE. Q·Kᵀ compara cada consulta com "
     "cada chave e gera os scores S. Um token com key 'parecida' com a query de outro será muito atendido por ele.",
     _mcam(["K"], 0.3), exp=True, formula="K = X̂ · W<sub>K</sub> ∈ ℝ<sup>T × d<sub>k</sub></sup> &nbsp;·&nbsp; S = Q·Kᵀ/√d<sub>k</sub>")
comp(EST, "E-V", "① V — values (T × d_k)",
     "Matriz 14 × 6 (a de baixo). Cada linha é o conteúdo que o token t entrega. Não recebe posição. Na fileira ② esses vetores são "
     "misturados pelos pesos de atenção: a saída de cada token é uma média ponderada das linhas de V.",
     _mcam(["V"], 0.3), exp=True, formula="V = X̂ · W<sub>V</sub> ∈ ℝ<sup>T × d<sub>k</sub></sup> &nbsp;·&nbsp; O = A·V")

# ---- fileira ② ----
comp(EST, "E-S", "② S = QKᵀ/√d_k — scores de atenção",
     "Matriz T × T = 14 × 14 (laranja). A célula [i, j] é o produto escalar entre a query do token i e a key do token j, dividido "
     "por √d_k para manter a variância estável (sem isso o softmax saturaria). É AQUI que mora a diferença central do Jev: num "
     "decoder, as células com j &gt; i recebem −∞ (máscara causal) e o modelo só enxerga o passado; no Jev a matriz é cheia — o "
     "token de um critério compara-se com qualquer token do state e vice-versa. Por isso a decisão inteira cabe em um passo.",
     _mcam(["S"], 0.3), exp=True, formula="S<sub>ij</sub> = (q<sub>i</sub> · k<sub>j</sub>) / √d<sub>k</sub> &nbsp;·&nbsp; sem máscara: definido para todo (i, j)")
comp(EST, "E-A", "② A = softmax(S) — pesos de atenção",
     "Matriz T × T. O softmax transforma cada linha de S numa distribuição de probabilidade (cada linha soma 1). A linha i diz quanto "
     "o token i 'olha' para cada um dos outros tokens. Passe o mouse: 'token i atende token j'. Linhas concentradas (uma célula "
     "escura) significam foco; linhas espalhadas significam contexto difuso. É a única não-linearidade da atenção.",
     _mcam(["A"], 0.3), exp=True, formula="A<sub>ij</sub> = e<sup>S<sub>ij</sub></sup> / Σ<sub>j′</sub> e<sup>S<sub>ij′</sub></sup> &nbsp;·&nbsp; Σ<sub>j</sub> A<sub>ij</sub> = 1")
comp(EST, "E-O1", "② O₁ = A·V — saída da cabeça 1",
     "Matriz T × d_k = 14 × 6. Média ponderada dos values: cada token recebe uma mistura dos vetores V dos tokens que ele atende, com "
     "os pesos da sua linha em A. Este é o único lugar do bloco em que informação viaja entre posições — todo o resto (Norm, FFN) "
     "trata cada token isoladamente." + JEVN + "é aqui que o critério 'bloquear' absorve evidências de 'ip divergente' e '12500'.",
     _mcam(["O₁"], 0.3), exp=True, formula="O<sub>h</sub> = A<sub>h</sub> · V<sub>h</sub> ∈ ℝ<sup>T × d<sub>k</sub></sup>")
comp(EST, "E-concat", "② concat(O₁ ‖ O₂) — junção das cabeças",
     "Matriz T × (h·d_k) = 14 × 12. As h cabeças são calculadas em paralelo, cada uma com seus próprios W_Q/W_K/W_V, e podem "
     "capturar relações diferentes (uma olha sintaxe, outra olha valores numéricos, etc.). Suas saídas são coladas lado a lado: "
     "h·d_k = d_model. A cabeça 2 aparece em cinza para distinguir os dois blocos de colunas.", _mcam(["concat"], 0.3), exp=True,
     formula="concat(O<sub>1</sub> ‖ … ‖ O<sub>h</sub>) ∈ ℝ<sup>T × d<sub>model</sub></sup>")
comp(EST, "E-WO", "② W_O — projeção de saída da atenção",
     "Matriz d_model × d_model = 12 × 12 de pesos aprendidos. Mistura as informações das h cabeças (que até aqui viviam em colunas "
     "separadas) e devolve o resultado ao espaço do modelo. Sem W_O, as cabeças nunca 'conversariam' entre si.",
     _mcam(["W_O"], 0.3), exp=True, formula="Y = concat(O<sub>1</sub> ‖ … ‖ O<sub>h</sub>) · W<sub>O</sub>, &nbsp; W<sub>O</sub> ∈ ℝ<sup>d<sub>model</sub> × d<sub>model</sub></sup>")
comp(EST, "E-Y", "② Y — saída da subcamada de atenção",
     "Matriz T × d_model. É a contribuição da atenção: um 'delta' por token, pronto para ser somado ao fluxo residual (X′ = X + Y). "
     "Leia Y como 'o que a atenção acrescentou a cada token depois de olhar para os demais'.", _mcam(["Y"], 0.3), exp=True,
     formula="Y = Attn(X̂) ∈ ℝ<sup>T × d<sub>model</sub></sup>")

# ---- fileira ③ ----
comp(EST, "E-X1", "③ X′ = X + Y — primeira ligação residual (2.3)",
     "Matriz T × d_model. Soma, não substitui: X passa intacta e Y adiciona correções. É a 'corrente residual' (o tubo lateral nos "
     "blocos da cena principal). Graças a ela é possível empilhar N blocos sem que o gradiente desapareça no treino, e cada bloco só "
     "precisa aprender o que acrescentar.", _mcam(["X′"], 0.3), exp=True, formula="X′ = X + Attn(X̂)")
comp(EST, "E-Xh1", "③ X̂′ — saída da segunda Norm (2.4)",
     "Matriz T × d_model. Segunda normalização, idêntica à primeira em forma, aplicada ao resultado do residual para preparar a "
     "entrada da rede densa (FFN). Novamente pre-norm: o fluxo residual X′ segue sem ser normalizado.", _mcam(["X̂′"], 0.3), exp=True,
     formula="X̂′ = Norm(X′)")
comp(EST, "E-Wg", "③ W_gate — pesos do ramo de porta (2.5)",
     "Matriz d_model × d_ff = 12 × 16 de pesos aprendidos (d_ff aqui truncado; na prática ≈ 4·d_model). Produz o sinal da porta, "
     "G = X̂′·W_gate: 'quanto abrir' cada um dos d_ff neurônios para cada token. Junto com W_up e W_down concentra a maior parte dos "
     "parâmetros de um bloco Transformer.", _mcam(["W_gate"], 0.32), exp=True,
     formula="G = X̂′ · W<sub>gate</sub>, &nbsp; W<sub>gate</sub> ∈ ℝ<sup>d<sub>model</sub> × d<sub>ff</sub></sup>")
comp(EST, "E-Wu", "③ W_up — pesos do ramo de conteúdo (2.5)",
     "Matriz d_model × d_ff de pesos aprendidos. Produz U = X̂′·W_up: o conteúdo candidato que a porta deixa (ou não) passar. Os dois "
     "ramos são calculados em paralelo a partir da mesma entrada X̂′.", _mcam(["W_up"], 0.32), exp=True,
     formula="U = X̂′ · W<sub>up</sub>, &nbsp; W<sub>up</sub> ∈ ℝ<sup>d<sub>model</sub> × d<sub>ff</sub></sup>")
comp(EST, "E-H", "③ H = SiLU(G) ⊙ U — ativação com porta (SwiGLU)",
     "Matriz T × d_ff = 14 × 16. A porta multiplicativa: SiLU(g) = g·σ(g) modula o ramo U elemento a elemento (⊙). Neurônios com g "
     "negativo ficam quase fechados; positivos deixam passar. A FFN é onde vive boa parte do 'conhecimento' do modelo (funciona como "
     "memória associativa chave→valor). Cada token é processado sozinho: aqui não há comunicação entre posições.",
     _mcam(["H"], 0.32), exp=True, formula="H = SiLU(G) ⊙ U &nbsp;·&nbsp; SiLU(g) = g · σ(g)")
comp(EST, "E-Wd", "③ W_down — projeção de volta a d_model",
     "Matriz d_ff × d_model = 16 × 12 de pesos aprendidos. Comprime a ativação oculta H de volta para a dimensão do modelo, "
     "produzindo F = H·W_down, o 'delta' da FFN para cada token.", _mcam(["W_down"], 0.32), exp=True,
     formula="F = H · W<sub>down</sub>, &nbsp; W<sub>down</sub> ∈ ℝ<sup>d<sub>ff</sub> × d<sub>model</sub></sup>")
comp(EST, "E-X2", "③ X″ = X′ + F — saída do bloco (2.6)",
     "Matriz T × d_model. O segundo residual fecha o bloco: X″ é a entrada do Bloco 2. Depois de N blocos, a matriz final passa pela "
     "normalização final e pelo pooling por interrogação, e cada vetor de pergunta vai para sua cabeça tipada (Choice, Score ou Noul)."
     + JEVN + "não existe, em nenhum ponto, um passo de 'gerar o próximo token' — a matriz inteira segue adiante de uma vez.",
     _mcam(["X″"], 0.3), exp=True, formula="X″ = X′ + H · W<sub>down</sub> &nbsp;·&nbsp; → Bloco 2 … Bloco N → Norm final → pooling → cabeças")

# ---- mapa: texto de hover (cena) -> card do painel ----
def _rx(name):
    return "^<b>" + re.escape(name) + "</b>\\["
CARD_MAP = [
    (_rx("X"), "E-X"), (_rx("X̂"), "E-Xh"), (_rx("W_Q"), "E-WQ"), (_rx("W_K"), "E-WK"), (_rx("W_V"), "E-WV"),
    (_rx("Q"), "E-Q"), (_rx("K"), "E-K"), (_rx("V"), "E-V"), (_rx("S"), "E-S"), (_rx("A"), "E-A"), (_rx("O₁"), "E-O1"),
    (_rx("concat"), "E-concat"), (_rx("W_O"), "E-WO"), (_rx("Y"), "E-Y"), (_rx("X′"), "E-X1"), (_rx("X̂′"), "E-Xh1"),
    (_rx("W_gate"), "E-Wg"), (_rx("W_up"), "E-Wu"), (_rx("H"), "E-H"), (_rx("W_down"), "E-Wd"), (_rx("X″"), "E-X2"),
    (r"^<b>Bloco 1 expandido</b>", "E0"),
    (r"1\.1 state", "1.1a"), (r"1\.1 Interrogação|criteria (Choice|Score|Noul)", "1.1b"), (r"1\.2 ", "1.2"),
    (r"1\.3 ", "1.3"), (r"1\.4 ", "1.4"), (r"Saída da etapa 1", "1.5"),
    (r"2\.1 Pre-Norm", "2.1"), (r"2\.2 ", "2.2"), (r"2\.3 Add", "2.3"), (r"2\.4 Norm", "2.4"), (r"2\.5 FFN", "2.5"),
    (r"2\.6 Add", "2.6"), (r"Fluxo residual|Residual [12]", "2.R"), (r"máscara causal|bidirecional densa", "2.M"),
    (r"3\.1 Normalização", "3.1a"), (r"[Pp]ooling|Vetor latente pooled", "3.1b"),
    (r"Cabeça Choice|Softmax · opção|argmax", "3.2a"), (r"Cabeça Score|Nível \d|\.score", "3.2b"),
    (r"Cabeça Noul|Sigmoide|\.noul", "3.2c"), (r"3\.3 |Calibração perfeita|LLM RLHF|calibrado", "3.3"),
    (r"3\.4 ", "3.4"), (r"^<b>✕|Loop autorregressivo", "X"),
]

# ---------- formulas por componente (painel) ----------
FORMULAS = {
 "1.1a": "state ⊂ tokens; |state| + max<sub>m</sub>|q<sub>m</sub>| ≤ 32k",
 "1.1b": "𝒬 = {(tipo<sub>m</sub>, instr<sub>m</sub>, crit<sub>m</sub>)}<sub>m=1..M</sub>, tipo ∈ {Choice, Score, Noul}",
 "1.2": "ids = tokenize(state ⊕ q<sub>1</sub> ⊕ … ⊕ q<sub>M</sub>) ∈ ℕ<sup>T</sup>, T ≤ 64k",
 "1.3": "x<sub>t</sub> = E[id<sub>t</sub>], E ∈ ℝ<sup>|V| × d<sub>model</sub></sup>",
 "1.4": "RoPE: (x<sub>2i</sub>, x<sub>2i+1</sub>) girado por θ = t·ω<sub>i</sub>, ω<sub>i</sub> = 10000<sup>−2i/d</sup>",
 "1.5": "X = E[ids] ⊕ pos ∈ ℝ<sup>T × d<sub>model</sub></sup>",
 "2.1": "X̂ = RMSNorm(X) = X / √(mean(X²) + ε) · γ",
 "2.2": "Attn(Q,K,V) = softmax(QKᵀ/√d<sub>k</sub>)·V (sem máscara) · Y = concat(cabeças)·W<sub>O</sub>",
 "2.3": "X′ = X + Attn(X̂)",
 "2.4": "X̂′ = Norm(X′)",
 "2.5": "FFN(x) = (SiLU(x·W<sub>gate</sub>) ⊙ x·W<sub>up</sub>)·W<sub>down</sub>",
 "2.6": "X″ = X′ + FFN(X̂′)",
 "2.R": "x<sub>ℓ+1</sub> = x<sub>ℓ</sub> + f<sub>ℓ</sub>(Norm(x<sub>ℓ</sub>))",
 "2.M": "S<sub>ij</sub> = q<sub>i</sub>·k<sub>j</sub>/√d<sub>k</sub> para todo (i, j) — decoder: só j ≤ i",
 "3.1a": "H = Norm(X<sup>(N)</sup>) ∈ ℝ<sup>T × d<sub>model</sub></sup>",
 "3.1b": "h<sub>m</sub> = H[pos(q<sub>m</sub>)] ∈ ℝ<sup>d<sub>model</sub></sup>, m = 1..M",
 "3.2a": "z = W<sub>c</sub>h<sub>m</sub> ∈ ℝ<sup>K</sup> · p = softmax(z/T) · choice = argmax<sub>k</sub> p<sub>k</sub> · confidence = max<sub>k</sub> p<sub>k</sub>",
 "3.2b": "p = softmax(z/T) ∈ ℝ<sup>L</sup> · score = Σ<sub>i</sub> p<sub>i</sub>·i (centroide, contínuo)",
 "3.2c": "noul = σ(z/T) = 1 / (1 + e<sup>−z/T</sup>)",
 "3.3": "p<sub>k</sub> = e<sup>z<sub>k</sub>/T</sup> / Σ<sub>j</sub> e<sup>z<sub>j</sub>/T</sup> · ℒ = ℒ<sub>CE</sub> + α·ℒ<sub>Brier</sub>, ℒ<sub>Brier</sub> = (1/K)Σ<sub>k</sub>(p<sub>k</sub> − y<sub>k</sub>)² · ECE = Σ<sub>m</sub> |B<sub>m</sub>|/N · |acc(B<sub>m</sub>) − conf(B<sub>m</sub>)|",
 "3.4": "out = {q<sub>m</sub> ↦ typed(p<sub>m</sub>)}<sub>m=1..M</sub> — 1 forward, custo O(1) em passos",
 "X": "LLM: y<sub>t</sub> ~ P(·| x, y<sub>&lt;t</sub>), t = 1..T (T forwards) · Jev: 1 forward",
}
for c_ in components:
    if c_.get("formula") is None and c_["id"] in FORMULAS:
        c_["formula"] = FORMULAS[c_["id"]]

# =====================================================================
# EXPORTACAO (Three.js)
# =====================================================================
_xoff = XOFF2   # cameras dos botoes usam coordenadas locais das etapas 2/3
CAM_B1 = view(11.3, 0.0, 3.0, 0.5, -80, 12)     # close-up do Bloco 1 (inicio da animacao)
views = [
    ("Visão geral", view(25.5 - XOFF2, 1.5, 3.0, 1.3, -82, 28)),
    ("1 · Entrada", view(11.4 - XOFF2, 0.0, 1.6, 0.6, -88, 14)),
    ("2 · Blocos", view(15.8, 0.0, 3.0, 0.62, -70, 18)),
    ("2 · Máscara", view(15.8, 0.0, 9.0, 0.55, -90, 75)),
    ("3 · Cabeças", view(29.5, 0.0, 1.5, 0.7, -55, 28)),
    ("3 · Calibração + saída", view(34.0, 0.0, 1.8, 0.55, -45, 28)),
    ("✕ Eliminado", view(30.2, 11.6, 1.2, 0.55, -95, 35)),
    ("Topo", view(25.5 - XOFF2, 2.0, 3.5, 1.5, -90, 89)),
]

# fantasmas da animacao: caixa de origem no Bloco 1 (coords absolutas) -> matriz destino
B1 = 10.5 + XOFF2
def _sb(y0, y1, z0, z1):
    return [B1, B1 + 1.6, y0, y1, z0, z1]
GH_DEF = [
    ("X",      [B1 + 1.75, B1 + 2.05, -0.2, 0.2, 0.0, 5.8], C_RES,  "#5aa77f"),
    ("X̂",     _sb(-2, 2, 0.0, 0.5),        C_TR3,  "#5aa77f"),
    ("W_Q",    _sb(-2.0, -0.75, 0.6, 1.15), C_TRQ,  "#6b7a94"),
    ("W_K",    _sb(-0.6, 0.6, 0.6, 1.15),   C_TRK,  "#6b7a94"),
    ("W_V",    _sb(0.75, 2.0, 0.6, 1.15),   C_TRV,  "#6b7a94"),
    ("Q",      _sb(-2.0, -0.75, 0.6, 1.15), C_TRQ,  "#5aa77f"),
    ("K",      _sb(-0.6, 0.6, 0.6, 1.15),   C_TRK,  "#5aa77f"),
    ("V",      _sb(0.75, 2.0, 0.6, 1.15),   C_TRV,  "#5aa77f"),
    ("S",      _sb(-2, 2, 1.25, 1.85),      C_TR,   "#d98b6a"),
    ("A",      _sb(-2, 2, 1.25, 1.85),      C_TR,   "#e8b9a4"),
    ("O₁",     _sb(-2, 2, 1.25, 1.85),      C_TR,   "#5aa77f"),
    ("concat", _sb(-2, 2, 1.25, 1.85),      C_TR,   "#7fa9a0"),
    ("W_O",    _sb(-2, 2, 1.95, 2.35),      C_TRO,  "#6b7a94"),
    ("Y",      _sb(-2, 2, 1.95, 2.35),      C_TRO,  "#5aa77f"),
    ("X′",     _sb(-2, 2, 2.45, 2.85),      C_TR4,  "#5aa77f"),
    ("X̂′",    _sb(-2, 2, 2.95, 3.45),      C_TR3,  "#5aa77f"),
    ("W_gate", _sb(-2.0, -0.1, 3.55, 4.25), C_TR2b, "#6b7a94"),
    ("W_up",   _sb(0.1, 2.0, 3.55, 4.25),   C_TR2b, "#6b7a94"),
    ("H",      _sb(-2, 2, 4.35, 4.7),       C_TR2,  "#5aa77f"),
    ("W_down", _sb(-2, 2, 4.8, 5.3),        C_TR2,  "#6b7a94"),
    ("X″",     _sb(-2, 2, 5.4, 5.8),        C_TR4,  "#5aa77f"),
]

# ---------- "respiro": afasta um pouco os componentes em x (posicoes, nao tamanhos) ----------
KX, X0S = 1.15, 25.5


def spx(x):
    return X0S + (x - X0S) * KX


def sp_pt(p):
    return [spx(p[0]), p[1], p[2]]


def sp_box(b):
    cx_ = (b[0] + b[1]) / 2
    d = spx(cx_) - cx_
    return [b[0] + d, b[1] + d, b[2], b[3], b[4], b[5]]


def sp_view(v):
    return dict(tg=sp_pt(v["tg"]), d=v["d"] * (1 + (KX - 1) * 0.5), az=v["az"], el=v["el"])


def sp_prim(p):
    p = dict(p)
    if p["t"] == "box":
        p["b"] = sp_box(p["b"])
    elif p["t"] == "cubes":
        cells = p["cells"]
        cx_ = (min(c[0] for c in cells) + max(c[1] for c in cells)) / 2
        d = spx(cx_) - cx_
        p["cells"] = [[c[0] + d, c[1] + d, c[2], c[3], c[4], c[5], c[6], c[7]] for c in cells]
    elif p["t"] == "label":
        p["p"] = sp_pt(p["p"])
    elif p["t"] in ("line", "points"):
        p["pts"] = [sp_pt(q) for q in p["pts"]]
    elif p["t"] == "arrow":
        p["p0"], p["p1"] = sp_pt(p["p0"]), sp_pt(p["p1"])
    elif p["t"] == "heat":
        cx_ = (p["x0"] + p["x1"]) / 2
        d = spx(cx_) - cx_
        p["x0"], p["x1"] = p["x0"] + d, p["x1"] + d
    return p


prims = [sp_prim(p) for p in PRIMS]
for c_ in components:
    c_["cam"] = sp_view(c_["cam"])
views = [(n, sp_view(v)) for n, v in views]
cams = dict(b1=sp_view(CAM_B1), exp=sp_view(CAM_EXP_ALL), blocks=views[2][1])
ghosts = [dict(name=nm_, src=sp_box(src_), dst=sp_box(MATBOX[nm_]), c0=c0_, c1=c1_) for nm_, src_, c0_, c1_ in GH_DEF]

# limites reais da cena (para luz/sombra e chao)
xs_, ys_, zs_ = [], [], []
for p in prims:
    if p["t"] == "box":
        xs_ += p["b"][0:2]; ys_ += p["b"][2:4]; zs_ += p["b"][4:6]
    elif p["t"] == "cubes":
        for c in p["cells"]:
            xs_ += c[0:2]; ys_ += c[2:4]; zs_ += c[4:6]
    elif p["t"] == "label":
        xs_.append(p["p"][0]); ys_.append(p["p"][1]); zs_.append(p["p"][2])
    elif p["t"] in ("line", "points"):
        for q in p["pts"]:
            xs_.append(q[0]); ys_.append(q[1]); zs_.append(q[2])
    elif p["t"] == "arrow":
        for q in (p["p0"], p["p1"]):
            xs_.append(q[0]); ys_.append(q[1]); zs_.append(q[2])
    elif p["t"] == "heat":
        xs_ += [p["x0"], p["x1"]]; ys_ += [p["y0"], p["y1"]]; zs_.append(p["z"])
bounds = dict(xmin=min(xs_), xmax=max(xs_), ymin=min(ys_), ymax=max(ys_), zmin=min(zs_), zmax=max(zs_))

SCENE = dict(bounds=bounds, prims=prims, groups=[[g, c] for g, c in GROUPS], views=views, cams=cams, ghosts=ghosts,
             cardmap=[[p_, c_] for p_, c_ in CARD_MAP])


def _js(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


# ---------- painel lateral ----------
stages = []
for c in components:
    if c["stage"] not in stages:
        stages.append(c["stage"])
panel = []
for st in stages:
    panel.append(f'<h3>{st}</h3>')
    for c in [c for c in components if c["stage"] == st]:
        f_ = f'<div class="f">{c["formula"]}</div>' if c.get("formula") else ""
        m_ = MORE.get(c["id"])
        more_ = (f'<button class="more-btn" aria-expanded="false">Saber mais ▾</button><div class="more" hidden>{m_}</div>' if m_ else "")
        panel.append(
            f'<div class="item" id="card-{c["id"]}" data-cam=\'{json.dumps(c["cam"])}\' data-exp="{1 if c.get("exp") else 0}">'
            f'<div class="t">{c["title"]}</div><div class="d">{c["desc"]}</div>{f_}'
            f'<div class="btns"><button class="focus">Focar na cena →</button>{more_}</div></div>')
panel_html = "\n".join(panel)
_faltam = [c["id"] for c in components if c["id"] not in MORE]
if _faltam:
    print("AVISO: cards sem Saber mais:", _faltam)
views_html = "".join(f'<button class="viewbtn" data-view=\'{json.dumps(v)}\'>{n}</button>' for n, v in views)
views_html += '<button class="do-expand accent">🔍 Expandir Bloco 1</button><button class="do-collapse">⤡ Recolher</button>'
legend_html = "".join(f'<div class="lg" data-g="{g}" title="clique para ocultar/mostrar"><span class="sw" style="background:{c}"></span>{g}</div>' for g, c in GROUPS)

HERE = os.path.dirname(os.path.abspath(__file__))
def _read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()
THREE_JS = _read(os.path.join(HERE, "lib", "three.min.js"))
ORBIT_JS = _read(os.path.join(HERE, "lib", "OrbitControls.js"))
VIEWER_JS = _read(os.path.join(HERE, "viewer.js"))

page = _read(os.path.join(HERE, "page_template.html"))
page = (page.replace("__PANEL__", panel_html).replace("__VIEWS__", views_html).replace("__LEGEND__", legend_html)
        .replace("__SCENE_JSON__", _js(SCENE)).replace("__THREE_JS__", THREE_JS).replace("__ORBIT_JS__", ORBIT_JS)
        .replace("__VIEWER_JS__", VIEWER_JS)
        .replace("__C_IN__", C_IN).replace("__C_TR__", C_TR).replace("__C_TR2__", C_TR2).replace("__C_TR3__", C_TR3)
        .replace("__C_TR4__", C_TR4).replace("__C_CHOICE__", C_CHOICE).replace("__C_SCORE__", C_SCORE).replace("__C_NOUL__", C_NOUL)
        .replace("__C_CAL__", C_CAL).replace("__C_OUT__", C_OUT).replace("__C_GHOST__", C_GHOST).replace("__INK__", INK).replace("__MUTED__", MUTED))

out = sys.argv[1] if len(sys.argv) > 1 else r"D:\6. Trabalho\5. Afya\1. codigo\_hub_dev\Arquitetura_Jev_3D.html"
with open(out, "w", encoding="utf-8") as f:
    f.write(page)
print("ok", out, len(prims), "primitivas", len(components), "componentes", f"{len(page)/1e6:.1f} MB")
