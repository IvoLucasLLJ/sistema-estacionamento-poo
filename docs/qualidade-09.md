# MOVE · Qualidade e estabilização da Etapa 09

**Parecer para entrega acadêmica local.** A retirada legada voltou a produzir um histórico que pode ser reaberto. Os dois portais recuperaram os mesmos estados financeiros após reinicialização. A suíte, os três ensaios Chromium e as verificações complementares passaram. Nas condições avaliadas, não ficou defeito bloqueante ou de severidade alta em aberto.

A validação ocorreu em Ubuntu 26.04.1 LTS, Python 3.14.4, com a aplicação na própria `.venv` e o Playwright já disponível no ambiente de ensaios. Os servidores ouviram em `127.0.0.1`. As contas, chaves e históricos dos ensaios eram temporários.

## Linha de base e escopo

A revisão começou em `trabalho-final`, no commit `e4c4040fa4bcfce7895c4d93715c0a5188d764ed`. Antes da correção, passaram os 130 testes, os ensaios 08A/08B/08C e o `pip check`. Os 14 arquivos modificados e os 13 novos da 08C foram conferidos e preparados por nome. As tarifas de 10, 5 e 20 reais por hora continuaram compartilhadas entre as subclasses de veículos e o catálogo do serviço. A titularidade das consultas pessoais continuou vinculada ao cadastro da conta e à entrada original. A inspeção do conteúdo e dos caminhos preparados incluiu senhas, hashes persistidos, chaves, arquivos operacionais e ambiente virtual.

O checkpoint local da 08C é `acccf1bf7d66a580fa10a2042977031c02c93b2b`. Ele inclui o registro histórico do defeito conhecido. A revisão da 09 acrescenta uma correção de domínio, duas suítes de regressão, a documentação e a formatação monetária de duas casas solicitada durante a validação. Os 130 métodos de teste continuam na suíte. Foram atualizadas as expectativas de apresentação em test_web, test_gestao, test_portal_cliente e nos ensaios Chromium 08B/08C. Os testes de cálculo, persistência e autorização continuam exigindo os mesmos resultados.

## Horários legados

| Registro | Severidade e situação | Reprodução e causa | Correção e evidência |
|---|---|---|---|
| Q09-01 · Histórico indisponível na reabertura | Bloqueante, corrigido | Com P0 temporário, executar o terminal, selecionar 7, informar LEG9 e 2 horas e sair pela opção 4. O evento 24 foi salvo. O Controller falhou ao reconstruir a saída por comparação direta de um `datetime` sem fuso com outro com fuso. Toda consulta web que precisasse recarregar esse histórico também perderia a disponibilidade. | A retirada e a reconstrução validam o mesmo par de horários e preservam os textos gravados. O teste executa `main.py` em outro processo, reabre o arquivo, autentica uma conta de Gestão e lê o histórico por HTTP. [Domínio](../model/estacionamento.py#L21) · [Regressão terminal–web](../tests/test_horarios_legados.py#L28) |
| Q09-02 · Saída cronologicamente impossível aceita na escrita | Alta, corrigido | Carregar uma entrada com data inequivocamente futura e solicitar a retirada. Antes da correção, o terminal podia liberar a vaga em memória e aceitar o evento que a reconstrução rejeitaria. O teste inicialmente falhou com `ValueError not raised`. | A validação ocorre antes de liberar a vaga ou acrescentar o evento. Na reprodução da saída persistida, o domínio recebe o horário gravado. [Retirada legada](../model/estacionamento.py#L216) · [Regressão da recusa](../tests/test_horarios_legados.py#L96) |

Diagnóstico real da reabertura antes da correção:

```text
TypeError: can't compare offset-naive and offset-aware datetimes
ValueError: Histórico JSON inconsistente; arquivo preservado: can't compare offset-naive and offset-aware datetimes
```

**Política de comparação**

- Dois horários com fuso permitem comparar instantes, inclusive quando os offsets diferem. Dois horários sem fuso mantêm a comparação civil já usada nos arquivos dessa geração.
- Quando apenas um tem fuso, o instante exato do relógio civil é desconhecido. O domínio usa o limite de um offset ISO aceito pelo Python, estritamente entre −24 h e +24 h. Se a saída preceder a entrada para **todos** os offsets possíveis, o evento é inconsistente. Nos pares ambíguos, a ordem é sustentada pela entrada prévia correspondente, pela placa e pela vaga ainda ocupada. Nenhum fuso é atribuído ao registro antigo.
- A referência civil e a referência UTC do comparador servem apenas para medir essa diferença. A função devolve um booleano. A duração cobrada continua sendo o campo autorizado `horas`. O histórico preserva os textos de entrada e saída, os IDs, a ordem e os valores financeiros. O contrato de estadias identificadas continua exigindo horário com fuso. [Escrita e reconstrução](../model/estacionamento.py#L274) · [Pares válidos e rejeitados](../tests/test_horarios_legados.py#L65)

**Red e Green.** Antes da alteração, as quatro regressões produziram três erros e três falhas, contando subcasos. Depois, os quatro métodos passaram. A reabertura recuperou AV1 e AM2 com os IDs 22 e 23, a saída legada com número 24, duas vagas ocupadas e faturamento subjacente de `50.005` reais (R$ 50,01 no painel) após a retirada de LEG9 por R$ 10,00. Esse ensaio usa uma cópia própria de P0. Em outro teste, uma saída antiga de R$ 0,005 continuou valendo R$ 0,005. As leituras mantiveram os bytes intactos. Arquivos válidos já afetados pela mistura de fusos voltam a abrir sem migração.

## Matriz de rastreabilidade

Os caminhos abaixo são rotas relativas a `/gestao` ou `/cliente`, conforme o modelo. Os guias anteriores detalham contratos e templates individuais. [Compartilhados](web-08a.md) · [Gestão](web-08b.md) · [Cliente](web-08c.md)

| Requisito e modelos | Rotas representativas | Classe ou operação responsável | Evidência aprovada |
|---|---|---|---|
| Acesso, papel, expiração e indisponibilidade · S01–S05 | `/entrar`, `/sair`, destinos protegidos | `AutenticacaoService.autenticar`, `ContaRepository.por_id`, guardas e tratamento HTTP | [HTTP, CLI e concorrência](../tests/test_web.py) · [Chromium 08A](../tests/navegador_08a.py) |
| Capacidade, mapa e estadias ativas · G01, G02, G08 | `/`, `/vagas`, `/estadias` | `consultar_ocupacao`, `consultar_vagas`, `listar_estadias_ativas`, `OcupacaoViewModel` | [Domínio](../tests/test_nucleo.py) · [HTTP](../tests/test_gestao.py#L35) |
| Clientes, veículos e vínculos · G03–G06 | `/clientes`, `/veiculos`, detalhes, `/vinculos` | `cadastrar_cliente`, `cadastrar_veiculo`, `vincular_veiculo`, UUID e placa normalizada | [Cadastro e homônimos](../tests/test_cadastro_clientes.py) · [HTTP](../tests/test_gestao.py#L46) |
| Entrada e disputa de vaga · G07 | `/entrada` | `Revisoes`, `iniciar_estadia`, `Vaga.ocupar` | [Entrada concorrente](../tests/test_service.py#L315) · [Revalidação HTTP](../tests/test_gestao.py#L70) |
| Cobrança, pagamento, fila e comprovante · G09–G11, G13 | `/estadias/<id>/saida`, `/pagamento` e `/concluir` sob a estadia, `/pagamentos`, detalhe | `Estadia.consultar_cobranca`, `Cobranca`, `confirmar_pagamento`, `concluir_saida`, `listar_pagamentos_abertos` | [Nove combinações, zero e frações](../tests/test_estadias.py#L66) · [Chromium 08B](../tests/navegador_08b.py) · [Reinício e revisão perdida](../tests/test_reinicio_web.py) |
| Eventos e relatórios · G12, G14 | `/historico`, `/relatorios` | `consultar_historico`, `consultar_faturamento`, `RelatorioSaidas.do_periodo` | [Projeções históricas](../tests/test_gestao.py#L140) · [Reabertura do legado](../tests/test_horarios_legados.py) |
| Início, estadias, frota e disponibilidade pessoal · C01–C04 | `/`, `/estadias`, `/veiculos`, `/disponibilidade` | `ConsultasPessoais.ativas`, `veiculos_do_cliente`, `consultar_ocupacao` | [HTTP e falha parcial](../tests/test_portal_cliente.py#L48) · [Chromium 08C](../tests/navegador_08c.py) |
| Tarifas e perfil · C05, C08 | `/tarifas`, `/perfil` | `consultar_tarifas`, `Identidade`, `ControleTema` | [Catálogo e papel](../tests/test_portal_cliente.py#L118) · [Perfil e sessão no navegador](../tests/navegador_08c.py) |
| Histórico pessoal e comprovante · C06, C07 | `/historico`, `/estadias/<id>`, respectivo `/comprovante` | `ConsultasPessoais.historico`, `consultar_estadia`, guarda pelo titular original | [Homônimos e equivalência de 404](../tests/test_portal_cliente.py#L81) · [Integração entre portais](../tests/test_portal_cliente.py#L170) |

## Integridade entre os portais

Com duas sessões autenticadas, um servidor e um arquivo temporário por percurso, a Gestão registrou as entradas. A cliente observou as mudanças em consultas subsequentes.

| Estado da estadia 22 | Ocupadas | Livres | Pagamentos aguardando saída | Faturamento no serviço (reais) | Exibição na Gestão |
|---|---:|---:|---:|---:|---:|
| P0 · cotada | 3 | 7 | 0 | `40.005` | R$ 40,01 |
| P1 · pagamento confirmado | 3 | 7 | 1 | `40.005` | R$ 40,01 |
| P2 · saída concluída | 2 | 8 | 0 | `46.135` | R$ 46,14 |

Lia Vale, VIP, viu AV1 na vaga 2 até P1. No comprovante pessoal, a duração aparece como 1,225 h, a tarifa-base como R$ 12,25, o desconto como R$ 6,13 e o total como R$ 6,13. O domínio conserva o desconto decimal `6.125` e os 613 centavos definitivos. O formatador compartilhado usa arredondamento decimal de meio centavo para cima e separadores pt-BR. A Gestão soma os valores persistidos antes de formatar o total. O teste de apresentação falhou primeiro porque o formatador antigo devolvia três casas. A regressão também verifica zero, valores menores que um centavo e mudança de milhar após arredondamento. [Formatador](../web/apresentacao.py#L17) · [Teste](../tests/test_web.py#L170) A estadia 23 de AM2 continuou ativa. As respostas pessoais omitiram o faturamento administrativo. Também foi exercitado no navegador o cancelamento da revisão de AM2. Os bytes continuaram iguais e a estadia ficou sem confirmação.

**Reinicialização real.** No percurso adicional por teclado, o processo servidor foi encerrado após confirmar o pagamento. Um novo processo abriu os mesmos arquivos e a mesma porta de loopback. A submissão de uma revisão anterior recebeu a página de revisão indisponível. A ação **Consultar estado** recuperou a estadia 22 com pagamento confirmado. A nova revisão permitiu concluir a saída uma vez. Depois de uma segunda reinicialização, o comprovante abriu com HTTP 200 e o faturamento continuou em R$ 46,135. A cifra exata do serviço aparece na tela como R$ 46,14 após a padronização monetária. O teste automatizado também verifica as respostas 405 para conclusão por GET e 409 para a revisão perdida. [Regressão HTTP](../tests/test_reinicio_web.py#L13)

**Persistência e concorrência.** A suíte exercitou escrita temporária com substituição atômica, conflito por alteração externa, histórico e contas corrompidos, falhas antes e depois da publicação, liberação do bloqueio e recuperação por leitura. Threads reais disputaram vaga, placa, cadastro, confirmação e saída. O terminal em subprocesso foi impedido de usar o histórico reservado pelo servidor. No ensaio adicional, duas CLIs tentaram provisionar simultaneamente contas para o mesmo UUID durante a execução do servidor. Os códigos de saída foram 0 e 1, uma conta pôde autenticar e os bytes operacionais permaneceram idênticos. [Repository](../tests/test_repository.py) · [Falhas e concorrência](../tests/test_service.py#L189) · [Reserva entre processos](../tests/test_web.py#L204)

**Segurança local.** Os testes verificaram credencial inválida com resposta uniforme, hash scrypt, rotação de sessão, expiração, logout por POST, CSRF, escape HTML, cookies e `no-store`. As rotas administrativas recusaram o papel Cliente. Para detalhe e impressão, um recurso inexistente e um de terceiro tiveram resposta pública equivalente. Foram conferidos UUID recebido pela URL, placa e ID de outra utilização, campos financeiros divergentes, formulário repetido, revisão expirada e revisão de outra sessão. A validação ocorreu em dados fictícios locais. [Contas, sessão e cabeçalhos](../tests/test_web.py) · [Expectativa financeira](../tests/test_service.py#L99) · [Escritas e revisões](../tests/test_gestao.py#L181) · [Titularidade histórica](../tests/test_portal_cliente.py#L145)

## Acessibilidade, responsividade e desempenho

A referência foi a [WCAG 2.2 do W3C](https://www.w3.org/TR/WCAG22/), em particular estrutura e relações, contraste, redimensionamento, reflow, teclado, ordem e visibilidade do foco, tamanho dos alvos e identificação de erros.

- Em Chromium, foram enviados comandos de teclado manualmente, observando o foco a cada decisão. Na Gestão, o percurso incluiu login, menu compacto, mapa, vaga 2, detalhe, cotação decimal, confirmação, revisão perdida, consulta do estado e conclusão da saída. No Cliente, incluiu login, **Mais**, Escape com retorno do foco, histórico, detalhe e impressão pelo teclado. O atalho **Ir ao conteúdo** levou ao primeiro controle do conteúdo na tabulação seguinte. O botão de impressão focado esteve visível acima da navegação inferior. Login, menu e ações apresentaram contorno de foco. A revisão financeira é uma página. O retorno do foco foi exercitado no menu pessoal expansível.
- Oito destinos de Gestão e oito de Cliente foram consultados a 320, 390, 768 e 1440 px. Nas 64 combinações verificadas houve uma região principal e um H1, campos com rótulo, IDs sem duplicação detectada, sequência de títulos sem saltos e largura do documento dentro do viewport. As amostras incluíram o mapa, formulários, histórico, tabelas de relatório e comprovante. A ampliação do texto raiz a 200% em desktop foi verificada no formulário de cobrança e no perfil pessoal. Ambos conservaram a largura de 1440 px.
- Oito pares semânticos foram medidos por luminância relativa das cores resolvidas no Chromium. Texto/fundo atingiu 16,96:1 no claro e 16,19:1 no escuro. Grafite/primário atingiu 11,58:1 e 9,25:1. Foco/superfície atingiu 6,70:1 e 8,14:1. Os demais pares avaliados foram secundário/superfície, confirmado/superfície, erro, VIP e livre sobre seus respectivos fundos. Vagas e pagamentos usam rótulos de texto. Os controles de perfil e impressão amostrados tinham 44 px de altura. Claro, Escuro e Sistema foram exercitados, inclusive a alteração da preferência do sistema e a navegação subsequente.
- Os ensaios 08A, 08B e 08C passaram em Chromium 158.0.8127.36. A instrumentação de rede do navegador registrou respectivamente 153, 756 e 1.448 requisições, todas em loopback, e zero exceções JavaScript não tratadas. Os percursos incluíram impressão nativa e geração de PDF em memória. As verificações foram em navegador emulado. Leitor de tela, dispositivos físicos, impressão em papel e uma auditoria normativa integral continuam sem avaliação.

Com uma fixture de 25 eventos em P2, a mediana de cinco chamadas locais foi 1,84 ms para ocupação, 0,97 ms para histórico e 1,36 ms para a estadia 22. A porta do servidor ficou pronta em 365, 423 e 911 ms nas três inicializações medidas. As medições de desempenho antecederam o ajuste de formatação monetária. A medição de navegação `loadEventEnd` em desktop variou de 97,5 a 154 ms nos 16 destinos amostrados. Os números descrevem uma execução local com recursos estáticos locais. O serviço relê e reconstitui o histórico em cada operação, e telas compostas fazem mais de uma consulta. Isso limita a extrapolação para arquivos maiores. Não foi realizado teste de carga.

## Evidências de arquitetura e POO

| Classes e estado relevante | Responsabilidade exercitada | Evidência |
|---|---|---|
| `Veiculo` (placa, modelo), `Carro`, `Moto`, `Caminhao`; `Cliente` (UUID, nome, categoria), `ClienteComum`, `ClienteVIP`, `ClienteMensalista` | ABCs e métodos abstratos. Cada objeto concreto implementa `calcular_tarifa` ou `calcular_cobranca`. As três tarifas por hora também alimentam o catálogo. | [Veículos](../model/veiculo.py#L4) · [Clientes](../model/cliente.py#L10) · [Nove combinações e persistência](../tests/test_estadias.py#L66) |
| `Estadia` e `Cobranca` | A estadia associa veículo, cliente e vaga. `consultar_cobranca` despacha para os dois objetos, arredonda no final e entrega uma cobrança imutável com horas, base, desconto, ID, placa e centavos. `confirmar_pagamento` e `situacao_para_saida` distinguem os dois atos. | [Métodos](../model/estadia.py#L47) · [Recálculo e recuperação](../tests/test_estadias.py#L129) |
| `EstacionamentoService` | Encapsula caminho e bloqueio. `_executar` coordena estado isolado, Controller e Repository. `_persistir` separa recusa, conflito e confirmação incerta. | [Serviço](../service/estacionamento_service.py#L38) · [Falhas de confirmação](../tests/test_service.py#L256) |
| `ContaUsuario`, `ContaRepository`, `AutenticacaoService` | A conta contém `Identidade` e hash. O Repository controla leitura e publicação por caminho. O serviço compõe repositório e estacionamento para `provisionar` e `autenticar`. | [Classes de acesso](../web/contas.py#L35) · [Testes de contas](../tests/test_web.py#L47) |
| `OcupacaoViewModel`, `RelatorioSaidas` | Objetos imutáveis. `da_consulta` e `percentual` organizam a ocupação. `do_periodo` agrega saídas, receita e distribuições a partir dos valores registrados. | [Ocupação](../web/apresentacao.py#L35) · [Relatório](../web/eventos.py#L49) · [Teste de projeção](../tests/test_gestao.py#L155) |
| `Revisoes`, `ConsultasPessoais` | A primeira encapsula validade, capacidade, registros e trava em `emitir` e `obter`. A segunda recebe serviço e titular no construtor e delimita `ativas`, `veiculos` e `historico` por requisição. | [Revisões](../web/revisoes.py#L16) · [Projeção pessoal](../web/consultas_pessoais.py#L5) · [Teste de isolamento](../tests/test_portal_cliente.py#L210) |
| `ControleTema`, `ControleSubmissao` | Campos privados retêm preferência, consulta de mídia e estado de envio. O primeiro sincroniza a preferência com os controles e a navegação. O segundo trata envio repetido e retorno à página. | [Objetos JavaScript](../web/static/js/controles.js#L3) · [Ensaio de submissão e tema](../tests/navegador_08a.py#L36) |

## Reprodução e limites do parecer

Na raiz do MOVE, com o ambiente da aplicação ativo:

```bash
source .venv/bin/activate
python -B -m unittest tests.test_horarios_legados tests.test_reinicio_web -v
python -B -m unittest discover -s tests -v
pip check
git diff --check
git status --short
```

Os ensaios existentes são executáveis no ambiente de QA que disponibiliza Playwright, a partir da mesma raiz:

```bash
python -B -m tests.navegador_08a --chrome /usr/bin/google-chrome
python -B -m tests.navegador_08b --chrome /usr/bin/google-chrome
python -B -m tests.navegador_08c --chrome /usr/bin/google-chrome
```

O total foi **135 testes aprovados**, dos quais 130 anteriores e cinco novos. A linha de base levou 52,949 s e a suíte com as regressões, 60,695 s em execução concomitante aos ensaios. As evidências abrangem unidade, integração de persistência e processos, HTTP e navegador. Cobertura percentual de linhas não foi medida.

O parecer abrange o ambiente acadêmico local de um servidor com múltiplas threads e escritores cooperativos. O logout encerra a sessão no navegador corrente. Revogação individual de cookies copiados, limitação de tentativas e implantação HTTPS exigem controles de implantação próprios. A troca atômica do JSON e as falhas de processo foram exercitadas. Durabilidade após corte de energia e consistência instantânea entre múltiplas consultas na mesma tela estão fora das garantias demonstradas. [Limites operacionais da aplicação](web-08a.md#segurança-e-limites-operacionais)
