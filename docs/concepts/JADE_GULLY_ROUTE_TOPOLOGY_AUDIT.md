# Jade Gully Act 1 — auditoria de trajetos antes da próxima arte 3D

**Fonte inspecionada:** a pintura original `docs/concepts/jade-gully-act1-concept.png` (cinco setores nomeados) e a captura lado a lado enviada pelo usuário em 22/11/2026. **Contrato inspecionado:** `assets/levels/jade_gully_concept_v4.json` na branch V5.

**Conclusão:** a geometria é mais detalhada, porém o mundo ainda NÃO reproduz as escolhas de navegação da pintura. A rota amarela é só o esqueleto; tracejados roxos são atalhos e anéis/plataformas sugerem outros percursos. **Não confundir uma passarela modelada, um efeito visual ou uma curva pintada com um caminho fisicamente transitável.**

## Implementação P3 — rede inferior do Hex + Canyon Basin

**Estado da branch V5 (prévia artística; colisão e física ainda NÃO verificadas):**

- **11 rotas declaradas no total:** 1 principal + 10 alternativas.
- **20 passarelas com geometria explícita:** os quatro tablados/escadas
  anteriormente distantes das linhas agora têm trechos correspondentes no
  grafo; nenhuma das 20 passarelas termina a mais de 6 unidades da linha
  de alguma rota de apresentação.
- **11 novos apoios físicos de modelo**, sendo 4 tablados de madeira, 4
  patamares de rocha sob Hex/entrada de Canyon e 3 apoios rochosos para
  a transição intermediária.
- **26 transferências aéreas tipadas** (salto, queda ou mola), cada uma
  com um nome de pouso e `physics_verified: false`. As novas rotas
  `hex_lower_underpass`, `canyon_mid_stairs` e `canyon_lower_docks`
  possuem início e fim em nós da rota principal.
- **Vista fechada do Canyon Basin obrigatória no Blender CI**, além da
  vista Sky Bridges, porque o mapa geral esconde erros de ligação entre
  tablados, degraus e cachoeiras.

**Cuidado: correspondência entre pontes e linhas de rota NÃO comprova
que Sonic consegue percorrê-las.** Especialmente a escadaria intermediária
pode ser inclinada demais, as molas ascendentes precisam ser testadas com
a física real e parte do desvio inferior do Hex cruza a área transformada
do loop. Esses itens são bloqueadores de jogabilidade, mesmo se o
Blender produzir uma imagem atraente.

A auditoria de 18 elementos foi registrada sobre a pintura original e
não se recalcula automaticamente a partir de novas propostas. Portanto,
não atualizar o histórico para 18/18 apenas porque há mais linhas no
JSON. A prioridade seguinte é avaliar o close-up do Canyon, revisar
inclinações, distâncias de salto e superfícies de aterrissagem no Saturn.

## Correção P2 — revisão visual das travessias (após rejeição do render)

A comparação da pintura original com o render `jade-gully-v4-routes.png`
revelou que **os nove acessos extras sobre as ilhas da Sky Bridges haviam
sido falsamente transformados em pontes e escadas**. A pintura representa
trechos de salto por nuvens, molas e plataformas suspensas, não uma pista
contínua de madeira no vazio.

**Alteração na branch V5:**

- **19 passarelas reais de conceito** (antes 27). Cada superfície restante
  é uma malha de deck contínuo com largura, corrimãos, treads e encaixes nos
  extremos; `scenic_walkway_stations` limita curvas para evitar passarelas
  serpentinas arbitrárias;
- **9 transferências aéreas explicitamente tipadas** como `jump`,
  `drop` ou `spring` em `navigation_transfers`, com destino ancorado
  nas ilhas nomeadas ou no caminho principal. Nenhuma recebe ponte
  automática. São *intenções*, NÃO saltos alcançáveis comprovados;
- **Tree Village**: a escadaria oeste–norte de 26m de elevação foi removida;
  duas rampas menores contornam o tronco, com escoras para a árvore;
- **Revisão do mapa**: a pintura mantém o amarelo da rota principal e roxo
  dos atalhos representados; sugestões cianas aparecem apenas no
  `jade-gully-v4-routes.png`, não no mapa de apresentação;
- **Grafo** `jade-gully-v5-navigation.json` distingue `walkway_id` de
  `transfer_id`, mantém `physics_verified: false` e
  `collision_verified: false` em todas as arestas.

Essa correção resolve o problema de **representação incorreta** das ligações,
não cria física do Sonic nem resolve lacunas de patamares, saltos e suporte no
Canyon Basin. **Não promover para main sem inspecionar o novo PNG.**

## Implementação P1 — ramificações com apoio geométrico (V5)

**Entregue na branch V5, ainda não validado como fase jogável do Saturn.**
A rede de rotas do Blender agora contém **1 percurso principal e 7 alternativas
de apresentação** (antes: 1+3). As passarelas subiram de **18 para 27**:

- `village_north_decks`: oeste → cabana norte → cabana central, apoiada nas
  passarelas/escadas já presentes;
- `village_lookout_decks`: cabana central → mirante → cabana leste, apoiada em
  duas passarelas já existentes;
- `sky_high_e`: ilha alta A → ilha E → ilha B, com duas novas pontes;
- `sky_middle_d`: ilha alta A → ilha intermediária D → ilha C, com duas novas
  passarelas xadrez;
- `lower_islands`: a alternativa baixa já declarada ganhou cinco segmentos
  físicos de acesso, travessia e reconexão entre ilhas.

Os quatro ramos novos são **candidatos cianos no render do mapa**, não atalhos
roxos que a pintura confirme explicitamente. A pintura continua sendo evidência
de uma rede muito mais rica, mas não tem detalhamento de física/aterrissagem.
As outras quatro linhas, `main`, `village_drop`, `lower_islands` e
`hex_bypass`, conservam seu sentido original.

`tools/compile_jade_navigation_v5.py` agora compila nós 3D e arestas
tipadas com IDs de passarelas quando **as duas extremidades coincidem**.
Gera `jade-gully-v5-navigation.json`; as arestas marcadas
`mode: unverified` não têm suporte geométrico provado. Todos os nós/arestas
declaram `collision_verified: false`: não houve teste de gameplay, colisão,
salto, mola, loop nem desempenho real do Saturn.

**O débito original de 13 elementos do desenho não está quitado por essas
novas curvas.** A validação de caminhos exige aterrissagens, retorno,
diferentes alturas e testes jogáveis. O relatório pode ser reproduzido com
`python3 tools/audit_jade_routes_v5.py`, e o grafo com
`python3 tools/compile_jade_navigation_v5.py`.

### Comparação da malha de apresentação

| Medida | Antes do P1 | Com P1 |
|---|---:|---:|
| Rotas alternativas declaradas | 3 | 7 |
| Passarelas modeladas | 18 | 27 |
| Passarelas com ponta a mais de 6 unidades das rotas declaradas | 8 | 4 |
| Navegação/colisão do Saturn verificada | Não | Não |

As **quatro passarelas ainda sem ancoragem** ficam no Canyon Basin:
`canyon_dock_walk`, `canyon_stairs_mid`, `canyon_dock_a`,
`canyon_dock_b`. A expansão funcional seguinte deve tratar do Hex Loop
inferior e dos três níveis do Canyon Basin.

## O que dá para contar com segurança

- **1** percurso principal amarelo contínuo START → GOAL, passando por cinco regiões.
- **Pelo menos 5 trechos/corredores de atalhos roxos** distinguíveis na pintura: salto da cabana oeste; atalho da árvore em direção ao leste; cadeia inferior de ilhas; contorno alternativo abaixo/ao redor do hex; continuação inferior até a região do cânion. A pintura tem oclusões e não fornece nós, superfícies de aterrissagem ou conexões sem ambiguidade.
- **8 famílias adicionais de circulação sugeridas**, não desenhadas como linhas contínuas, por anéis, molas, patamares e passarelas.
- **18 elementos de circulação auditados ao todo:** 5 *trechos setoriais* da MESMA linha principal, 5 corredores de atalho roxo e 8 possibilidades sugeridas pela geometria. **Não são 18 caminhos independentes completos.** O inventário verificável está em `assets/levels/jade_gully_route_audit_v5.json`.

| Setor | Elementos auditados | Evidência na arte | O que está faltando no modelo |
|---|---:|---|---|
| 1 Entry Hills | 3 | Linha sinuosa, arco de anéis por cima do lago, plataformas inferiores junto às piscinas | Desvio do arco com entrada/saída reais; caminho inferior com saltos/aterrissagens |
| 2 Tree Village | 5 | Escada amarela, deck circular no tronco em alturas diferentes, dois saltos roxos oeste/leste, passarela inferior até cachoeira | Grafo em torno da árvore e bifurcações de diferentes alturas; distinguir subir, contornar e descer |
| 3 Sky Bridges | 3 | Pontes superiores amarelas, ilhas inferiores ligadas por roxo, degraus de nuvem e pequenos patamares com anéis | Rotas superior/inferior independentes, saltos reais e reconexão |
| 4 Hex Loop | 3 | Loop interno azul com anéis; a própria legenda cita trilhas internas/ao redor; roxo inferior segue até ilhas do cânion | Dentro / fora / por baixo como travessias distintas; entrada, saída e transição da gravidade |
| 5 Canyon Basin | 4 | Subida superior amarela ao GOAL, tablados sobre a água, plataformas inferiores com molas/cachoeiras, saliências escalonadas | Travessia média sobre a água, rota baixa de cachoeiras, conexão entre esses níveis e rota da meta |

### Diferença objetiva entre a pintura e o JSON

Na **linha de base anterior ao P1**, o JSON tinha **1** `main` com **33** pontos e só **3** rotas `alternate`: `village_drop`, `lower_islands`, `hex_bypass`. Naquele momento continha **18** `walkways`, mas elas não eram automaticamente ramificações completas. Um teste geométrico 3D de distância a segmentos dos quatro caminhos declarados encontrou **8 de 18 passarelas na linha de base** com pelo menos uma ponta a mais de 6 unidades da linha de rota mais próxima: `village_rope_north`, `village_rope_lookout`, `canyon_dock_walk`, `canyon_stairs_mid`, `canyon_dock_a`, `canyon_dock_b`, `village_rope_lookout_east`, `village_stairs_west_north`. **É indício de falta de ancoragem no grafo — não prova, isoladamente, que a geometria seja inalcançável**, pois pulos e plataformas intermediárias podem existir.

Os demais 10 de 18 elementos também NÃO estão necessariamente completos: há rotas com pontos que não seguem precisamente o bordo de uma passarela, aterrissagens não modeladas e trecho principal sugerido em cima de terreno que não foi validado como jogável.

### Inventário cruzado

- **5** trechos da linha principal: registrados numa única `main`, não em cinco rotas distintas.
- **3** alternativas parcialmente representadas: `village_drop`, `lower_islands`, `hex_bypass`.
- **9** elementos com cenário, mas sem corredor completo no grafo (arco, piscinas, anel da árvore, salto leste, ponte inferior, nuvens intermediárias, tablados, cascata inferior e subida lateral).
- **1** corredor sem representação adequada: passagem roxa **por baixo do Hex Loop rumo ao cânion inferior**.
- **13 de 18** elementos auditados têm cobertura incompleta ou ausente. Esta métrica de **cobertura de desenho** não mede se a cena pode ser percorrida no Saturn.

## Próximo contrato de implementação — antes de outro passe de texturas

1. **Nós de navegação:** START, entradas/saídas dos cinco setores, bifurcações e reconexões, plataformas e alturas; um nó precisa ter posição 3D e área de aterrissagem, não só coordenada em overlay.
2. **Arestas tipadas:** `run`, `slope`, `bridge`, `jump`, `spring`, `gravity_loop`, `drop`. Cada aresta tem largura, desnível, direção, landing/launch, material ou colisão e fallback caso o salto falhe.
3. **Entry Hills:** inserir desvio do arco e travessia baixa, com pontos de reconexão ao principal.
4. **Tree Village:** três níveis independentes (solo, deck anelar, alto); construir trechos leste/oeste roxos e a passarela inferior sob a árvore, com retornos reais.
5. **Sky Bridges + Hex:** três faixas verticais (alta, intermediária, baixa); separar interior do Hex, contorno externo e passagem inferior; conferir geometria do loop, velocidade e comportamento de gravidade.
6. **Canyon Basin:** conectar o trajeto baixo de molas e cachoeiras aos tablados médios e ao caminho alto que sobe ao GOAL; sem atalhos para o objetivo atravessando o vazio.
7. **Gates técnicos:** testar componentes conectados a START/GOAL, rotas alternativas que se separam e reencontram, ausência de pontas soltas exceto mirantes e segredos, distância entre saltos vs física do Sonic, colisões, desempenho do Saturn (meta prudente: 30 fps), e revisão visual 3D no Ymir/Mednafen.

**Estado atual:** a V5 é uma concept scene offline no Blender, NÃO uma fase navegável de Saturn; testes de geometria e métricas de cores não certificam rotas jogáveis. Não promover `main` até a rede de caminhos ter os gates acima.

### Reprodução da auditoria

```bash
python3 tools/audit_jade_routes_v5.py
python3 -m unittest tests.test_jade_route_audit -v
```

Essa auditoria é intencionalmente uma lista de dívida: **não** cria rotas por decorar a imagem com mais setas roxas, nem assume que o mapa ilustrado especifica trajetos completos de ponta a ponta.
