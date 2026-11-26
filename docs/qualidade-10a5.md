# MOVE · Campanha de qualidade 10A.5

## Resultado da campanha local

Em Ubuntu 26.04.1 x86-64, os **185 testes originais e oito novas regressões passaram**. A execução final de 193 métodos levou 57,371 s em CPython 3.14.4. Uma segunda instalação, CPython 3.13.18 em ambiente isolado, passou pelos mesmos 193 métodos em 52,915 s. Houve zero falhas e zero testes ignorados nessas execuções. Os métodos originais foram preservados. Os exercícios intensivos, os subcasos e as repetições ficam fora dessa contagem. [Inventário por arquivo, classe, método, requisito, técnica e risco](../qa/evidencias/inventario.csv) · [Resultados das execuções](../qa/evidencias/execucoes.json)

A campanha encontrou três defeitos no produto, corrigidos e revalidados localmente. O valor acumulado de saídas legadas podia divergir do relatório de período. O servidor carecia de uma verificação da geração de sessão após a troca de contexto. O nome acessível dos links das vagas divergia do texto visível. A campanha local qualificou a revisão para a matriz multiplataforma. A execução citada a seguir identifica o checkpoint da 10A.4 usado como linha de base. [CI da linha de base](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/actions/runs/45722379195)

## Ambiente, isolamento e método

- Repositório original em `trabalho-final`, inicialmente limpo. O HEAD local e remoto era `1f83d0680c855fa3d1087c8404c0194b87f7bf0c`. A verificação de integridade com `git fsck` passou. A referência local e remota da `main` era `040792d08c60e823345e2b5e12a79904328efc61`.
- O ponto de partida foi extraído com `git archive`. O candidato foi exercitado em outra cópia, com os arquivos de revisão. Cada ensaio criou suas próprias contas, chaves e históricos fictícios. Os servidores HTTP escutaram em loopback com portas independentes. O teste do inicializador utilizou uma terceira pasta, com espaço e acento no nome. A primeira suíte terminou em 66,777 s.
- Máquina com Intel Core i5-7200U, quatro processadores lógicos e aproximadamente 7,1 GiB de RAM. O Python 3.13.18 foi preparado somente na área de QA. As medições incluem o escalonamento do computador local.
- A campanha combinou oráculos independentes em Decimal, máquina de estados com sementes fixas, concorrência com barreiras e timeouts, interrupção real de processos filhos, injeção de falhas, testes HTTP, navegadores, mutação e análise estática.
- Ferramentas em venv separada: coverage.py 7.17.5, Ruff 0.17.6, Bandit 1.9.4, pip-audit 2.10.1, Playwright 1.64.1 e python-xlib 0.33. O axe-core 4.14.1 veio do pacote npm de distribuição, com SHA-512 verificado antes do uso. A aplicação continuou usando seus requisitos anteriores. [Requisitos opcionais da campanha](../requirements-qa.txt)

## Registro de defeitos e regressão

| ID e severidade | Requisito e evidência anterior | Correção e verificação |
|---|---|---|
| QA-01 · Alta · Financeiro | Duas retiradas legadas de carro, com 0,01 e 0,02 hora, geram eventos de 0,10 e 0,20 real. Na reabertura, o serviço devolvia `0.30000000000000004` e não conseguia representar o acumulado em centavos. O relatório do período dava `0.3`. O novo teste reproduziu a desigualdade no checkpoint. | O domínio soma as representações decimais dos valores registrados, reservando precisão para as casas originais e o transporte da soma. A rota antiga do terminal conserva o tipo numérico legado quando ele representa a soma na conversão pública. Os arquivos históricos conservam seus valores. O serviço devolveu 30 centavos, e P0–P2 continuou preservando os milésimos. [Domínio](../model/estacionamento.py#L251) · [Regressão](../tests/test_qualidade_10a5.py#L26) |
| QA-02 · Crítica · Contexto de acesso | A inspeção do checkpoint identificou que o contexto selecionado existia no cookie assinado. Trocar o portal descartava revisões pendentes, mas faltava autoridade no servidor para exigir a geração corrente da sessão. O primeiro teste do novo contrato encontrou ausência do registro (`KeyError: sessoes`). Essa evidência é estrutural. | O login registra o resumo da geração e sua expiração em `sessoes.json`, na pasta privada. Cada acesso autenticado consulta a geração. A troca substitui a anterior sob trava de arquivo. Logout ou perda do vínculo encerram a geração; outras sessões continuam independentes. A publicação usa o mecanismo atômico existente. O teste verifica duas trocas concorrentes, expiração e arquivo corrompido. A regressão de reinício confirma a continuidade das sessões válidas. [Registro privado](../web/sessoes.py#L10) · [Guarda](../web/seguranca.py) · [Regressões](../tests/test_qualidade_10a5.py#L41) |
| QA-03 · Média · Acessibilidade | O axe detectou `label-content-name-mismatch` em nove links do dashboard nos dois temas. A vaga identificada visualmente por “02” tinha “2” no nome acessível. O atributo substituía também o texto visível da placa. | A macro deriva o nome acessível do próprio conteúdo e reutiliza a classe de texto para leitores de tela para o prefixo “Vaga”. O ensaio 08B agora seleciona “Vaga 02 Ocupada AV1”. O axe voltou a executar os mesmos oito exames de página e tema e encontrou zero violações no recorte. Os PNGs do dashboard antes/depois da correção coincidiram em desktop e mobile. [Macro](../web/templates/components/gestao.html#L32) · [Ensaio de navegação](../tests/navegador_08b.py#L74) · [Resultados e hashes](../qa/evidencias/navegadores.json) |

**Intercorrências da campanha.** A primeira implementação de QA-01 passou pelo novo teste mas falhou em cinco subcasos existentes de horários legados, pois o retorno original era um float. A conversão compatível corrigiu a regressão sem trocar as expectativas dos testes. No ensaio adicional de navegador, o primeiro roteiro tentou navegar durante o redirecionamento da troca de portal. A espera pelo destino resolveu a corrida do roteiro. Para o zoom nativo, o Chrome foi direcionado explicitamente ao X11 privado do Xvfb. O WebKit precisou de bibliotecas de execução do Ubuntu extraídas numa pasta de QA. Essas ocorrências foram classificadas separadamente dos defeitos do MOVE.

**Efeito da atualização sobre as sessões.** As sessões emitidas antes da atualização precisam de um novo login. O arquivo de contas, seus hashes e o histórico de estacionamento preservam o formato. O registro privado guarda resumos e vencimentos, descarta os vencidos nas mutações e respeita a exclusividade entre processos. A revogação atua na admissão da próxima requisição. Uma operação já admitida antes da troca pode terminar. [Configuração e limites](web-08a.md)

## Domínio, fronteiras e propriedades

As oito regressões regulares cobrem o faturamento legado, a geração de sessão na alternância e no logout, a disputa e expiração de gerações, a retomada concorrente do autocadastro, o conflito de UUID na recuperação, a falha de fsync, as fronteiras do cálculo polimórfico e o erro do abridor do Android. [Novos testes](../tests/test_qualidade_10a5.py)

| Técnica | Amostra executada e critério |
|---|---|
| Matriz financeira | Três tipos de veículo × três categorias × nove durações, totalizando **81** cotações. O oráculo calcula base, desconto e centavos por constantes independentes, com arredondamento `ROUND_HALF_UP` apenas no total. Inclui zero, frações próximas da meia unidade de centavo, notação científica e grande quantidade de algarismos. A exibição mantém duas casas. A suíte anterior exercita sinal negativo, booleanos, NaN, infinito e limite numérico. |
| Máquina de estados | **840 passos**, 280 por semente (613, 22023, 20262). O modelo guarda titular, vaga, valor previsto, pagamento e ID. Confronta entradas, cotações, pagamentos, saídas, cancelamentos e reabertura com a ocupação, o faturamento e os bytes do histórico. A consulta ou recusa deixa o histórico intacto. Pagamento sem estadia, repetição e expectativa antiga são transições inválidas. |
| Partições e fuzz limitado | 240 textos gerados com a semente 613, aplicados a três normalizadores. Foram **720 verificações**, 19 aceitações canônicas e 701 recusas. Houve sete estruturas inválidas de histórico nesse ensaio, seis amostras adicionais de leitura inválida e **117 submissões/consultas** de formulários e filtros, com respostas verificadas. O domínio recebeu entradas sintéticas de tamanho limitado. |
| Combinações de uso | A matriz de leitura cruzou dez configurações de identidade/contexto com 23 destinos dos portais. Os ensaios de navegador combinaram temas, tamanhos e percursos. O teste financeiro usa produto cartesiano completo; as demais dimensões usam combinações de risco selecionadas, sem alegação de cobertura pairwise de todo o produto. |

[Contagem das transições e sementes](../qa/evidencias/estados.json) · [Modelo executável](../qa/estados.py) · [Formulários](../qa/formularios.py)

### Fixture financeira integrada

| Estado | Ocupadas / livres | Pagamentos aguardando saída | Faturamento interno | Exibição |
|---|---:|---:|---:|---:|
| P0 · cotação | 3 / 7 | 0 | 40.005 | R$ 40,01 |
| P1 · pagamento confirmado | 3 / 7 | 1 | 40.005 | R$ 40,01 |
| P2 · saída concluída | 2 / 8 | 0 | 46.135 | R$ 46,14 |

Para a estadia 22, Lia Vale, VIP, AV1 permaneceu na vaga 2 em P1. A cotação de 1,225 hora tem base de 12,250 reais, desconto exato de 6,125 e 613 centavos definitivos. O valor entrou uma vez no faturamento, na saída. AM2 continuou ativo e o comprovante pessoal consultou o titular original. As duas casas da interface são uma decisão de apresentação. O ensaio da Master Demo usa uma instalação fictícia própria e confirma outra estadia de 613 centavos após reabrir o arquivo. [Fixture P0](../tests/cenario_gestao.py) · [Integração pessoal](../tests/test_portal_cliente.py) · [Jornada Master](../tests/navegador_master_demo.py)

## Persistência, concorrência e recuperação

- As regressões anteriores exercitam terminal e servidor, segundo servidor, duas CLIs, travas independentes e liberação após morte de processo. A suíte também disputa duas vagas pelo mesmo veículo, dois veículos pela mesma vaga, pagamento e saída, leitura durante gravação e operações em arquivos distintos. [Serviço](../tests/test_service.py) · [Processos e arquivos](../tests/test_multiplataforma.py)
- No autocadastro, um processo filho foi encerrado com código conhecido antes e depois da reserva da conta, da gravação do cliente e da ativação. **As seis fronteiras passaram.** Cada caso reabriu os arquivos, verificou o estado intermediário e confirmou que a retomada legítima terminava com uma conta e um titular. Uma reserva conflitante permaneceu pendente com seus dados preservados. Duas autenticações concorrentes recuperaram a mesma identidade. O contrato é recuperação em três gravações, sem atomicidade global entre os dois JSONs. [Interrupções reais](../qa/estados.py) · [Falhas simuladas](../tests/test_cadastro_pessoal.py)
- Foram injetadas falhas de criação do temporário, escrita, flush, fsync e imediatamente antes/depois do replace. Antes da publicação, os bytes antigos permaneceram legíveis. Depois dela, o leitor encontrou a versão nova inteira. Os temporários foram removidos. A disputa pela mesma revisão produziu um único consumo, e expiração e capacidade foram verificadas. [Ensaio](../qa/persistencia.py) · [Resultados](../qa/evidencias/execucoes.json)
- A reconstrução histórica foi exercitada com eventos atuais, legados e mistos, identificadores, ordem inválida, centavos divergentes, JSON truncado e UTF-8 inválido. Os quatro métodos de horários legados passaram com `TZ=UTC`, `America/Sao_Paulo` e `Pacific/Kiritimati`. As comparações preservaram offsets e duração registrada. [Regressões de horários](../tests/test_horarios_legados.py)
- A recuperação de pagamento e saída usa o ID original após resposta perdida, nova estadia da mesma placa ou reinício com perda de revisão. A suite conferiu os bytes antes de permitir outro envio. Cortes físicos de energia, disco defeituoso e interrupções do kernel permanecem fora da evidência obtida.

## Autorização, privacidade e análise estática

Foram verificadas **230 respostas HTTP** em dez configurações e 23 destinos, incluindo visitante, sessão revogada no servidor, sessão expirada, conta pessoal, novo cliente, gestor exclusivo, gestor vinculado e ambos os contextos da Master Demo. Cada célula verificou status e `no-store`. O conjunto terminou com bytes históricos idênticos aos iniciais. Os testes específicos complementam essa matriz com POST, CSRF, revisões expiradas, pertencimento ao titular da entrada original, comprovantes de terceiros, contexto operacional da Master e recuperação do autocadastro. Um recurso pessoal indisponível e um de outro titular recebem a mesma resposta pública nos testes específicos. [Matriz por destino](../qa/evidencias/perfis.csv) · [Testes de contexto](../tests/test_contexto_acesso.py)

A avaliação de sessões usou inspeção da guarda, invariantes de gerações no servidor, navegação normal, expiração e logout. O registro não contém senhas nem o valor bruto dos tokens. Os testes anteriores de reinício passaram com a sessão válida e revisão perdida. A matriz é uma verificação defensiva local. Sua aprovação não certifica segurança para hospedagem pública.

O pip-audit consultou a base disponível para os sete pacotes de execução do Linux e separadamente para a versão fixada de pywin32. Foram encontrados **zero avisos conhecidos nessas versões consultadas**. A consulta do pacote Windows foi documental. Em 21 commits alcançáveis, a inspeção de diffs textuais não encontrou padrões selecionados de chave privada, tokens GitHub ou chave de acesso AWS. A inspeção de nomes rastreados também não identificou contas, históricos privados, chaves de sessão ou venv. A busca por padrões é limitada. [Resultados por pacote](../qa/evidencias/execucoes.json)

Ruff (`F,E9,B`) encontrou seis F401 e dois B904 no código do produto. Cinco importações verificam pré-requisitos, uma importação de `MASTER_DEMO` está sem uso em demonstração e dois levantamentos de exceção do inicializador podem explicitar a cadeia de causas. Bandit registrou 15 avisos baixos sobre subprocessos, execução do interpretador e resolução do comando de abertura do navegador. A inspeção encontrou chamadas locais com argumentos separados. O único B607 é a resolução de `open` pelo sistema no macOS. Nenhum dos avisos motivou troca de dependência ou reescrita. [Localização dos avisos](../qa/evidencias/execucoes.json)

## Navegadores, regressão visual e acessibilidade

Os seis ensaios existentes foram executados com Flask real e Google Chrome 158.0.8127.36. O roteiro 08A cobre autenticação e mensagens compartilhadas; 08B cobre os 14 modelos administrativos, consulta, confirmação, isenção, recuperação e impressão; 08C liga as consultas pessoais aos dados da Gestão. Os três roteiros da 10A.4 cobrem aparência, alternância, cadastro e Master Demo. A jornada Master percorreu cadastro de veículo, vínculo, entrada, consulta pelo titular, pagamento simulado, saída, comprovante, logout e reabertura dos dados, em 1440, 1024 e 390 px. Os cenários usam um servidor por fixture e consumidores independentes quando o requisito é comparar Gestão e Cliente.

| Motor no Ubuntu | Versão | Resultado |
|---|---|---|
| Google Chrome | 158.0.8127.36 | Seis roteiros, ensaio de zoom, axe e varredura de reflow aprovados |
| Chromium do Playwright | 156.0.8078.4 | Login, cadastro e passagem da Master pelos dois portais aprovados |
| Microsoft Edge | 158.0.4370.33 | Mesmo recorte aprovado |
| Firefox do Playwright | 157.0 | Mesmo recorte aprovado |
| WebKit MiniBrowser | 27.2 | Mesmo recorte aprovado com dependências extraídas localmente |

Cada motor percorreu 48 combinações de login/cadastro, tema e viewport, de 320 a 1920 px, incluindo 360, 430 e 600 px. Os roteiros do Chrome complementaram a verificação com toque emulado e orientações retrato e paisagem. O controle de tema acompanhou a preferência do sistema e preservou a seleção durante a navegação. O ensaio de zoom do Chrome usou atalhos nativos em Xvfb, mediu a duplicação de `devicePixelRatio` e verificou um viewport útil de 683 px a 200%, com login/cadastro nos dois temas e três destinos administrativos. [Ensaio de zoom](../qa/zoom.py) · [Matriz de motores e dimensões](../qa/evidencias/navegadores.json)

A comparação utilizou o mesmo Chrome, fontes locais e dimensões. Foram **55 PNGs idênticos byte a byte** para login, cadastro e estados de interação entre o checkpoint e o candidato. Outros dois PNGs confirmaram a igualdade do dashboard antes e depois do ajuste do nome acessível das vagas. O roteiro testou recursos da própria origem. A seleção de capturas para revisão ficou fora do repositório. Os hashes permitem conferir a correspondência sem incorporar as 57 imagens. [Hashes das comparações](../qa/evidencias/navegadores.json)

O axe foi aplicado a login, cadastro, dashboard e início pessoal em ambos os temas, com regras A e AA aplicáveis até WCAG 2.2. O resultado final foi zero violações detectadas nessas oito amostras. Os roteiros empregaram teclado, foco visível, acionamento de formulários, menu e alternância. O ensaio automatizado não substitui avaliação humana com leitor de tela, teste por voz, amostra integral de todas as páginas ou aprovação em dispositivo físico. [WCAG 2.2](https://www.w3.org/TR/WCAG22/) · [Antes e depois do axe](../qa/evidencias/navegadores.json)

## Cobertura e eficácia da suíte

| Recorte de Python próprio | Instruções executadas | Ramos executados |
|---|---:|---:|
| Checkpoint, suíte regular, processo principal | 2.132 / 2.469 · 86,35% | 533 / 716 · 74,44% |
| Candidato, suíte regular com coleta adicional nos subprocessos instrumentáveis | **2.195 / 2.521 · 87,07%** | **550 / 732 · 75,14%** |

As duas medições têm escopos de coleta diferentes. A diferença não representa, isoladamente, ganho de cobertura causado pelos novos testes. A coleta final deixou 326 instruções e 182 ramos sem execução registrada. O filtro de relatório inclui explicitamente as pastas Python próprias e os dois pontos de entrada. CSS, JavaScript, Jinja, bibliotecas de terceiros, scripts de QA e os próprios testes ficam fora desse denominador. Subprocessos com outro interpretador isolado ou encerramento abrupto podem não emitir dados do coverage. O relatório HTML local e o JSON completo identificam linhas e destinos de ramificações. [Resumo por módulo](../qa/evidencias/cobertura.json) · [Configuração](../qa/coverage.ini)

| Módulo crítico | Instruções | Ramos |
|---|---:|---:|
| Estadia e cobrança | 100,0% | 100,0% |
| Estacionamento | 96,9% | 90,0% |
| Serviço | 99,3% | 94,4% |
| JSON do histórico | 96,2% | 100,0% |
| Contas | 94,1% | 86,8% |
| Guardas | 95,9% | 92,5% |
| Registro de sessões | 90,0% | 80,0% |
| Exclusividade entre processos | 66,1% | 31,2% |
| Privacidade de arquivos | 20,0% | 15,4% |

O alvo de referência de 85% de instruções foi atingido no conjunto Python. Os caminhos de Windows nativo em ACL, substituição de arquivos e bloqueios explicam parte importante das lacunas nos dois últimos módulos. O inicializador compartilhado ficou em 35,6% de instruções; sua execução funcional em venv própria fornece evidência complementar, fora de parte da instrumentação. Certos ramos de erros do sistema operacional também ficaram pendentes. Executar o código em uma plataforma e medir uma linha são evidências distintas.

A campanha de mutação partiu de um controle positivo e executou cada mudança em uma cópia descartável. **19 de 19 mutantes aplicáveis foram detectados**; zero inválidos, equivalentes, sobreviventes finais ou timeouts. Na primeira seleção de métodos, a inversão da guarda de vaga sobreviveu ao teste de vínculo: aquele teste não ocupava a vaga. O teste preexistente de duplicidade, ocupação e reentrada detectou o mesmo mutante. O denominador não mudou. Foram exercitados os três preços, desconto, isenção, arredondamento, ocupação, vínculo, cobrança, faturamento, confirmação, titularidade, papel, Master, CSRF, revisão, expiração, ativação e exclusividade. Para controles de acesso também se usaram mutações restritivas que recusam fluxos legítimos. O índice descreve exclusivamente essas 19 alterações. [Operadores e método que detectou cada um](../qa/evidencias/mutacao.json) · [Executor](../qa/mutacao.py)

Quanto à qualidade dos testes, 20 casos críticos de cadastro, recuperação e regressão foram executados em três ordens determinadas pelas sementes 613, 1225 e 22023. As 60 execuções passaram. Os testes de disputa usam barreiras, os ensaios de navegador esperam respostas ou destinos, e os arquivos privados pertencem à fixture. As execuções repetidas aumentam a confiança nos cenários examinados; não estimam uma taxa global de intermitência.

## Desempenho, resistência e limites

Na rodada registrada, criar a Application Factory levou 118,897 ms. Em três instâncias novas, do início da fábrica à leitura completa de `/entrar` por HTTP, foram 159,403, 152,989 e 151,027 ms. Essa medição inclui a preparação da chave, a escuta local e a renderização, com os módulos Python já importados. O login com carregamento do dashboard teve mediana de 114,790 ms em oito acessos seriados. As medianas de consulta direta de ocupação, histórico e cotação da fixture foram 0,659, 0,723 e 0,670 ms. Esses números medem o servidor local e o custo de scrypt por login nas condições identificadas.

| Eventos fictícios válidos | Mediana de reconstrução e consulta | Pico de alocações Python na consulta |
|---:|---:|---:|
| 10 | 0,125 ms | 133.412 bytes |
| 100 | 0,723 ms | 143.831 bytes |
| 1.000 | 7,024 ms | 930.146 bytes |
| 5.000 | 36,500 ms | 4.585.498 bytes |

O ensaio de carga utilizou sessões autenticadas separadas, três páginas de leitura e uma rampa de **1, 2, 4, 8 e novamente 1** cliente. Foram 96 requisições com zero erros e histórico idêntico ao original. Com oito clientes, a mediana foi 45,469 ms, p95 de 67,380 ms, máximo de 85,688 ms e 166,92 requisições/s. Ao voltar a um cliente, a mediana foi 4,941 ms. A serialização do acesso e a reconstrução do agregado a cada operação têm custo observável. A rampa limitada não estabeleceu o ponto de saturação.

Na resistência, 40 ciclos completos de entrada, consulta e saída isenta preservaram faturamento, ocupação e reabertura. Foram observados quatro descritores de arquivo no início e no fim e zero temporários residuais. A memória residente do processo passou de 59.240 KiB no ciclo 10 para 59.460 KiB no ciclo 40, enquanto o histórico crescia legitimamente. Esse ensaio curto não comprova ausência de vazamento de longo prazo. Não foram definidos SLAs nem projetados limites de produção distribuída. [Médias, medianas, p95, máximos, throughput, CPU e memória](../qa/evidencias/desempenho.json)

## Rastreabilidade acadêmica e evidência de POO

| Origem e requisito | Classe, método e caso de uso | Tela ou entrada | Teste e resultado local |
|---|---|---|---|
| Enunciado · classes, abstração, herança e polimorfismo | `Veiculo.calcular_tarifa`; Carro, Moto e Caminhao executam o mesmo contrato com tarifas distintas | Terminal e G09 | Polimorfismo do núcleo e 81 cotações aprovados. [ABC](../model/veiculo.py#L29) · [Implementação concreta](../model/carro.py#L7) · [Oráculo](../tests/test_qualidade_10a5.py#L126) |
| Enunciado · objetos, encapsulamento, composição e exceções | Estacionamento compõe dez Vagas. `Vaga.ocupar` valida o objeto e `liberar` confere a estadia associada | Terminal, G02, G07 e G08 | Vaga inválida, lotação, reentrada e disputa aprovadas. [Vaga](../model/vaga.py#L24) · [Agregado](../model/estacionamento.py#L34) · [Testes](../tests/test_nucleo.py) |
| Enunciado · JSON e interface de texto | `Controller.salvar` delega ao Repository; a reconstrução restaura eventos e objetos | main.py, G12 | Falhas de gravação e terminal → reabertura web aprovadas. [Controller](../controller/controller.py#L96) · [Repository](../repository/estacionamento_repository.py#L18) · [Teste](../tests/test_horarios_legados.py#L29) |
| Extensão do trabalho final · hierarquia de clientes | `Estadia.consultar_cobranca` combina o veículo e o cliente. ClienteVIP aplica o desconto antes do arredondamento; Cobranca é imutável | G09–G11, G13 e C07 | Categorias, isenção, P0–P2 e reabertura aprovados. [Estadia](../model/estadia.py#L47) · [ClienteVIP](../model/cliente_vip.py#L7) · [Testes](../tests/test_estadias.py) |
| MOVE · serviço, concorrência e recuperação | `EstacionamentoService._executar` coordena uma leitura atual e a publicação. A revisão vincula a operação ao contexto | G03–G14, formulários, `/gestao/estadias/<id>/concluir` | Conflito, confirmação incerta e reinício aprovados. [Serviço](../service/estacionamento_service.py#L48) · [Revisoes](../web/revisoes.py#L36) · [Teste](../tests/test_reinicio_web.py) |
| MOVE · acesso, sessão e cadastro | ContaUsuario compõe Identidade. AutenticacaoService compõe repositório e serviço; SessoesAtivas mantém gerações no servidor | S01–S05, `/criar-conta`, `/ambiente`, `/sair` | Seis interrupções de cadastro, isolamento e troca concorrente aprovados. [Contas](../web/contas.py#L60) · [Cadastro](../web/contas.py#L202) · [Sessões](../web/sessoes.py#L35) |
| MOVE · associação histórica e apresentação | `ConsultasPessoais.ativas` projeta dados do titular. `OcupacaoViewModel.da_consulta` adapta os agregados para o template | C01–C08, `/cliente/estadias/<id>/comprovante` | Projeção, homônimos e comprovantes aprovados. [Consultas](../web/consultas_pessoais.py#L13) · [ViewModel](../web/apresentacao.py#L30) · [Testes](../tests/test_portal_cliente.py) |
| MOVE · interação web | ControleTema e ControleSubmissao encapsulam a preferência visual e o estado transitório de envio | `/entrar`, cadastro e cabeçalhos | Tema, teclado, toque e envio único nos ensaios reais. [Classes JS](../web/static/js/controles.js#L3) · [Teste](../tests/navegador_ui_10a4_1.py) |

O inventário individual complementa a matriz com arquivo, classe, método, linha, técnica, comportamento e risco. A medida de cobertura refere-se ao Python. A execução dos objetos JavaScript foi verificada no navegador. [Inventário completo](../qa/evidencias/inventario.csv)

## Compatibilidade e pendências

- **Validado localmente:** Ubuntu 26.04.1 x64, CPython 3.14.4 e 3.13.18. O inicializador Linux preparou a cópia independente, fez duas aberturas, três logins reais em cada uma e preservou histórico, contas e chave. As reaberturas do ensaio restringem o pip ao ambiente offline.
- **Preparado para CI:** a descoberta regular inclui os oito testes novos nas dez combinações de Ubuntu x64/ARM64, Windows Server x64 e macOS Intel/Apple Silicon, com Python 3.12 e 3.14. As referências de checkout e setup-python foram consultadas por SHA nos repositórios oficiais. A permissão continua sendo leitura de conteúdo. Nos dois jobs macOS/Python 3.12, o workflow agora executa também Master Demo, cadastro e troca/aparência. O workflow de publicação associa cada resultado ao SHA que o GitHub recebeu. [Workflow](../.github/workflows/compatibilidade.yml)
- **Simulado:** Termux, SDK, pasta interna, seleção de dependências nativas, instalador e erro do abridor de URL. A abertura anterior no tablet Android 16 com Python 3.13.13 foi relatada pelo acadêmico na etapa anterior. O Python 3.13.18 executado nesta campanha foi o de Linux x64.
- **Emulado:** viewports, toque e preferências de aparência via navegador. WebKit no Linux não comprova Safari em iPhone ou iPad. Windows desktop, Mac, smartphone, tablet físico e ChromeOS não receberam validação física nova nesta campanha.
- **Escopo residual:** ausência de ensaio de saturação até a falha, durabilidade a corte de energia, revogação de uma requisição já em curso, leitura assistiva humana e varredura exaustiva de todas as combinações de entradas e plataformas. As verificações de segurança foram defensivas; a campanha não certifica serviço público.

## Reprodução

Executar na raiz de uma cópia descartável do candidato, com os arquivos da revisão. Manter a pasta de evidências e a venv de QA fora dos arquivos de distribuição. Os comandos abaixo usam o Python da venv de QA já selecionada. O produto continua exigindo somente `requirements.txt`.

```sh
python -m pip install -r requirements-qa.txt
python -m pip check
python -B -m unittest discover -s tests -v
python -B -m qa.estados
python -B -m qa.formularios
python -B -m qa.perfis
python -B -m qa.persistencia
python -B -m qa.mutacao
python -B -m qa.desempenho
```

Para medir cobertura com subprocessos, defina o arquivo de configuração absoluto e uma pasta de saída **nova**. A combinação deve usar somente os dados dessa rodada.

```sh
export COVERAGE_RCFILE="$PWD/qa/coverage.ini"
saida_qa=$(mktemp -d)
export COVERAGE_FILE="$saida_qa/.coverage"
python -m coverage run -m unittest discover -s tests -v
python -m coverage combine "$saida_qa"
python -m coverage json -o "$saida_qa/cobertura.json"
python -m coverage html -d "$saida_qa/html"
ruff check --select F,E9,B model controller persistence repository service view web iniciar_move.py main.py
bandit -qr model controller persistence repository service view web iniciar_move.py main.py
pip-audit -r requirements.txt --no-deps --disable-pip
```

Ensaios com Playwright e motores instalados na máquina de QA:

```sh
for roteiro in 08a 08b 08c ui_10a4_1 master_demo cadastro; do
  python -B -m "tests.navegador_$roteiro" --chrome /usr/bin/google-chrome || break
done
python -B -m qa.navegadores chromium --executavel /usr/bin/google-chrome --axe /caminho/local/axe.min.js
python -B -m qa.navegadores firefox
python -B -m qa.navegadores webkit
python -B -m qa.zoom
```

O ensaio de zoom requer Chrome, Xvfb, xauth e python-xlib no Linux. Para Edge, usar o motor chromium com o executável local do Edge. Para a comparação visual, passar `--capturas` ao ensaio de cadastro do checkpoint e do candidato em diretórios distintos, com as mesmas versões do navegador e das fontes, e comparar os bytes de nomes correspondentes. No Ubuntu utilizado, as bibliotecas opcionais de WebKit foram fornecidas somente ao MiniBrowser em execução. Os roteiros de QA não precisam ser instalados para iniciar o MOVE normalmente.

## Estado da entrega

As mudanças de produto concentram-se no acumulador do domínio e projeção de faturamento, registro privado de sessões, configuração, guardas, logout e macro das vagas. Os ajustes de demonstração e de exclusão do Git acompanham o novo arquivo privado. As mudanças de teste incluem o módulo de regressões, o nome acessível verificado em 08B e o logout no fim da jornada Master. A árvore contém também os ensaios intensivos, requisitos opcionais, evidências, documentação e a extensão do workflow.

Na consolidação, a suíte completa voltou a aprovar os 185 métodos anteriores e os oito novos. O inventário e as evidências de mutação, fuzzing, recuperação, acessibilidade, análise estática e auditoria de dependências acompanham o código. As evidências brutas volumosas ficaram fora do controle de versão.

Para conferir a execução remota desta revisão, abra o workflow **Compatibilidade do MOVE** e selecione a execução da branch `trabalho-final` com o SHA do commit de encerramento. Cada configuração registra o resultado da suíte e das duas aberturas do pacote extraído. Os dois executores macOS com Python 3.12 registram também os percursos de navegador. O aceite em smartphone e tablet físicos fica para a reta final. [Execuções da branch](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/actions/workflows/compatibilidade.yml?query=branch%3Atrabalho-final)
