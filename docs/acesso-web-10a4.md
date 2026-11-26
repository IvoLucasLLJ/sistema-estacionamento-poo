# MOVE · Login e cadastro pessoal

Em `/entrar`, **Criar conta** abre `/criar-conta`. O usuário informa nome completo, nome de usuário, senha e confirmação. Depois do cadastro, o MOVE volta ao login com uma confirmação. Uma conta recém-criada entra no portal Cliente com categoria Comum, sem veículos nem histórico de outras pessoas. A associação a um cliente já cadastrado continua disponível no provisionamento autorizado.

## Responsabilidades e persistência

| Componente | Responsabilidade |
|---|---|
| `web/rotas.py` | Receber os quatro campos previstos, exigir CSRF e uma revisão de uso único vinculada à sessão, exibir erros e redirecionar após sucesso. |
| `AutenticacaoService` em `web/contas.py` | Fixar o papel Cliente, reservar os nomes demonstrativos e coordenar o cadastro e sua retomada. |
| `ClienteComum`, `Identidade` e `ContaUsuario` | O domínio atribui o UUID. A identidade referencia esse titular. A conta compõe a identidade com o hash scrypt e guarda o nome apenas durante a recuperação pendente. |
| `ContaRepository` | Sob a trava existente, reservar o nome de usuário e o UUID, ler registros anteriores e ativar a reserva após a confirmação do domínio. |
| `EstacionamentoService.confirmar_cadastro_pessoal` | Sob a trava do histórico, gravar o evento de cadastro ou reconhecer a gravação anterior pelo mesmo UUID, categoria e nome. Uma divergência interrompe a recuperação. |
| Templates e JavaScript | O cadastro estende a composição do login. Ambos reutilizam as macros de marca, tema, campo, alerta e ação. ControleTema gerencia a preferência e ControleSubmissao gerencia o envio. Cada controle de visibilidade atua no campo identificado por aria-controls. |

A persistência usa três substituições de arquivo em sequência. Primeiro o arquivo de contas recebe uma reserva privada com nome normalizado de usuário, hash e UUID. O histórico recebe o cliente. Por último, o repositório ativa a conta removendo o campo opcional `nome_pendente`. As contas já ativas conservam o formato anterior.

Existe uma janela em que a Gestão pode ver o cadastro no histórico enquanto a conta pessoal ainda aguarda ativação. Cada substituição é atômica em seu arquivo. A consistência entre os arquivos depende da **retomada pelo UUID reservado**. Após uma interrupção, o titular pode entrar com a senha escolhida. O serviço verifica o hash antes de retomar, reconhece um evento já gravado e só entrega a identidade ativa depois de confirmar as duas persistências. Se a primeira gravação nunca ocorreu, o formulário aceita uma nova tentativa. Uma conta pendente não inicia sessão nem pode ser usada como identidade vinculada.

## Composição e recurso gráfico

A tela institucional ocupa 58% da largura, e a região de autenticação, 42%. Os campos têm até 416 px de largura. O fundo usa o WebP local de 1536 × 1024 px e 244.298 bytes em `web/static/images/estacionamento.webp`. O enquadramento preserva a proporção. Cada tema aplica sua própria sobreposição. A fotografia é decorativa e o texto permanece no HTML.

**Origem da imagem.** Imagem sintética original criada com ImageGen a pedido do responsável, para incorporação ao MOVE. O pedido autorizou a geração e o uso neste projeto. A fonte é a geração direta, sem fotografia de acervo de terceiros. A exportação local em WebP usou qualidade 83.

**Prompt de geração.** “Crie uma única fotografia arquitetônica fotorrealista para o fundo do login desktop do MOVE. Paisagem horizontal 3:2. Vista elevada oblíqua de um estacionamento moderno de concreto, com vagas paralelas bem demarcadas, poucos carros grafite e prata, linhas amarelas de circulação e luz lateral natural. Componha a imagem com as vagas e carros mais reconhecíveis na metade superior e ao centro, deixando o primeiro plano de asfalto mais calmo. Estética editorial sóbria, nitidez e textura reais. Sem pessoas, textos, logos, marcas-d’água ou interface.”

Login e cadastro compartilham o painel institucional a partir de 70 rem de largura da viewport (1120 px CSS com fonte inicial de 16 px). A grade mantém 58% para a apresentação e 42% para o formulário. Janelas menores exibem o cartão compacto. A fotografia só é solicitada quando o painel é exibido.

No Lenovo TB390FU com Android 16, o acadêmico verificou o login amplo em paisagem após remover as condições de hover e ponteiro na cópia do Termux. No repositório, o Chrome reproduziu a diferença a 1280 × 800 antes da correção. A regra oficial agora usa somente a largura, inclusive com toque, janela dividida ou mouse conectado. O registro físico se refere ao login experimental.

O ensaio atualizado em `tests/navegador_cadastro.py` passou no Chrome 158 do Ubuntu em dez perfis com mouse e doze com toque emulado, nos dois temas. Login e cadastro exibiram o cartão compacto a 1119 px e a grade 58/42 a 1120 e 1121 px. O teste conferiu a largura do formulário, o carregamento local da foto e a ausência de rolagem horizontal. A regra de hover do cabeçalho afeta somente a cor do seletor. Nos portais e na impressão, as demais regras de layout usam largura ou meio de saída.

## Verificação visual original da 10A.4

A matriz usa a página Flask renderizada no Chrome 158.0.8127.36 no Ubuntu. As dimensões são da **área de conteúdo em pixels CSS**, com fator de escala 1 nas capturas de referência. O zoom foi alterado no próprio navegador, em um perfil temporário. As dimensões físicas do monitor e os dispositivos móveis físicos ficaram fora deste ensaio.

| ID | Critério | Resultado observado |
|---|---|---|
| CV-01 | Identidade | Marca B em SVG, Inter, Lucide, grafite e amarelo do projeto. |
| CV-02 | Linguagem desktop | Foto e apresentação à esquerda, formulário independente à direita. |
| CV-03 | Fotografia | WebP local inspecionado, sem textos promocionais ou marca-d’água visível. |
| CV-04 | Enquadramento | Carros, demarcações e arquitetura reconhecíveis nas amostras de 1280 a 3440 px. |
| CV-05 | Composição | Divisão de 58/42 verificada pelas caixas renderizadas. |
| CV-06 | Espaço | A fotografia ocupa a altura disponível. O formulário preserva a largura de leitura nos monitores maiores. |
| CV-07 | Hierarquia | Marca no topo do painel, título de entrada e ação amarela visíveis na abertura do login. |
| CV-08 | Formulário | Campos alinhados, rótulos persistentes e controles de envio com pelo menos 48 px no desktop. |
| CV-09 | Informação institucional | A descrição e os três destaques correspondem às operações do MOVE. |
| CV-10 | Aparência | Controle único no topo. A lista abre na faixa superior do desktop. Seleção por teclado e toque verificada. |
| CV-11 | Tema claro | Na amostra, subtítulo sobre a superfície branca com contraste 7,58:1. |
| CV-12 | Tema escuro | Texto secundário sobre grafite com contraste 9,89:1. A fotografia mantém sua cor. |
| CV-13 | Legibilidade | Menor contraste do título grande sobre a fotografia de 5,61:1. O parágrafo institucional atingiu no mínimo 14,26:1. |
| CV-14 | Consistência | Rótulos, alertas, campos, controle de senha e botão reutilizam os componentes compartilhados. |
| CV-15 | Responsividade | Sete viewports desktop e seis de toque, cada um nos dois temas, para login e cadastro. |
| CV-16 | Integridade | Inspeção de imagens e caixas de layout, inclusive com erro, menu aberto e formulário preenchido. O cadastro longo permite rolagem vertical. |
| CV-17 | Acessibilidade | Rótulos associados, foco de teclado e erro anunciado. O anel de foco mediu 6,70:1 no claro e 8,14:1 no escuro. A borda do campo mediu 4,76:1 e 5,72:1. |
| CV-18 | Desempenho visual | As caixas do painel, títulos, formulário e botão conservaram posição e tamanho quando o navegador recebeu a imagem após o HTML. |
| CV-19 | Smartphone | Cartão compacto em 320 e 390 px e em paisagem. A versão atual acrescenta a chamada de cadastro e ajusta o subtítulo. |
| CV-20 | Tablet | Cartão compacto em retrato e paisagem, inclusive a 1366 px de largura com toque. |
| CV-21 | Autonomia | Todas as requisições observadas vieram do servidor local. As configurações compactas dispensaram a fotografia. |
| CV-22 | Qualidade percebida | A composição permite reconhecer o estacionamento e localizar a ação principal. Juízo preliminar sujeito ao aceite do responsável. |

O contraste foi medido sobre o fundo renderizado, ocultando somente o primeiro plano dos textos e mantendo suas caixas. As medições de borda e foco utilizaram pixels das capturas com o campo em foco. Esses resultados cobrem os critérios avaliados por amostragem. A referência é a [WCAG 2.2](https://www.w3.org/TR/WCAG22/).

### Autoavaliação preliminar

| Dimensão | Peso | Nota |
|---|---:|---:|
| Composição | 20% | 8,6 |
| Identidade | 15% | 9,3 |
| Aparência de site desktop | 15% | 8,6 |
| Integração da fotografia | 10% | 8,5 |
| Hierarquia | 10% | 9,0 |
| Legibilidade e contraste | 10% | 9,2 |
| Responsividade | 10% | 9,0 |
| Consistência entre temas | 5% | 8,8 |
| Refinamento dos componentes | 5% | 8,4 |

**Resultado ponderado de 8,84/10.** A largura do formulário favorece a leitura no ultrawide e deixa margens amplas nessa configuração.

O responsável pelo projeto concedeu o aceite visual no encerramento da Etapa 10A.4. No cabeçalho aprovado, o seletor mostra o ambiente ativo em texto secundário junto à marca MOVE, com uma seta discreta e área de toque de 44 px.

## Reprodução dos ensaios

Na raiz, use o Python do ambiente de execução para a suíte. Para os ensaios de navegador, use o ambiente de testes com Playwright e indique o executável do Chrome instalado.

```sh
python -B -m unittest discover -s tests -v
python -B -m tests.navegador_cadastro --chrome /caminho/para/chrome --capturas /destino/fora/do/projeto
```

A suíte de cadastro usa arquivos temporários e simula falhas antes e depois de cada uma das três escritas. Inclui autenticação após reabertura, preservação de homônimos, concorrência, CSRF, reenvio e campos de privilégio indevidos. O ensaio de navegador percorre criação, validação, primeiro login e tentativa de acesso à Gestão. Os ensaios existentes 08A, UI 10A.4.1 e Master Demo cobrem as contas anteriores e a alternância. O cenário de prévia e as capturas desta avaliação ficam fora do projeto.
