# -*- coding: utf-8 -*-
"""Cena 3D interativa e detalhada da arquitetura do Jev (TypeSafe AI / System One Model)
com painel lateral de estudo. Gera um único HTML autocontido."""
import json
import numpy as np
import plotly.graph_objects as go

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

traces = []
_legend_seen = set()
_xoff = 0.0   # deslocamento em x aplicado por todos os helpers (muda apos a etapa 1)
components = []   # para o painel lateral: (etapa, id, titulo, descricao, camera)


def box(x0, x1, y0, y1, z0, z1, color, name, hover, group, opacity=1.0, legend_label=None):
    x0, x1 = x0 + _xoff, x1 + _xoff
    xs = [x0, x1, x1, x0, x0, x1, x1, x0]
    ys = [y0, y0, y1, y1, y0, y0, y1, y1]
    zs = [z0, z0, z0, z0, z1, z1, z1, z1]
    i = [0, 0, 4, 4, 0, 0, 1, 1, 2, 2, 3, 3]
    j = [1, 2, 5, 6, 1, 5, 2, 6, 3, 7, 0, 4]
    k = [2, 3, 6, 7, 5, 4, 6, 5, 7, 6, 4, 7]
    lname = legend_label or group
    show = lname not in _legend_seen
    _legend_seen.add(lname)
    traces.append(go.Mesh3d(
        x=xs, y=ys, z=zs, i=i, j=j, k=k,
        color=color, opacity=opacity, flatshading=True,
        lighting=dict(ambient=0.6, diffuse=0.65, specular=0.12, roughness=0.9),
        lightposition=dict(x=100, y=200, z=300),
        hovertext=f"<b>{name}</b><br>{hover}", hoverinfo="text",
        name=lname, legendgroup=lname, showlegend=show,
    ))


def label(x, y, z, text, size=11, color=INK, bold=False):
    t = f"<b>{text}</b>" if bold else text
    x = x + _xoff
    traces.append(go.Scatter3d(
        x=[x], y=[y], z=[z], mode="text", text=[t],
        textfont=dict(size=size, color=color, family="Segoe UI, Arial"),
        hoverinfo="skip", showlegend=False,
    ))


def line(pts, color=MUTED, width=4, dash=None, hover=None):
    pts = np.array(pts, float)
    pts[:, 0] += _xoff
    traces.append(go.Scatter3d(
        x=pts[:, 0], y=pts[:, 1], z=pts[:, 2], mode="lines",
        line=dict(color=color, width=width, dash=dash or "solid"),
        hoverinfo="text" if hover else "skip", hovertext=hover, showlegend=False,
    ))


def arrow(p0, p1, color=MUTED, width=4, hover=None, head=0.5):
    p0, p1 = np.array(p0, float), np.array(p1, float)
    d = p1 - p0
    u = d / np.linalg.norm(d)
    line([p0, p1 - u * 0.3], color=color, width=width, hover=hover)
    traces.append(go.Cone(
        x=[p1[0] - u[0] * 0.3 + _xoff], y=[p1[1] - u[1] * 0.3], z=[p1[2] - u[2] * 0.3],
        u=[u[0]], v=[u[1]], w=[u[2]], sizemode="absolute", sizeref=head, anchor="tail",
        colorscale=[[0, color], [1, color]], showscale=False, hoverinfo="skip", showlegend=False,
    ))


def floor(x0, x1, y0, y1, color, title, z=-0.35):
    box(x0, x1, y0, y1, z - 0.08, z, color, title, "Piso da etapa", "Etapas", opacity=0.12, legend_label="Etapas (piso)")
    label((x0 + x1) / 2, y0 - 1.0, z, title, size=13, color=color, bold=True)


# ---------- cameras ----------
XOFF2 = 14.0
XMIN, XMAX, YMIN, YMAX, ZMIN, ZMAX = -0.5, 37.5 + XOFF2, -8.5, 13.0, -0.5, 11.5
RX, RY, RZ = XMAX - XMIN, YMAX - YMIN, ZMAX - ZMIN
GM = (RX * RY * RZ) ** (1 / 3)   # plotly (aspectmode='data') normaliza pela media geometrica
CX, CY, CZ = (XMIN + XMAX) / 2, (YMIN + YMAX) / 2, (ZMIN + ZMAX) / 2


def nc(x, y, z):
    return ((x - CX) / GM, (y - CY) / GM, (z - CZ) / GM)


def view(cx, cy, cz, dist, az_deg, el_deg):
    cx = cx + _xoff
    if dist < 1.0:
        dist *= 1.5   # vistas focadas: afastar um pouco
    c = nc(cx, cy, cz)
    az, el = np.radians(az_deg), np.radians(el_deg)
    e = (c[0] + dist * np.cos(el) * np.cos(az), c[1] + dist * np.cos(el) * np.sin(az), c[2] + dist * np.sin(el))
    return dict(center=dict(x=c[0], y=c[1], z=c[2]), eye=dict(x=e[0], y=e[1], z=e[2]), up=dict(x=0, y=0, z=1))


def comp(stage, cid, title, desc, cam):
    components.append(dict(stage=stage, id=cid, title=title, desc=desc, cam=cam))


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
    """Muitos cubinhos num unico Mesh3d. cells = [(x0,x1,y0,y1,z0,z1,color,hover), ...]"""
    X, Y, Z, I, J, K, FC, HT = [], [], [], [], [], [], [], []
    bi = [0, 0, 4, 4, 0, 0, 1, 1, 2, 2, 3, 3]
    bj = [1, 2, 5, 6, 1, 5, 2, 6, 3, 7, 0, 4]
    bk = [2, 3, 6, 7, 5, 4, 6, 5, 7, 6, 4, 7]
    for n, (x0, x1, y0, y1, z0, z1, col, hv) in enumerate(cells):
        x0, x1 = x0 + _xoff, x1 + _xoff
        o = 8 * n
        X += [x0, x1, x1, x0, x0, x1, x1, x0]
        Y += [y0, y0, y1, y1, y0, y0, y1, y1]
        Z += [z0, z0, z0, z0, z1, z1, z1, z1]
        I += [o + v for v in bi]
        J += [o + v for v in bj]
        K += [o + v for v in bk]
        FC += [col] * 12
        HT += [hv] * 8
    lname = legend_label or group
    show = lname not in _legend_seen
    _legend_seen.add(lname)
    traces.append(go.Mesh3d(
        x=X, y=Y, z=Z, i=I, j=J, k=K, facecolor=FC, opacity=opacity, flatshading=True,
        lighting=dict(ambient=0.85, diffuse=0.35, specular=0.05, roughness=1.0, fresnel=0.0),
        lightposition=dict(x=0, y=-1000, z=800),
        hovertext=HT, hoverinfo="text", name=lname, legendgroup=lname, showlegend=show,
    ))


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
    traces.append(go.Surface(
        x=xx + x_off + _xoff, y=yy, z=np.full_like(w, z0), surfacecolor=w, cmin=0, cmax=1,
        colorscale=[[0, "#f3f5f8"], [0.001, "#f3f5f8"], [0.35, "#9fb3c8"], [1, C_TR]],
        showscale=False, hovertext=hover, hoverinfo="text", name=title, showlegend=False,
        contours=dict(x=dict(show=True, color="#ffffff", width=1), y=dict(show=True, color="#ffffff", width=1)),
    ))
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
traces.append(go.Scatter3d(x=[_xoff + 29.35], y=[-5.79], z=[0.72 * 3.2 + 0.35], mode="markers+text",
                           marker=dict(size=6, color=C_CHOICE, symbol="diamond"),
                           text=["<b>.choice = 'bloquear' · .confidence 0.72</b>"], textposition="top center",
                           textfont=dict(size=9, color=C_CHOICE), hoverinfo="skip", showlegend=False))
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
traces.append(go.Scatter3d(x=[_xoff + 29.35], y=[yc], z=[3.0], mode="markers+text",
                           marker=dict(size=7, color=C_SCORE, symbol="diamond"),
                           text=[f"<b>.score = {sc:.3f}</b> (centroide)"], textposition="top center",
                           textfont=dict(size=9, color=C_SCORE),
                           hovertext=f"Centroide: Σ p_i · i = 0.10·0 + 0.75·1 + 0.15·2 = {sc:.3f}<br>Contínuo, não truncado ao inteiro.",
                           hoverinfo="text", showlegend=False))
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
traces.append(go.Scatter3d(x=_xoff + 29 + (zz + 6) / 12 * 2.2, y=np.full_like(zz, 5.0), z=sig * 3.0, mode="lines",
                           line=dict(color=C_NOUL, width=5), hoverinfo="text",
                           hovertext=[f"σ({z:.1f}) = {s:.2f}" for z, s in zip(zz, sig)], showlegend=False))
line([(29, 5, 0), (31.2, 5, 0)], color=MUTED, width=2)
line([(29, 5, 1.5), (31.2, 5, 1.5)], color=MUTED, width=1, dash="dot", hover="σ = 0.5 (indiferença)")
z_ex = 1.2
s_ex = 1 / (1 + np.exp(-z_ex))
traces.append(go.Scatter3d(x=[_xoff + 29 + (z_ex + 6) / 12 * 2.2], y=[5.0], z=[s_ex * 3.0], mode="markers+text",
                           marker=dict(size=7, color=C_NOUL),
                           text=[f"<b>.noul = {s_ex:.2f}</b>"], textposition="top center",
                           textfont=dict(size=9, color=C_NOUL),
                           hovertext=f"logit z = {z_ex} → σ(z) = {s_ex:.2f}", hoverinfo="text", showlegend=False))
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
traces.append(go.Scatter3d(x=_xoff + 32.2 + 0.8 * cal_x, y=-6.2 + 4.0 * cal_x, z=3.5 + 2.2 * (acc_llm - cal_x), mode="lines+markers",
                           line=dict(color=C_RED, width=3, dash="dot"), marker=dict(size=3, color=C_RED),
                           hovertext=[f"LLM RLHF: conf {c:.1f} → acc {a:.2f} (sobreconfiança)" for c, a in zip(cal_x, acc_llm)],
                           hoverinfo="text", showlegend=False))
traces.append(go.Scatter3d(x=_xoff + 32.2 + 0.8 * cal_x, y=-6.2 + 4.0 * cal_x, z=3.5 + 0.12 * np.sin(cal_x * 9), mode="markers",
                           marker=dict(size=4, color=C_CAL, line=dict(color=INK, width=1)),
                           hovertext=[f"Jev: conf {c:.1f} → acc ≈ {c:.2f}" for c in cal_x], hoverinfo="text", showlegend=False))
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
traces.append(go.Scatter3d(x=_xoff + 31.7 + 1.0 * np.cos(th), y=11.6 + 0.6 * np.sin(th), z=2.6 + 0.0 * th, mode="lines",
                           line=dict(color=C_RED, width=4), hovertext="Loop: y_t ~ P(· | x, y_1..y_{t−1}), repetido T vezes",
                           hoverinfo="text", showlegend=False))
label(31.7, 11.6, 3.1, "× T", size=9, color=C_RED, bold=True)
label(30.2, 11.6, 3.9, "PIPELINE DE UM LLM GENERATIVO — ELIMINADO NO JEV", size=11, color=C_RED, bold=True)
line([(24, 10.2, 0), (36.4, 10.2, 0)], color=C_RED, width=2, dash="dot")
comp("✕ O que o Jev elimina", "X", "Pipeline autorregressivo eliminado",
     "Faixa cinza riscada ao fundo da etapa 3, alinhada com o ponto em que um decoder entraria em cada peça: "
     "(1) LM head para vocabulário aberto; (2) amostragem estocástica; (3) loop de T passos, um forward por token; "
     "(4) destokenização e parsing de JSON. É a ausência dessas quatro peças que dá O(1), custo zero de saída e "
     "impossibilidade estrutural de erro de formato.", view(30.2, 11.6, 1.2, 0.55, -95, 35))

# =====================================================================
# LAYOUT / FIGURA
# =====================================================================
views = [
    ("Visão geral", view(25.5 - XOFF2, 1.5, 3.0, 1.95, -82, 28)),
    ("1 · Entrada", view(11.4 - XOFF2, 0.0, 1.6, 0.6, -88, 14)),
    ("2 · Blocos", view(15.8, 0.0, 3.0, 0.62, -70, 18)),
    ("2 · Máscara", view(15.8, 0.0, 9.0, 0.55, -90, 75)),
    ("3 · Cabeças", view(29.5, 0.0, 1.5, 0.7, -55, 28)),
    ("3 · Calibração + saída", view(34.0, 0.0, 1.8, 0.55, -45, 28)),
    ("✕ Eliminado", view(30.2, 11.6, 1.2, 0.55, -95, 35)),
    ("Topo", view(25.5 - XOFF2, 2.0, 3.5, 1.9, -90, 89)),
]
buttons = [dict(label=n, method="relayout", args=[{"scene.camera": c}]) for n, c in views]

fig = go.Figure(data=traces)
fig.update_layout(
    paper_bgcolor="#f7f8fa",
    scene=dict(xaxis=dict(visible=False, range=[XMIN, XMAX]), yaxis=dict(visible=False, range=[YMIN, YMAX]), zaxis=dict(visible=False, range=[ZMIN, ZMAX]),
               aspectmode="data", bgcolor="#f7f8fa", camera=views[0][1]),
    legend=dict(x=0.995, y=0.98, xanchor="right", yanchor="top", bgcolor="rgba(255,255,255,0.88)",
                bordercolor="#d8dde5", borderwidth=1, font=dict(size=10.5, color=INK, family="Segoe UI, Arial"),
                title=dict(text="<b>Componentes</b>", font=dict(size=11.5))),
    updatemenus=[dict(type="buttons", direction="right", x=0.01, y=0.01, xanchor="left", yanchor="bottom",
                      buttons=buttons, bgcolor="#ffffff", bordercolor="#d8dde5",
                      font=dict(size=11, color=INK, family="Segoe UI, Arial"), pad=dict(r=4, t=4))],
    margin=dict(l=0, r=0, t=0, b=0),
    hoverlabel=dict(bgcolor="#ffffff", bordercolor="#d8dde5", font=dict(size=12, color=INK, family="Segoe UI, Arial"), align="left"),
    font=dict(family="Segoe UI, Arial"),
)

plot_div = fig.to_html(full_html=False, include_plotlyjs=True, div_id="jev",
                       config=dict(displaylogo=False, responsive=True, scrollZoom=True))

# ---------- painel lateral ----------
stages = []
for c in components:
    if c["stage"] not in stages:
        stages.append(c["stage"])
panel = []
for s in stages:
    panel.append(f'<h3>{s}</h3>')
    for c in [c for c in components if c["stage"] == s]:
        panel.append(
            f'<div class="item" data-cam=\'{json.dumps(c["cam"])}\'>'
            f'<div class="t">{c["title"]}</div><div class="d">{c["desc"]}</div>'
            f'<button class="focus">Focar na cena →</button></div>')
panel_html = "\n".join(panel)

page = f"""<!DOCTYPE html>
<html lang="pt"><head><meta charset="utf-8">
<title>Arquitetura 3D do Jev — guia de estudo</title>
<style>
  :root {{ --ink:{INK}; --muted:{MUTED}; --navy:{C_TR}; --accent:{C_CHOICE}; --line:#d8dde5; --panel:#ffffff; --bg:#f7f8fa; }}
  * {{ box-sizing:border-box; }}
  html,body {{ margin:0; height:100%; font-family:"Segoe UI",Arial,sans-serif; color:var(--ink); background:var(--bg); }}
  .wrap {{ display:grid; grid-template-columns: 1fr 380px; grid-template-rows: auto 1fr; height:100vh; }}
  header {{ grid-column:1/3; padding:10px 18px 8px; border-bottom:1px solid var(--line); background:#fff; }}
  header h1 {{ margin:0; font-size:18px; color:var(--navy); }}
  header p {{ margin:4px 0 0; font-size:12px; color:var(--muted); }}
  #jev {{ height:100%; min-height:0; }}
  .plot {{ min-height:0; position:relative; }}
  aside {{ border-left:1px solid var(--line); background:var(--panel); overflow-y:auto; padding:12px 14px 30px; font-size:12.5px; line-height:1.45; }}
  aside h2 {{ font-size:13px; margin:0 0 8px; color:var(--navy); letter-spacing:.06em; text-transform:uppercase; }}
  aside h3 {{ font-size:12px; margin:16px 0 6px; padding-bottom:4px; border-bottom:2px solid var(--navy); color:var(--navy); }}
  .item {{ border:1px solid var(--line); border-radius:6px; padding:8px 10px; margin-bottom:8px; background:#fff; }}
  .item.active {{ border-color:var(--accent); box-shadow:0 0 0 2px #fbeee8; }}
  .item .t {{ font-weight:600; margin-bottom:3px; }}
  .item .d {{ color:#333a47; }}
  .item button {{ margin-top:6px; font-size:11px; border:1px solid var(--line); background:#f4f6f9; color:var(--navy); border-radius:4px; padding:3px 8px; cursor:pointer; }}
  .item button:hover {{ background:#e8eef6; }}
  #detail {{ position:sticky; top:0; background:#fbeee8; border-left:4px solid var(--accent); padding:8px 10px; margin:0 0 10px; font-size:12px; min-height:52px; z-index:2; }}
  #detail b {{ display:block; margin-bottom:2px; }}
  .facts {{ display:grid; grid-template-columns:1fr 1fr; gap:6px; margin:6px 0 4px; }}
  .fact {{ background:#f4f6f9; border-radius:6px; padding:6px 8px; }}
  .fact .v {{ font-size:15px; font-weight:700; color:var(--navy); }}
  .fact .k {{ font-size:10.5px; color:var(--muted); }}
  .legendnote {{ font-size:11px; color:var(--muted); margin-top:6px; }}
  .sw {{ display:inline-block; width:10px; height:10px; border-radius:2px; vertical-align:middle; margin-right:4px; }}
</style></head>
<body>
<div class="wrap">
  <header>
    <h1>Arquitetura do Jev (TypeSafe AI · System One Model) — cena 3D interativa</h1>
    <p>Arraste para girar · roda do mouse para zoom · passe o mouse em qualquer peça para ler o que ela faz · clique numa peça para fixar o texto no painel · botões no rodapé mudam a câmera. O fluxo vai da esquerda (entrada) para a direita (objeto tipado); a faixa cinza riscada ao fundo é o que um LLM generativo teria e o Jev não tem.</p>
  </header>
  <div class="plot">{plot_div}</div>
  <aside>
    <div id="detail"><b>Detalhe do componente</b><span id="detail-body">Passe o mouse ou clique numa peça da cena.</span></div>
    <h2>Guia de estudo</h2>
    <div class="facts">
      <div class="fact"><div class="v">1 passo</div><div class="k">forward único, O(1) em decodificação</div></div>
      <div class="fact"><div class="v">70–500 ms</div><div class="k">latência ponta a ponta</div></div>
      <div class="fact"><div class="v">64k / 32k</div><div class="k">tokens por chamada / state + maior pergunta</div></div>
      <div class="fact"><div class="v">2–255</div><div class="k">opções por Choice · 2–10 níveis por Score</div></div>
      <div class="fact"><div class="v">ECE 3,3–3,5%</div><div class="k">vs. 15–35% em LLMs RLHF</div></div>
      <div class="fact"><div class="v">$0,042 / 1M</div><div class="k">tokens de entrada · saída $0</div></div>
    </div>
    <div class="legendnote">
      <span class="sw" style="background:{C_IN}"></span>Entrada &nbsp;
      <span class="sw" style="background:{C_TR}"></span>Atenção &nbsp;
      <span class="sw" style="background:{C_TR2}"></span>FFN &nbsp;
      <span class="sw" style="background:{C_TR3}"></span>Norm &nbsp;
      <span class="sw" style="background:{C_TR4}"></span>Add &nbsp;
      <span class="sw" style="background:{C_CHOICE}"></span>Choice &nbsp;
      <span class="sw" style="background:{C_SCORE}"></span>Score &nbsp;
      <span class="sw" style="background:{C_NOUL}"></span>Noul &nbsp;
      <span class="sw" style="background:{C_CAL}"></span>Calibração &nbsp;
      <span class="sw" style="background:{C_OUT}"></span>Saída &nbsp;
      <span class="sw" style="background:{C_GHOST}"></span>Eliminado
    </div>
    {panel_html}
    <h3>Leitura sugerida da cena</h3>
    <div class="item"><div class="d">1) Comece em <b>Visão geral</b> e siga o fluxo da esquerda para a direita. 2) Em <b>1 · Entrada</b>, leia as matrizes da esquerda para a direita: página do state → esteira do tokenizer (fragmentos → IDs) → matriz de embedding (linha laranja = lookup) → RoPE senoidal → X = E[ids] ⊕ pos, com as colunas dos critérios coloridas. 3) Em <b>2 · Blocos</b>, leia as subcamadas de baixo para cima em cada coluna; o tubo claro à direita é o fluxo residual. 4) Em <b>2 · Máscara</b>, compare o triângulo (decoder) com o quadrado cheio (Jev): essa diferença é o que elimina o loop. 5) Em <b>3 · Cabeças</b>, veja que cada primitiva tem uma projeção restrita e uma leitura própria (argmax, centroide, sigmoide). 6) Em <b>Calibração</b>, todas as cabeças passam por z/T. 7) Termine em <b>✕ Eliminado</b>.</div></div>
  </aside>
</div>
<script>
(function(){{
  var gd = document.getElementById('jev');
  var body = document.getElementById('detail-body');
  var items = document.querySelectorAll('.item[data-cam]');
  items.forEach(function(it){{
    it.querySelector('button.focus').addEventListener('click', function(){{
      var cam = JSON.parse(it.getAttribute('data-cam'));
      Plotly.relayout(gd, {{'scene.camera': cam}});
      items.forEach(function(o){{ o.classList.remove('active'); }});
      it.classList.add('active');
      body.innerHTML = '<b>' + it.querySelector('.t').textContent + '</b>' + it.querySelector('.d').textContent;
    }});
  }});
  function show(ev){{
    if(!ev || !ev.points || !ev.points.length) return;
    var p = ev.points[0];
    var ht = (p.hovertext !== undefined) ? p.hovertext : (p.data && p.data.hovertext);
    if(Array.isArray(ht)) ht = ht[p.pointNumber] || ht[0];
    if(ht) body.innerHTML = ht;
  }}
  gd.on('plotly_hover', show);
  gd.on('plotly_click', show);
  window.addEventListener('resize', function(){{ Plotly.Plots.resize(gd); }});
  setTimeout(function(){{ Plotly.Plots.resize(gd); }}, 50);
}})();
</script>
</body></html>"""

out = r"D:\6. Trabalho\5. Afya\1. codigo\_hub_dev\Arquitetura_Jev_3D.html"
with open(out, "w", encoding="utf-8") as f:
    f.write(page)
print("ok", out, len(traces), "traces", len(components), "componentes")
import os, sys
if "--test" in sys.argv:
    for i in [1, 2, 4, 5, 6]:
        fig.update_layout(scene_camera=views[i][1])
        fig.write_html(f"test_view{i}.html", include_plotlyjs=True, config=dict(displaylogo=False))
    print("test views written")
