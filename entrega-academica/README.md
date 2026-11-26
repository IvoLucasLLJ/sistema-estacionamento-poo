# MOVE — Materiais para avaliação acadêmica

O relatório de 25 páginas, o atlas de 17 diagramas, a apresentação de 23 slides e suas capturas documentam o [checkpoint funcional original](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/commit/fa323dca437853cdd6cd64c1f1c682298dd88ecb).

## Ampliações posteriores

| Material | Uso na avaliação |
|---|---|
| [Evolução do portal Cliente em PDF](evolucao-portal-cliente/MOVE_Relatorio_Evolucao_Cliente.pdf) · [Texto editável](evolucao-portal-cliente/relatorio.md) | Cadastro de múltiplos veículos, reservas e cancelamentos, compras simuladas e preservação da categoria da estadia original. |
| [Adendo MOVE 2.0](../docs/move-2/ADENDO.md) · [Capturas da aplicação](../docs/move-2/capturas/) | Distribuição das 200 vagas, UML do núcleo ampliado, elegibilidade, equipamentos, destinação VIP e roteiro integrado. |
| [Manual de execução](../docs/inicializacao-10a2.md) | Instalação pelos quatro inicializadores e escolha entre a demonstração inicial e o cenário de vagas inteligentes. |

## Relatório, arquitetura e rastreabilidade

| Material | Arquivos | Finalidade |
|---|---|---|
| Relatório técnico, 25 páginas | [PDF](10B1/MOVE_Relatorio_Tecnico.pdf) · [Word editável](10B1/MOVE_Relatorio_Tecnico.docx) · [Markdown](10B1/MOVE_Relatorio_Tecnico.md) | Ler o relatório paginado ou consultar o texto e suas referências em formato editável. |
| Atlas UML, 17 diagramas | [Atlas em PDF](10B1/Atlas_UML.pdf) · [Índice por diagrama](10B1/uml/indice.html) · [Fontes PlantUML](10B1/uml/fontes/) · [Exportações SVG](10B1/uml/svg/) | Localizar cada diagrama, ampliar a figura ou editar a fonte correspondente. |
| Matriz de rastreabilidade | [Matriz CSV](10B1/matriz-rastreabilidade.csv) | Relacionar os 30 itens documentados à origem, implementação e evidência de teste. |
| Caderno de POO | [Conceitos e exemplos](10B1/conceitos-poo.md) | Localizar 18 conceitos no código, com responsabilidades, trechos e testes. |
| Fontes e evidências | [Inventário](10B1/fontes-e-evidencias.md) · [Figuras do relatório](10B1/evidencias/) · [Base de fontes para a 10B.2](10B1/base-de-fontes-10B2.md) | Conferir a procedência do material, os registros da campanha de qualidade e as referências para pesquisa. |
| Guia da etapa 10B.1 | [Orientações de leitura e edição](10B1/LEIA-ME.md) | Consultar o escopo, a organização dos arquivos e os limites das evidências. |

## Apresentação e imagens

| Material | Arquivos | Finalidade |
|---|---|---|
| Apresentação definitiva, 23 slides | [PowerPoint](apresentacao/MOVE_POO_23_Slides_Final.pptx) · [Apresentação aprovada no Canva](https://www.canva.com/d/RUHkx_YXAh77z24) | Apresentar a POO do domínio Python à interface web, com exemplos de execução e de qualidade. O PPTX é a cópia integral do arquivo final fornecido pelo acadêmico. |
| Seleção de 30 capturas do produto | [PNGs](capturas-apresentacao/selecao-30/) · [Ordem e aplicação nos slides](capturas-apresentacao/selecao-30/ordem-e-aplicacao.csv) · [Matriz das 30 capturas](capturas-apresentacao/selecao-30/matriz-capturas-poo.csv) | Cruzar cada imagem com a tela, o estado, o conceito de POO, o dispositivo, o código e o SHA-256. Os nomes na coluna Arquivo são relativos à própria matriz. |
| Estados da estadia 22 | [Resultados por perfil e tema](capturas-apresentacao/estadia-22.csv) | Conferir as leituras de ocupação, pagamento e faturamento em P0, P1 e P2. Os números de passo identificam a sequência do ensaio original. |
| Código em execução, 20 capturas | [Galeria offline](codigo-em-execucao/index.html) · [Índice e hashes](codigo-em-execucao/indice.csv) | Mostrar instâncias, polimorfismo, proteção do estado da vaga, persistência, testes e depuração. |
| Frontend e integração, 21 capturas | [Galeria offline](codigo-em-execucao-front/index.html) · [Índice e hashes](codigo-em-execucao-front/indice.csv) · [Guia para os slides](codigo-em-execucao-front/LEIA-ME.md) | Seguir os objetos JavaScript, as alterações no DOM e o caminho do cálculo no Python até a resposta HTML. |

As galerias abrem localmente quando os arquivos HTML e suas pastas de capturas são mantidos juntos. As duas coleções de execução têm 41 entradas e compartilham cinco PNGs, identificados no índice de frontend. O Git armazena uma única vez cada conteúdo idêntico. As imagens da aplicação usam dados de demonstração.

<details>
<summary>Abrir diretamente uma das 30 imagens do produto</summary>

| Ordem | Captura | Utilização sugerida |
|---|---|---|
| 01 | [Composição de templates Jinja2](capturas-apresentacao/selecao-30/01-S01-login-desktop-1920-claro-janela.png) | Abertura institucional em formato panorâmico. |
| 02 | [Composição de templates Jinja2](capturas-apresentacao/selecao-30/02-S01-login-desktop-1440-escuro-janela.png) | Mesma composição com o tema escuro para comparação. |
| 03 | [Composição de serviços no autocadastro](capturas-apresentacao/selecao-30/03-S01C-cadastro-smartphone-claro-integral.png) | Entrada pública e formulário responsivo. |
| 04 | [ControleTema](capturas-apresentacao/selecao-30/04-S01-aparencia-smartphone-escuro-recorte.png) | Menu compacto em uso por toque. |
| 05 | [OcupacaoViewModel](capturas-apresentacao/selecao-30/05-G01-dashboard-desktop-1920-claro-janela.png) | Visão da operação antes da confirmação. |
| 06 | [OcupacaoViewModel](capturas-apresentacao/selecao-30/06-G01-dashboard-tablet-paisagem-escuro-recorte.png) | OcupacaoViewModel nos números exibidos. |
| 07 | [Composição de dez vagas](capturas-apresentacao/selecao-30/07-G02-mapa-desktop-1440-claro-recorte.png) | Dez vagas em uma composição legível. |
| 08 | [Identidade e reconstrução](capturas-apresentacao/selecao-30/08-G02-legada-tablet-paisagem-escuro-janela.png) | Diferença entre vínculo conhecido e ocupação legada. |
| 09 | [Herança na família Cliente](capturas-apresentacao/selecao-30/09-G03-clientes-desktop-1440-claro-janela.png) | Categorias distintas e clientes homônimos. |
| 10 | [Herança na família Veiculo](capturas-apresentacao/selecao-30/10-G05-veiculos-desktop-1440-escuro-janela.png) | Tipos concretos de veículos na mesma coleção. |
| 11 | [Duas hierarquias comerciais](capturas-apresentacao/selecao-30/11-C05-tarifas-tablet-retrato-claro-janela.png) | Catálogo das duas hierarquias no portal pessoal. |
| 12 | [Associação e identidade](capturas-apresentacao/selecao-30/12-G04-cliente-tablet-paisagem-claro-integral.png) | Associação da titular a mais de um veículo. |
| 13 | [Associação e identidade](capturas-apresentacao/selecao-30/13-G07-revisar-smartphone-claro-recorte.png) | Revisão de uma entrada antes da persistência. |
| 14 | [Encapsulamento e rejeição](capturas-apresentacao/selecao-30/14-G05-duplicada-desktop-1440-escuro-recorte.png) | Resposta observável à violação de uma invariante. |
| 15 | [Estadia, encapsulamento e transições](capturas-apresentacao/selecao-30/15-G13-ativa-desktop-1440-claro-janela.png) | Passo 1. Identidade da estadia 22 antes da cobrança. |
| 16 | [Despacho polimórfico no cálculo](capturas-apresentacao/selecao-30/16-G09-cotacao-desktop-1920-claro-recorte.png) | Passo 2. Base, duração e valor definitivo. |
| 17 | [Cobranca como objeto de valor](capturas-apresentacao/selecao-30/17-G10-revisao-desktop-1440-escuro-janela.png) | Passo 3. Confirmação simulada separada da conclusão. |
| 18 | [ControleSubmissao](capturas-apresentacao/selecao-30/18-G10-submissao-desktop-1440-claro-janela.png) | Estado do botão no evento de submissão, antes da navegação. |
| 19 | [Estadia, encapsulamento e transições](capturas-apresentacao/selecao-30/19-G13-confirmado-tablet-paisagem-claro-janela.png) | Passo 4. Retorno de confirmação com persistência real. |
| 20 | [Composição de dez vagas](capturas-apresentacao/selecao-30/20-G02-ocupada-p1-desktop-1440-claro-recorte.png) | Passo 5. O carro continua na vaga 2. |
| 21 | [Estadia, encapsulamento e transições](capturas-apresentacao/selecao-30/21-G11-fila-tablet-retrato-escuro-janela.png) | Fila de valores confirmados aguardando saída. |
| 22 | [Estadia, encapsulamento e transições](capturas-apresentacao/selecao-30/22-G13-saida-desktop-1440-claro-janela.png) | Passo 6. Encerramento da utilização. |
| 23 | [Composição de dez vagas](capturas-apresentacao/selecao-30/23-G02-liberada-desktop-1440-claro-recorte.png) | Passo 7. Comparação direta entre os estados da vaga. |
| 24 | [Identidade e reconstrução](capturas-apresentacao/selecao-30/24-G12-historico-tablet-paisagem-escuro-integral.png) | Passo 8. Ordem dos eventos da placa AV1. |
| 25 | [Cobranca como objeto de valor](capturas-apresentacao/selecao-30/25-C07-comprovante-smartphone-claro-recorte.png) | Passo 9. Comprovante pessoal da estadia 22. |
| 26 | [ConsultasPessoais](capturas-apresentacao/selecao-30/26-C02-confirmadas-tablet-retrato-escuro-janela.png) | Consulta do titular com dois estados financeiros simultâneos. |
| 27 | [ContextoAcesso e troca de portal](capturas-apresentacao/selecao-30/27-G01-seletor-desktop-1440-escuro-recorte.png) | Alternância dos ambientes autorizados em uma sessão. |
| 28 | [Despacho polimórfico no cálculo](capturas-apresentacao/selecao-30/28-G13-isenta-desktop-1440-claro-janela.png) | Política Mensalista em uma utilização concluída. |
| 29 | [RelatorioSaidas e agregação](capturas-apresentacao/selecao-30/29-G14-relatorios-desktop-1920-claro-recorte.png) | Distribuições de saídas por veículo e categoria histórica. |
| 30 | [Serviço, repositório e recuperação](capturas-apresentacao/selecao-30/30-G13-recuperada-tablet-paisagem-claro-janela.png) | Consulta de recuperação após perda simulada de resposta. |

</details>

## Documentação de engenharia já versionada

| Etapas | Documentação no repositório |
|---|---|
| 08A, 08B e 08C | [Infraestrutura web](../docs/web-08a.md) · [MOVE Gestão](../docs/web-08b.md) · [MOVE Cliente](../docs/web-08c.md) |
| 09 | [Estabilização e validação integrada](../docs/qualidade-09.md) |
| 10A.1 e 10A.2 | [Compatibilidade](../docs/compatibilidade-10a1.md) · [Inicialização e demonstração](../docs/inicializacao-10a2.md) · [Android e Termux](../docs/android-termux.md) |
| 10A.4 e 10A.5 | [Acesso web e integração dos portais](../docs/acesso-web-10a4.md) · [Campanha de qualidade](../docs/qualidade-10a5.md) · [Evidências da campanha](../qa/evidencias/) |
