# MOVE Cliente · Etapa 08C

O mesmo servidor Flask atende Gestão e Cliente. O papel da conta define a área de acesso. Um cliente autenticado pode consultar sua frota, suas utilizações e a disponibilidade agregada. A Gestão registra a entrada, confirma o pagamento simulado e conclui a saída. O portal pessoal reflete essas operações na consulta seguinte. [Execução e provisionamento](web-08a.md) · [Operações administrativas](web-08b.md) · [Referência visual](https://www.figma.com/design/oamoaxU0OJRHHKcuLIlFOi?node-id=55-7672)

## Modelos, rotas e permissões

Todas as rotas abaixo são GET e exigem sessão com papel Cliente e cadastro de domínio válido. A identidade vem do vínculo entre a conta autenticada e o UUID. O encerramento da sessão utiliza o POST compartilhado com CSRF.

| Modelo | Rota | Consulta, seleção e apresentação |
|---|---|---|
| C01 · Início | `/cliente/` | Nome e categoria atuais, estadias próprias, frota e ocupação agregada. Uma falha parcial é apresentada no bloco afetado. |
| C02 · Minhas estadias | `/cliente/estadias` | Filtra as ativas pelo titular histórico e enriquece o modelo pela frota autorizada. Um pagamento confirmado ainda ocupa a vaga. |
| C03 · Meus veículos | `/cliente/veiculos` | Consulta os vínculos pelo UUID da sessão. A placa relaciona um veículo com uma estadia que já passou pelo filtro de titularidade. Uma falha na leitura das ativas aparece como situação indisponível. |
| C04 · Disponibilidade | `/cliente/disponibilidade` | Capacidade, livres, ocupadas, percentual e horário da consulta. Atualizar repete a leitura agregada. Lotação é um resultado válido e indisponibilidade recebe o estado S05. |
| C05 · Tarifas e benefícios | `/cliente/tarifas` | O catálogo do serviço lê o valor por hora das classes Carro, Moto e Caminhao. O texto explica os benefícios comerciais e destaca a categoria do cadastro. |
| C06 · Meu histórico | `/cliente/historico` | Uma linha por entrada identificada do titular, em ordem decrescente de ID de entrada. Mostra também as utilizações em andamento. Os filtros usam placa pessoal, situação e datas inclusivas de entrada, pelo dia civil registrado. |
| C07 · Detalhes e comprovante | `/cliente/estadias/<id>` e `/cliente/estadias/<id>/comprovante` | As duas rotas autorizam pela entrada original. A segunda exige utilização concluída, usa os dados financeiros persistidos e oferece impressão acadêmica. |
| C08 · Meu perfil | `/cliente/perfil` | Nome, categoria, UUID para atendimento, conta atual, preferência de tema e encerramento da sessão. |

A aplicação pessoal mantém os estados de erro compartilhados. A resposta para uma utilização de terceiro é a mesma de uma utilização inexistente, inclusive no acesso direto ao comprovante. Erros de infraestrutura preservam os valores desconhecidos. O servidor entrega respostas privadas com `Cache-Control: no-store`. As telas de consulta deixam os bytes do histórico intactos. [Guarda de papel e titularidade](../web/seguranca.py#L54) · [Teste da equivalência pública](../tests/test_portal_cliente.py#L81) · [Teste das consultas e dos bytes](../tests/test_portal_cliente.py#L155)

## Composição e POO em execução

| Objeto ou estrutura | Responsabilidade e aplicação | Teste ou referência |
|---|---|---|
| `ConsultasPessoais` | O Blueprint cria um objeto por requisição autorizada. O construtor recebe a instância de `EstacionamentoService` e o UUID da sessão. Os atributos internos `_servico` e `_titular` encapsulam essas dependências. `veiculos()`, `ativas()` e `historico()` produzem coleções de leitura para aquele titular. | [Classe](../web/consultas_pessoais.py#L5) · [Composição no Blueprint](../web/cliente.py#L17) · [Isolamento de dois objetos para homônimas](../tests/test_portal_cliente.py#L210) |
| Projeção histórica | `historico()` reutiliza `eventos_identificados`. Para pagamento e saída, a projeção recupera o titular e a categoria pelo ID da entrada. O adaptador pessoal seleciona os dados desse titular e organiza os estados da utilização. Uma associação cadastral posterior pode tornar um veículo visível na frota enquanto sua utilização legada continua ausente do histórico pessoal. | [Projeção comum](../web/eventos.py#L14) · [Agrupamento pessoal](../web/consultas_pessoais.py#L16) · [Teste do vínculo posterior](../tests/test_portal_cliente.py#L145) |
| `Identidade` e `OcupacaoViewModel` | A primeira identifica a conta autenticada e seu papel. O segundo é um objeto imutável construído a partir das três contagens do serviço. A propriedade `percentual` atende a C01 e C04. | [Identidade](../web/contas.py) · [ViewModel](../web/apresentacao.py#L35) · [Teste de lotação e falha](../tests/test_portal_cliente.py#L100) |
| Hierarquias de domínio e catálogo | Cada subclasse concreta de veículo possui `TARIFA_POR_HORA`. Seu método `calcular_tarifa(horas)` utiliza esse atributo. `consultar_tarifas()` entrega uma cópia dos três preços de referência para C05. Em uma utilização, o domínio aplica a implementação concreta de veículo e de cliente. C02/C06/C07 apresentam os valores confirmados ou concluídos que o serviço disponibiliza. | [Catálogo](../service/estacionamento_service.py#L121) · [Carro](../model/carro.py#L4) · [Cálculo de Estadia](../model/estadia.py#L47) · [Teste de correspondência](../tests/test_portal_cliente.py#L118) |
| `ControleTema` e `ControleSubmissao` | O primeiro objeto mantém a preferência local, resolve Sistema e acompanha alterações do navegador. C08 reutiliza o seletor dentro do perfil. O segundo protege a interação durante o envio do logout. A verificação do token e do acesso ocorre no servidor. | [Controles](../web/static/js/controles.js) · [Jornadas no navegador](../tests/navegador_08c.py) |

A View compõe o template-base, o layout do portal e os templates de cada modelo. As macros Jinja são funções de composição visual. C01 reaproveita o template pessoal da 08A. Os demais templates pessoais estão em [cliente/](../web/templates/cliente/).

| Referência do design | Uso efetivo no código |
|---|---|
| N01/N02/N03/N06/N07 | Cabeçalho, navegação por perfil, navegação inferior no celular, menu da conta e seletor de tema. **Mais** abre as quatro consultas complementares no celular. Escape fecha o menu e devolve o foco. [Layout pessoal](../web/templates/layouts/cliente.html) · [Layout compartilhado](../web/templates/layouts/portal.html) |
| D03/D04, V03/V04/V05, P06 | Frota, card de estadia e rótulos de categoria e situação. A confirmação mostra o valor e informa que o veículo está estacionado. [Macros pessoais](../web/templates/components/pessoal.html) |
| D01/V01, M04/M09 | Indicador agregado, medidor de ocupação e mensagens de indisponibilidade. [Macros compartilhadas](../web/templates/components/ui.html) |
| D09, P01/P02/P03 e V07 | Filtros, ficha da estadia, linhas de tarifa, desconto e total, comprovante e impressão. São reutilizadas as macros de leitura introduzidas na Gestão. C07 oferece somente ações pessoais. [Macros de consulta](../web/templates/components/gestao.html) · [Detalhes e comprovante](../web/templates/cliente/estadia.html) |

## Evidência de integração

O ensaio de navegador utiliza dois contextos independentes, um servidor em loopback e um histórico temporário por largura. A Gestão registra as entradas de AV1 e AM2 no navegador e realiza as operações financeiras sobre a estadia 22. A cliente observa cada mudança por nova consulta. O teste HTTP também reabre o serviço e confere a gravação de 613 centavos. [Percurso Chromium](../tests/navegador_08c.py) · [Teste HTTP integrado](../tests/test_portal_cliente.py#L170)

| Momento | Consulta da titular | Disponibilidade exibida ao Cliente | Faturamento exclusivo da Gestão |
|---|---|---|---|
| P0 | AV1 e AM2 ativos, sem valor confirmado | 3 ocupadas, 7 livres | R$ 40,005 |
| P1 | AV1 na vaga 2 com R$ 6,13 confirmados. AM2 continua sem confirmação | 3 ocupadas, 7 livres | R$ 40,005 |
| P2 | AV1 concluído, com comprovante. AM2 continua ativo | 2 ocupadas, 8 livres | R$ 46,135 |

O comprovante usa a duração de 1,225 h, a base de R$ 12,25, o desconto exato de R$ 6,125 e o total persistido de R$ 6,13. O portal também permite imprimir saída isenta do próprio titular. O período filtrado e a impressão são consultas. Cada consulta do serviço lê um estado validado. Requisições simultâneas podem produzir instantes de leitura distintos entre blocos de uma página.

### Limitação observada no histórico legado

Em uma cópia temporária, a retirada pelo terminal de um veículo com entrada legada sem fuso produziu uma saída com fuso. Ao reabrir esse histórico, a reconstrução falhou ao comparar os dois horários. A ocorrência envolve a retirada legada pelo terminal. As consultas pessoais são somente de leitura e o cenário P0–P2 usa estadias identificadas. [Gravação da saída legada](../model/estacionamento.py#L224) · [Comparação na reconstrução](../model/estacionamento.py#L270)

## Reprodução local

```bash
cd /home/lucas/MOVE
source .venv/bin/activate
python -B -m web
```

O login local fica em [127.0.0.1:5000/entrar](http://127.0.0.1:5000/entrar). Use uma conta pessoal vinculada ao UUID de um cliente cadastrado. Para provisionar uma conta, execute no terminal autorizado:

```bash
read -r -p 'UUID do cliente: ' cliente_move
python -m flask --app web criar-conta --papel cliente --usuario cliente.local --cliente-id "$cliente_move"
```

A CLI solicita a senha com entrada oculta. A conta administrativa continua usando o mesmo login. O serviço opera em um processo com threads. A atualização entre portais depende de nova leitura.

A suíte usa `python -B -m unittest discover -s tests -v`. O ensaio opcional usa `python -B -m tests.navegador_08c --chrome /usr/bin/google-chrome` no ambiente de QA com Playwright disponível. A opção `--capturas` grava PNGs em uma pasta externa. A validação usa larguras emuladas e impressão pelo Chromium. [Instruções da infraestrutura](web-08a.md)
