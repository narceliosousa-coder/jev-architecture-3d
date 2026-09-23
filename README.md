# Arquitetura do Jev — cena 3D interativa

Visualização 3D interativa da arquitetura do modelo **Jev** (TypeSafe AI · System One Model), feita com Three.js:
entrada e pré-processamento em matrizes, N blocos Transformer com atenção bidirecional, cabeças tipadas
Choice / Score / Noul, calibração RLCD e o pipeline autorregressivo que o modelo elimina.

- **Página publicada:** https://narceliosousa-coder.github.io/jev-architecture-3d/
- Passe o mouse nas peças para ler o que fazem; clique para abrir o card no guia de estudo.
- Passe o mouse no **Bloco 1** e clique em "Expandir": o bloco sobe, se abre e vira as matrizes reais
  de um bloco Transformer (X, LayerNorm, W_Q/W_K/W_V, Q/K/V, scores, softmax, A·V, concat, W_O, residual, FFN SwiGLU),
  todas calculadas em numpy, com um card explicativo por matriz.

## Arquivos

- `index.html` — página autocontida (funciona offline).
- `src/jev_scene.py` — gerador: descreve a cena e escreve o HTML (`python src/jev_scene.py index.html`; requer `numpy`).
- `src/viewer.js` — visualizador Three.js (render, hover, câmeras, animação de expansão).
- `src/page_template.html` — layout da página. `src/lib/` — three.js r128 + OrbitControls (embutidos).

Material de estudo pessoal, baseado em fontes públicas sobre o Jev e o RLCD.
