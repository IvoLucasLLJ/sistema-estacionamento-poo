# MOVE — Sistema Inteligente de Estacionamento

Projeto acadêmico de POO em Python com aplicação web Flask, interface de terminal e persistência JSON.

## Abrir a demonstração acadêmica

| Ambiente | Inicializador |
|---|---|
| Linux | `./INICIAR_MOVE_LINUX.sh` |
| macOS Intel ou Apple Silicon | Abrir `INICIAR_MOVE_MAC.command` |
| Windows 10/11 x64 | Abrir `INICIAR_MOVE_WINDOWS.cmd` em uma pasta privada NTFS |
| Android 15+ com Termux | Na pasta interna `$HOME/MOVE`, executar `sh INICIAR_MOVE_ANDROID.sh` |

Use Python 3 com venv e pip. No Android, use o Python dos pacotes do Termux.
Na primeira abertura, escolha no terminal senhas distintas para `gestao.demo`, `cliente.demo` e `master.demo`.
Para a apresentação, entre como **master.demo** e use o seletor junto à marca MOVE para alternar da Gestão para o portal pessoal de Lia Vale. Em uma demonstração já instalada, o inicializador solicita apenas as senhas das contas que faltam.
O endereço padrão é `http://127.0.0.1:5000/entrar`. Encerre com Ctrl+C.
O guia distingue as plataformas em preparação das efetivamente testadas.
[Inicialização](docs/inicializacao-10a2.md) · [Matriz de compatibilidade](docs/compatibilidade-10a1.md) · [Instalação e aceite no Android](docs/android-termux.md)

## Executar a aplicação web

Para usar o histórico operacional, prepare o ambiente na raiz do repositório e
provisione a primeira conta de Gestão. O comando solicita a senha duas vezes
com entrada oculta. Em um ambiente já preparado, ative a mesma `.venv` e use
apenas o comando de inicialização.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m flask --app web criar-conta --usuario operador --papel gestao
python -B -m web
```

Abra [o login local](http://127.0.0.1:5000/entrar). O terminal continua disponível com `python3 -B main.py`. Os dois executáveis reservam o histórico durante o uso.

O guia da 08A apresenta o provisionamento pessoal por UUID, os arquivos privados, as opções de ambiente, a arquitetura de apresentação e a reprodução dos testes. [Guia da aplicação web](docs/web-08a.md)

O guia da Gestão descreve os 14 modelos administrativos, o fluxo de pagamento e saída, a recuperação por estadia e os testes em Chromium. [Guia MOVE Gestão](docs/web-08b.md)

No portal Cliente é possível cadastrar vários veículos, reservar uma vaga livre, acompanhar as estadias e imprimir os comprovantes. Em **Tarifas e benefícios**, a compra simulada cobra a diferença entre as categorias Comum (R$ 0,00), VIP (R$ 250,00) e Mensalista (R$ 500,00). A categoria da entrada determina a cobrança daquela estadia. [Guia MOVE Cliente](docs/web-08c.md) · [Relatório das novidades e roteiro para o professor](entrega-academica/evolucao-portal-cliente/MOVE_Relatorio_Evolucao_Cliente.pdf)

## Serviço de aplicação — Etapa 05

`service.estacionamento_service.EstacionamentoService(arquivo)` é a entrada Python
para os casos de uso de MOVE Cliente e MOVE Gestão. A arquitetura é
`serviço → Controller → domínio`, com `Controller → Repository → arquivo JSON`
para carga e gravação. O menu textual mantém seu ciclo de salvamento da versão 3.

| Operações do serviço | Contrato |
|---|---|
| `cadastrar_cliente(categoria, nome)`, `buscar_cliente(identificador)`, `listar_clientes()` | Cadastro ou consulta por UUID. Cada registro contém identificador, nome e categoria. |
| `cadastrar_veiculo(tipo, placa, modelo)`, `buscar_veiculo(placa)`, `listar_veiculos()` | Veículos com placa normalizada, tipo, modelo e motorização opcional. |
| `vincular_veiculo(placa, cliente_id)`, `veiculos_do_cliente(cliente_id)`, `cliente_do_veiculo(placa)` | O vínculo retorna as duas chaves. A consulta do responsável retorna `None` para um veículo cadastrado sem vínculo. |
| `consultar_vagas()`, `consultar_ocupacao()` | Mapa administrativo das 200 vagas em ordem numérica. A consulta agregada informa livres, ocupadas e total. A opção detalhada inclui indicadores por classificação. |
| `iniciar_estadia(placa, vaga, cliente_id)`, `listar_estadias_ativas()`, `consultar_estadia(estadia_id)` | Entrada identificada, ocupações atuais e detalhe de uma estadia identificada, inclusive após a saída. A ocupação legada aparece com suas chaves de cliente e estadia nulas. |
| `consultar_cobranca(placa, horas)` | Cotação sem gravação, com identificador da estadia, placa, horas, tarifa-base, desconto e valor final em centavos. |
| `confirmar_pagamento(placa, horas, expectativa, confirmado=True)`, `consultar_pagamento(placa)` | Confirmação simulada explícita. A consulta retorna a cobrança confirmada da estadia vinculada ativa, ou `None` enquanto aguarda confirmação. |
| `concluir_saida(placa, horas, expectativa)` | Retorna a estadia concluída e libera a vaga após pagamento confirmado ou por isenção. |
| `listar_pagamentos_abertos()`, `consultar_faturamento()`, `consultar_historico()` | Cobranças confirmadas de estadias ainda abertas, total das saídas concluídas e cópia dos eventos em ordem. |

O chamador pode enviar as horas em texto decimal com ponto. A permanência segue
informada pelo usuário. Em `expectativa`, devolva o dicionário recebido de
`consultar_cobranca`. O serviço recalcula a cotação para a placa e a duração
solicitadas, confere seus seis campos e encaminha a cobrança calculada pelo
domínio. Uma nova entrada da mesma placa recebe outro identificador. Uma
resposta antiga é rejeitada mesmo quando as horas e os centavos coincidem.

```python
from pathlib import Path
from tempfile import TemporaryDirectory
from service.estacionamento_service import EstacionamentoService

with TemporaryDirectory() as pasta:
    arquivo = Path(pasta) / "exemplo.json"
    s = EstacionamentoService(arquivo)
    cliente = s.cadastrar_cliente("vip", "Cliente fictício")
    s.cadastrar_veiculo("carro", "DEMO1", "Modelo")
    s.vincular_veiculo("DEMO1", cliente["identificador"])
    entrada = s.iniciar_estadia("DEMO1", 1, cliente["identificador"])
    cotacao = s.consultar_cobranca("DEMO1", "1.225")
    s.confirmar_pagamento("DEMO1", "1.225", cotacao, confirmado=True)
    s.concluir_saida("DEMO1", "1.225", cotacao)
    assert EstacionamentoService(arquivo).consultar_faturamento()["centavos"] == 613
```

As respostas são listas, dicionários e valores simples. Os horários preservam o
formato ISO dos eventos. Horas, tarifa-base e desconto das cobranças são textos
decimais. O valor definitivo das novas cobranças é um inteiro em centavos.
No histórico de consulta, o campo `valor` de uma saída legada é a representação
textual do número recuperado pelo domínio. O faturamento expõe `reais` em texto
e `centavos` inteiro quando a conversão é exata. Por exemplo, um total misto de
R$ 10,005 produz `{"reais": "10.005", "centavos": null}`. Se a soma de valores
legados exceder o intervalo de ponto flutuante do relatório antigo, a resposta
expõe `"Infinity"` e centavos nulos. O arquivo continua usando o formato anterior.

### Concorrência e recuperação

Cada chamada adquire o bloqueio do caminho absoluto resolvido do arquivo,
carrega e valida o histórico em um Controller exclusivo e produz uma resposta
independente dos objetos do domínio. Nas escritas, a resposta só é entregue
depois do salvamento atômico. As consultas usam o mesmo bloqueio. Instâncias
que apontam para o mesmo caminho compartilham o bloqueio dentro de **um único
processo servidor**. Caminhos distintos podem avançar em paralelo.
**A interface textual e o servidor web não deverão escrever simultaneamente no
mesmo histórico.** Processos independentes ficam fora da proteção de threads.
O Repository continua comparando os bytes do destino antes da substituição.

- `ErroDeNegocio` indica que a solicitação foi recusada, como placa em uso ou cotação antiga.
- `ErroDeInfraestrutura` cobre histórico inválido, falha de leitura e falha de gravação. Se a escrita falhar no temporário, o estado de trabalho é descartado. Uma nova chamada válida pode ser feita após resolver a causa.
- `ConflitoDeHistorico` indica que a versão em disco mudou desde a leitura. O arquivo externo é preservado.
- `ResultadoIncerto` indica perda da confirmação da gravação. O serviço relê e valida o arquivo sob o bloqueio. Se os bytes anteriores estão intactos, informa falha de gravação. Caso contrário, o atributo `verificacao` registra `operacao_presente`, `historico_divergente` ou `releitura_indisponivel`. Após uma confirmação incerta ou a perda de uma resposta, consulte a estadia pelo identificador e o histórico antes de decidir como prosseguir. O serviço nunca repete o pagamento ou a saída automaticamente.

UUID, placa e identificador da estadia identificam registros. A autenticação e
a autorização das interfaces pertencem a uma etapa posterior. A carga e a
validação do histórico completo a cada chamada priorizam consistência e têm
custo crescente com o número de eventos.

## Estacionamento e compatibilidade com o exercício da Aula 09

- Capacidade padrão de 200 vagas. O mapa oferece dez setores de vinte vagas, com filtros de classificação, estado, equipamento e destinação VIP. [Distribuição, migração e roteiro de demonstração](docs/move-2/ADENDO.md)
- Cadastro separado, com placa única normalizada (maiúsculas, sem espaços/hífens).
- Retirada por placa; horas informadas pelo usuário, incluindo frações e zero.
- Tarifas: carro R$ 10/h, moto R$ 5/h, caminhão R$ 20/h.
- Cadastro permanece após retirada; o mesmo veículo pode entrar novamente.
- Histórico JSON preserva cadastro, entradas, saídas, ocupação e faturamento entre execuções.
- JSON inválido impede inicialização; nunca é substituído silenciosamente.
- Operações antigas por vaga continuam disponíveis para compatibilidade.

## Executar no Termux

O aparelho hospeda a Gestão, o Cliente e o terminal na própria instalação. Depois de preparar o ambiente com o inicializador Android, use `.venv/bin/python -B main.py` para o menu textual. O guia inclui instalação, utilização sem internet e recuperação após interrupções. [MOVE completo em Android 15 e 16](docs/android-termux.md)

## Demonstração pelo menu

1. Opção **5**: cadastrar carro, placa `abc-1234`, modelo `Onix`.
2. Opção **6**: estacionar `ABC1234` na vaga 1.
3. Opção **3**: uma ocupada, 199 livres, faturamento zero.
4. Opção **7**: retirar `ABC1234`, informando duas horas: R$ 20.
5. Opção **3**: zero ocupadas, 200 livres, faturamento R$ 20.
6. Opção **4**: salvar e sair.
7. Executar novamente e usar **3**: faturamento R$ 20 preservado.
8. Usar **6** com a mesma placa: cadastro já recuperado.

As opções 1 e 2 preservam o fluxo anterior. Na entrada rápida, placa já
cadastrada deve ter o mesmo tipo e modelo; dados divergentes são rejeitados.

## Classes e POO

- `Veiculo` é classe-base abstrata: placa/modelo comuns e contrato de tarifa.
- `Carro`, `Moto` e `Caminhao` herdam o construtor e implementam tarifas.
- `Vaga` contém um veículo ou nenhum; `ocupada` deriva dessa referência.
- `Estacionamento` compõe as 200 vagas e seus equipamentos, gerencia cadastro e eventos.
- `Controller` cria o tipo correto, encaminha operações e coordena o Repository.
- `repository/estacionamento_repository.py` carrega/salva o agregado e controla a referência para detectar alterações externas.
- `view/ui_texto.py` recebe entradas, trata erros e apresenta resultados.
- `persistence/historico_json.py` decodifica JSON e executa a gravação atômica.
- `Estacionamento.reconstruir(dados)` valida e reproduz eventos em memória, sem acessar arquivos.

Atributos internos usam `_`; propriedades permitem leitura sem atribuição
pública. Vagas e veículos são expostos em tuplas, e o histórico é uma cópia
profunda. O encapsulamento em Python é uma convenção: acessar deliberadamente
atributos internos pode contornar a API.

O polimorfismo ocorre quando `Estacionamento.retirar` chama
`veiculo.calcular_tarifa(horas)`: cada subclasse responde com sua tarifa.

## Persistência e erros

O terminal e o servidor usam `historico.json` ao lado de `main.py`, inclusive
quando o terminal é aberto de outra pasta. Para continuar usando um histórico
guardado em outro lugar, defina `MOVE_HISTORICO` com o caminho absoluto desse
arquivo em ambas as execuções. Caminhos relativos em `MOVE_HISTORICO`,
`MOVE_DADOS` e `MOVE_CONTAS` partem da raiz da instalação. Se antes você usava
um caminho relativo a outra pasta, use o endereço absoluto anterior para
reabrir os mesmos dados. Consulte a [matriz de compatibilidade](docs/compatibilidade-10a1.md).
O histórico é uma lista de eventos:

- `cadastro`: placa, tipo e modelo;
- `entrada`: placa, tipo, modelo, vaga e horário de entrada;
- `saida`: esses dados, horário de saída, horas informadas e valor.

Na abertura, os eventos são reproduzidos em ordem usando as regras do modelo.
Isso recupera cadastros, vagas ainda ocupadas e faturamento acumulado. Horários
originais são mantidos. Sem arquivo, inicia uma sessão vazia.

Arquivos da versão anterior com entradas/saídas e sem modelo são aceitos;
nesse caso o modelo fica `Modelo não registrado`. Históricos incompletos de
versões mais antigas, sem os campos necessários, são rejeitados: não há dados
suficientes para reconstruir o estado com segurança.

JSON malformado, evento desconhecido ou sequência inconsistente interrompe a
abertura com mensagem; o arquivo fica intacto. Erros de acesso também são
mostrados. Ao sair, grava um temporário no mesmo diretório, descarrega os dados
e substitui o destino com `os.replace`. Falha antes da substituição preserva o
arquivo anterior e permite tentar novamente. Alteração externa detectada desde
a leitura bloqueia a sobrescrita; reinicie após preservar/resolver o arquivo.

Execute uma instância por vez: a detecção de alterações não é um bloqueio de
concorrência. O salvamento acontece na opção 4; encerramento forçado pode perder
operações ainda não salvas. A permanência não é calculada pelo relógio, e não há
arredondamento financeiro específico além da apresentação com duas casas.

## Decisões desta versão

| Decisão | Motivo e impacto | Conceito de POO / defesa oral |
|---|---|---|
| Propriedades de leitura e ocupação derivada | Evita alterações públicas que contradizem o veículo presente | Encapsulamento: “a vaga controla seu próprio estado”. |
| `Veiculo` abstrato | Impede veículo concreto sem tarifa | Abstração/herança: “cada tipo precisa definir o cálculo”. |
| Cadastro separado e busca por placa | Atende casos de uso; cadastro permanece após saída | Responsabilidade: “o estacionamento gerencia os veículos cadastrados”. |
| Recuperação por eventos JSON | Preserva formato de lista e histórico anterior, sem banco | Objetos recuperados reaplicam as mesmas regras de negócio. |
| Repository coordenado pelo Controller | Encapsula carga/salvamento e detecção de alterações; utiliza o módulo JSON | Separação entre domínio, coordenação e acesso a dados. |

## Arquitetura da Aula 09 e adaptação ao MOVE

A referência `REFERENCIA_AULA09/ProjetoParkSys_2` introduz
`EstacionamentoRepository`: o Controller coordena a carga e o salvamento,
enquanto o Model cuida das regras de negócio. O MOVE v3 adota essa divisão.

O professor grava um objeto com `historico` e `vagas`, reconstruindo os tipos
concretos das vagas ocupadas. O MOVE mantém sua lista de eventos JSON para
preservar os arquivos anteriores e recuperar também veículos cadastrados que
estão fora do estacionamento. A reconstrução reaplica as regras em um agregado
novo, rejeita tipos desconhecidos e só retorna depois de validar tudo. A vaga
ocupada aponta para o mesmo objeto do cadastro, preservando o polimorfismo.

Fluxo principal: `UI → Controller → Model`, com `Controller → Repository →
persistence/historico_json.py` para acesso ao arquivo. O Repository solicita ao
Model a reconstrução em memória e usa a cópia pública do histórico ao salvar;
não altera atributos internos do domínio. Os bytes esperados do arquivo ficam
no Repository e só são atualizados após carga válida ou gravação bem-sucedida.

Uso direto:

```python
from repository.estacionamento_repository import EstacionamentoRepository

repository = EstacionamentoRepository("historico.json")
estacionamento = repository.carregar()
# Operações de negócio no estacionamento...
repository.salvar(estacionamento)
```

`Controller(arquivo)` continua aceitando um destino personalizado. Também aceita
`Controller(repository=repository)` para injeção de um repositório. Um Repository
novo precisa carregar um arquivo existente antes de sobrescrevê-lo.

Os métodos `Estacionamento.carregar_historico` e `salvar_historico` e a função
antiga `persistence.historico_json.carregar` permanecem como adaptadores da API
v2. Eles delegam ao Repository; o Controller não os utiliza. As regras do Model
e a reconstrução podem ser utilizadas sem acesso ao sistema de arquivos.

A referência foi apenas lida. SQLite e interface gráfica não fazem parte desta
rodada. O Prompt Mestre não foi encontrado como arquivo no projeto; a adaptação
segue os requisitos fornecidos e o código da Aula 09.

## Validação

Comando executado na versão 3:

```sh
python -B -m unittest discover -s tests -v
```

Resultado: **26 testes passaram**, sendo os 18 casos anteriores e oito novos.
O teste anterior de salvamento do Controller teve seu mock ajustado para
verificar a delegação ao Repository, conforme a nova arquitetura. Os demais
casos anteriores não foram alterados.

Os testes adicionais verificam injeção do Repository, independência dos
adaptadores, reconstrução das três subclasses, identidade entre cadastro e
vaga, preservação de horários, isolamento de dados, conflito entre sessões,
repetição após falha de gravação, tipos desconhecidos, destino existente e
compatibilidade do salvamento legado. Os testes de persistência usam diretórios
temporários. A suite anterior também cobre JSON antigo, corrupção, cadastro,
retirada, tarifas, faturamento e caminhos do menu.
