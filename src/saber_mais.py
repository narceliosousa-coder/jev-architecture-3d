# -*- coding: utf-8 -*-
"""Textos "Saber mais" do guia de estudo: explicacao por analogia, em passos numerados, um por card.
Chave = id do card (mesmo id usado em comp()). Valor = HTML."""

MORE = {}

# =====================================================================
# ETAPA 1 — ENTRADA
# =====================================================================
MORE["1.1a"] = """
<p class="lead">Imagine um juiz que só pode decidir com base no que está dentro da pasta do processo. Nada de telefonar para
uma testemunha, nada de consultar a internet. O <b>state</b> é essa pasta: tudo o que o Jev vai saber sobre o caso está aqui.</p>
<ol class="steps">
<li><b>A pasta fechada.</b> O modelo não busca nada fora do state. Se a informação não está no texto, para ele não existe. Isso é
diferente de um assistente que "lembra" de conversas anteriores ou pesquisa em documentos: o Jev é um oráculo sem memória.</li>
<li><b>Formatos misturados, sem cerimônia.</b> A pasta pode ter texto corrido, um JSON de telemetria e logs de sistema. O Jev lê tudo
como sequência de tokens, sem exigir um esquema de entrada. É a aplicação que decide o que colocar ali.</li>
<li><b>Faça as contas antes de entregar a pasta.</b> O modelo trata números e datas como texto: não soma, não conta, não calcula
"quantos dias se passaram". Se a decisão depende de "mais de 4 falhas no trimestre", quem conta as falhas é o seu código, e o
resultado da conta entra no state já pronto (ex.: <code>falhas_trimestre: 5</code>).</li>
<li><b>Menos é mais.</b> Pasta cheia de papel irrelevante dilui a atenção do modelo (o chamado <i>context rot</i>) e reduz a confiança
das respostas. Higienize: o state ideal tem só o que a decisão precisa.</li>
<li><b>O limite.</b> A soma do state com a pergunta mais longa não pode passar de 32k tokens. Para textos maiores, divida em partes ou
resuma antes.</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> como não há loop de raciocínio nem ferramentas, a qualidade da decisão é limitada pela
qualidade da pasta. Um state bem montado vale mais do que qualquer ajuste de prompt.</p>
"""

MORE["1.1b"] = """
<p class="lead">Junto com a pasta do processo vai um formulário de múltipla escolha. O Jev não escreve uma sentença: ele preenche o
formulário. Cada pergunta desse formulário é uma <b>interrogação</b>, e o formulário inteiro tem M perguntas.</p>
<ol class="steps">
<li><b>Três tipos de pergunta, e só três.</b> <i>Choice</i> é a múltipla escolha clássica (de 2 a 255 alternativas, cada uma com uma
descrição). <i>Score</i> é uma nota numa régua com patamares descritos em palavras ("negligível", "moderado", "crítico"). <i>Noul</i>
é uma afirmação que o modelo julga verdadeira ou falsa, devolvendo uma probabilidade.</li>
<li><b>Instruções ao pé da letra.</b> Cada pergunta traz um texto de instrução e os critérios. O Jev é hiper-literal: se uma exceção não
estiver escrita nos critérios, ele não a inventa. Pense num estagiário muito obediente que só faz exatamente o que o formulário pede.</li>
<li><b>Perguntas independentes.</b> As M perguntas não conversam entre si nem esperam a resposta da anterior. É por isso que dá para
fazer vinte perguntas sobre o mesmo incidente de uma vez (<i>speculative fan-out</i>) pagando quase o mesmo que por uma: o custo
grande é ler a pasta, não responder ao formulário.</li>
<li><b>O esquema é fechado.</b> Se a Choice tem quatro alternativas, a resposta é uma dessas quatro. Não existe "outro", não existe
texto livre. Se você precisa de mais de 255 alternativas, a receita é filtrar primeiro com um Score e escolher depois com uma Choice.</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> o formulário fechado é o que torna a saída à prova de erros de formato. O modelo pode
errar a resposta, mas nunca pode responder algo que não estava no formulário.</p>
"""

MORE["1.2"] = """
<p class="lead">Antes de ler, o modelo pica todo o texto em peças pequenas e numeradas, como se transformasse uma frase em blocos de
montar. Cada peça é um <b>token</b> e cada token tem um número de identificação fixo no vocabulário.</p>
<ol class="steps">
<li><b>Picar e numerar.</b> "transação" pode virar duas peças ("trans" + "ação"); "12500" vira uma peça de número; "aprovar" vira uma
peça só. O tokenizador é um dicionário fixo: a mesma palavra sempre vira os mesmos IDs.</li>
<li><b>Uma fila só.</b> Aqui está o detalhe que muda tudo: o state e as M perguntas (instruções + critérios) entram na <i>mesma</i>
fila de tokens. Na cena, os tokens azuis vieram do state e os coloridos vieram dos critérios das perguntas, mas todos ficam lado a
lado, numerados de 1 a T.</li>
<li><b>Por que juntar tudo?</b> Porque, mais adiante, a atenção só consegue relacionar o que está na mesma fila. Se a pergunta e o
contexto entrassem em canais separados, o modelo não teria como cruzar "ip divergente" com "bloquear".</li>
<li><b>O teto de 64k.</b> Somando contexto e todas as perguntas, a fila pode ter até 64 mil tokens por chamada. O limite de 32k vale
para state + a pergunta mais longa.</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> a "fila única" é a primeira peça da ideia central: pergunta e evidência são processadas
juntas, num passo só, em vez de o modelo ler o contexto e depois "pensar" a resposta token a token.</p>
"""

MORE["1.3"] = """
<p class="lead">Um número de identificação não diz nada sobre o significado de um token. A <b>matriz de embedding</b> é o dicionário
que troca cada número por uma "ficha de características": um vetor com d_model medidas (aqui, 12; em modelos reais, centenas).</p>
<ol class="steps">
<li><b>Uma linha por palavra do vocabulário.</b> A matriz tem |V| linhas (dezenas de milhares) e d_model colunas. Procurar o token
1042 é simplesmente ir até a linha 1042 e copiar a ficha inteira. Na cena, essa linha aparece em laranja.</li>
<li><b>Fichas aprendidas, não escritas à mão.</b> Ninguém decidiu o que significa cada coluna. Durante o treino, o modelo ajustou as
fichas até que palavras usadas em contextos parecidos ficassem com fichas parecidas. "bloquear" e "conter" acabam próximas; "12500"
fica perto de outros números.</li>
<li><b>Mesma língua para tudo.</b> A mesma matriz é usada para os tokens do state e para os tokens dos critérios das perguntas. Assim,
"bloquear" na pergunta e "bloqueio" no contexto viram fichas comparáveis.</li>
<li><b>Resultado.</b> Depois do lookup, a fila de T números vira uma tabela de T linhas × d_model colunas: uma ficha por token.</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> é o embedding que permite ao modelo perceber que o critério "risco explícito de
apropriação de conta" tem a ver com "ip divergente" mesmo sem nenhuma palavra em comum.</p>
"""

MORE["1.4"] = """
<p class="lead">Se você embaralhar as fichas de todos os tokens, a tabela de embeddings continua idêntica. Ela não sabe a ordem das
palavras. A <b>codificação posicional</b> resolve isso carimbando em cada ficha "eu sou o token número t".</p>
<ol class="steps">
<li><b>O carimbo é um relógio.</b> A técnica mais usada, RoPE, pega as dimensões da ficha aos pares e gira cada par por um ângulo
proporcional à posição t. Cada par gira numa velocidade diferente, como os ponteiros de um relógio: um dá uma volta a cada poucos
tokens, outro leva milhares de tokens para completar a volta. Na cena, é o padrão senoidal roxo: listras rápidas embaixo, lentas em cima.</li>
<li><b>Ordem relativa, não absoluta.</b> A mágica do RoPE é que, ao comparar dois tokens na atenção, o que sobra é a diferença entre os
ângulos, ou seja, a distância entre eles. O modelo aprende "o token 3 posições antes" e não "o token na posição 7".</li>
<li><b>Sem sentido único de leitura.</b> Num decoder, a posição vem junto com uma regra: só olhe para trás. Aqui a posição é só
informação. A ficha da posição 5 pode se relacionar com a da posição 12 e vice-versa.</li>
<li><b>Onde entra de fato.</b> No RoPE, a rotação é aplicada aos vetores Q e K dentro da atenção. Neste diagrama a mostramos como um
passo separado da entrada para deixar a ideia visível.</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> posição sem causalidade é exatamente o que um modelo de decisão precisa: saber que "não"
veio antes de "aprovar" sem ser obrigado a ler o texto numa direção só.</p>
"""

MORE["1.5"] = """
<p class="lead">Ao fim da etapa 1 existe uma planilha pronta: T linhas (uma por token) e d_model colunas. Chame-a de X. É essa planilha
inteira, de uma vez, que entra no primeiro bloco Transformer.</p>
<ol class="steps">
<li><b>Tudo junto, tudo ao mesmo tempo.</b> Não existe "primeiro token, depois o segundo". A planilha completa é a entrada. Isso é
comum a todos os Transformers; a diferença do Jev é que a saída também sai inteira, sem gerar tokens novos.</li>
<li><b>Colunas coloridas à direita.</b> Na cena, as últimas colunas de X têm cores das primitivas: são os tokens dos critérios das
perguntas. Eles são linhas comuns da planilha, com o mesmo formato dos tokens do contexto.</li>
<li><b>O que cada célula significa.</b> X[t, j] é a medida j da ficha do token t, já com a posição incorporada. Sozinha, a célula não
diz nada legível; o significado está no padrão das 12 medidas juntas.</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> a partir daqui, a pergunta e o contexto são indistinguíveis para a rede. Toda a
"conversa" entre eles acontecerá dentro dos blocos, na atenção.</p>
"""

# =====================================================================
# ETAPA 2 — BLOCOS TRANSFORMER
# =====================================================================
MORE["2.1"] = """
<p class="lead">Antes de uma reunião com muitas pessoas falando, alguém equaliza os microfones para que ninguém domine só por falar
mais alto. A <b>normalização</b> faz isso com os tokens: cada ficha é ajustada para ter a mesma "escala" antes de entrar na atenção.</p>
<ol class="steps">
<li><b>O ajuste.</b> Para cada token (cada linha da planilha), o modelo tira a média e divide pelo desvio das suas medidas. O resultado
tem média 0 e desvio 1. Depois multiplica por γ e soma β, dois vetores aprendidos que devolvem a "cor" que o modelo preferir.</li>
<li><b>RMSNorm é a versão econômica.</b> Em vez de subtrair a média, divide só pela raiz da média dos quadrados. Faz o mesmo papel com
menos contas; é a variante mais comum em modelos recentes.</li>
<li><b>"Pre" porque vem antes.</b> Pre-norm significa que a normalização é aplicada na entrada da subcamada, e não na saída. Vantagem:
o fluxo residual (a esteira que atravessa todos os blocos) nunca é normalizado, o que deixa o treino de redes profundas muito mais
estável.</li>
<li><b>Sem isso, o que aconteceria?</b> Tokens com vetores grandes gerariam scores de atenção gigantes, o softmax saturaria e o modelo
"olharia" para um único token. A equalização evita esse monopólio.</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> a mesma receita dos LLMs. Nada específico do Jev aqui, mas é o que permite empilhar N
blocos e treinar com RLCD sem instabilidade.</p>
"""

MORE["2.2"] = """
<p class="lead">Imagine uma reunião de especialistas debruçados sobre um relatório aberto na mesa, em vez de uma pessoa escrevendo uma
frase palavra por palavra. A <b>atenção</b> é essa reunião.</p>
<ol class="steps">
<li><b>Busca, etiqueta e conteúdo (Q, K, V).</b> Cada token produz três coisas: uma <i>Query</i> ("o que eu preciso saber agora?"),
uma <i>Key</i> ("qual assunto eu resumo?") e um <i>Value</i> ("a informação detalhada que eu entrego"). O modelo cruza cada busca com
todas as etiquetas; quanto maior a afinidade, mais peso o conteúdo daquele token recebe.</li>
<li><b>Vários especialistas ao mesmo tempo (MHA e GQA).</b> Em vez de um leitor só, há h "cabeças", cada uma com seus próprios moldes
de Q, K e V. Uma presta atenção em quem executa a ação, outra em valores numéricos, outra em regras de negócio. GQA é a versão
econômica: em vez de cada especialista manter o próprio fichário (K e V), grupos de cabeças compartilham o mesmo fichário.</li>
<li><b>Olhar o quadro inteiro, sem venda nos olhos.</b> Num modelo gerador, cada token só pode olhar para trás, porque está prevendo
o próximo (a máscara causal). Aqui não existe essa restrição: a matriz de afinidades T × T é completa. A pergunta no fim da fila examina
os dados do início, e os dados do início levam a pergunta em conta, ao mesmo tempo.</li>
<li><b>Decisão de uma vez só.</b> Se uma resposta tem 50 palavras, um gerador roda a rede 50 vezes. Com atenção global, o modelo
analisa o cenário inteiro e chega ao fim das N camadas em uma única passada ("profundidade constante"). É como bater o olho numa
planilha preenchida e decidir, em vez de redigir uma redação linha a linha.</li>
<li><b>O resumo final (W_O).</b> Depois que todos os especialistas deram suas notas, o modelo junta tudo lado a lado (concatena) e passa
por um alinhamento final (W_O) que consolida as visões num único parecer, pronto para a próxima etapa.</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> é o único lugar do bloco em que tokens trocam informação. Sem máscara, essa troca é
completa em cada bloco, e é por isso que a decisão inteira cabe num passo.</p>
"""

MORE["2.3"] = """
<p class="lead">Depois da reunião, ninguém reescreve o relatório do zero. Cada participante cola um post-it na margem com o que
acrescentaria. A <b>ligação residual</b> é o post-it: a saída da atenção (Y) é somada à planilha original (X), e não a substitui.</p>
<ol class="steps">
<li><b>Somar, não trocar.</b> X′ = X + Y. A informação original continua lá; a atenção só acrescenta correções. Se a atenção não tiver
nada útil a dizer, Y é pequeno e o token passa quase intacto.</li>
<li><b>A rodovia dos gradientes.</b> No treino, o sinal de erro precisa viajar de trás para frente por dezenas de blocos. Sem o residual,
ele se perderia (o "gradiente que desaparece"). Com ele, existe sempre um caminho direto, e por isso é possível ter N blocos.</li>
<li><b>Cada bloco aprende só o delta.</b> Como o modelo só precisa aprender o que acrescentar, blocos podem ser pequenos ajustes
sucessivos: refinar, não recomeçar.</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> é a mesma receita de qualquer Transformer. O que muda no Jev não está aqui, mas o residual
é o que permite que o "dossiê" atravesse os N blocos ganhando anotações sem se perder.</p>
"""

MORE["2.4"] = """
<p class="lead">Nova equalização de microfones, agora antes da segunda parte do bloco (a rede densa). A ideia é idêntica à Pre-Norm:
deixar cada token na mesma escala antes de processá-lo.</p>
<ol class="steps">
<li><b>Mesma conta, outro momento.</b> Cada linha de X′ é normalizada (média 0, desvio 1, ou RMSNorm) e reescalada com γ e β próprios
desta subcamada.</li>
<li><b>Por que de novo?</b> Porque o residual acabou de somar Y a X, e a escala das linhas mudou. A FFN aprende melhor com entradas
"padronizadas".</li>
<li><b>O residual continua limpo.</b> A normalização gera uma cópia (X̂′) que entra na FFN. A linha original X′ segue pela esteira sem ser
tocada.</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> nada específico; é higiene numérica que mantém os N blocos estáveis.</p>
"""

MORE["2.5"] = """
<p class="lead">Se a atenção foi a reunião, a <b>FFN</b> é o momento em que cada participante volta para a própria mesa e consulta seus
livros. Aqui cada token é processado sozinho, sem olhar para os outros, mas com acesso à "memória" do modelo.</p>
<ol class="steps">
<li><b>Expandir para pensar.</b> Duas matrizes (W_gate e W_up) levam a ficha do token de d_model para d_ff dimensões, tipicamente
quatro vezes mais. É como abrir a ficha numa mesa maior para ter espaço para associações.</li>
<li><b>A porta (SwiGLU).</b> O ramo "gate" decide quanto abrir cada neurônio; o ramo "up" carrega o conteúdo. Multiplicados elemento a
elemento, viram H: só passa o que a porta deixa. É uma forma de o modelo ligar e desligar "conceitos" conforme o token.</li>
<li><b>Comprimir de volta.</b> W_down traz H de volta para d_model. O resultado (F) é o post-it da FFN, que será somado ao residual.</li>
<li><b>Onde mora o conhecimento.</b> A FFN concentra cerca de dois terços dos parâmetros de um bloco. Pesquisas mostram que ela funciona
como uma memória associativa: padrões na entrada (chave) ativam neurônios que devolvem informação armazenada (valor).</li>
<li><b>Sem comunicação entre tokens.</b> Diferente da atenção, a FFN nunca cruza posições. Cada linha da planilha entra e sai
independentemente.</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> é a FFN que "sabe" que um IP divergente é sinal de apropriação de conta. A atenção junta
as evidências; a FFN aplica o que foi aprendido sobre elas.</p>
"""

MORE["2.6"] = """
<p class="lead">Segundo post-it na margem: a contribuição da FFN (F) é somada ao que já estava na esteira (X′). O resultado, X″, é a saída
do bloco e a entrada do próximo.</p>
<ol class="steps">
<li><b>Fechando o bloco.</b> X″ = X′ + F. Dois post-its por bloco: um da atenção, um da FFN. Nada foi apagado desde a entrada.</li>
<li><b>Repete N vezes.</b> X″ entra no bloco 2, que faz exatamente o mesmo com pesos próprios. Bloco após bloco, as fichas dos tokens
vão acumulando informação de contexto e de conhecimento.</li>
<li><b>Sem volta ao início.</b> Num gerador, ao fim dos N blocos sai um token e o processo recomeça. Aqui, ao fim dos N blocos, a
planilha vai direto para a normalização final e para as cabeças de decisão.</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> a ausência de "volta ao início" é o que dá a latência de 70 a 500 ms: N blocos, uma vez.</p>
"""

MORE["2.R"] = """
<p class="lead">Pense numa esteira que atravessa a fábrica inteira carregando a mesma folha. Cada estação (atenção, FFN) lê a folha, escreve
um post-it e cola de volta. A folha nunca sai da esteira. Esse é o <b>fluxo residual</b>, o tubo claro ao lado de cada bloco na cena.</p>
<ol class="steps">
<li><b>Uma folha por token.</b> A esteira carrega a planilha inteira (T linhas × d_model). Cada estação soma sua contribuição a todas as
linhas.</li>
<li><b>Leitura e escrita.</b> As subcamadas leem uma cópia normalizada da folha (as setas tracejadas saindo do tubo) e devolvem um delta
que é somado (as setas voltando para o tubo).</li>
<li><b>Por que funciona.</b> Como a folha original sempre chega ao fim, o modelo pode ser profundo sem perder o que estava na entrada, e o
treino tem um caminho direto para propagar erros.</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> é a mesma corrente residual dos LLMs. A folha que chega ao fim da esteira é a que vai ser lida
pelas cabeças tipadas.</p>
"""

MORE["2.M"] = """
<p class="lead">Duas formas de ler o mesmo documento. Na primeira, o leitor usa uma venda que só deixa ver o que já foi lido; na segunda, o
documento inteiro está aberto sobre a mesa. As duas grades acima dos blocos mostram essa diferença em forma de matriz.</p>
<ol class="steps">
<li><b>O triângulo (decoder).</b> Na grade da esquerda, a linha i (uma query) só tem células preenchidas até a coluna i. Tudo à direita
está bloqueado com −∞: o token não pode olhar para o futuro. É necessário porque o modelo está prevendo o próximo token; se pudesse
ver a resposta, o treino seria uma trapaça.</li>
<li><b>O quadrado (Jev).</b> Na grade da direita, todas as células estão preenchidas. O token 3 olha para o token 12 e o 12 olha para o 3.
Como o Jev não gera texto, não há "futuro" a esconder.</li>
<li><b>Consequência prática.</b> Com o triângulo, entender o texto inteiro exige percorrê-lo token a token, e responder exige gerar token a
token. Com o quadrado, todo o contexto é absorvido de uma vez em cada bloco; N blocos bastam.</li>
<li><b>De onde vem essa família.</b> Modelos bidirecionais são a linhagem BERT/ModernBERT (encoders). As reconstituições abertas do Jev
usam exatamente esse tipo de espinha dorsal, com cerca de 151 milhões de parâmetros.</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> esta grade é a imagem mais curta da tese do modelo: tirar a venda dos olhos elimina o loop.</p>
"""

# =====================================================================
# ETAPA 3 — SAIDA TIPADA
# =====================================================================
MORE["3.1a"] = """
<p class="lead">Última equalização antes de as fichas serem lidas pelas cabeças de decisão. Depois de N blocos somando post-its, as
escalas das linhas variam; a normalização final coloca todas no mesmo padrão.</p>
<ol class="steps">
<li><b>A mesma conta de sempre.</b> Cada linha da planilha final é normalizada e reescalada com γ e β aprendidos.</li>
<li><b>Por que existe.</b> As cabeças tipadas são projeções lineares simples. Elas funcionam melhor (e calibram melhor) quando a entrada
tem escala previsível.</li>
<li><b>Nada muda de forma.</b> Continua sendo T × d_model. O que muda é só a escala das linhas.</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> a calibração das probabilidades (etapa 3.3) depende de logits bem comportados; a Norm
final ajuda nisso.</p>
"""

MORE["3.1b"] = """
<p class="lead">O dossiê passou por toda a fábrica e cada folha ganhou anotações. Agora é hora de separar apenas as folhas de resposta:
uma por pergunta. Esse é o <b>pooling por interrogação</b>.</p>
<ol class="steps">
<li><b>Onde está a resposta de cada pergunta.</b> Cada interrogação ocupa algumas posições da fila de tokens. O modelo pega o vetor de uma
posição representativa de cada pergunta (por exemplo, o token que a abre) e descarta o resto. Sobram M vetores de d_model dimensões.</li>
<li><b>Por que esse vetor já "sabe" a resposta.</b> Nos N blocos, a atenção bidirecional deixou o token da pergunta absorver o contexto
inteiro. O vetor que sai dele é um resumo do que o modelo concluiu sobre aquela pergunta.</li>
<li><b>Paralelismo.</b> Os M vetores são tratados de forma independente pelas cabeças. Vinte perguntas, vinte vetores, vinte respostas ao
mesmo tempo. Nenhuma espera pela outra.</li>
<li><b>Sem vocabulário.</b> Repare no que não acontece aqui: o vetor não é comparado com dezenas de milhares de palavras para "gerar"
uma resposta. Ele vai direto para uma projeção pequena e restrita.</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> o pooling é a ponte entre "ler o dossiê" e "preencher o formulário". É aqui que o
Transformer deixa de ser um leitor e vira um decisor.</p>
"""

MORE["3.2a"] = """
<p class="lead">Uma urna com exatamente K cédulas, uma para cada alternativa cadastrada. A cabeça <b>Choice</b> distribui 100% de
probabilidade entre essas K cédulas e nada mais.</p>
<ol class="steps">
<li><b>A projeção restrita.</b> O vetor da pergunta (d_model medidas) é multiplicado por uma matriz que tem só K saídas. Não existe
saída para "outra coisa". Se a pergunta tem quatro opções, saem quatro números (logits).</li>
<li><b>Do logit à probabilidade.</b> O softmax transforma os K números numa distribuição: valores positivos que somam 1. É o campo
<code>.probabilities</code>.</li>
<li><b>A escolha e a confiança.</b> <code>.choice</code> é a alternativa com maior probabilidade (argmax). <code>.confidence</code> mede quanto
a distribuição está concentrada nela. Uma distribuição 0,72 / 0,15 / 0,09 / 0,04 é uma decisão firme; 0,30 / 0,28 / 0,22 / 0,20 é um
"não sei" honesto.</li>
<li><b>Impossível votar fora da urna.</b> Como não há vocabulário aberto, o modelo não pode devolver uma alternativa inexistente, nem
um texto, nem uma recusa. Isso elimina a alucinação de formato, mas não o erro de julgamento: ele ainda pode escolher a alternativa
errada com convicção.</li>
<li><b>Mais de 255 alternativas?</b> Use duas etapas: um Score para filtrar candidatos e uma Choice entre os melhores.</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> Choice é o coração do "confidence-gated routing": o código lê <code>.choice</code> e
<code>.confidence</code> e decide sozinho se executa, se pede verificação ou se chama um humano.</p>
"""

MORE["3.2b"] = """
<p class="lead">Um termômetro com marcas escritas em palavras ("negligível", "moderado", "crítico"). A cabeça <b>Score</b> não devolve só
a marca mais próxima: devolve a posição exata do ponteiro entre as marcas.</p>
<ol class="steps">
<li><b>Patamares ordenados.</b> Diferente da Choice, as opções do Score têm ordem. O modelo projeta o vetor da pergunta sobre L patamares
(de 2 a 10) e obtém uma probabilidade para cada um.</li>
<li><b>O centroide.</b> Em vez de escolher o patamar vencedor, o modelo calcula a média ponderada das posições: Σ p_i · i. Com 10% em
"negligível" (0), 75% em "moderado" (1) e 15% em "crítico" (2), o ponteiro para em 1,05: moderado, com leve inclinação para crítico.</li>
<li><b>Por que contínuo.</b> Um sistema pode usar o valor 1,05 diretamente num limiar ("acima de 1,4, escalar"), sem perder a nuance que
um inteiro perderia.</li>
<li><b>Campos.</b> <code>.score</code> é o centroide, <code>.probabilities</code> são os pesos por patamar e <code>.confidence</code> mede a
concentração.</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> Score é a ferramenta para ranquear e filtrar (por exemplo, ordenar 500 tickets por
urgência) antes de decisões discretas com Choice.</p>
"""

MORE["3.2c"] = """
<p class="lead">Um detector que responde a uma única afirmação com um número entre 0 e 1: a probabilidade de ela ser verdadeira. É a
cabeça <b>Noul</b>, a mais simples das três.</p>
<ol class="steps">
<li><b>Uma projeção, um número.</b> O vetor da pergunta é projetado em um único logit z. A sigmoide, σ(z) = 1 / (1 + e^(−z)), leva z para o
intervalo [0, 1]. z = 0 dá 0,5 (indiferença); z = 1,2 dá 0,77.</li>
<li><b>Sem campo de confiança separado.</b> Numa Choice, "probabilidade" e "confiança" são coisas diferentes (distribuição versus
concentração). No Noul, o próprio número já é a confiança: 0,77 significa "77% de chance de a afirmação ser verdadeira", nem mais nem
menos.</li>
<li><b>Como usar.</b> Ideal para guardas binárias: "a transação requer bloqueio imediato?", "este e-mail contém dados pessoais?". O código
compara <code>.noul</code> com um limiar escolhido conforme o custo do erro.</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> o Noul só é útil porque é calibrado. Um 0,77 descalibrado seria apenas um número
bonito; calibrado, ele é uma taxa de acerto que dá para prever.</p>
"""

MORE["3.3"] = """
<p class="lead">Um termômetro que marca 38 °C quando a temperatura real é 38 °C está aferido. Um modelo que diz "80% de certeza" e acerta
8 em cada 10 vezes está <b>calibrado</b>. O RLCD é o processo de aferição do Jev.</p>
<ol class="steps">
<li><b>O problema dos LLMs comuns.</b> Modelos treinados com RLHF aprendem a soar convincentes, porque avaliadores humanos preferem
respostas confiantes. O resultado é sobreconfiança: dizem "90%" e acertam 60%. O erro típico de calibração (ECE) fica entre 15% e 35%.</li>
<li><b>Treinar com regras de pontuação próprias.</b> O RLCD usa dados sintéticos com resposta certa conhecida e uma perda que combina
entropia cruzada (acertar a classe) com o termo de Brier, (p − y)², que pune confiança descolada do acerto. Dizer 0,99 e errar custa caro;
dizer 0,55 num caso ambíguo e errar custa pouco.</li>
<li><b>Ajuste fino de contraste (temperatura).</b> Depois do treino, os logits são divididos por uma temperatura T ajustada num conjunto
de validação. T não muda a ordem das alternativas (a escolha continua a mesma), só "espalha" ou "concentra" as probabilidades até que
elas batam com a taxa de acerto real.</li>
<li><b>Medindo a aferição.</b> O ECE agrupa as previsões por faixa de confiança e compara, em cada faixa, confiança média com acurácia
real. O mini diagrama sobre a placa dourada mostra isso: a linha preta é a aferição perfeita, os pontos dourados (Jev) ficam sobre ela,
os vermelhos (LLM RLHF) ficam abaixo. Para o Jev, o ECE fica entre 3,3% e 3,5%.</li>
<li><b>O que a calibração compra.</b> Limiares em código passam a ter significado: "executar acima de 0,88, revisar abaixo de 0,60" vira
uma política de risco previsível.</li>
<li><b>O que ela não compra.</b> Calibração não se compõe: se a saída de um Jev alimenta outro, a garantia se perde ao longo da cadeia.
Use o modelo como sensor sem estado, um passo por vez, e deixe a orquestração para software clássico.</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> sem calibração, as três primitivas seriam só formatos bonitos. Com ela, viram
instrumentos de medida que um sistema pode confiar.</p>
"""

MORE["3.4"] = """
<p class="lead">O formulário volta preenchido. Não há redação para ler, nem texto para interpretar: para cada pergunta há um campo com
o tipo certo e valores numéricos prontos para o código usar.</p>
<ol class="steps">
<li><b>O que não acontece.</b> Não há amostragem (nada de escolher o próximo token), não há loop (nada de repetir a rede T vezes) e não há
destokenização (nada de converter números em letras e depois validar JSON). A passagem única termina e o objeto já existe na memória.</li>
<li><b>O que volta.</b> Um dicionário com uma entrada por interrogação: para Choice, <code>choice</code>, <code>probabilities</code> e
<code>confidence</code>; para Score, <code>score</code>, <code>probabilities</code> e <code>confidence</code>; para Noul, apenas <code>noul</code>.</li>
<li><b>Custo e tempo.</b> Como não há geração, a saída é gratuita e a latência fica entre 70 e 500 ms. Paga-se apenas pela leitura do
state ($0,042 por milhão de tokens de entrada).</li>
<li><b>Como o código consome.</b> Via SDK (Python, TypeScript, Java, Go), com <code>if</code>s sobre os campos: bloquear se confiança ≥ 0,88,
mandar para analista se &lt; 0,60, pedir MFA no meio.</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> o objeto tipado é o produto final da tese: IA como componente de infraestrutura, que
responde a software com valores, não a pessoas com prosa.</p>
"""

MORE["X"] = """
<p class="lead">Uma fábrica de texto tem quatro máquinas no fim da linha que uma máquina de decisão simplesmente não precisa. A faixa
cinza riscada mostra as quatro, e por que cada uma sobra.</p>
<ol class="steps">
<li><b>LM head (a tradução para o vocabulário).</b> Num gerador, o vetor final é comparado com todas as dezenas de milhares de palavras
do vocabulário para achar a próxima. É uma matriz enorme e cara. O Jev projeta o vetor direto em K alternativas, L patamares ou 1
logit.</li>
<li><b>Amostragem (o sorteio do próximo token).</b> Greedy, top-p, top-k: estratégias para escolher uma palavra entre as candidatas.
Sem próxima palavra, não há o que sortear. As probabilidades do Jev são a resposta, não um passo intermediário.</li>
<li><b>O loop (× T).</b> Cada token gerado exige rodar a rede inteira de novo, com o texto até ali como entrada. Uma resposta de 400
tokens são 400 passagens e alguns segundos. O Jev roda uma passagem e para.</li>
<li><b>Destokenização e parsing.</b> Transformar IDs em texto e depois validar se o texto é um JSON correto é onde nascem os erros de
formato (campos inventados, aspas faltando, recusas). No Jev, o objeto nasce tipado; não há texto a validar.</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> a ausência dessas quatro máquinas explica, ao mesmo tempo, a latência baixa, a saída
gratuita e a impossibilidade estrutural de alucinar formato.</p>
"""

# =====================================================================
# BLOCO 1 EXPANDIDO — uma matriz por card
# =====================================================================
MORE["E0"] = """
<p class="lead">Pense numa fábrica de três andares. No térreo, as fichas dos tokens são equalizadas e ganham três "papéis" (busca,
etiqueta, conteúdo). No primeiro andar acontece a reunião (atenção). No segundo, cada token vai sozinho consultar a memória do modelo
(FFN). A folha entra no térreo e sai do segundo andar com duas anotações a mais.</p>
<ol class="steps">
<li><b>Como ler.</b> Da esquerda para a direita em cada fileira, de baixo para cima entre fileiras. As setas diagonais mostram a subida:
Q, K e V alimentam os scores; Y volta para somar-se a X.</li>
<li><b>Três cores, três tipos de matriz.</b> Verde: ativações, que mudam a cada chamada porque dependem da entrada. Cinza-azul: pesos
aprendidos, iguais em toda chamada. Laranja: matrizes de atenção (T × T), que relacionam token com token.</li>
<li><b>Os números são reais.</b> X vem dos 14 tokens da etapa 1; os pesos são aleatórios com a escala típica de um modelo treinado; todo
o resto é calculado de verdade (LayerNorm, produtos, softmax, SwiGLU). Passe o mouse em qualquer célula para ver o valor.</li>
<li><b>Tamanhos de brinquedo.</b> d_model = 12, d_k = 6, h = 2, d_ff = 16. Num modelo real, seriam centenas ou milhares, mas a forma das
matrizes e a sequência de operações são exatamente estas.</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> um bloco do Jev é um bloco Transformer comum, com uma única diferença visível: a matriz S
não tem triângulo mascarado.</p>
"""

MORE["E-X"] = """
<p class="lead">A planilha de entrada do bloco: 14 linhas, uma por token, e 12 colunas, uma por medida da ficha. É a mesma folha que
corre pela esteira residual.</p>
<ol class="steps">
<li><b>Linhas.</b> Os 9 primeiros tokens vêm do state ("trans", "ação", "ip", …); os 5 últimos vêm dos critérios das perguntas
("aprovar", "bloq", "risco", …). Dentro da planilha, não há nada que os distinga.</li>
<li><b>Colunas.</b> Nenhuma coluna tem nome legível. O significado está no padrão das 12 juntas, aprendido no treino.</li>
<li><b>De onde vem.</b> No Bloco 1, é E[ids] ⊕ pos, a saída da etapa 1. No Bloco 2, seria o X″ do Bloco 1, e assim por diante.</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> pergunta e evidência entram no bloco como linhas iguais da mesma planilha; é o pré-requisito
para a atenção cruzá-las.</p>
"""

MORE["E-Xh"] = """
<p class="lead">A mesma planilha depois da equalização de microfones: cada linha foi centrada e reescalada, de modo que nenhum token entra
na reunião "gritando".</p>
<ol class="steps">
<li><b>Linha a linha.</b> Para cada token, subtrai-se a média das 12 medidas e divide-se pelo desvio. Compare com X: o padrão de cores é
parecido, mas os contrastes ficam uniformes em todas as linhas.</li>
<li><b>γ e β.</b> Depois, cada coluna é multiplicada por um fator e somada a um deslocamento aprendidos. O modelo pode devolver ênfase a
certas medidas se quiser.</li>
<li><b>Uma cópia, não a original.</b> X̂ vai para as projeções Q, K e V. A original X continua na esteira, à espera do post-it.</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> scores de atenção bem comportados dependem desta escala uniforme.</p>
"""

MORE["E-WQ"] = """
<p class="lead">Um molde de 12 × 6: recebe a ficha equalizada de um token (12 medidas) e devolve a sua "pergunta de busca" (6 medidas).
É a matriz que ensina cada token a perguntar.</p>
<ol class="steps">
<li><b>Pesos, não dados.</b> W_Q não muda de uma chamada para outra. Foi ajustada no treino e é a mesma para todos os tokens. O que muda é
a ficha que entra.</li>
<li><b>Uma por cabeça.</b> Com h = 2, existem duas W_Q; aqui está a da cabeça 1. Cada cabeça aprende a fazer um tipo diferente de pergunta.</li>
<li><b>O que "pergunta" quer dizer.</b> A query de um token é um vetor cuja direção codifica que tipo de informação ele procura nos outros:
"quem é o sujeito?", "há um valor monetário perto?".</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> o critério "bloq" só consegue "perguntar" ao contexto porque passa por este molde como
qualquer token.</p>
"""

MORE["E-WK"] = """
<p class="lead">O molde da etiqueta: transforma a ficha de um token no rótulo que os outros vão comparar com suas perguntas. Query e
Key são as duas metades de uma busca.</p>
<ol class="steps">
<li><b>Como funciona a busca.</b> A afinidade entre o token i e o token j é o produto escalar q_i · k_j. Um treino bem-sucedido faz W_Q e
W_K "conversarem": a pergunta certa e a etiqueta certa ficam alinhadas.</li>
<li><b>GQA.</b> Em modelos grandes, várias cabeças compartilham a mesma W_K (e W_V). O custo de memória do cache de K e V cai sem perder
muito de qualidade.</li>
<li><b>Sem direção.</b> A etiqueta de um token pode ser lida por tokens antes e depois dele. Sem máscara, isso é literal.</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> as etiquetas dos tokens do state ficam à disposição dos tokens dos critérios, e vice-versa.</p>
"""

MORE["E-WV"] = """
<p class="lead">O molde do conteúdo: transforma a ficha de um token na informação que ele entrega quando alguém "presta atenção" nele.</p>
<ol class="steps">
<li><b>Separar achar de entregar.</b> Key é o que faz um token ser encontrado; Value é o que ele fornece quando encontrado. Separar os
dois deixa o modelo achar um token por um motivo e usar dele outra coisa.</li>
<li><b>Sem posição.</b> O RoPE gira Q e K, mas não V. A posição serve para decidir a quem prestar atenção, não altera o conteúdo entregue.</li>
<li><b>Compartilhada em GQA.</b> Como W_K, pode ser dividida entre cabeças de um grupo.</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> o conteúdo de "ip divergente" que chega até "bloq" passa por este molde.</p>
"""

MORE["E-Q"] = """
<p class="lead">As buscas prontas: 14 linhas (uma por token) com 6 medidas cada. É a matriz de cima na pilha de três.</p>
<ol class="steps">
<li><b>Uma pergunta por token.</b> A linha t é o que o token t procura. A linha de "bloq" pergunta, em essência, "há sinais de apropriação
de conta neste contexto?".</li>
<li><b>Posição embutida.</b> Com RoPE, cada linha foi girada segundo sua posição na fila, então a comparação com as keys leva a distância
em conta.</li>
<li><b>Curta de propósito.</b> d_k = 6 é a dimensão por cabeça. Somando as h cabeças (6 + 6), volta-se a d_model = 12.</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> as queries dos critérios são o mecanismo pelo qual a pergunta "varre" o contexto num passo.</p>
"""

MORE["E-K"] = """
<p class="lead">As etiquetas prontas: 14 linhas, uma por token. Ao serem comparadas com as queries (Q · Kᵀ), geram a tabela de
afinidades S.</p>
<ol class="steps">
<li><b>Uma etiqueta por token.</b> A linha j resume "o que este token tem para oferecer". Tokens parecidos em papel têm keys parecidas.</li>
<li><b>Posição embutida.</b> Também girada pelo RoPE, para que a diferença de posição entre query e key apareça no produto escalar.</li>
<li><b>Para todos os lados.</b> Cada key pode ser consultada por qualquer query, à esquerda ou à direita.</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> a etiqueta de "12500" (valor da transação) está disponível para a query de "risco" mesmo
estando antes dela na fila.</p>
"""

MORE["E-V"] = """
<p class="lead">Os conteúdos prontos: 14 linhas, uma por token, na base da pilha. São estas linhas que a atenção mistura.</p>
<ol class="steps">
<li><b>O que é entregue.</b> A linha j é o pacote de informação que o token j fornece a quem prestar atenção nele.</li>
<li><b>Sem posição.</b> Não passa pelo RoPE. Conteúdo é conteúdo, independentemente de onde o token está.</li>
<li><b>Como é usado.</b> Na fileira ②, a saída de cada token é uma média ponderada destas linhas, com pesos vindos de A.</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> é o que efetivamente "viaja" do contexto para a pergunta.</p>
"""

MORE["E-S"] = """
<p class="lead">A tabela de afinidades: 14 × 14 células, uma para cada par (token que pergunta, token que responde). Quanto maior o número,
mais a busca de i "casa" com a etiqueta de j.</p>
<ol class="steps">
<li><b>Cada célula é um produto escalar.</b> S[i, j] = q_i · k_j / √d_k. A divisão por √d_k evita que os valores cresçam com a dimensão e
saturem o softmax.</li>
<li><b>Sem triângulo bloqueado.</b> Num decoder, tudo acima da diagonal (j &gt; i) seria −∞: o token só olharia para trás. Aqui a tabela
está preenchida inteira. A linha de "bloq" (token 11) tem valores para "ip" (token 3) e para "conten" (token 14).</li>
<li><b>Leitura.</b> Passe o mouse: cada célula diz "query do token i × key do token j" com o valor calculado.</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> esta tabela cheia é a diferença estrutural entre um modelo que gera e um que decide. Tudo o
mais no bloco é igual.</p>
"""

MORE["E-A"] = """
<p class="lead">A mesma tabela, convertida em percentuais por linha. Cada linha agora diz como o token i distribui 100% da sua atenção
entre os 14 tokens.</p>
<ol class="steps">
<li><b>Softmax por linha.</b> Exponencia cada valor e divide pela soma da linha. Valores grandes viram pesos grandes; a linha inteira soma 1.</li>
<li><b>Foco e difusão.</b> Uma linha com uma célula escura e o resto claro é um token focado em um único outro. Uma linha uniforme é um
token que "olha para todos um pouco".</li>
<li><b>Interpretação.</b> A[i, j] é "quanto o token i atende o token j". É a parte mais interpretável de um Transformer, e a que os
visualizadores de atenção costumam mostrar.</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> se a linha do critério "bloquear" concentra peso em "ip divergente" e "12500", a decisão
tem uma trilha visível.</p>
"""

MORE["E-O1"] = """
<p class="lead">O resumo que cada token levou da reunião: 14 linhas × 6 medidas. Cada linha é uma mistura dos conteúdos (V) dos tokens
que ele atendeu, nas proporções de A.</p>
<ol class="steps">
<li><b>Média ponderada.</b> O_1 = A · V. A linha i é Σ_j A[i, j] · V[j]: os values dos tokens mais atendidos pesam mais.</li>
<li><b>Onde a informação viaja.</b> Este é o único produto do bloco que mistura linhas diferentes. Antes e depois dele, cada token é
tratado sozinho.</li>
<li><b>Cabeça 1 de 2.</b> A outra cabeça fez a mesma conta com seus próprios Q, K e V e produziu outra matriz 14 × 6.</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> é aqui que a linha de "bloquear" incorpora evidências vindas de "ip divergente" e do valor
da transação.</p>
"""

MORE["E-concat"] = """
<p class="lead">As anotações dos dois especialistas, lado a lado: as 6 colunas da cabeça 1 seguidas das 6 colunas da cabeça 2. Volta-se
a uma planilha 14 × 12.</p>
<ol class="steps">
<li><b>Colar, não somar.</b> Concatenar preserva o que cada cabeça viu separadamente. A mistura entre cabeças fica para W_O.</li>
<li><b>Por que a soma dá d_model.</b> h · d_k = 2 · 6 = 12. A largura por cabeça é escolhida para que a concatenação tenha exatamente a
dimensão do modelo.</li>
<li><b>Cinza.</b> As colunas da cabeça 2 aparecem em cinza só para distinguir os dois blocos.</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> mais cabeças, mais tipos de relação capturados de uma vez, sem passos extras.</p>
"""

MORE["E-WO"] = """
<p class="lead">O redator que consolida os pareceres: uma matriz 12 × 12 aprendida que mistura as colunas das duas cabeças e devolve o
resultado ao "idioma" do modelo.</p>
<ol class="steps">
<li><b>Sem W_O, as cabeças não se falam.</b> Até aqui, cada cabeça ocupava suas próprias colunas. W_O combina colunas de cabeças
diferentes.</li>
<li><b>Pesos fixos.</b> Como todas as W, é a mesma em toda chamada.</li>
<li><b>Tamanho.</b> d_model × d_model. Em modelos grandes, é uma das quatro grandes matrizes da atenção (com W_Q, W_K e W_V).</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> o parecer consolidado é o que será somado à folha na esteira.</p>
"""

MORE["E-Y"] = """
<p class="lead">O parecer da atenção: uma planilha 14 × 12 com o que cada token "aprendeu" na reunião. Não é a nova versão da folha; é o
post-it que será colado nela.</p>
<ol class="steps">
<li><b>Um delta por token.</b> Cada linha de Y é a correção que a atenção sugere para aquele token.</li>
<li><b>Pode ser pequeno.</b> Se o contexto não acrescentou nada relevante a um token, sua linha em Y fica próxima de zero.</li>
<li><b>Próximo passo.</b> Y entra no residual: X′ = X + Y.</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> separar "folha" de "post-it" é o que mantém a informação original disponível ao longo dos N
blocos.</p>
"""

MORE["E-X1"] = """
<p class="lead">A folha com o primeiro post-it colado: X′ = X + Y. Compare com X: o padrão geral se mantém, com ajustes onde a atenção
tinha algo a dizer.</p>
<ol class="steps">
<li><b>Soma célula a célula.</b> Cada X′[t, j] é X[t, j] + Y[t, j]. Nada foi apagado.</li>
<li><b>A rodovia.</b> Este atalho direto entre entrada e saída é o que permite treinar redes com dezenas de blocos.</li>
<li><b>Ainda não é a saída.</b> Falta a segunda metade do bloco (FFN).</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> mesma receita dos LLMs; o Jev não muda nada no residual.</p>
"""

MORE["E-Xh1"] = """
<p class="lead">A folha equalizada de novo, agora para entrar na consulta individual (FFN). É uma cópia normalizada de X′; a original segue
pela esteira.</p>
<ol class="steps">
<li><b>Mesma conta.</b> Média 0 e desvio 1 por linha, depois γ e β desta subcamada.</li>
<li><b>Por que repetir.</b> A soma com Y mudou as escalas; a FFN prefere entradas padronizadas.</li>
<li><b>Destino.</b> X̂′ multiplica W_gate e W_up em paralelo.</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> higiene numérica que mantém os N blocos estáveis.</p>
"""

MORE["E-Wg"] = """
<p class="lead">A matriz da porta: 12 × 16 pesos aprendidos. Cada coluna é um "neurônio" da FFN, e esta matriz decide, para cada token,
quanto cada neurônio abre.</p>
<ol class="steps">
<li><b>Expansão.</b> De 12 para 16 dimensões (na prática, de d_model para cerca de 4·d_model). Mais espaço para representar associações.</li>
<li><b>Sinal da porta.</b> G = X̂′ · W_gate. Valores positivos abrem o neurônio; negativos fecham.</li>
<li><b>Um dos maiores blocos de parâmetros.</b> W_gate, W_up e W_down juntas dominam a contagem de pesos de um bloco.</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> é o começo da "consulta à memória" que aplica o conhecimento aprendido a cada token.</p>
"""

MORE["E-Wu"] = """
<p class="lead">A matriz do conteúdo: 12 × 16 pesos aprendidos, calculada em paralelo com a porta. Traz o que cada neurônio "tem a dizer"
sobre o token.</p>
<ol class="steps">
<li><b>Mesma entrada, papel diferente.</b> U = X̂′ · W_up. Enquanto a porta decide quanto abrir, este ramo carrega o conteúdo candidato.</li>
<li><b>Por que dois ramos.</b> Separar "quanto" de "o quê" (o padrão GLU) deixa a FFN mais expressiva do que uma única camada com ativação.</li>
<li><b>Tamanho.</b> d_model × d_ff, igual a W_gate.</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> nada específico do Jev; é a FFN padrão dos modelos recentes (SwiGLU).</p>
"""

MORE["E-H"] = """
<p class="lead">O que passou pela porta: 14 tokens × 16 neurônios. É a ativação oculta da FFN, onde o modelo consulta sua memória
associativa.</p>
<ol class="steps">
<li><b>A multiplicação.</b> H = SiLU(G) ⊙ U, elemento a elemento. SiLU(g) = g · σ(g) é uma rampa suave: quase zero para g negativo,
aproximadamente g para g positivo.</li>
<li><b>Neurônios como conceitos.</b> Pesquisas mostram que colunas da FFN reagem a padrões específicos (uma a valores monetários, outra a
negações). A porta decide quais "acendem" para cada token.</li>
<li><b>Cada token sozinho.</b> Nenhuma linha de H depende de outra linha. Toda a comunicação entre tokens já aconteceu na atenção.</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> é aqui que "ip divergente" + "valor alto" viram, para o token do critério, algo como
"padrão de apropriação de conta".</p>
"""

MORE["E-Wd"] = """
<p class="lead">A matriz que comprime de volta: 16 × 12 pesos aprendidos. Traz a ativação expandida de volta para a dimensão do modelo.</p>
<ol class="steps">
<li><b>De volta a d_model.</b> F = H · W_down tem 14 × 12, como a folha da esteira.</li>
<li><b>Onde o conhecimento é "escrito".</b> Na visão de memória associativa, W_up/W_gate são as chaves e W_down são os valores: as
linhas de W_down são o que cada neurônio devolve quando ativado.</li>
<li><b>Pesos fixos.</b> Como todas as W.</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> F é o segundo post-it, o da FFN.</p>
"""

MORE["E-X2"] = """
<p class="lead">A folha na saída do bloco, com dois post-its colados: X″ = X′ + F. É exatamente o que o Bloco 2 vai receber como X.</p>
<ol class="steps">
<li><b>Nada perdido.</b> Ainda dá para reconhecer o padrão da entrada; os blocos refinam, não reescrevem.</li>
<li><b>N vezes.</b> O Bloco 2 repete tudo com pesos próprios. Ao fim do Bloco N, a folha vai para a normalização final e para o pooling.</li>
<li><b>O que nunca acontece.</b> Em nenhum ponto a folha é usada para gerar um token e reiniciar a leitura. O fluxo é só para frente.</li>
</ol>
<p class="why"><b>Por que isso importa no Jev:</b> a linha de cada pergunta, ao sair do Bloco N, já contém a decisão; as cabeças tipadas só a
leem e a convertem em Choice, Score ou Noul.</p>
"""
