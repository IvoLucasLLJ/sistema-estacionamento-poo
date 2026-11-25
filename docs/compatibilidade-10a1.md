# MOVE · Compatibilidade técnica da Etapa 10A.1

**Parecer para a avaliação do professor.** O MOVE executou no Ubuntu a partir de uma cópia independente, com instalação limpa das dependências, dois papéis autenticados e persistência recuperada em outro processo. A análise sustenta preparar o uso em Mac Intel e Apple Silicon. A confirmação em macOS com Chrome exige um ensaio no Mac. O Windows nativo tem um impedimento identificado no bloqueio de arquivos.

## Escopo e referência

Avaliação do terminal, do servidor Flask local, dos dois portais e dos dados JSON. A estação disponível era Ubuntu 26.04.1 LTS, kernel 7.0.0-44-generic, x86-64. A Etapa 09 entrou na revisão com 12 arquivos modificados e três novos sobre `acccf1bf7d66a580fa10a2042977031c02c93b2b`. Os 130 métodos de teste anteriores e cinco regressões passaram. O checkpoint local dos 15 arquivos é `b110899e45a1be46562e2a323078913aeb1838b9` na branch `trabalho-final`. A política temporal e as evidências originais estão no [relatório de qualidade](qualidade-09.md).

## Inventário de execução

| Camada | Recursos utilizados | Dependência de plataforma |
|---|---|---|
| Model, Controller e serviço | ABCs, subclasses de veículos e clientes, dataclasses, UUID, Decimal, datetime, cópias e bloqueios de threads por caminho | CPython com biblioteca padrão. O relógio local fornece o offset de novas operações. O bloqueio de threads vale dentro do processo. |
| Repository e persistência | JSON UTF-8, versão em bytes, temporário no diretório de destino, `fsync`, `os.replace` | Diretório gravável e sistema de arquivos local com substituição no mesmo volume. |
| Terminal | `main.py`, `view/ui_texto.py`, Controller e apresentação monetária | Entrada e saída de texto no terminal. A reserva do histórico usa `fcntl`. O menu usa funções Python, sem comandos de limpeza de tela ou subprocessos de shell. |
| Web e acesso | Fábrica Flask, Blueprints, guardas de papel e titularidade, CSRF, cookie assinado, scrypt, contas separadas | O Python precisa oferecer `hashlib.scrypt`. A criação concorrente da chave usa um link físico. O repositório de contas usa `flock`. |
| Apresentação | ViewModels, consultas pessoais, projeções de histórico e relatórios, 33 templates Jinja, HTML em pt-BR | Carregamento dos templates pelo pacote Flask. As classes de apresentação consomem os valores produzidos pelo domínio. |
| Navegador | CSS com tokens, Grid, Flexbox, consultas de mídia e impressão, SVGs, Inter WOFF2 e Bootstrap Grid locais, JS com campos privados | Tema Sistema usa `matchMedia`. A preferência usa `localStorage` quando disponível. Há seletores `:has()`, unidades `svh` e área segura móvel. |
| Qualidade | `unittest`, diretórios temporários, subprocessos, cliente HTTP do Flask, ensaios Playwright | Playwright e os binários de automação pertencem ao ambiente de QA. A instalação normal do MOVE usa apenas os requisitos do produto. |

O fluxo de negócio continua sendo serviço → Controller → domínio, com persistência pelo Repository. A seleção do caminho de instalação e a formatação monetária são funções compartilhadas. Suas responsabilidades dispensam novas classes ou subclasses de plataforma. [Serviço](../service/estacionamento_service.py) · [Persistência](../persistence/historico_json.py) · [Infraestrutura web](web-08a.md) · [Gestão](web-08b.md) · [Cliente](web-08c.md)

## Python e dependências

**Recomendado para reproduzir a avaliação: CPython 3.14.4 convencional, em ambiente virtual nativo.** A menor versão executada com a suíte completa foi **3.12.3**. Utilizou-se o interpretador já disponível no Core 24 em uma venv temporária independente. Como esse interpretador vinha sem o instalador de pip da venv, o pip da estação instalou os pacotes indicando a venv 3.12 como destino. A instalação 3.14 da cópia foi criada com `python3 -m venv`. Ambas passaram em `pip check`.

O piso potencial identificado foi **3.11**. O código usa `datetime.UTC`, `enum.StrEnum`, opções de contexto em `decimal.localcontext` e o formato numérico com `z`. A suíte também usa `TestCase.enterContext` e `contextlib.chdir`. A análise sintática com a gramática 3.11 foi complementar. O interpretador 3.8.10 encontrado em um runtime do sistema fica abaixo do piso. Não houve execução em 3.11 ou 3.13. [Alterações do Python 3.11](https://docs.python.org/3/whatsnew/3.11.html) · [CPython 3.14.4](https://www.python.org/downloads/release/python-3144/) · [Disponibilidade de scrypt](https://docs.python.org/3.14/library/hashlib.html#hashlib.scrypt)

| Distribuição | Versão fixada | Requires-Python | Uso |
|---|---:|---|---|
| Flask | 3.1.3 | ≥ 3.9 | Fábrica, requisições, sessões, CLI |
| Werkzeug | 3.1.9 | ≥ 3.9 | WSGI, HTTP e verificação de senhas |
| Jinja2 | 3.1.6 | ≥ 3.7 | Templates e macros |
| Click | 8.5.1 | ≥ 3.10 | Provisionamento local e CLI do Flask |
| itsdangerous | 2.2.0 | ≥ 3.8 | Assinatura de dados da sessão |
| blinker | 1.9.0 | ≥ 3.9 | Dependência do Flask |
| MarkupSafe | 3.0.4 | ≥ 3.9 | Escape de texto com extensão nativa na distribuição instalada |

Foram verificadas as distribuições instaladas e baixados os sete wheels de cada alvo com `pip download --only-binary=:all:` para CPython 3.14. Seis são `py3-none-any`. O MarkupSafe tem wheels `cp314-cp314` específicos para `macosx_10_15_x86_64`, `macosx_11_0_arm64` e `win_amd64`, além do wheel Linux x86-64 usado na execução. Essas etiquetas descrevem o pacote, não o requisito mínimo de todo o produto. As versões aprovadas foram mantidas. [Requisitos](../requirements.txt) · [Arquivos publicados de MarkupSafe 3.0.4](https://pypi.org/project/MarkupSafe/3.0.4/#files)

## Caminhos, arquivos e correções

1. **Histórico dependente da pasta de abertura.** Na cópia anterior à correção, executar `main.py` por caminho absoluto a partir de outra pasta criou ali `historico.json` e sua trava, mesmo com `MOVE_HISTORICO` definido. O terminal e a web agora usam o mesmo resolvedor antes de abrir o arquivo ou reservar a trava. Por padrão o histórico fica ao lado de `main.py`. Caminhos absolutos são respeitados. Os relativos de `MOVE_HISTORICO`, `MOVE_DADOS` e `MOVE_CONTAS` partem da raiz da instalação. A expansão de `~` usa a conta do sistema. Para reabrir dados antes guardados relativamente a outra pasta, informe seu caminho absoluto. Nenhum dado é migrado automaticamente. As APIs legadas do Controller e do Repository continuam aceitando um caminho explícito ou o padrão relativo de programação. As menções a `/home/lucas/MOVE` nos relatórios identificam o ambiente anterior. [Resolvedor](../persistence/caminhos.py) · [Terminal](../main.py) · [Configuração web](../web/config.py)
2. **Identidade dos bytes gravados.** O código anterior calculava a versão em UTF-8, decodificava e escrevia por um fluxo de texto. Em plataformas que traduzem LF para CRLF isso pode fazer o Repository comparar o arquivo com bytes diferentes dos publicados. O temporário recebe agora diretamente os bytes que a persistência devolve. A regressão parte de um arquivo CRLF e verifica duas gravações com texto Unicode. A análise da tradução no Windows é estática. [Gravação](../persistence/historico_json.py#L38) · [Regressões](../tests/test_portabilidade.py)
3. **Apresentação do terminal.** A reprodução mostrou `R$ 0.00`. O menu e os portais agora compartilham o formatador decimal pt-BR, com vírgula e duas casas. A entrada de horas no menu continua aceitando ponto ou vírgula. Uma interrupção por EOF ou Ctrl+C recebe diagnóstico e o descritor é fechado no bloco de finalização. A opção 4 continua sendo a saída com salvamento. [Formato monetário](../view/formatacao.py) · [Menu](../view/ui_texto.py)

Os padrões privados da web são `instance/contas.json` e `instance/sessao.key`. Os ensaios encontraram modo 0600 nos dois arquivos em ext4. O temporário do JSON é fechado antes da substituição. A publicação inicial da chave usa um link físico no mesmo diretório para preservar a chave de um inicializador concorrente. Use caminhos privados distintos considerando a equivalência de caixa e Unicode do volume e conceda ao usuário permissão de criar os arquivos auxiliares. Volumes de rede, pastas sincronizadas, mídia FAT/exFAT, ACLs do Windows e durabilidade após corte de energia ficam fora da validação.

### Exclusividade, horários e idioma

A reserva do histórico usa um descritor de arquivo auxiliar e `LOCK_EX | LOCK_NB`. O repositório de contas usa outra trava, bloqueante, durante leitura, validação e substituição. Duas CLIs reais concorreram pelo mesmo nome e produziram uma conta. A conta pessoal foi provisionada sobre o UUID existente. Outros escritores do histórico devem participar do mesmo protocolo. Manter o arquivo auxiliar no disco permite que todos os processos abram a mesma trava. Os ensaios confirmaram recusa de um segundo servidor e do terminal, aquisição após encerramento normal e recuperação após `SIGKILL`. [Reserva do histórico](../persistence/exclusividade.py) · [Trava de contas](../web/contas.py#L86)

Horários novos incluem offset. A reconstrução compara instantes conscientes, respeita a ordem civil entre dois registros sem fuso e aplica a política da 09 quando apenas um contém offset. A duração informada, os IDs e os textos originais foram preservados nos testes em `America/Sao_Paulo` e `Pacific/Auckland`. JSON, templates e recursos textuais usam UTF-8. A cópia continha nomes acentuados e ideogramas, com conservação até o login, gravação e reabertura. Os ensaios usaram terminais ou fluxos UTF-8. Um terminal explicitamente configurado com uma codificação incapaz de representar o texto exige ajuste de codificação. [Regressões temporais](../tests/test_horarios_legados.py) · [Política da Etapa 09](qualidade-09.md)

Na estadia 22, a duração permanece 1,225 h, a base é `12.25` reais, o desconto exato é `6.125` reais e o total confirmado é **613 centavos**. A apresentação mostra R$ 6,13 no total. O serviço preserva `40.005` reais antes da conclusão e `46.135` depois dela, exibidos como R$ 40,01 e R$ 46,14. A suíte cobriu as nove combinações de clientes e veículos, autorizações, concorrência, conflitos, falhas de gravação e recuperação por ID. [Ciclo integrado](../tests/test_portal_cliente.py) · [Recuperação](../tests/test_reinicio_web.py)

## Matriz de compatibilidade

| Sistema e arquitetura | Python e pacotes | Terminal / Flask | JSON / exclusividade | Navegador | Classificação e alcance |
|---|---|---|---|---|---|
| Ubuntu 26.04.1 x86-64 | 3.14.4, sete pins | Ambos executados | Reabertura, dois escritores, encerramento normal e forçado | Google Chrome 158.0.8127.36 | **Validado por execução**. Suíte completa, três ensaios de navegador e instalação relocada. |
| Ubuntu 26.04.1 x86-64 | 3.12.3, mesmos pins, outra venv | Terminal por subprocesso e Flask pelo cliente de testes | Suíte completa, incluindo persistência e disputa de travas | Ensaios de navegador com servidor 3.14 | **Validado parcialmente**. A suíte completa passou em 3.12. O percurso em navegador com servidor 3.12 fica pendente. |
| Outras distribuições Linux | Versão e arquitetura a confirmar, Python com scrypt e fcntl | Código Python e recursos locais | Requer arquivo local, flock, link físico e replace | Conforme distribuição | **Compatibilidade esperada**. Nenhuma chamada a apt, systemd ou utilitário Ubuntu no produto. Ambiente gráfico e pacotes do sistema variam. |
| macOS Intel x86-64 | Alvo 3.14.4 nativo, sete wheels disponíveis | APIs analisadas | flock Darwin e operações de arquivo disponíveis | Chrome para Mac, versão local por verificar | **Avaliado estaticamente**. Sem execução em hardware Intel ou APFS. |
| macOS Apple Silicon arm64 | Alvo 3.14.4 nativo, sete wheels disponíveis | APIs analisadas | Mesmas condições do Intel | Chrome nativo, versão local por verificar | **Avaliado estaticamente**. Sem execução em hardware Apple Silicon ou APFS. |
| Windows 10 e 11 x86-64 | Alvo 3.14, sete wheels disponíveis | A importação de fcntl impede iniciar ambos nativamente | Bloqueios do histórico e das contas dependem de Unix | Chrome ou Edge como cliente exigiria servidor acessível | **Incompatibilidade identificada**. Sem execução nativa. |
| Android e iOS | Somente cliente web | Backend em computador | Dados tratados no servidor | Chrome Android e Safari iOS | **Não testado** em sistema móvel real. A emulação Linux cobriu a composição responsiva. |

**Mac.** A distribuição de CPython para macOS oferece execução nativa nas arquiteturas de interesse e o Darwin implementa o bloqueio utilizado pelo MOVE. O ensaio de aceitação no Mac deve registrar versão do macOS, arquitetura efetiva de Python e do navegador, funcionamento de scrypt, persistência em volume local, exclusividade e login. A porta 5000 pode estar ocupada pelo Receptor AirPlay. Na estação Linux a porta também estava ocupada e os ensaios usaram portas efêmeras de loopback. O endereço padrão do produto continua [http://127.0.0.1:5000/entrar](http://127.0.0.1:5000/entrar). [Python no macOS](https://docs.python.org/3.14/using/mac.html) · [flock no Darwin](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/man/man2/flock.2) · [Requisitos do Chrome](https://support.google.com/chrome/a/answer/7100626) · [Porta ocupada no macOS](https://flask.palletsprojects.com/en/stable/server/#address-already-in-use)

**Windows.** Os imports incondicionais de `fcntl` em `persistence/exclusividade.py` e `web/contas.py` impedem iniciar os executáveis. A adaptação possível é implementar reserva nativa por região de arquivo com a biblioteca padrão do Windows para os dois usos. Exigiria validar espera e recusa imediata, liberação após morte de processo, substituição de arquivos abertos, proteção da chave e permissões em NTFS. É trabalho localizado no código, com custo de validação em Windows real. A proteção existente foi mantida para as plataformas prioritárias. [Disponibilidade de fcntl](https://docs.python.org/3/library/fcntl.html) · [Bloqueios nativos de arquivo](https://docs.python.org/3/library/msvcrt.html#msvcrt.locking)

### Navegadores

| Navegador efetivamente executado no Ubuntu | Verificação |
|---|---|
| Google Chrome 158.0.8127.36 | Ensaios 08A, 08B e 08C. Autenticação, papéis, tema, recursos locais e fluxos financeiros. Gestão e Cliente em 390 e 1440 px. A infraestrutura também exercita 320 e 768 px. |
| Chromium 156.0.8078.4 | Ensaio 08A aprovado com o binário de QA do Playwright. |
| Microsoft Edge 158.0.4370.33 | Ensaio 08A aprovado com o executável instalado. |
| Mozilla Firefox 158.0 | Login renderizado em 390 × 844 px, inspecionado na captura. O invocador Snap encontrou uma restrição do ambiente. O binário Firefox instalado executou em modo headless com perfil temporário. Cobertura restrita à abertura e apresentação dessa página. |

Safari, Chrome para macOS e navegadores em dispositivos físicos continuam pendentes. Impressão por navegador e fontes locais foram exercitadas nos ensaios Chromium. A impressão física e as diferenças de teclado virtual e área segura em iOS/Android precisam de ensaio próprio.

## Evidências e reprodução

Copiaram-se apenas os arquivos de projeto selecionados pelo Git e as alterações legítimas em revisão. A instalação final ocorreu em uma pasta temporária ext4 com o sufixo `Usuária Íris 林/Curso de Programação/MOVE portátil`, com venv nova, sem contas, sessão ou histórico da estação. Houve também ensaios em tmpfs. A execução funcional usou um segundo diretório de trabalho, um usuário fictício Unicode, uma conta de cada papel e arquivos privados exclusivos da cópia.

| Verificação | Resultado observado |
|---|---|
| Antes do checkpoint | 135/135 em 29,889 s. Diferenças preparadas verificadas. |
| Final, Python 3.14.4 | 138/138 em 45,882 s na árvore de desenvolvimento e 138/138 em 47,267 s na cópia, esta com `LC_ALL=C.UTF-8`, `TZ=Pacific/Auckland` e `TMPDIR` apontando para um link simbólico com espaços. |
| Final, Python 3.12.3 | 138/138 em 44,740 s a partir da cópia, com o mesmo link para temporários, `LC_ALL=pt_BR.UTF-8` e `TZ=America/Sao_Paulo`. |
| Regressões novas | Configuração relativa comum aos executáveis, abertura do terminal fora da raiz com encerramento por EOF, e identidade dos bytes UTF-8 entre gravações. Nos testes anteriores, atualizaram-se o caminho temporário explícito nos subprocessos e três expectativas de moeda do terminal. Os 135 casos anteriores permanecem. |
| Web e persistência | Provisionamento por CLI, login HTTP dos dois papéis, consulta, seis estáticos conferidos byte a byte, bloqueio de outro escritor, reinício após encerramento forçado e liberação normal. Histórico preservado entre consultas e reinicialização. 14 modelos Gestão, oito Cliente e cinco compartilhados renderizados por HTTP em fixture própria. 33 templates compilados. |
| Interrupção do terminal | Um subprocesso recebeu SIGINT no prompt do menu. O diagnóstico de interrupção apareceu, o histórico manteve os mesmos bytes e um novo terminal conseguiu abrir a mesma trava e sair pela opção 4. |
| Isolamento | Nenhum dado operacional original entrou nas cópias. A primeira tentativa de CLI no ensaio ext4 começou antes de o pip terminar. A repetição após a instalação passou integralmente. |

Na raiz da cópia, com a venv do produto ativa:

```console
python -B -m unittest tests.test_portabilidade tests.test_horarios_legados -v
python -B -m unittest discover -s tests -v
python -m pip check
```

Os comandos para repetir os ensaios de navegador no ambiente opcional de QA estão no [guia da 08A](web-08a.md), no [guia da 08B](web-08b.md) e no [guia da 08C](web-08c.md). O argumento `--chrome` recebe o executável instalado no equipamento de teste.

## Pré-requisitos para a Etapa 10A.2

- Localizar a raiz pela localização do inicializador, preservar espaços e Unicode e usar o interpretador da venv daquela instalação. O comando `python -m web` precisa que o pacote local esteja no caminho de importação.
- Verificar Python, venv, pip, scrypt e importação dos pacotes fixados. Para o Mac, usar Python nativo da arquitetura. A venv deve ser criada no destino. Playwright é opcional para QA.
- Escolher uma pasta privada gravável em volume local com exclusividade, links físicos e substituição atômica. Reutilizar os caminhos e dados existentes. Para dados em outra árvore, preferir configuração absoluta.
- Verificar a disponibilidade da porta 5000 e informar conflitos. Iniciar um único servidor em loopback, com debug e recarga desativados. Abrir o navegador somente após o login responder.
- Na primeira oportunidade em Mac, registrar as versões e repetir o fluxo terminal → reabertura web, login dos dois papéis, confirmação/saída, disputa de trava e reinício. Esse é o critério para promover a classificação do Mac a validado por execução.
