# Aplicação web local do MOVE · Etapa 08A

## Execução e provisionamento

O [README](../README.md) contém os comandos de instalação na `.venv`, criação do primeiro gestor e inicialização. O servidor escuta em `127.0.0.1:5000`, em um processo com threads, debug e recarga desativados. Use Ctrl+C para liberar o histórico. As contas são provisionadas por quem tem acesso local autorizado ao terminal.

Para uma conta pessoal, use um **cliente já cadastrado no mesmo histórico**. Com a `.venv` ativa, execute na raiz do projeto:

```bash
read -r -p 'UUID cadastral do cliente: ' cliente_move
python -m flask --app web criar-conta --papel cliente --usuario cliente.local --cliente-id "$cliente_move"
```

A senha é solicitada em prompt oculto com confirmação, tem de 12 a 256 caracteres e não é argumento de linha de comando. O operador consulta o UUID no cadastro confiável. O nome de usuário aceita até 64 letras ASCII, números, pontos, hífens e sublinhados e é normalizado para minúsculas. Há uma conta por nome de usuário e no máximo uma conta pessoal por cliente. A Gestão pode ter vários usuários individuais. A conta de Gestão não recebe UUID de cliente. Um histórico novo aceita a primeira conta administrativa e mostra as dez vagas livres. O provisionamento pessoal precisa de cadastro prévio pelo serviço do MOVE.

### Configuração

| Opção | Padrão e finalidade |
|---|---|
| `MOVE_HISTORICO` | `historico.json` na raiz do MOVE. A pasta precisa existir. O serviço lê o histórico novamente a cada operação. |
| `MOVE_DADOS` | Diretório privado `instance/` na raiz. Também pode ser uma pasta externa, separada por ambiente. |
| `MOVE_CONTAS` | `contas.json` na pasta privada. O diretório do arquivo deve existir. |
| `MOVE_SECRET_KEY` | Opcional. Na ausência, a fábrica gera 32 bytes aleatórios em `sessao.key`, com permissão 0600 e publicação atômica. Uma chave fornecida deve conter pelo menos 32 bytes de entropia adequada. |
| `MOVE_HTTPS` | `0` para HTTP local. O valor `1` marca o cookie como Secure para um transporte HTTPS configurado separadamente. |
| `DURACAO_SESSAO` | Configuração da fábrica, 1.800 segundos a partir do login. O prazo é absoluto. |

Use arquivos privados distintos, em diretórios de acesso restrito. Faça backup de contas e dados operacionais em conjunto. A substituição da chave invalida todos os cookies assinados anteriormente. O JSON de contas contém identificadores, papel, vínculo pessoal e hashes scrypt com salt individual. O arquivo é publicado com permissão 0600. Uma falha de validação ou gravação é informada ao operador. Os arquivos reais de contas, chaves, histórico e ambientes virtuais ficam fora do versionamento.

## Componentes e responsabilidades

O caminho de uma leitura começa no Blueprint, passa pela autorização e chega ao `EstacionamentoService`. Este usa o Controller, o Repository e o domínio existentes. A rota entrega ao Jinja os dados autorizados e os objetos de apresentação. O fluxo financeiro mantém as responsabilidades das hierarquias de veículos e clientes. A fábrica compõe uma instância do serviço de autenticação com um repositório de contas e o serviço de estacionamento. [Fábrica](../web/__init__.py#L16) · [Serviço do estacionamento](../service/estacionamento_service.py#L35)

| Conceito e aplicação | Objeto, atributos e comportamento | Justificativa e evidência |
|---|---|---|
| Identidade e composição | Uma `ContaUsuario` contém uma `Identidade` imutável e o hash. `PapelAcesso` identifica Gestão ou Cliente. `do_registro` valida a representação e `registro` a serializa. | A sessão e os templates podem consumir a identidade sem receber o hash. O papel tem ciclo de vida próprio em relação à categoria do cliente. [Classes](../web/contas.py#L15) · [Teste de recuperação](../tests/test_web.py#L47) |
| Encapsulamento da persistência | Uma instância de `ContaRepository` conhece seu caminho e coordena `adicionar`, `por_id` e `por_usuario`. A leitura valida estrutura e unicidade. O bloqueio cobre a releitura e a troca atômica do arquivo. | Duas tentativas simultâneas de provisionar o mesmo nome produzem uma única conta. Um arquivo inválido é preservado. [Classe](../web/contas.py#L61) · [Testes de concorrência e falha](../tests/test_web.py#L190) |
| Abstração e composição de serviços | `AutenticacaoService` recebe os objetos de persistência e de estacionamento pelo construtor. `provisionar` valida o vínculo e cria o hash. `autenticar` verifica a senha e devolve a identidade. | A mesma classe trata as três categorias comerciais. Usuário inexistente também passa pela verificação de um hash auxiliar. [Classe](../web/contas.py#L103) · [Teste de login inválido](../tests/test_web.py#L93) |
| ViewModel imutável | `OcupacaoViewModel.da_consulta` constrói um objeto com `livres`, `ocupadas` e `total`. A propriedade `percentual` organiza o valor visual. As funções `dinheiro`, `centavos` e `horario` formatam dados já calculados. | O indicador é compartilhado pelos dois portais. O serviço conserva o faturamento legado exato de `40.005` reais. Desde a 09, a View mostra R$ 40,01 e apresenta 613 centavos como R$ 6,13. [Apresentação](../web/apresentacao.py#L6) · [Teste unitário](../tests/test_web.py#L170) |
| Encapsulamento da reserva de execução | O objeto `EscritorLocal` mantém o descritor e a trava interna. `abrir` reserva o caminho real com flock. `fechar` libera o descritor. | Terminal e servidor do MOVE cooperam inclusive entre processos. O arquivo auxiliar de bloqueio permanece no disco. Apagá-lo durante uma execução invalidaria a coordenação. [Classe](../persistence/exclusividade.py#L11) · [Teste com subprocesso](../tests/test_web.py#L204) |
| Estado e comportamento no navegador | Uma instância de `ControleTema` guarda a preferência e a consulta de mídia em campos privados. `conectar` associa os controles. Cada formulário cria um `ControleSubmissao` com estado privado de envio. | O tema acompanha o sistema e a navegação. A segunda submissão durante o envio é cancelada no navegador. O servidor continua responsável por CSRF, autorização e consistência. [Classes JavaScript](../web/static/js/controles.js#L3) · [Percurso de navegador](../tests/navegador_08a.py#L36) |

### Contratos HTTP e reutilização visual

| Entrada | Controle e dados entregues |
|---|---|
| `GET /entrar`, `POST /entrar` · S01 | Formulário de credenciais com CSRF. Ao autenticar, a sessão anterior é limpa. O servidor escolhe um destino interno pelo papel. Credenciais inválidas recebem resposta uniforme. |
| `POST /sair` | Exige sessão e CSRF, limpa a sessão corrente e volta ao login. |
| `GET /gestao/` · G01 inicial | Gestão. Consulta ocupação, vagas, faturamento de saídas concluídas e quantidade de pagamentos confirmados em aberto. Uma falha no bloco financeiro pode coexistir com uma leitura válida das vagas. |
| `GET /cliente/` · C01 inicial | Cliente. Revalida o cadastro associado à conta, consulta sua frota e filtra as estadias por UUID da entrada antes da renderização. A disponibilidade só recebe contagens agregadas. |
| `GET /cliente/estadias/<int:estadia_id>` | Seleciona uma utilização no C01. A guarda consulta a estadia e compara o titular histórico com a identidade autenticada. Inexistência e titularidade de terceiro têm a mesma mensagem e status 404. |
| Estados compartilhados | S02 devolve 403 para papel incorreto. S03 devolve 401 para sessão expirada reconhecida. S04 devolve 404 para recurso indisponível. S05 devolve 503 para falhas de infraestrutura. Um conflito recebe 409 e uma rejeição de negócio recebe 422. Resultado incerto oferece consulta sem repetir a escrita. |

A autorização ocorre em cada requisição protegida. O servidor relê a conta pelo ID assinado antes de verificar o papel. O vínculo pessoal vem da conta. Uma placa ou um UUID recebidos pela URL não concedem acesso. A guarda de titularidade e a projeção de estadias respeitam o evento de entrada, inclusive se houver ocupação legada sem titular. O serviço devolve DTOs simples e a apresentação não abre o arquivo operacional. [Guardas](../web/seguranca.py#L54) · [Rotas](../web/rotas.py) · [DTOs do serviço](../service/representacoes.py)

Os layouts Gestão, Cliente e compartilhado reutilizam o template-base. As macros Jinja2 implementam os botões A01/A02, campos F01/F03, seletor N07, mensagens M04/M09 e disponibilidade. O portal compartilha o cabeçalho N01, a navegação N02/N03 e o menu N06. A herança de templates e as macros são mecanismos de composição da View. As classes Python e JavaScript da tabela são as estruturas executáveis de POO desta etapa. [Templates](../web/templates/) · [Correspondência aprovada no Figma](https://www.figma.com/design/oamoaxU0OJRHHKcuLIlFOi?node-id=55-7672)

A assinatura e o monograma SVG são exportações vetoriais da marca B. O CSS usa tokens `--move-*` para cores, espaçamentos, tipografia, raios, foco, altura de controles e navegação. As consultas de mídia utilizam limites literais compatíveis com o grid Bootstrap. A casca muda a navegação em 768 e 992 px, a grade do painel em 1200 px e o refinamento compacto se aplica abaixo de 360 px. A preferência Sistema acompanha `prefers-color-scheme`. O navegador guarda somente `move.tema` em localStorage. [Marca B](https://www.figma.com/design/oamoaxU0OJRHHKcuLIlFOi?node-id=18-480) · [CSS](../web/static/css/move.css)

### Segurança e limites operacionais

- Flask assina o cookie de sessão. Seu conteúdo pode ser lido pelo portador. Ele contém o ID da conta, a expiração e o token CSRF. A renovação do token ocorre no login. Desde a 10A.5, o servidor registra o resumo da geração ativa em `sessoes.json` na pasta privada. A alternância substitui a geração, e o logout a encerra. Sessões anteriores à atualização exigem novo login. Outras sessões da mesma conta mantêm seu próprio prazo. Uma assinatura inválida ou já descartada pelo Flask exige novo login.
- Login e logout verificam o token de formulário em tempo constante. O cookie é HttpOnly e SameSite=Lax. As respostas usam no-store, política de conteúdo de mesma origem, bloqueio de incorporação em frames e proteção de tipo de conteúdo. O Jinja escapa os valores do cadastro. Erros públicos omitem detalhes de arquivos, hashes e exceções.
- Conflitos e resultados incertos têm respostas próprias. Quando uma estadia pessoal já foi autorizada na requisição, o link de recuperação preserva seu ID e passa novamente pela guarda. A 08A expõe somente consultas operacionais. As futuras escritas financeiras precisarão validar a expectativa e o ID originais com o serviço.
- Este executável destina-se ao uso acadêmico local em Ubuntu. A reserva cooperativa dos executáveis protege o histórico compartilhado. Scripts independentes que escrevam diretamente pelo serviço devem respeitar o mesmo regime. A proteção entre threads e a detecção de conflito do Repository continuam em vigor. Cada consulta do dashboard é uma leitura independente.
- Exposição pública exigiria uma decisão de implantação, HTTPS, servidor apropriado, política de limitação de tentativas, monitoramento e gestão de sessões. O projeto atual não oferece autenticação multifator, recuperação por e-mail, encerramento remoto de outras sessões ou integração de pagamento.

### Dependências e validação

O ambiente testado utiliza Python 3.14.4 em Ubuntu 26.04.1 LTS. O arquivo de requisitos fixa Flask, Werkzeug, Jinja2 e as dependências transitivas realmente utilizadas. Os recursos estáticos locais incluem Bootstrap Grid 5.3.8, Inter 4.1 e um subconjunto Lucide 0.468.0. As cópias das licenças acompanham os arquivos. A aplicação inicia sem acesso a CDNs. [Requisitos](../requirements.txt) · [Licenças locais](../web/static/vendor/) · [Controles de segurança do Flask](https://flask.palletsprojects.com/en/stable/web-security/)

```bash
source .venv/bin/activate
python -B -m unittest discover -s tests -v
git diff --check
git status --short
```

Os 78 testes anteriores cobrem domínio, Controller, serviço e histórico. Os testes da 08A acrescentam cobertura unitária, HTTP, CLI, persistência, concorrência e reserva entre processos. Todos usam persistência temporária.

O ensaio opcional de navegador usa Playwright para Python 1.64.1 e Chrome/Chromium. Ele inicia um servidor de teste em porta local livre, cria dois titulares fictícios pelo serviço, testa os dois papéis, os cinco modelos compartilhados, a submissão, os temas e as larguras de 320, 390, 768 e 1440 px. A senha é aleatória e dura somente durante a execução. A opção `--capturas` aceita uma pasta externa ao repositório. Com o Playwright disponível no ambiente de testes e Chrome instalado:

```bash
python -B -m tests.navegador_08a --chrome /usr/bin/google-chrome
```

O ensaio em Chromium verifica dimensões emuladas. Testes em aparelhos físicos, leitores de tela, impressão e a implantação pública permanecem fora desta validação.
