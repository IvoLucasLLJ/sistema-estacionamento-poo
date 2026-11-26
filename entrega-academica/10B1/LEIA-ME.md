# Entrega acadêmica do MOVE · Etapa 10B.1

**Ivo Lucas de Lima Júnior** · Análise e Desenvolvimento de Sistemas · Programação Orientada a Objetos · 2026/2

O [relatório técnico em PDF](MOVE_Relatorio_Tecnico.pdf) examina o enunciado, a ampliação da hierarquia de clientes e as decisões do projeto. Para acompanhar o exemplo financeiro, leia os capítulos 7 e 8 e consulte o diagrama 10 do atlas. O capítulo 9 e o diagrama 16 mostram por que confirmar o pagamento ainda deixa o carro estacionado.

## Arquivos para avaliação

| Material | Conteúdo |
|---|---|
| [Relatório técnico](MOVE_Relatorio_Tecnico.pdf) | 25 páginas A4, com sumário, oito tabelas, quatro figuras, referências e links permanentes para a implementação. |
| [Documento editável](MOVE_Relatorio_Tecnico.docx) e [fonte estruturada](MOVE_Relatorio_Tecnico.md) | Texto, estrutura, excertos, tabelas e referências. A numeração do sumário corresponde ao PDF entregue. |
| [Atlas UML em PDF](Atlas_UML.pdf) e [índice local navegável](uml/indice.html) | 17 pranchas A4 em orientação paisagem. O índice abre os SVG ampliáveis e as fontes PlantUML individuais. |
| [Matriz de atendimento](matriz-rastreabilidade.csv) | 30 entradas com origem, caráter, classe ou módulo, método, linha, implementação, teste e situação. CSV UTF-8 separado por vírgula. |
| [Caderno de conceitos de POO](conceitos-poo.md) | 18 conceitos associados a responsabilidades, trechos do código e testes do checkpoint. |
| [Inventário das fontes e evidências](fontes-e-evidencias.md) | Enunciado, código, documentação, QA, resultados individuais da CI, hashes das figuras e histórico de commits. |
| [Base de fontes para o ensaio posterior](base-de-fontes-10B2.md) | Questões, recortes de código, evidências e bibliografia para consulta posterior. |

## Registro do checkpoint

A versão documentada é a branch `trabalho-final` no [commit `fa323dca437853cdd6cd64c1f1c682298dd88ecb`](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/commit/fa323dca437853cdd6cd64c1f1c682298dd88ecb). A [execução 45726276531](https://github.com/IvoLucasLLJ/sistema-estacionamento-poo/actions/runs/45726276531) aponta para esse mesmo SHA. Os dez trabalhos concluíram com sucesso. O levantamento documental começou com a árvore limpa. A documentação está em uma pasta própria, fora dos módulos do produto.

A matriz agrupa 13 itens do enunciado e de seus anexos, seis itens da ampliação de clientes, dez extensões e um limite de dados legados. O01 a O07 correspondem à lista obrigatória numerável no texto original. O08 registra a instrução de oferecer o terminal. O09, opcional, registra a ausência de vagas especiais. O10 registra o relatório opcional implementado. A categoria “parcialmente atendido” fica disponível como critério de classificação; nenhum dos itens examinados precisou recebê-la. A atribuição da ampliação à orientação docente procede da informação do acadêmico. A conferência documental identifica a implementação, sem atribuir uma nota ao trabalho.

## Edição e leitura dos diagramas

Os arquivos em `uml/fontes/` são independentes e codificados em UTF-8. As exportações em `uml/svg/` conservam texto e traços vetoriais. A diagramação utilizou PlantUML 1.2025.10. O índice funciona ao abrir o HTML junto às duas pastas, inclusive sem conexão. Os links de evidência para o GitHub e o Figma requerem acesso à rede.

Nas sequências, mensagens com “via Controller” ou “via rota” representam trechos intermediários omitidos e identificados pelo nome. O diagrama de estados trata da estadia identificada. A ocupação legada é discutida separadamente no texto. A figura 1 do relatório resume a prancha do núcleo, disponível para ampliação em [SVG](uml/svg/01-nucleo.svg).

## Alcance das evidências

Os resultados de software são os da campanha registrada no checkpoint. A revisão desta entrega conferiu os dados, as fontes dos diagramas, a paginação, os links e a exportação gráfica. As duas capturas incluídas vêm da aplicação em execução com dados fictícios e têm SHA-256 conferível no inventário. O registro do tablet Android 16 cobre a abertura inicial. O conjunto de ensaios físicos e as amostras de acessibilidade têm os limites descritos nos capítulos 17 e 18.
