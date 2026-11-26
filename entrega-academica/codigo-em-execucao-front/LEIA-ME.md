# MOVE — POO no frontend e integração com o backend

Abra **index.html** no navegador, mesmo com o MOVE desligado. A galeria tem 21 PNGs. O botão **Seleção para slides** reúne seis imagens do frontend e de sua comunicação com o servidor. Clique em qualquer miniatura para abrir o PNG original. As capturas 02, 03, 06 e 07 também permitem ampliar o painel Watch dentro da galeria.

O índice CSV usa UTF-8 com BOM e ponto e vírgula como separador. Ele identifica dimensões do PNG, viewport, tema, arquivo-fonte, trecho, classe, comportamento, origem e SHA-256. Os caminhos das imagens são relativos à pasta deste guia.

## Um percurso de seis imagens para apresentar em sala

| Captura | O que apontar | Pergunta que ela responde |
|---|---|---|
| **13** | O mesmo formulário na aplicação e no template, a macro de botão e a linha que cria um objeto para cada formulário marcado com `data-submissao`. | De onde vem o objeto que controla este botão? |
| **06** | No início do evento `submit`, `this.#enviando` e `botao.disabled` valem `false`. | Qual era o estado antes de o objeto agir? |
| **07** | No mesmo objeto, `#enviando` e `botao.disabled` agora valem `true`. O formulário também está marcado como ocupado para tecnologia assistiva. | Como o método altera o comportamento da interface? |
| **09** | O POST do vínculo retorna 303. O GET da ficha retorna 200 e o MOVE exibe Lia Vale como responsável. | Onde termina a ação do botão e como chega a confirmação do servidor? |
| **03** | O painel Watch permite ler `this.#preferencia` no contexto de execução de `ControleTema`. | Onde a escolha de aparência fica encapsulada? |
| **04** | A ficha de LV5 está escura e o menu indica a opção escolhida. | O que a pessoa vê depois que o método aplica a preferência? |

A captura **08** serve como detalhe para o slide 07. Ela mostra o botão realmente pintado como desabilitado enquanto o navegador aguardava a resposta. Para encerrar o percurso, use **19 → 20 → 21**. As três imagens acompanham a mesma consulta financeira desde o objeto Python até o HTML que o usuário lê.

## Como ler as demais sequências

- **01–04 · Aparência.** O Chrome carregou a classe original. A execução parou no construtor e, depois, dentro do evento de alteração. O Watch leu campos privados no frame da própria classe. A aplicação de `data-tema` ao documento e a preferência salva em `localStorage` foram conferidas depois do clique. A primeira preferência de sistema foi emulada como clara.
- **05–09 · Submissão.** O exemplo usa a vinculação de LV5 à cliente fictícia Lia Vale. O construtor associa uma instância ao formulário, o evento modifica o campo privado e o estado chega ao DOM. A autorização e a efetivação do vínculo pertencem ao servidor. O bloqueio do botão demonstra proteção do lado do navegador.
- **10–12 · Troca de contexto.** No tablet, a mesma sessão Master Demo abre o seletor na Gestão e segue para o Cliente. O navegador registrou `POST /ambiente` com 303 e `GET /cliente/` com 200. No smartphone, uma sessão separada da mesma conta toca em Estadias. A interface mostra as duas estadias de Lia.
- **13 · Composição.** O template produz o formulário e usa a macro `ui.botao`. O navegador conecta o formulário a uma instância de `ControleSubmissao`. A macro evidencia reutilização de apresentação. A classe, a instância, o campo privado e o comportamento encapsulado estão no JavaScript.
- **14–18 · Apoio em Python.** Compare o despacho de métodos para três veículos e três categorias de clientes. Em seguida observe uma reocupação recusada por `Vaga`, a construção de `OcupacaoViewModel` e o serviço que `ConsultasPessoais` utiliza para projetar as estadias do titular.
- **19–21 · A mesma consulta em três pontos.** Lia Vale, VIP, AV1, vaga 2 e estadia 22. A duração de 1,225 h produz base de R$ 12,25 e desconto exato de R$ 6,125. O domínio arredonda o valor devido para 613 centavos. A rota entrega o resultado ao Jinja2 e a tela exibe R$ 6,13. No portal, valores monetários aparecem com duas casas, inclusive o desconto apresentado. O estado da tela é **Sem confirmação**. O clique em **Consultar cobrança** não registra pagamento.

## Origem e limites das evidências

- **Referência:** `fa323dca437853cdd6cd64c1f1c682298dd88ecb`. As novas sessões utilizaram uma extração do Git desse commit, o Flask do MOVE, o navegador Google Chrome, o Chrome DevTools e o depurador Python `pdb`. O servidor ouviu apenas no loopback. O cenário veio de `tests/cenario_gestao.py` e do provisionamento demonstrativo do projeto.
- **16 imagens novas:** 01–13 e 19–21. **Cinco reutilizadas:** 14–18, provenientes do banco anterior de execução do mesmo checkpoint. O SHA-256 individual foi conferido com o índice anterior. São ensaios independentes com os mesmos dados fictícios. Os pares 06/07 e 10/11 e o trio 19/20/21, por sua vez, preservam a continuidade de seu próprio evento ou requisição.
- **Leitura do depurador:** Watch e pdb mostram valores observados em pausas reais. A pintura de um botão pode acontecer depois que o JavaScript volta a executar. Na captura 08, um invólucro de ensaio atrasou temporariamente a entrega do POST ao Flask. Retomado o processamento, a aplicação tratou a requisição real e redirecionou para a ficha. Os tempos no painel Network incluem as pausas e a espera controlada.
- **Dispositivos e resolução:** o desktop em 04 tem viewport de 1440 × 900 CSS. Nos registros combinados, o produto ocupa uma janela mais estreita, ao lado do depurador. Tablet de 1024 × 768 e smartphone de 390 × 844 usam emulação de toque e DPR 2. O CSV identifica a dimensão efetiva de cada arquivo. Os terminais de Python têm 1920 × 1080 pixels.
- **Edição e privacidade:** as vistas lado a lado são capturas simultâneas de janelas reais. Alguns PNGs são recortes contíguos para aproximar o formulário, o código ou a resposta HTTP. As miniaturas e lupas do índice derivam dos PNGs. Os arquivos de contas, senhas, cookies, tokens, históricos e perfis temporários do navegador ficam fora da entrega.
- **Reprodução:** use a mesma fixture e abra `web/static/js/controles.js` em Sources. Pare nas linhas 12 e 48 para o tema, e 59, 60 e 67 para a vinculação. Para a consulta de AV1, os pontos observados foram `model/estadia.py:65` e `web/gestao.py:254`. O arquivo CSV relaciona cada imagem à sua fonte no checkpoint.


## Conferência da entrega

A galeria abriu diretamente pelo sistema de arquivos em um Chrome configurado offline, em 1440 × 900 e 390 × 844 CSS. Em cada largura foram abertos os 21 PNGs originais, as miniaturas, a seleção de seis slides, a lupa do Watch e o atalho para a cobrança. O navegador registrou zero requisições HTTP ou HTTPS e zero erros de execução da página. As 21 somas SHA-256 foram recalculadas e a estrutura interna dos PNGs foi conferida.
