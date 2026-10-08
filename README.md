# MOVE — Sistema Inteligente de Estacionamento

Projeto acadêmico de POO em Python, sem dependências externas.

## Critérios desta versão

- Dez vagas comuns: todas aceitam carro, moto e caminhão. Não há vagas especiais.
- Cadastro separado, com placa única normalizada (maiúsculas, sem espaços/hífens).
- Retirada por placa; horas informadas pelo usuário, incluindo frações e zero.
- Tarifas: carro R$ 10/h, moto R$ 5/h, caminhão R$ 20/h.
- Cadastro permanece após retirada; o mesmo veículo pode entrar novamente.
- Histórico JSON preserva cadastro, entradas, saídas, ocupação e faturamento entre execuções.
- JSON inválido impede inicialização; nunca é substituído silenciosamente.
- Operações antigas por vaga continuam disponíveis para compatibilidade.

## Executar no Termux

```sh
cd ~/MOVE
python -B main.py
python -B -m unittest discover -s tests -v
```

SQLite, aplicativo mobile e vagas especiais ficam para versões futuras.

## Demonstração pelo menu

1. Opção **5**: cadastrar carro, placa `abc-1234`, modelo `Onix`.
2. Opção **6**: estacionar `ABC1234` na vaga 1.
3. Opção **3**: uma ocupada, nove livres, faturamento zero.
4. Opção **7**: retirar `ABC1234`, informando duas horas: R$ 20.
5. Opção **3**: zero ocupadas, dez livres, faturamento R$ 20.
6. Opção **4**: salvar e sair.
7. Executar novamente e usar **3**: faturamento R$ 20 preservado.
8. Usar **6** com a mesma placa: cadastro já recuperado.

As opções 1 e 2 preservam o fluxo anterior. Na entrada rápida, placa já
cadastrada deve ter o mesmo tipo e modelo; dados divergentes são rejeitados.

## Classes e POO

- `Veiculo` é classe-base abstrata: placa/modelo comuns e contrato de tarifa.
- `Carro`, `Moto` e `Caminhao` herdam o construtor e implementam tarifas.
- `Vaga` contém um veículo ou nenhum; `ocupada` deriva dessa referência.
- `Estacionamento` cria dez vagas (composição), gerencia cadastro e eventos.
- `Controller` cria o tipo correto e encaminha operações.
- `view/ui_texto.py` recebe entradas, trata erros e apresenta resultados.
- `persistence/historico_json.py` lê, valida e grava o arquivo.

Atributos internos usam `_`; propriedades permitem leitura sem atribuição
pública. Vagas e veículos são expostos em tuplas, e o histórico é uma cópia
profunda. O encapsulamento em Python é uma convenção: acessar deliberadamente
atributos internos pode contornar a API.

O polimorfismo ocorre quando `Estacionamento.retirar` chama
`veiculo.calcular_tarifa(horas)`: cada subclasse responde com sua tarifa.

## Persistência e erros

O arquivo `historico.json` fica no diretório de execução. Use sempre `~/MOVE`
para manter o mesmo arquivo. O histórico é uma lista de eventos:

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
| Módulo simples de persistência | Separa operações de arquivo das entidades | Separação de responsabilidades, sem framework ou reestruturação geral. |

## Validação

Os oito testes anteriores permanecem intactos. Os novos testes cobrem contrato,
encapsulamento, cadastro, placa normalizada, duplicidade, vagas comuns, retirada
por placa, recuperação entre sessões, JSON antigo, corrupção, falha de gravação,
alteração externa e novos caminhos do menu. Arquivos de teste usam diretórios
temporários. A demonstração real de duas execuções foi feita em diretório
temporário para não inserir dados de exemplo no histórico do aluno.
