# Como iniciar o MOVE para a demonstração acadêmica

## Primeira abertura

1. Extraia o projeto em uma pasta do seu usuário onde você possa criar arquivos. Mantenha juntos os inicializadores, o arquivo `requirements.txt` e as pastas do MOVE.
2. Tenha Python 3 com `venv`, pip, scrypt e suporte a bloqueios nativos. A versão de referência é **3.14.4**. A versão **3.12.3** também passou na suíte. Em um Mac Intel ou Apple Silicon, use Python nativo da máquina. [Python para macOS](https://docs.python.org/3.14/using/mac.html) · [Matriz de compatibilidade](compatibilidade-10a1.md)
3. **Mac:** abra `INICIAR_MOVE_MAC.command` no Finder. **Ubuntu:** abra um terminal na pasta extraída e execute `./INICIAR_MOVE_LINUX.sh`. **Windows 10/11 x64:** abra `INICIAR_MOVE_WINDOWS.cmd` pelo Explorador ou execute `.\INICIAR_MOVE_WINDOWS.cmd` no PowerShell. **Android 15+ em smartphone ou tablet:** abra o Termux, entre em `$HOME/MOVE` e execute `sh INICIAR_MOVE_ANDROID.sh`. Mantenha a janela ou sessão do terminal aberta. [Procedimento completo no Android](android-termux.md)
4. Na primeira abertura, aguarde a criação da `.venv` e a instalação dos pacotes fixados para seu sistema. Essa instalação pode precisar de internet. O MOVE prepara quatro clientes fictícios e pede que você escolha uma senha para cada conta abaixo. Use senhas diferentes, exclusivas da demonstração, com 12 a 256 caracteres. Digite cada senha duas vezes. O terminal oculta os caracteres.
5. Aguarde **MOVE disponível em**. O navegador abre na página de login. Também é possível copiar a URL exibida. O endereço padrão é [http://127.0.0.1:5000/entrar](http://127.0.0.1:5000/entrar).
6. Para encerrar, volte ao terminal, pressione **Ctrl+C** e aguarde o prompt do sistema. Fechar a aba do navegador encerra apenas a visualização.

| Conta fictícia | O que demonstrar |
|---|---|
| `master.demo` | Apresentação completa com um único login. Começa na Gestão e alterna para o portal pessoal de Lia Vale. |
| `gestao.demo` | Mapa de vagas, entrada e saída, confirmação simulada, faturamento, histórico e comprovante. |
| `cliente.demo` | Portal consultivo de Lia Vale, com os próprios veículos e estadias, histórico, perfil e disponibilidade agregada. |

Na próxima abertura, execute o mesmo inicializador. Ele verifica a venv e as versões instaladas. Se estiverem consistentes, passa diretamente à verificação local e ao início do servidor. As mesmas contas, senhas, estadias e movimentações continuam disponíveis.

### UI-001 — Simplificação do controle de aparência

No login e nas mensagens de acesso, o botão de aparência fica no canto superior direito. Nos portais, fica no cabeçalho, junto à conta. O monitor indica **Sistema**, o sol indica **Claro** e a lua indica **Escuro**. Abra o botão para ver os nomes. Com teclado, use Enter ou Espaço para abrir, Tab para chegar à opção selecionada, as setas para mudar a preferência e Esc para fechar.

Na primeira visita, o MOVE acompanha a aparência do dispositivo, inclusive quando ela muda com a página aberta. A escolha manual vale para os portais e para o próximo login no mesmo endereço e perfil de navegador. A classe `ControleTema` aplica a preferência antes das folhas de estilo e usa a chave já existente `move.tema`. [Controle de aparência](../web/static/js/controles.js)

### UI-002 — Integração da navegação entre Gestão e Cliente

Para demonstrar os dois portais, entre como **master.demo**. Ao lado da marca MOVE, abra **Gestão** e escolha **MOVE Cliente**. A área pessoal apresenta os veículos e as estadias de Lia Vale. Use o mesmo seletor para voltar à Gestão. A conta **gestao.demo** conserva a alternância prevista na 10A.4.1. A entrada direta com **cliente.demo** continua exclusivamente pessoal. **Sair** encerra a sessão atual dos dois ambientes.

O provisionamento confere os papéis das contas e o UUID de Lia registrado na criação do cenário. O servidor vincula os IDs de Gestão autorizados ao ID de `cliente.demo`. Uma instalação existente conserva suas contas, senhas e histórico e usa o mesmo formato JSON. Na configuração operacional, o mapa `VINCULOS_PORTAIS` começa vazio e o nome `master.demo` é reservado. O serviço recusa seu provisionamento, login e uso por uma sessão anterior mesmo que um registro demonstrativo tenha sido copiado. [Provisionamento da demonstração](../web/demonstracao.py) · [Serviço de autenticação](../web/contas.py)

`AutenticacaoService` compõe o objeto imutável `ContextoAcesso` com a identidade autenticada e, quando autorizada, a identidade pessoal. A sessão assinada mantém o ID de quem entrou e o prazo original. A troca usa `POST /ambiente` com CSRF e grava o ID pessoal efetivo ao entrar nesse ambiente. O servidor verifica as contas a cada requisição, aplica as guardas do ambiente ativo e consulta as estadias pelo titular da entrada. Uma troca de ambiente renova o token dos formulários. Reabra os formulários de abas antigas antes de enviá-los. Se o vínculo pessoal ativo for removido ou substituído, o próximo acesso exige autenticação. [Contexto e identidades](../web/contas.py) · [Guardas de acesso](../web/seguranca.py) · [Regressões HTTP](../tests/test_contexto_acesso.py) · [Ensaio no navegador](../tests/navegador_ui_10a4_1.py)

### 10A.4.3 — Roteiro de apresentação com a Master Demo

1. Encerre o servidor anterior e abra o inicializador demonstrativo da sua plataforma. Se as duas contas anteriores já existem, o terminal pede somente a nova senha de `master.demo` e sua confirmação. Escolha uma senha exclusiva, de 12 a 256 caracteres. Nas próximas aberturas, use a mesma senha.
2. Entre como `master.demo`. No cenário inicial, AV1 e AM2 já estão estacionados. Para mostrar uma nova entrada, cadastre um carro fictício com uma placa disponível, vincule-o a Lia Vale e selecione **Registrar entrada**. Revise uma vaga livre e confirme.
3. Abra o seletor junto à marca MOVE e escolha **MOVE Cliente**. Consulte a nova estadia de Lia. Volte à **Gestão**, abra **Estadias ativas**, escolha **Preparar saída** e informe, por exemplo, `1,225` hora.
4. Consulte a cobrança, revise e confirme o pagamento simulado. Troque para **Cliente** e confira o pagamento de **R$ 6,13** e a ocupação da vaga. Volte à **Gestão**, abra **Pagamentos** e conclua a saída.
5. Em **Cliente**, abra **Meu histórico**, selecione a estadia da placa utilizada e abra **Ver comprovante**. No celular, o histórico fica em **Mais**.

O cabeçalho identifica a conta que fez login. No portal pessoal, a guarda aplica o UUID de Lia às consultas. A cada troca, o servidor elimina as revisões pendentes daquela sessão e renova o token CSRF. Retome uma confirmação pela consulta à estadia original. [Revisões de formulários](../web/revisoes.py) · [Ensaio integrado em uma aba](../tests/navegador_master_demo.py)

### Se a porta 5000 estiver ocupada

Na demonstração interativa, o terminal oferece a escolha de outra porta. Digite, por exemplo, **5001**. Enter em branco encerra a tentativa. Também é possível escolher antes de iniciar:

```sh
./INICIAR_MOVE_MAC.command --porta 5001
```

No Linux, use `./INICIAR_MOVE_LINUX.sh --porta 5001`. No Windows, use `.\INICIAR_MOVE_WINDOWS.cmd --porta 5001`. No Android, use `sh INICIAR_MOVE_ANDROID.sh --porta 5001`. Com essa escolha a URL será [http://127.0.0.1:5001/entrar](http://127.0.0.1:5001/entrar). O Receptor AirPlay pode ocupar a porta 5000 no Mac. A escolha de outra porta permite manter o processo existente em funcionamento. Para fazer a abertura manual do navegador, acrescente `--sem-navegador`. [Conflito de porta no macOS](https://flask.palletsprojects.com/en/stable/server/#address-already-in-use)

## O que existe no cenário inicial

São dez vagas comuns, três ocupadas e sete livres. As estatísticas a seguir descrevem a primeira criação do cenário. As próximas aberturas mostram as operações já realizadas.

| Titular | Categoria | Estado inicial |
|---|---|---|
| Lia Vale | VIP | Carro Atlas, placa AV1, na vaga 2. Moto Brisa, placa AM2, na vaga 5. |
| Caio Reis | Comum | Caminhão Serra, placa CB3. Há uma saída paga de duas horas e o veículo está disponível para nova entrada. |
| Noa Reis | Mensalista | Moto Lua, placa NM4, na vaga 1. Há também uma utilização anterior concluída com isenção. |
| Iara Luz | Comum | Cadastro sem veículo vinculado. |

O faturamento inicial é **R$ 40,00**, da saída concluída do caminhão. Para demonstrar o desconto VIP, consulte **1,225 h** para AV1 na Gestão. O domínio retorna **613 centavos**. Confirmar o pagamento mantém a vaga ocupada. Concluir a saída libera a vaga e torna o comprovante visível para Lia. Com NM4, uma consulta de duas horas oferece saída isenta. Para acompanhar as mudanças simultaneamente, use um perfil separado ou uma janela privativa para a segunda conta e atualize a página após cada operação.

## Ambiente virtual e instalação

Os quatro inicializadores usam `iniciar_move.py`. No Windows, o preparador procura `.venv\Scripts\python.exe`. No Android, confere o nível de API e a instalação nativa do Termux. Ele localiza a instalação pela posição do arquivo, inclusive em caminhos com espaços ou Unicode. Verifica Python e os recursos indispensáveis, serializa a preparação, cria a venv local se necessário e verifica o prefixo do interpretador, o pip local e as distribuições. Executa a instalação pelos pins de `requirements.txt` quando encontra versões divergentes ou ausentes, roda `pip check` e verifica as importações, incluindo a extensão do MarkupSafe quando presente. O processo do preparador então dá lugar ao servidor. [Preparador](../iniciar_move.py) · [Versões fixadas](../requirements.txt)

- Python 3.11 e 3.13 são aceitos com aviso de avaliação estática. As famílias anteriores a 3.11 e posteriores a 3.14 ficam fora do intervalo adotado nesta etapa.
- Para indicar um interpretador específico, execute, por exemplo, `MOVE_PYTHON="/caminho/para/python3.14" ./INICIAR_MOVE_MAC.command`. Use o caminho real da máquina. A verificação no macOS recusa execução detectada sob Rosetta.
- A instalação é local à venv. Uma venv copiada ou incompatível exige intervenção explícita. Com o MOVE encerrado, renomeie a venv antiga para uma pasta de sua escolha e inicie novamente para criar outra. Preserve a pasta de dados.
- Os sete pins comuns são Flask, Werkzeug, Jinja2, Click, itsdangerous, blinker e MarkupSafe. Somente no Windows, o marcador em `requirements.txt` acrescenta pywin32 para criar e verificar arquivos privados com ACL. Playwright é usado nos ensaios de desenvolvimento. O professor pode operar os dois portais apenas com o Python preparado e um navegador.
- Uma fonte local de wheels compatíveis pode ser fornecida via `PIP_FIND_LINKS` e `PIP_NO_INDEX=1`. O uso comum de uma venv já completa dispensa essa configuração e uma nova consulta ao índice.

## Onde ficam os dados

| Contexto | Histórico, contas e sessão |
|---|---|
| Inicializadores ou `python -B -m web --demonstracao` | Pasta privada `.move-demonstracao/` ao lado do projeto. Guarda `historico.json`, `contas.json`, `sessao.key`, a identificação do cenário em `cenario.json` e as travas deste ambiente. Cookie próprio `move_demo_session`. |
| `python -B -m web` | Operação local da instalação. Por padrão usa `historico.json` na raiz, `instance/contas.json`, `instance/sessao.key` e o cookie operacional. As variáveis `MOVE_HISTORICO`, `MOVE_DADOS`, `MOVE_CONTAS`, `MOVE_SECRET_KEY` e `MOVE_HTTPS` mantêm seus usos documentados. [Configuração da operação](web-08a.md#configuração) |

A demonstração usa caminhos e chave próprios inclusive quando há configuração operacional no ambiente. A preparação recusa colisão detectada com os caminhos operacionais e arquivos de demonstração vinculados externamente. O cenário nasce em um diretório temporário privado, recebe os eventos pelo serviço do estacionamento e só então é publicado. O UUID gerado para Lia identifica o vínculo da conta pessoal. O provisionamento chama o comando existente `criar-conta`, com as regras de unicidade e hash do serviço de autenticação. Se o segundo prompt for interrompido, a próxima abertura preserva a primeira conta e solicita apenas a que falta. [Cenário e provisionamento](../web/demonstracao.py)

A demonstração conserva os dados em disco. Para uma apresentação independente desde o início, use outra cópia limpa dos **arquivos de projeto**, em outra pasta, deixando na instalação original a venv, históricos, contas, chaves e travas. Para trabalhar com um histórico operacional antigo, informe em `MOVE_HISTORICO` o caminho absoluto desse arquivo antes de iniciar o modo operacional. Uma porta diferente continua apontando para o mesmo histórico daquele contexto.

No Windows, extraia o projeto em uma pasta privada do seu perfil em NTFS. A venv é criada com o Python nativo. O console permanece aberto até o encerramento do servidor. Para a operação manual depois do preparo, execute `.venv\Scripts\python.exe -B -m web` ou `.venv\Scripts\python.exe -B main.py`. O provisionamento operacional usa o mesmo executável com `-m flask --app web criar-conta` e as opções abaixo. Se uma ACL for recusada, verifique o diretório selecionado e preserve os arquivos existentes. [Estado da validação em Windows](compatibilidade-10a1.md)

### Alternativa manual

Na raiz do projeto, em Linux ou macOS:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip check
python -B -m web --demonstracao
```

Em execuções seguintes, basta ativar a mesma venv e executar a última linha. A alternativa manual reutiliza o mesmo cenário e os mesmos prompts. Para iniciar a operação com os seus caminhos configurados e provisionar as contas correspondentes, use o fluxo separado abaixo. A segunda linha de provisionamento se aplica somente quando já existir o cliente identificado no histórico operacional.

```sh
python -m flask --app web criar-conta --usuario gestor --papel gestao
python -m flask --app web criar-conta --usuario cliente.local --papel cliente --cliente-id UUID_DO_CADASTRO
python -B -m web
```

Para o menu textual, execute `python -B main.py` com o servidor que utiliza aquele histórico encerrado. O padrão do terminal é o histórico operacional. A opção **4** salva e sai. Servidor e terminal disputam a mesma trava quando escolhem o mesmo arquivo. [Configuração de caminhos](compatibilidade-10a1.md#caminhos-arquivos-e-correções)

## Acesso de smartphone e tablet a um servidor na rede

Para hospedar o próprio servidor no Android e utilizar o navegador do mesmo aparelho em loopback, siga o [roteiro Termux](android-termux.md). A alternativa abaixo usa outro computador como servidor.

1. Conecte o computador Ubuntu e os dispositivos a uma rede **privada, autorizada e de confiança**. Consulte o IPv4 da interface Wi-Fi nas configurações do Ubuntu. Por exemplo, se o endereço exibido for `192.168.1.20`, use-o no comando abaixo. Substitua-o pelo endereço real da sua interface.
2. Encerre a demonstração anterior com Ctrl+C. No Ubuntu, execute:

   ```sh
   ./INICIAR_MOVE_LINUX.sh --rede-privada 192.168.1.20 --porta 5001
   ```
3. Aguarde a URL confirmada pelo terminal. No exemplo, abra `http://192.168.1.20:5001/entrar` no smartphone ou tablet. O endereço `127.0.0.1` no telefone aponta para o próprio telefone.
4. Entre com a conta fictícia do papel desejado. **HTTP transmite senhas e cookies sem criptografia.** Use senhas exclusivas dessa demonstração e encerre o servidor assim que terminar.

A opção aceita um endereço específico nas faixas privadas 10/8, 172.16/12 e 192.168/16 e depende da presença desse endereço na máquina. Ela usa o cenário fictício, um só processo e o host selecionado na lista de hosts confiáveis. Autenticação, autorização e CSRF permanecem ativos. O padrão de todas as outras aberturas é loopback.

Se a rede institucional isolar os dispositivos, prossiga no computador com a visualização responsiva do Chrome ou use uma rede privada autorizada pelo responsável. O procedimento deixa firewall e roteador sob a configuração existente.

## Disponibilidade, encerramento e recuperação

O servidor reserva o endereço e a porta, adquire a trava do histórico, valida o estado e verifica a capacidade de criar um temporário nos diretórios de dados. Usa o mesmo socket reservado para atender o Flask. Só anuncia disponibilidade depois de receber HTTP 200 com o formulário de login pela própria conexão. Na demonstração tenta abrir o Chrome uma vez, com alternativa pelo navegador padrão. A URL impressa permite abertura manual. Durante a saída, as requisições em andamento dispõem de tempo para terminar. Conexões ociosas do navegador têm tempo limite. [Execução do servidor](../web/__main__.py)

| Mensagem ou situação | Como prosseguir |
|---|---|
| Python adequado não encontrado, falta de venv, scrypt, bloqueio nativo ou pip | Instale ou selecione o Python nativo com esses recursos. No Ubuntu, verifique se a instalação possui o suporte de venv correspondente. O preparador não instala Python. No Windows, use o inicializador CMD e a venv nativa. |
| Falha de instalação ou venv incompatível | Confira a disponibilidade dos pacotes para a sua plataforma, a conectividade da primeira instalação e o acesso de escrita à pasta. Preserve uma venv inválida ao renomeá-la antes de criar outra. |
| Permissão negada ao iniciar o arquivo | Use uma pasta extraída gravável de sua propriedade. Se apenas o bit executável se perdeu na cópia, na raiz execute `chmod u+x INICIAR_MOVE_MAC.command INICIAR_MOVE_LINUX.sh`. Em uma máquina institucional, respeite as regras de execução de aplicativos da instituição. |
| Conta aguardando provisionamento | Abra pelo terminal interativo. O provisionamento precisa conseguir ocultar o que você digita. Senhas existentes são preservadas. |
| Porta ocupada, IP inválido ou IP indisponível | Escolha uma porta livre. No modo móvel, confira o IPv4 da interface privada. |
| Histórico em uso ou outra preparação em andamento | Encerre a execução anterior pelo próprio terminal ou aguarde o preparo. Os arquivos auxiliares de trava podem continuar em disco após a saída. Apagá-los pode comprometer a exclusividade. |
| Histórico, contas, identificação do cenário ou chave inválidos | Preserve a pasta para diagnóstico. Para a demonstração, uma nova cópia limpa permite recomeçar sem tocar nos dados antigos. |
| Falha ao gravar ou confirmar a inicialização | Confira espaço e permissões antes de reabrir. Só use a URL anunciada como disponível pelo novo processo. Para uma operação financeira interrompida, consulte a estadia original ao reabrir. |

## Evidências da 10A.2 e limites

- O checkpoint local da 10A.1 é `0cbd2d784232961c144dd8b318ab8dc97b0964bb`. Os 138 testes dessa base passaram antes das alterações.
- A suíte final reuniu os 138 testes anteriores e 12 regressões de inicialização. Passaram os 150 testes em Python 3.14.4 (43,871 s) e em Python 3.12.3 (43,712 s), com `pip check` aprovado nos dois ambientes.
- No Ubuntu 26.04.1 LTS x86-64, uma cópia temporária com espaços, acentos e ideograma foi aberta de outra pasta. O primeiro início em Python 3.14.4 criou a venv, instalou os sete pins e preparou o cenário. A simulação usou um pseudo-terminal e verificou o eco desabilitado nos prompts. Uma interrupção entre as duas contas foi recuperada, preservando o hash da primeira.
- Na cópia com Python 3.12.3, a venv já estava preparada com pip. O inicializador provisionou as duas contas, permitiu login nos dois papéis e encerrou por Ctrl+C mesmo com uma conexão ociosa. Em um ensaio separado da cópia 3.14.4, removemos apenas blinker da venv descartável. O inicializador recuperou a versão fixada 1.9.0 de uma wheel local, conservou os dados e dispensou nova instalação na abertura seguinte.
- A Gestão e o Cliente fizeram login em contextos independentes no Google Chrome 158. A abertura automática foi observada com um adaptador de ensaio que encaminhou a URL ao Chrome real em modo headless e perfil descartável. A escolha explícita de uma porta alternativa produziu uma única abertura no destino correto.
- Reinícios com o índice de pacotes desabilitado conservaram os bytes do cenário, contas e chave. Foram exercitados Ctrl+C, encerramento forçado, bloqueio de uma segunda instância e do terminal, ambiente desconhecido, Python ausente, diretório sem permissão, falha de instalação, arquivo corrompido, colisão de caminhos e falha na consulta de prontidão. O armazenamento operacional fictício usado como controle permaneceu idêntico.
- O modo de rede foi verificado por validação de argumentos e cliente de testes Flask, com a chamada de associação de rede simulada. Os ensaios reais de servidor usaram apenas loopback. Conectividade entre os dispositivos e uso físico em Android ou iOS ficam pendentes.
- Ambos os inicializadores passaram em `sh -n`. O arquivo `.command` foi executado no Linux para verificar o encaminhamento dos argumentos. Abertura pelo Finder, execução nativa com macOS Intel e Apple Silicon, integração com o Chrome do Mac e políticas de execução locais exigem teste em um Mac real. [Compatibilidade da etapa anterior](compatibilidade-10a1.md)

Para repetir a parte automatizada com a venv ativa, execute `python -B -m unittest tests.test_inicializacao -v` e `python -B -m unittest discover -s tests -v`. Para a revisão da 10A.3, os pontos de distribuição a conferir são a presença dos quatro inicializadores (incluindo Windows e Android), a preservação dos bits executáveis Unix, os sete pins comuns e o pin condicional Windows e a exclusão da venv, das pastas privadas, contas, chaves e travas. [Testes de inicialização](../tests/test_inicializacao.py)
