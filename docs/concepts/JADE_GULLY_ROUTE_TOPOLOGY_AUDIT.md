# Jade Gully Act 1 — auditoria de trajetos antes da próxima arte 3D

**Fonte inspecionada:** a pintura original \`docs/concepts/jade-gully-act1-concept.png\` (cinco setores nomeados) e a captura lado a lado enviada pelo usuário em 22/11/2026. **Contrato inspecionado:** \`assets/levels/jade_gully_concept_v4.json\` na branch V5.

**Conclusão:** a geometria é mais detalhada, porém o mundo ainda NÃO reproduz as escolhas de navegação da pintura. A rota amarela é só o esqueleto; tracejados roxos são atalhos e anéis/plataformas sugerem outros percursos. **Não confundir uma passarela modelada, um efeito visual ou uma curva pintada com um caminho fisicamente transitável.**

## O que dá para contar com segurança

- **1** percurso principal amarelo contínuo START → GOAL, passando por cinco regiões.
- **Pelo menos 5 trechos/corredores de atalhos roxos** distinguíveis na pintura: salto da cabana oeste; atalho da árvore em direção ao leste; cadeia inferior de ilhas; contorno alternativo abaixo/ao redor do hex; continuação inferior até a região do cânion. A pintura tem oclusões e não fornece nós, superfícies de aterrissagem ou conexões sem ambiguidade.
- **8 famílias adicionais de circulação sugeridas**, não desenhadas como linhas contínuas, por anéis, molas, patamares e passarelas.
- **18 elementos de circulação auditados ao todo:** 5 *trechos setoriais* da MESMA linha principal, 5 corredores de atalho roxo e 8 possibilidades sugeridas pela geometria. **Não são 18 caminhos independentes completos.** O inventário verificável está em \`assets/levels/jade_gully_route_audit_v5.json\`.

| Setor | Elementos auditados | Evidência na arte | O que está faltando no modelo |
|---|---:|---|---|
| 1 Entry Hills | 3 | Linha sinuosa, arco de anéis por cima do lago, plataformas inferiores junto às piscinas | Desvio do arco com entrada/saída reais; caminho inferior com saltos/aterrissagens |
| 2 Tree Village | 5 | Escada amarela, deck circular no tronco em alturas diferentes, dois saltos roxos oeste/leste, passarela inferior até cachoeira | Grafo em torno da árvore e bifurcações de diferentes alturas; distinguir subir, contornar e descer |
| 3 Sky Bridges | 3 | Pontes superiores amarelas, ilhas inferiores ligadas por roxo, degraus de nuvem e pequenos patamares com anéis | Rotas superior/inferior independentes, saltos reais e reconexão |
| 4 Hex Loop | 3 | Loop interno azul com anéis; a própria legenda cita trilhas internas/ao redor; roxo inferior segue até ilhas do cânion | Dentro / fora / por baixo como travessias distintas; entrada, saída e transição da gravidade |
| 5 Canyon Basin | 4 | Subida superior amarela ao GOAL, tablados sobre a água, plataformas inferiores com molas/cachoeiras, saliências escalonadas | Travessia média sobre a água, rota baixa de cachoeiras, conexão entre esses níveis e rota da meta |

### Diferença objetiva entre a pintura e o JSON

O JSON atual tem **1** \`main\` com **33** pontos e só **3** rotas \`alternate\`: \`village_drop\`, \`lower_islands\`, \`hex_bypass\`. Contém **18** \`walkways\`, mas elas não são automaticamente ramificações completas. Um teste geométrico 3D de distância a segmentos dos quatro caminhos declarados encontrou **8 de 18 passarelas** com pelo menos uma ponta a mais de 6 unidades da linha de rota mais próxima: \`village_rope_north\`, \`village_rope_lookout\`, \`canyon_dock_walk\`, \`canyon_stairs_mid\`, \`canyon_dock_a\`, \`canyon_dock_b\`, \`village_rope_lookout_east\`, \`village_stairs_west_north\`. **É indício de falta de ancoragem no grafo — não prova, isoladamente, que a geometria seja inalcançável**, pois pulos e plataformas intermediárias podem existir.

Os demais 10 de 18 elementos também NÃO estão necessariamente completos: há rotas com pontos que não seguem precisamente o bordo de uma passarela, aterrissagens não modeladas e trecho principal sugerido em cima de terreno que não foi validado como jogável.

### Inventário cruzado

- **5** trechos da linha principal: registrados numa única \`main\`, não em cinco rotas distintas.
- **3** alternativas parcialmente representadas: \`village_drop\`, \`lower_islands\`, \`hex_bypass\`.
- **9** elementos com cenário, mas sem corredor completo no grafo (arco, piscinas, anel da árvore, salto leste, ponte inferior, nuvens intermediárias, tablados, cascata inferior e subida lateral).
- **1** corredor sem representação adequada: passagem roxa **por baixo do Hex Loop rumo ao cânion inferior**.
- **13 de 18** elementos auditados têm cobertura incompleta ou ausente. Esta métrica de **cobertura de desenho** não mede se a cena pode ser percorrida no Saturn.

## Próximo contrato de implementação — antes de outro passe de texturas

1. **Nós de navegação:** START, entradas/saídas dos cinco setores, bifurcações e reconexões, plataformas e alturas; um nó precisa ter posição 3D e área de aterrissagem, não só coordenada em overlay.
2. **Arestas tipadas:** \`run\`, \`slope\`, \`bridge\`, \`jump\`, \`spring\`, \`gravity_loop\`, \`drop\`. Cada aresta tem largura, desnível, direção, landing/launch, material ou colisão e fallback caso o salto falhe.
3. **Entry Hills:** inserir desvio do arco e travessia baixa, com pontos de reconexão ao principal.
4. **Tree Village:** três níveis independentes (solo, deck anelar, alto); construir trechos leste/oeste roxos e a passarela inferior sob a árvore, com retornos reais.
5. **Sky Bridges + Hex:** três faixas verticais (alta, intermediária, baixa); separar interior do Hex, contorno externo e passagem inferior; conferir geometria do loop, velocidade e comportamento de gravidade.
6. **Canyon Basin:** conectar o trajeto baixo de molas e cachoeiras aos tablados médios e ao caminho alto que sobe ao GOAL; sem atalhos para o objetivo atravessando o vazio.
7. **Gates técnicos:** testar componentes conectados a START/GOAL, rotas alternativas que se separam e reencontram, ausência de pontas soltas exceto mirantes e segredos, distância entre saltos vs física do Sonic, colisões, desempenho do Saturn (meta prudente: 30 fps), e revisão visual 3D no Ymir/Mednafen.

**Estado atual:** a V5 é uma concept scene offline no Blender, NÃO uma fase navegável de Saturn; testes de geometria e métricas de cores não certificam rotas jogáveis. Não promover \`main\` até a rede de caminhos ter os gates acima.

### Reprodução da auditoria

\`\`\`bash
python3 tools/audit_jade_routes_v5.py
python3 -m unittest tests.test_jade_route_audit -v
\`\`\`

Essa auditoria é intencionalmente uma lista de dívida: **não** cria rotas por decorar a imagem com mais setas roxas, nem assume que o mapa ilustrado especifica trajetos completos de ponta a ponta.
