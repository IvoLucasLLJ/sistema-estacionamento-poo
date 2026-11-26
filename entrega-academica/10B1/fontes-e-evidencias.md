# Inventário de fontes e evidências

## Versão examinada

Branch `trabalho-final`. Checkpoint [`fa323dca437853cdd6cd64c1f1c682298dd88ecb`](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/commit/fa323dca437853cdd6cd64c1f1c682298dd88ecb). Consulta em 25 de novembro de 2026. O histórico Git local, o objeto da revisão, o relatório da campanha e o resultado remoto foram conferidos. A documentação acadêmica desta pasta foi produzida posteriormente à revisão do software.

A matriz de atendimento aponta métodos e linhas. Este inventário indica o tipo de evidência que cada fonte oferece. As linhas dos permalinks correspondem ao conteúdo no SHA acima. A ampliação de clientes consta da orientação relatada pelo acadêmico. O Git comprova sua implementação e a data, mas não contém uma transcrição da aula.

## Requisitos e documentação

| Fonte no checkpoint | Contribuição |
|---|---|
| [_Enunciado/enunciado.txt](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/_Enunciado/enunciado.txt) | Lista obrigatória, dois desafios e instrução sobre o terminal. |
| [_Enunciado/regrasDeNegocio.txt](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/_Enunciado/regrasDeNegocio.txt) | Tarifas, ocupação unitária, exceção e campos mínimos do histórico. |
| [_Enunciado/casosDeUso.txt](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/_Enunciado/casosDeUso.txt) | Quatro interações do exercício original. |
| [_Enunciado/diagramaDeClasses](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/_Enunciado/diagramaDeClasses) | Esboço didático anterior à implementação e referência de comparação com o núcleo atual. |
| [README.md](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/README.md) | Propósito do exercício e ponto de entrada histórico. |
| [docs/web-08a.md](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/docs/web-08a.md) | Infraestrutura Flask, responsabilidades de apresentação e acesso. |
| [docs/web-08b.md](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/docs/web-08b.md) | Gestão, revisão financeira e IDs de estadia. |
| [docs/web-08c.md](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/docs/web-08c.md) | Projeção pessoal e integração dos portais. |
| [docs/qualidade-09.md](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/docs/qualidade-09.md) | Regressões de reconstrução temporal e liberação de vaga. |
| [docs/compatibilidade-10a1.md](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/docs/compatibilidade-10a1.md) | Ambientes investigados e evolução das verificações. |
| [docs/inicializacao-10a2.md](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/docs/inicializacao-10a2.md) | Ambiente demonstrativo, quatro inicializadores e processo de execução. |
| [docs/android-termux.md](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/docs/android-termux.md) | ABI, diretório privado do Termux e limites da validação física. |
| [docs/acesso-web-10a4.md](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/docs/acesso-web-10a4.md) | Controle de aparência, Master Demo, seleção de ambiente e cadastro público. |
| [docs/qualidade-10a5.md](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/docs/qualidade-10a5.md) | Campanha, três correções, resultados e limites de inferência. |

## Modelo e coordenação

| Fonte no checkpoint | Contribuição |
|---|---|
| [model/veiculo.py](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/model/veiculo.py) | Contrato abstrato e normalização de placa. |
| [model/carro.py](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/model/carro.py) | Tarifa horária do carro. |
| [model/moto.py](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/model/moto.py) | Tarifa horária da moto. |
| [model/caminhao.py](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/model/caminhao.py) | Tarifa horária do caminhão. |
| [model/cliente.py](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/model/cliente.py) | Identidade, nome e contrato comercial abstrato. |
| [model/cliente_comum.py](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/model/cliente_comum.py) | Cobrança integral. |
| [model/cliente_vip.py](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/model/cliente_vip.py) | Metade da base validada. |
| [model/cliente_mensalista.py](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/model/cliente_mensalista.py) | Isenção por utilização. |
| [model/categorias_cliente.py](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/model/categorias_cliente.py) | Recuperação da classe a partir da categoria registrada. |
| [model/vaga.py](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/model/vaga.py) | Referência do veículo e guarda de ocupação e liberação. |
| [model/estadia.py](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/model/estadia.py) | Despacho nas duas hierarquias, arredondamento, cobrança congelada e guarda de saída. |
| [model/estacionamento.py](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/model/estacionamento.py) | Composição das vagas, associação, eventos e reconstrução. |
| [controller/controller.py](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/controller/controller.py) | Seleção dos tipos concretos e coordenação do modelo. |
| [repository/estacionamento_repository.py](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/repository/estacionamento_repository.py) | Leitura, salvamento e controle de versão do histórico. |
| [persistence/historico_json.py](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/persistence/historico_json.py) | Leitura e escrita da unidade de persistência. |
| [persistence/exclusividade.py](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/persistence/exclusividade.py) | Coordenação entre processos. |
| [service/estacionamento_service.py](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/service/estacionamento_service.py) | Limite do caso de uso, contratos públicos e tratamento do resultado da escrita. |
| [main.py](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/main.py) | Entrada da interface de texto. |
| [view/ui_texto.py](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/view/ui_texto.py) | Casos de uso do menu. |
| [view/formatacao.py](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/view/formatacao.py) | Apresentação monetária compartilhada. |

## Aplicação e distribuição

| Fonte no checkpoint | Contribuição |
|---|---|
| [web/__init__.py](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/web/__init__.py) | Fábrica Flask e composição dos serviços. |
| [web/contas.py](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/web/contas.py) | Identidades, repositório de contas, autenticação e autocadastro. |
| [web/sessoes.py](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/web/sessoes.py) | Registro de gerações ativas. |
| [web/revisoes.py](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/web/revisoes.py) | Revisão transitória de formulário. |
| [web/seguranca.py](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/web/seguranca.py) | Admissão, titularidade e troca de contexto. |
| [web/gestao.py](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/web/gestao.py) | Operações administrativas. |
| [web/consultas_pessoais.py](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/web/consultas_pessoais.py) | Projeções filtradas pelo titular da entrada. |
| [web/apresentacao.py](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/web/apresentacao.py) | Modelo de ocupação e formatação web. |
| [web/static/js/controles.js](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/web/static/js/controles.js) | Classes JavaScript e interação de apresentação. |
| [iniciar_move.py](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/iniciar_move.py) | Preparação compartilhada por plataforma. |
| [.github/workflows/compatibilidade.yml](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/.github/workflows/compatibilidade.yml) | Matriz declarada, permissões e etapas do ensaio. |

## Ensaios e resultados

| Fonte no checkpoint | Contribuição |
|---|---|
| [tests/cenario_gestao.py](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/tests/cenario_gestao.py) | Fixture da estadia 22 e da receita legada. |
| [tests/ensaio_pacote.py](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/tests/ensaio_pacote.py) | Procedimento para instalação e reabertura da distribuição. |
| [qa/evidencias/inventario.csv](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/qa/evidencias/inventario.csv) | 193 métodos distintos, classificados por finalidade e risco. |
| [qa/evidencias/execucoes.json](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/qa/evidencias/execucoes.json) | Versões locais e duração da suíte. |
| [qa/evidencias/cobertura.json](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/qa/evidencias/cobertura.json) | Denominadores e medição de código Python próprio. |
| [qa/evidencias/mutacao.json](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/qa/evidencias/mutacao.json) | Mutantes selecionados, resultado e testes que os detectam. |
| [qa/evidencias/estados.json](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/qa/evidencias/estados.json) | Sementes e transições do modelo de referência. |
| [qa/evidencias/navegadores.json](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/qa/evidencias/navegadores.json) | Motores, acessibilidade e hashes das comparações visuais. |
| [qa/evidencias/desempenho.json](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/qa/evidencias/desempenho.json) | Volumetria e medições em ambiente controlado. |
| [qa/evidencias/perfis.csv](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/qa/evidencias/perfis.csv) | Matriz de autorização por perfil e rota. |

## Resultados remotos e design

A [execução 45726276531](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/actions/runs/45726276531) registra sucesso e o SHA documentado. Há dez trabalhos de compatibilidade. Cada um combina um dos cinco sistemas/arquiteturas com Python 3.12 ou 3.14. A suíte e o ensaio de extração, provisionamento, autenticação, persistência e nova abertura pertencem a essa evidência. A execução de navegador em macOS é um recorte adicional dos trabalhos com Python 3.12.

| Executor | Python 3.12 | Python 3.14 |
|---|---|---|
| Ubuntu x64 | [Aprovado](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/actions/runs/45726276531/job/139596830907) | [Aprovado](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/actions/runs/45726276531/job/139596831146) |
| Ubuntu ARM64 | [Aprovado](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/actions/runs/45726276531/job/139596830630) | [Aprovado](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/actions/runs/45726276531/job/139596831160) |
| Windows Server 2025 x64 | [Aprovado](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/actions/runs/45726276531/job/139596831093) | [Aprovado](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/actions/runs/45726276531/job/139596831049) |
| macOS Intel | [Aprovado](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/actions/runs/45726276531/job/139596830922) | [Aprovado](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/actions/runs/45726276531/job/139596830914) |
| macOS Apple Silicon | [Aprovado](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/actions/runs/45726276531/job/139596831110) | [Aprovado](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/actions/runs/45726276531/job/139596831002) |

O [arquivo de design](https://www.figma.com/design/oamoaxU0OJRHHKcuLIlFOi) e o [quadro 07E de referência para a implementação](https://www.figma.com/design/oamoaxU0OJRHHKcuLIlFOi?node-id=55-7672) documentam as escolhas visuais. Os quantitativos históricos de 27 modelos, 131 configurações, 366 frames, 58 componentes, 269 variantes e 182 variáveis descrevem o processo visual. O cadastro público pertence à extensão 10A.4. A avaliação da versão executada usa as capturas da campanha.

## Integridade das figuras de execução

As duas imagens PNG foram recuperadas da campanha local em ambiente fictício e comparadas ao registro versionado de SHA-256. O dashboard usa a chave de imagem de comparação do ensaio 08B. O corte físico completo da página foi preservado.

- [08b-1440-dashboard.png](evidencias/08b-1440-dashboard.png) · SHA-256 `c61d240c9e15c2174dc4e757c4438c8fc03835fc5da6a7baf9f138307f69092e`.

- [login-1366x768-claro.png](evidencias/login-1366x768-claro.png) · SHA-256 `c882ca9734ae4bbcf4a1fb12ee94201be7a6384d2c2a580b1a52f49be248aba9`.

## Linhagem do checkpoint

Datas de autoria e identificadores do histórico Git. Os marcos de design e o aceite visual têm evidências próprias no quadro 07E e nos registros de etapa.

| Data | Commit | Assunto registrado |
|---|---|---|
| 2026-09-23 | [`f2880670`](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/commit/f28806704c734c31b2ba359cdf8eec962d6c245a) | Versao inicial do sistema de estacionamento |
| 2026-09-24 | [`e611be27`](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/commit/e611be2756bff80720de519b2464bd0f0e47a214) | Evolui sistema de estacionamento com MVC, validacoes e testes |
| 2026-10-08 | [`0c61b763`](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/commit/0c61b76351b1769928e31edbffbb7eb5ab85b991) | Evolui MOVE com cadastro, encapsulamento e persistencia |
| 2026-10-08 | [`040792d0`](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/commit/040792d08c60e823345e2b5e12a79904328efc61) | Evolui MOVE v3 com Repository da Aula 09 |
| 2026-11-24 | [`69bf82ee`](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/commit/69bf82eed684c31fa7eae662fab2564d50f7e900) | Implementa hierarquia polimorfica de clientes e fortalece testes |
| 2026-11-24 | [`75cb24f8`](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/commit/75cb24f87bb351becf2d85881ef4b9a94547df6f) | Implementa cadastro persistente de clientes com UUID |
| 2026-11-24 | [`355cfac7`](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/commit/355cfac7728a26fbe56ec3a6c44ad7eb7479a5a9) | Integra clientes, estadias, cobranca polimorfica e pagamentos |
| 2026-11-24 | [`536c46b4`](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/commit/536c46b4188e8ba3a6d3252ee771ec8937df6d0e) | Implementa camada de servico com concorrencia e persistencia imediata |
| 2026-11-24 | [`b77bda8b`](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/commit/b77bda8b6d177342f02b60f086732f87fb75cfd2) | feat: implementa infraestrutura web e controle de acesso do MOVE |
| 2026-11-24 | [`e4c4040f`](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/commit/e4c4040fa4bcfce7895c4d93715c0a5188d764ed) | feat: implementa operacoes administrativas do MOVE |
| 2026-11-24 | [`acccf1bf`](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/commit/acccf1bf7d66a580fa10a2042977031c02c93b2b) | feat: implementa portal pessoal e integracao gestao-cliente |
| 2026-11-24 | [`b110899e`](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/commit/b110899e45a1be46562e2a323078913aeb1838b9) | fix: estabiliza persistencia e valida qualidade do MOVE |
| 2026-11-24 | [`0cbd2d78`](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/commit/0cbd2d784232961c144dd8b318ab8dc97b0964bb) | chore: prepara compatibilidade multiplataforma do MOVE |
| 2026-11-25 | [`33ef6527`](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/commit/33ef6527be96b15c9bbc6ed8e7827887ced2f38e) | feat: amplia compatibilidade multiplataforma e inicializacao do MOVE |
| 2026-11-25 | [`a49011ac`](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/commit/a49011ac600dfaed6cb3843284094781962e64dc) | fix: verifica a venv em um novo processo apos instalar pywin32 |
| 2026-11-25 | [`a47e063e`](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/commit/a47e063ed76c5ef72d56832f75562d310b8cdcc2) | test: valida arquivos extraidos e navegadores nas duas arquiteturas Mac |
| 2026-11-25 | [`b62ddb2b`](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/commit/b62ddb2ba2e2029ca9e436c36455b42abfdcbe5b) | fix: preserva leitores abertos durante a substituicao atomica em NTFS |
| 2026-11-25 | [`a4a74c94`](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/commit/a4a74c9466de9383931b5c398c95f24ed82418ea) | fix: usa nome relativo na troca NTFS e sincroniza ensaios de navegador |
| 2026-11-25 | [`55cc3be8`](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/commit/55cc3be8f9ca97a2b414d11c8a9ee62a47271a49) | fix: conclui o caminho UTF-16 e exercita a reabertura pelos inicializadores |
| 2026-11-25 | [`6d660354`](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/commit/6d66035403f856b8c977e88fd38774c66b78d924) | docs: registra a validacao multiplataforma e o aceite do pacote MOVE |
| 2026-11-25 | [`1f83d068`](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/commit/1f83d0680c855fa3d1087c8404c0194b87f7bf0c) | feat: consolida UX/UI, cadastro publico e Master Demo do MOVE |
| 2026-11-25 | [`fa323dca`](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/commit/fa323dca437853cdd6cd64c1f1c682298dd88ecb) | test: consolida campanha intensiva de qualidade e corrige defeitos do MOVE |

## Bibliografia externa

As referências bibliográficas e técnicas estão discriminadas na última página do [relatório](MOVE_Relatorio_Tecnico.pdf) e em sua [fonte pesquisável](MOVE_Relatorio_Tecnico.md#secao-referencias). As fontes da aplicação e do processo de desenvolvimento são primárias para este estudo de caso.
