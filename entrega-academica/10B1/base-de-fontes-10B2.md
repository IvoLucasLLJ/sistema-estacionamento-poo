# Base de fontes para o futuro ensaio acadêmico

Os recortes a seguir permitem desenvolver questões independentes da descrição do sistema. São pontos de partida para a etapa posterior.

## Contratos e variação

**Questão.** Qual decisão fica mais simples quando veículo e cliente respondem por contratos distintos? Contrastar o despacho de dois métodos em Estadia com as escolhas explícitas de classe no cadastro. Explicar por que a escolha concreta continua necessária em uma fronteira. Conferir os cinco comandos do exemplo do capítulo 7 e a tabela de uma hora. [Estadia.consultar_cobranca](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/model/estadia.py#L47) · [Controller._criar_veiculo](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/controller/controller.py#L52) · [Oráculo para as combinações](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/tests/test_qualidade_10a5.py#L126). Leitura de apoio: [DeNero, seção 2.5](https://www.composingprograms.com/pages/25-object-oriented-programming.html).

## Identidade e responsabilidade

**Questão.** O que se perde ao tratar uma placa como identidade histórica ou uma categoria como permissão? Confrontar a identidade comercial, o identificador da entrada e a identidade ativa de uma sessão. O caso dos homônimos e a recusa de um comprovante de terceiro oferecem contraexemplos concretos. [Cliente](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/model/cliente.py#L10) · [ContextoAcesso](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/web/contas.py#L40) · [Consulta pessoal](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/web/consultas_pessoais.py#L16) · [Resposta pública equivalente](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/tests/test_portal_cliente.py#L81).

## Encapsulamento e persistência

**Questão.** O que o agregado protege enquanto está em memória e o que depende do protocolo de publicação em arquivo? Examinar a cópia do histórico, a reconstituição de objetos e a escrita em etapas do autocadastro. Uma eventual interrupção oferece um limite observável para a discussão sobre atomicidade e recuperação. [Propriedade historico](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/model/estacionamento.py#L51) · [Repository.carregar](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/repository/estacionamento_repository.py#L18) · [Retomada concorrente da mesma reserva](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/tests/test_qualidade_10a5.py#L69). Apoio: [Hieatt e Mee, Repository](https://martinfowler.com/eaaCatalog/repository.html).

## O que os testes permitem afirmar

**Questão.** Executar um ramo é suficiente para detectar uma mudança de comportamento? Comparar os denominadores de cobertura, uma mutação financeira selecionada e o oráculo independente em Decimal. Relacionar a divergência de faturamento legado com o momento da conversão. Delimitar o alcance das 19 mutações e das amostras de navegador. [Cobertura Python](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/qa/evidencias/cobertura.json) · [Mutantes e testes detectores](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/qa/evidencias/mutacao.json) · [Relato dos três defeitos](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/docs/qualidade-10a5.md) · [Semântica da cobertura de ramos](https://coverage.readthedocs.io/en/latest/branch.html).

## Representação visual e execução

**Questão.** Que informação de uma interface reaparece em um objeto de apresentação e que comportamento só existe no código? Comparar uma instância da biblioteca visual, a composição Jinja2 e uma instância JavaScript que reage ao sistema. Examinar o [quadro de implementação](https://www.figma.com/design/oamoaxU0OJRHHKcuLIlFOi?node-id=55-7672), [OcupacaoViewModel](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/web/apresentacao.py#L24), [ControleTema](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/blob/fa323dca437853cdd6cd64c1f1c682298dd88ecb/web/static/js/controles.js#L3) e os diagramas 03 e 04 do [atlas](Atlas_UML.pdf).

## Assistência por inteligência artificial e avaliação acadêmica

**Questão.** Quais decisões podem ser atribuídas com segurança ao acadêmico, quais atividades receberam assistência e quais atribuições individuais continuam indeterminadas? Cruzar as determinações de escopo e o aceite visual relatado com a sequência pública de commits e os defeitos encontrados após as implementações. Uma revisão datada comprova uma alteração. Isoladamente, ela não mede aprendizado nem identifica quem elaborou cada linha. Utilizar o [inventário e a cronologia](fontes-e-evidencias.md), as capturas rastreadas e o capítulo 20 como conjunto documental.
