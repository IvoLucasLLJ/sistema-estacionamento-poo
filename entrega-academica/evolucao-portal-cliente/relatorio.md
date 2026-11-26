# Veículos, reservas e compra de categoria no MOVE

Ivo Lucas de Lima Júnior · Análise e Desenvolvimento de Sistemas · Programação Orientada a Objetos · 2026/2

O portal Cliente passou a permitir três operações que antes dependiam do atendimento ou não existiam no sistema. O titular pode cadastrar veículos, reservar uma vaga livre e comprar uma mudança de categoria com pagamento simulado.

## O que o professor pode avaliar

**Cadastro de veículos.** Ao criar a conta, o cliente pode marcar “Cadastrar meus veículos logo após criar a conta”. O MOVE abre a ficha de veículos, onde é possível informar tipo, placa e modelo e repetir o cadastro para cada veículo. O registro e o vínculo com o titular são gravados juntos. Uma placa já cadastrada conserva seu responsável. Na Gestão, o mesmo formulário também está disponível na ficha do cliente recém-criado.

**Reserva de vaga.** Em “Disponibilidade”, o cliente vê os números das vagas livres, escolhe uma vaga e confirma um veículo próprio. A vaga sai da lista de livres, mas o estacionamento só passa a contá-la como ocupada quando a Gestão registra a entrada desse veículo. O titular pode cancelar a reserva na mesma tela. Cada veículo pode ter uma reserva ativa, válida até a entrada ou o cancelamento.

**Mudança de categoria.** Em “Tarifas e benefícios”, o cliente escolhe a categoria, revisa o valor e confirma a operação simulada. A diferença entre os níveis determina o preço do upgrade. A redução de categoria é gratuita, sem reembolso. A operação é avulsa, sem renovação automática. O histórico pessoal de mudanças permite conferir o valor registrado.

| Categoria | Valor de referência | Cobrança por estadia |
|---|---|---|
| Comum | R$ 0,00 | Tarifa integral do veículo |
| VIP | R$ 250,00 | Desconto de 50% |
| Mensalista | R$ 500,00 | R$ 0,00 por utilização |

**Exemplo financeiro.** Do Comum para VIP, a compra custa R$ 250,00. Do VIP para Mensalista, custa mais R$ 250,00. Do Comum direto para Mensalista, custa R$ 500,00. A categoria aplicável à estadia continua sendo a da entrada. Uma estadia de carro iniciada como Comum custa R$ 10,00 por uma hora mesmo que o cliente compre o upgrade antes da saída.

## Demonstração e verificação

1. Crie uma conta Comum, marque a opção de cadastrar veículos e adicione um carro e uma moto. Confira que ambos aparecem em “Meus veículos”.
2. Em “Disponibilidade”, reserve uma vaga para o carro. Em outra sessão, abra o mapa da Gestão, selecione a vaga reservada e registre a entrada. Ao atualizar o portal Cliente, confira a estadia ativa.
3. No Cliente, abra “Tarifas e benefícios” e simule as compras de VIP e Mensalista. Confira os dois lançamentos de R$ 250,00. Pela Gestão, consulte uma hora da estadia aberta e compare com a cobrança de uma nova entrada como Mensalista.

**Onde aparece a POO.** A classe Vaga controla a passagem entre livre, reservada e ocupada. ReservaVaga guarda a identidade da reserva, o titular e a placa. O cadastro do cliente mantém o mesmo UUID após a mudança de categoria. Cada Estadia conserva o objeto Cliente recebido na entrada e utiliza seu método polimórfico para calcular a cobrança. O serviço persiste os eventos no JSON e as rotas obtêm o titular da sessão autenticada.

**Validação local.** A suíte passou de 196 para 202 testes aprovados. As seis novas regressões cobrem cadastro e vínculo dos veículos, disputa pela mesma vaga, cancelamento, consumo da reserva na entrada, preço progressivo, preservação de estadias anteriores, reabertura do histórico e o percurso HTTP autenticado.

**Validação no navegador.** O percurso foi executado no Google Chrome em 1440 × 900 e em uma janela móvel emulada de 390 × 844, com toque. Foram utilizados clientes fictícios e arquivos temporários. O ensaio incluiu o cadastro de um caminhão pela Gestão. As compras simuladas ficam separadas do faturamento das estadias concluídas.
