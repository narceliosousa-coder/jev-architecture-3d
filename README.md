# Arquitetura do Jev — cena 3D interativa

Visualização 3D interativa (Plotly) da arquitetura do modelo **Jev** (TypeSafe AI · System One Model):
entrada e pré-processamento em matrizes, N blocos Transformer com atenção bidirecional, cabeças tipadas
Choice / Score / Noul, calibração RLCD e o pipeline autorregressivo que o modelo elimina.

- **Página publicada:** https://narceliosousa-coder.github.io/jev-architecture-3d/
- `index.html` — cena autocontida (funciona offline).
- `build_scene.py` — gerador em Python (`pip install plotly numpy`; `python build_scene.py`).

Material de estudo pessoal, baseado em fontes públicas sobre o Jev e o RLCD.
