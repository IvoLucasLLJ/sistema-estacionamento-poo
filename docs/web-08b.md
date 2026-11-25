# MOVE Gestão · Etapa 08B

O executável continua sendo `python -B -m web`, após ativar a `.venv`. A Gestão usa a conta local provisionada para esse papel. A tabela indica os destinos que podem ser abertos após o login. Os cadastros, a confirmação da entrada, o pagamento e a saída retornam HTTP 303 para uma consulta após a persistência. [Execução e provisionamento](web-08a.md) · [Referência visual do Figma](https://www.figma.com/design/oamoaxU0OJRHHKcuLIlFOi?node-id=55-7672)

## Telas e contratos

As rotas abaixo têm o prefixo `/gestao`. Cada página usa o layout Gestão, a marca B e as mesmas preferências de tema do portal compartilhado. Os templates administrativos estão em [web/templates/gestao](../web/templates/gestao/) e o dashboard em [gestao.html](../web/templates/gestao.html).

| Modelo | Rota | Operação e resultado |
|---|---|---|
| G01 · Dashboard | `GET /` | Mostra ocupação, fila de confirmações e faturamento de saídas. Os atalhos iniciam entrada ou preparação de saída. |
| G02 · Mapa | `GET /vagas?vaga=2` | Seleciona uma das dez vagas. A consulta mostra a situação e a identificação disponível. Uma ocupação legada só oferece leitura. |
| G03 · Clientes | `GET, POST /clientes` | Busca por nome ou UUID, filtra a categoria e cadastra nome e categoria. Homônimos têm UUIDs próprios. |
| G04 · Cliente | `GET /clientes/<uuid>`, `POST /vinculos` | Mostra cadastro, frota, estadias ativas e eventos atribuíveis ao titular. O vínculo passa pelo serviço. |
| G05 · Veículos | `GET, POST /veiculos` | Busca por placa, filtra por tipo e cadastra tipo, placa e modelo. A decisão sobre duplicidade pertence ao domínio. |
| G06 · Veículo | `GET /veiculos/<placa>`, `POST /vinculos` | Mostra responsável e ocupação. Oferece vinculação ou entrada conforme os dados consultados. |
| G07 · Entrada | `GET, POST /entrada` | Seleciona cliente, veículo e vaga. O GET permite revisar. A confirmação usa os dados da revisão no servidor. O serviço verifica vínculo e disponibilidade novamente sob bloqueio. |
| G08 · Estadias ativas | `GET /estadias` | Busca por placa, estadia ou titular e filtro financeiro. Identifica registros legados. |
| G09 · Saída e cobrança | `GET /estadias/<id>/saida?horas=1,225` | Consulta a tarifa pelo serviço e mostra base, desconto e centavos definitivos. A duração aceita vírgula ou ponto. Um total zero habilita a saída isenta. |
| G10 · Confirmação | `GET, POST /estadias/<id>/pagamento` | Exibe a revisão original. Confirmar registra o pagamento simulado. Cancelar descarta a revisão. |
| G11 · Pagamentos abertos | `GET /pagamentos` | Seleciona as estadias ativas com pagamento confirmado, mostra os dados persistidos e encaminha para concluir a saída. |
| G12 · Histórico | `GET /historico` | Filtra por texto e tipo. O parâmetro `evento` abre os campos disponíveis sob o número original do evento. |
| G13 · Estadia e comprovante | `GET /estadias/<id>`, `POST /estadias/<id>/concluir` | Consulta o estado persistido pelo ID da entrada. A conclusão libera a vaga. Uma utilização concluída tem resumo acadêmico com folha de impressão. |
| G14 · Relatórios | `GET /relatorios?inicio=AAAA-MM-DD&fim=AAAA-MM-DD` | Separa ocupação atual e faturamento acumulado da receita, contagens e distribuições por período de saída. |

## Caminho da cobrança no código

1. A rota converte a vírgula decimal em ponto e entrega o texto a `consultar_cobranca`. O serviço converte o texto em `Decimal` e chama o Controller. [Rota G09](../web/gestao.py#L240) · [Serviço](../service/estacionamento_service.py#L134) · [Controller](../controller/controller.py#L39)
2. O objeto `Estadia` contém referências a um veículo, um cliente e uma vaga. Em `consultar_cobranca`, a chamada `self.veiculo.calcular_tarifa(horas)` seleciona a implementação de carro, moto ou caminhão. Em seguida, `self.cliente.calcular_cobranca(base)` seleciona a regra de comum, VIP ou mensalista. O domínio calcula o desconto exato e arredonda o total com `ROUND_HALF_UP`. Esse despacho entre implementações concretas é o polimorfismo demonstrado pelo fluxo. [Estadia](../model/estadia.py#L35) · [Cálculo](../model/estadia.py#L47) · [Carro](../model/carro.py#L5) · [ClienteVIP](../model/cliente_vip.py#L7)
3. O objeto `Cobranca` fornece dados para a expectativa com seis campos. O servidor guarda `estadia_id`, `placa`, `horas`, `tarifa_base`, `desconto` e `valor_centavos`. O formulário remete uma chave opaca. A apresentação organiza os números já calculados. [Objeto](../model/estadia.py#L16) · [Validação da expectativa](../service/representacoes.py#L25) · [Resumo P01](../web/templates/components/gestao.html)
4. O serviço recarrega o histórico, refaz a consulta e compara a expectativa na mesma operação protegida. Confirmar pagamento mantém a vaga e o faturamento. Concluir a saída exige uma confirmação compatível ou valor definitivo zero. O Repository publica o resultado antes do redirecionamento. [Operações financeiras](../service/estacionamento_service.py#L142) · [Validação da saída](../model/estadia.py#L76) · [Persistência](../service/estacionamento_service.py#L58)

## Objetos, composição e testes

| Responsabilidade | Aplicação concreta | Evidência |
|---|---|---|
| Encapsular uma revisão | A fábrica cria uma instância de `Revisoes` por aplicação. Ela mantém um índice privado, uma trava e limites de duração e quantidade. `emitir` cria uma `Revisao` vinculada ao token da sessão autenticada, à operação e à expiração. `obter` valida esses vínculos, devolve uma cópia dos campos escalares e, para escrita, consome a chave dentro da trava. | [Classes e métodos](../web/revisoes.py#L9) · [Isolamento e expiração](../tests/test_gestao.py#L230) · [Concorrência no cadastro](../tests/test_gestao.py#L244) |
| Preparar um relatório | `RelatorioSaidas.do_periodo` constrói um objeto imutável com a receita, quantidades pagas, isentas e legadas, e distribuições em tuplas. Cada observação é uma saída registrada. | [Classe](../web/eventos.py#L49) · [Teste da projeção](../tests/test_gestao.py#L155) |
| Separar HTTP, apresentação e negócio | O Blueprint compõe consultas públicas do serviço, aplica a guarda do papel e entrega dados ao Jinja. A instância de `OcupacaoViewModel` atende ao painel e aos relatórios. `ContaUsuario`, `Identidade`, `ContaRepository` e `AutenticacaoService` continuam respondendo pelo acesso. | [Rotas](../web/gestao.py) · [Modelo de ocupação](../web/apresentacao.py#L31) · [Teste das escritas protegidas](../tests/test_gestao.py#L181) |
| Compor as telas | G02 reutiliza V02 e D05. G09, G10 e G13 compartilham o resumo P01 e suas linhas monetárias. G04 e G12 compartilham a lista de eventos D06/D07. A revisão usa o controle de submissão existente e o menu responsivo expõe o estado expandido ao navegador. As macros parametrizadas compõem HTML. A execução da POO está nas classes Python e nos objetos JavaScript. | [Macros](../web/templates/components/gestao.html) · [Controles de interação](../web/static/js/controles.js) · [Percurso no navegador](../tests/navegador_08b.py) |

## Concorrência, recuperação e privacidade

- O Blueprint aplica o papel Gestão antes de atender qualquer rota administrativa. O CSRF da aplicação protege todos os POSTs. As consultas usam a identidade da sessão e as respostas privadas usam `no-store`. Os dados operacionais chegam exclusivamente pelo `EstacionamentoService`.
- As revisões duram até 15 minutos. O processo guarda até 4.096 revisões e descarta as mais antigas quando atinge o limite. Reiniciar o servidor exige revisar novamente formulários pendentes. Os pagamentos e as saídas persistidos continuam recuperáveis pelo identificador da estadia.
- Uma revisão repetida, expirada ou incompatível exige nova consulta. Em caso de resultado incerto, **Consultar estado** lê o ID original. Para uma estadia ativa com confirmação, a próxima ação elegível é concluir a saída. Para uma estadia concluída, a consulta devolve o comprovante. Se o próprio navegador perder a resposta, o operador pode reabrir a página da estadia pelo ID exibido na revisão ou no histórico. Reabrir por placa pode levar a outra utilização.
- Para cadastro com resultado incerto, consulte os registros. Duas submissões concorrentes do mesmo formulário compartilham uma única oportunidade de escrita. Formulários distintos continuam podendo cadastrar clientes homônimos. Uma busca pelo nome pode deixar a tentativa indeterminada.
- O provisionamento de contas pessoais permanece na CLI local. Ela serializa as escritas com a trava do repositório de contas e só consulta o estacionamento para validar o UUID. As leituras veem arquivos substituídos atomicamente. O servidor e a interface de terminal continuam reservando o histórico operacional com `EscritorLocal`. A implantação é local, com um processo servidor e múltiplas threads.

## Valores e períodos

O histórico mantém a posição original de cada evento, contando a partir de 1 antes de aplicar filtros. A entrada identificada fornece a categoria e o titular históricos do pagamento. O legado conserva seus próprios campos. A ausência de horário em um cadastro ou pagamento permanece visível pela ausência desse campo nos detalhes.

O filtro de período usa a **data civil registrada na saída**, incluindo as duas extremidades e respeitando o horário gravado mesmo quando o legado não traz fuso. A receita soma os valores definitivos identificados e os valores decimais legados do período. Registros positivos ou de valor zero no legado ficam em uma contagem própria porque esses eventos não registraram uma confirmação ou isenção identificada. As distribuições contam utilizações concluídas no período. O faturamento geral vem da consulta oficial do serviço e mantém a política de acumulação legada. Cada consulta pública lê um estado consistente por operação. Em uma tela composta, outra requisição pode concluir uma operação entre duas consultas.

### Evidência reproduzível

A fixture P0 utiliza arquivos temporários novos. Inclui duas clientes homônimas, uma saída legada de R$ 0,005, uma saída comum de R$ 40,00 e três vagas ocupadas. A estadia VIP 22 recebe base de R$ 12,25, desconto exato de R$ 6,125 e total de 613 centavos. Confirmar mantém sete vagas livres e R$ 40,005 de faturamento. Concluir deixa oito livres e R$ 46,135. A estadia 23 continua ativa. [Fixture](../tests/cenario_gestao.py) · [Teste com reabertura](../tests/test_gestao.py#L92)

```bash
source .venv/bin/activate
python -B -m unittest discover -s tests -v
pip check
```

O ensaio opcional usa Playwright para Python e Chrome/Chromium já disponíveis no ambiente de testes. Ele inicia um servidor em loopback com persistência temporária por percurso, testa os dois papéis, injeta uma falha após a gravação, imprime um PDF em memória e encerra o servidor. Com Playwright acessível ao interpretador de QA, utilize `python -B -m tests.navegador_08b --chrome /usr/bin/google-chrome`. A opção `--capturas` recebe uma pasta externa para os PNGs. [Ensaio](../tests/navegador_08b.py)
