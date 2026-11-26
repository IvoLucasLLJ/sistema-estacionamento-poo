# Conceitos de programação orientada a objetos no MOVE

O caderno acompanha os capítulos 3–9. Cada excerto foi conferido no arquivo do checkpoint. Os nomes precedidos de sublinhado expressam convenções de uso em Python.

## Classe

Definição de um tipo com dados e operações comuns.

**Finalidade e relação entre os objetos.** Uma definição única torna a numeração e a transição de ocupação coerentes nas dez partes criadas por Estacionamento.__init__.

**Classe, atributos e operação.** Vaga • _numero, _veiculo. [Vaga](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/model/vaga.py#L4).

```python
class Vaga:
```

Uma mesma definição permite construir as dez partes com números diferentes. [Teste correspondente](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/tests/test_evolucao.py#L63).

## Objeto

Instância concreta cujo estado pode mudar sob uma identidade.

**Finalidade e relação entre os objetos.** Reter uma referência permite a Vaga.liberar devolver o mesmo objeto Veiculo que entrou. Duas vagas distintas mantêm estados independentes.

**Classe, atributos e operação.** Vaga e Veiculo • _veiculo. [Vaga.ocupar](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/model/vaga.py#L24).

```python
self._veiculo = veiculo
```

A vaga passa a referenciar aquele veículo até a liberação. [Teste correspondente](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/tests/test_nucleo.py#L63).

## Atributo

Dado associado à instância ou à classe, com escopo distinto.

**Finalidade e relação entre os objetos.** Ler o atributo da classe pela instância permite que Carro.calcular_tarifa e o catálogo do serviço consultem o mesmo preço autorizado.

**Classe, atributos e operação.** Carro • TARIFA_POR_HORA. [Carro](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/model/carro.py#L4).

```python
TARIFA_POR_HORA = 10
```

Preço horário compartilhado entre os carros e lido no catálogo pelo serviço. [Teste correspondente](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/tests/test_portal_cliente.py#L118).

## Método

Operação definida pelo tipo e vinculada ao objeto quando chamada sobre a instância.

**Finalidade e relação entre os objetos.** A estadia envia uma mensagem ao veículo concreto. A chamada reúne os dados da instância e o comportamento fornecido por sua classe.

**Classe, atributos e operação.** Moto • TARIFA_POR_HORA. [Moto.calcular_tarifa](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/model/moto.py#L8).

```python
return self.TARIFA_POR_HORA * horas
```

O resultado da mensagem depende da tarifa da classe concreta. [Teste correspondente](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/tests/test_nucleo.py#L25).

## Construtor e inicialização

A chamada à classe cria a instância; __init__ estabelece seu estado inicial após a criação.

**Finalidade e relação entre os objetos.** O construtor herdado impõe os mesmos critérios a Carro, Moto e Caminhao antes de o Controller registrar o objeto.

**Classe, atributos e operação.** Veiculo • _placa e _modelo. [Veiculo.__init__](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/model/veiculo.py#L5).

```python
self._placa = self.normalizar_placa(placa)
```

Uma subclasse concreta herda a normalização e a validação do modelo. [Teste correspondente](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/tests/test_evolucao.py#L20).

## Instanciação

Produção de um objeto concreto a partir de sua classe.

**Finalidade e relação entre os objetos.** Criar dez instâncias no agregado preserva um número e uma ocupação próprios por posição. A propriedade vagas publica uma tupla dessas referências.

**Classe, atributos e operação.** Estacionamento • _vagas. [Estacionamento.__init__](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/model/estacionamento.py#L35).

```python
self._vagas = [Vaga(num+1) for num in range(10)]
```

Cada avaliação de Vaga cria uma parte distinta do mesmo estacionamento. [Teste correspondente](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/tests/test_evolucao.py#L63).

## Estado

Conjunto de valores que afeta a resposta do objeto em um instante.

**Finalidade e relação entre os objetos.** Guardar a cobrança em Estadia.pagamento permite a situacao_para_saida verificar se a utilização pode terminar.

**Classe, atributos e operação.** Estadia • pagamento. [Estadia.confirmar_pagamento](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/model/estadia.py#L67).

```python
self.pagamento = cobranca
```

Depois da confirmação, a duração aceita fica vinculada à cobrança. [Teste correspondente](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/tests/test_estadias.py#L129).

## Encapsulamento

Acesso ao comportamento por uma interface que preserva as condições internas.

**Finalidade e relação entre os objetos.** Separar a coleção interna de sua cópia preserva a ordem dos eventos mesmo se um consumidor modificar o resultado da consulta.

**Classe, atributos e operação.** Estacionamento • _historico. [Estacionamento.historico](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/model/estacionamento.py#L51).

```python
return deepcopy(self._historico)
```

Uma consulta pode alterar a cópia recebida sem alterar o agregado. [Teste correspondente](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/tests/test_repository.py#L120).

## Abstração

Contrato que expõe o que é necessário para usar um objeto e oculta escolhas concretas.

**Finalidade e relação entre os objetos.** A interface entre Estadia e Veiculo limita o conhecimento necessário para calcular a base. O cliente comercial intervém somente após esse cálculo.

**Classe, atributos e operação.** Estadia e Veiculo • veiculo. [Estadia.consultar_cobranca](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/model/estadia.py#L47).

```python
base = self.veiculo.calcular_tarifa(horas)
```

A estadia pode operar com um veículo sem nomear sua subclasse. [Teste correspondente](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/tests/test_estadias.py#L66).

## Classe abstrata

Tipo de base com operações cuja implementação é exigida para instanciação concreta.

**Finalidade e relação entre os objetos.** Definir calcular_cobranca como abstrato torna explícita a operação que toda categoria concreta aceita. O construtor comum concentra nome e identidade.

**Classe, atributos e operação.** Cliente • nome e identificador. [Cliente](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/model/cliente.py#L10).

```python
class Cliente(ABC):
```

O decorador abstractmethod impede instanciar Cliente enquanto o contrato faltar. [Teste correspondente](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/tests/test_clientes.py#L11).

## Herança

Relação de especialização que permite reutilizar e estender a definição da base.

**Finalidade e relação entre os objetos.** Especializar Cliente conserva a semântica do identificador e a validação de valores enquanto permite que cada subclasse determine o resultado comercial.

**Classe, atributos e operação.** ClienteVIP e Cliente • CATEGORIA. [ClienteVIP](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/model/cliente_vip.py#L4).

```python
class ClienteVIP(Cliente):
```

O VIP herda a inicialização e o acesso ao UUID, comuns às categorias. [Teste correspondente](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/tests/test_clientes.py#L15).

## Sobrescrita

Uma classe derivada fornece implementação própria para uma operação herdada.

**Finalidade e relação entre os objetos.** ClienteVIP responde à mesma operação aceita por ClienteComum. A sobrescrita localiza a política de desconto em uma única implementação.

**Classe, atributos e operação.** ClienteVIP • calcular_cobranca. [ClienteVIP.calcular_cobranca](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/model/cliente_vip.py#L7).

```python
return tarifa_base / 2
```

A regra especializa a cobrança do contrato comum após validar a base. [Teste correspondente](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/tests/test_clientes.py#L20).

## Polimorfismo

Uma única mensagem seleciona comportamento segundo o tipo efetivo do objeto.

**Finalidade e relação entre os objetos.** Compor as respostas de dois objetos evita uma decisão tarifária para cada par possível de subclasses. O caso de uma hora distingue seis cobranças positivas e três isentos.

**Classe, atributos e operação.** Estadia e Cliente • cliente. [Estadia.consultar_cobranca](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/model/estadia.py#L47).

```python
devido = Decimal(self.cliente.calcular_cobranca(base))
```

A mesma operação de estadia obtém integral, metade ou zero. [Teste correspondente](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/tests/test_qualidade_10a5.py#L126).

## Composição

Relação todo–parte cujo proprietário cria e organiza suas partes.

**Finalidade e relação entre os objetos.** Estacionamento cria e conserva cada Vaga. Os veículos associados podem sair e retornar à mesma parte numerada.

**Classe, atributos e operação.** Estacionamento e Vaga • _vagas. [Estacionamento.__init__](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/model/estacionamento.py#L35).

```python
self._vagas = [Vaga(num+1) for num in range(10)]
```

O agregado forma as dez vagas durante sua construção. O leitor recebe uma tupla. [Teste correspondente](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/tests/test_evolucao.py#L63).

## Associação

Ligação entre objetos com identidades e ciclos de vida distintos.

**Finalidade e relação entre os objetos.** Vincular dois cadastros satisfaz um pré-requisito de entrada sem fazer do veículo uma parte criada ou destruída com o cliente.

**Classe, atributos e operação.** Estacionamento, Cliente e Veiculo • _vinculos. [Estacionamento.vincular_veiculo](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/model/estacionamento.py#L80).

```python
self._vinculos[veiculo.placa] = cliente
```

O cliente e o veículo existem antes do vínculo e continuam cadastrados após a saída. [Teste correspondente](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/tests/test_estadias.py#L30).

## Imutabilidade

Um valor construído preserva os campos que definem sua igualdade durante sua utilização.

**Finalidade e relação entre os objetos.** Confrontar uma expectativa anterior com a cobrança atual exige que o objeto revisado preserve estadia_id, placa, horas, tarifa_base, desconto e valor_centavos.

**Classe, atributos e operação.** Cobranca • valor_centavos, placa, horas, base e desconto. [Cobranca](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/model/estadia.py#L16).

```python
@dataclass(frozen=True)
```

Campos escalares e Decimal tornam a cotação estável para comparação com nova consulta. [Teste correspondente](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/tests/test_estadias.py#L129).

## Exceção

Sinalização que interrompe o fluxo normal antes de realizar uma transição inválida.

**Finalidade e relação entre os objetos.** Validar antes da atribuição conserva a primeira ocupação quando uma segunda entrada é recusada. O serviço pode então apresentar o erro de negócio.

**Classe, atributos e operação.** Vaga • _veiculo. [Vaga.ocupar](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/model/vaga.py#L24).

```python
if self.ocupada:
```

Tentar ocupar a vaga já ocupada produz ValueError e conserva a primeira ocupação. [Teste correspondente](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/tests/test_nucleo.py#L63).

## Responsabilidade

Delimitação dos dados e decisões que cabem a um objeto para manter coesão.

**Finalidade e relação entre os objetos.** O repositório delega a interpretação dos eventos ao agregado e a leitura dos bytes à persistência. O Controller recebe o estacionamento reconstruído.

**Classe, atributos e operação.** EstacionamentoRepository • _conteudo_esperado. [EstacionamentoRepository.carregar](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/repository/estacionamento_repository.py#L18).

```python
estacionamento = Estacionamento.reconstruir(dados)
```

O repositório lê e devolve o agregado validado; o domínio interpreta os eventos. [Teste correspondente](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/tests/test_repository.py#L22).
