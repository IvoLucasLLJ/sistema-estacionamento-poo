# MOVE completo no Android com Termux

O telefone ou tablet executa o servidor, o terminal, a Gestão e o Cliente. O navegador do próprio aparelho acessa o loopback. A instalação depende de internet ou de uma fonte local completa de pacotes. Depois do preparo, a aplicação usa arquivos e recursos estáticos locais. O aceite físico em Android 15 e 16 está pendente.

## Instalar e abrir

1. Use Android 15 (API 35) ou superior e o Termux nativo da distribuição oficial para o aplicativo `com.termux`. Use o mesmo canal para atualizações do aplicativo. O alvo prioritário é ARM64. [Distribuição oficial do Termux](https://github.com/termux/termux-app#installation) · [Níveis de API do Android](https://developer.android.com/tools/releases/platforms)
2. No terminal do aplicativo, prepare o Python, pip, os recursos de venv, o compilador para extensões nativas e o comando de abertura de URLs. Estes comandos utilizam o usuário do aplicativo.

   ```sh
   pkg update
   pkg install python python-pip python-ensurepip-wheels clang termux-tools
   ```

3. Coloque os arquivos do projeto em `$HOME/MOVE` dentro do Termux. Pode importar uma cópia limpa previamente autorizada pelo seletor de arquivos do Android. Se utilizar armazenamento compartilhado para transportar o projeto, extraia ou copie **apenas o código** para a pasta privada antes de executá-lo. Mantenha ali a venv, as contas, as chaves, os JSON e as travas. O inicializador confere os caminhos físicos e recusa redirecionamentos para fora do armazenamento privado. [Organização do sistema de arquivos do Termux](https://github.com/termux/termux-packages/wiki/Termux-file-system-layout)
4. Execute na sessão do Termux:

   ```sh
   cd "$HOME/MOVE"
   sh INICIAR_MOVE_ANDROID.sh
   ```

5. Escolha no terminal as senhas fictícias de `gestao.demo` e `cliente.demo`, com a digitação oculta. O navegador recebe a URL após o teste HTTP do login. Se a abertura via `termux-open-url` falhar, abra manualmente `http://127.0.0.1:5000/entrar` ou a URL da porta escolhida. Gestão e Cliente podem ocupar uma aba normal e outra anônima. [Comando de abertura do Termux](https://github.com/termux/termux-tools/blob/master/scripts/termux-open-url.in)

Para escolher outra porta ou abrir o navegador manualmente, use `sh INICIAR_MOVE_ANDROID.sh --porta 5001 --sem-navegador`. Para encerrar, retorne ao Termux e pressione Ctrl+C. Na próxima abertura, repita o comando inicial. O modo local dispensa rede Wi-Fi, outro computador e conexão externa depois da instalação.

Se recebeu o ZIP do GitHub, ele contém uma pasta de topo com o nome do projeto e a revisão. Com o ZIP importado para `$HOME/MOVE.zip`, a primeira extração pode ser feita no próprio Termux. O comando exige que a pasta de destino seja nova, para preservar instalações anteriores.

```sh
pkg install unzip
mkdir "$HOME/MOVE" && unzip -q "$HOME/MOVE.zip" -d "$HOME/MOVE" &&
  cd "$HOME/MOVE"/sistema-estacionamento-poo-*/ && sh INICIAR_MOVE_ANDROID.sh
```

Nas próximas execuções, entre na mesma pasta extraída e abra somente o inicializador. O teste no tablet pode ocorrer depois da publicação. Registre a API do Android e o resultado da execução no aparelho seguindo o roteiro no fim deste guia.

## Base técnica e recuperação

O inicializador verifica o nível de API pelo `getprop` do sistema, a origem do Python, `venv`, scrypt e a capacidade de obter uma trava local. A versão de correção do Python pode variar dentro das famílias admitidas pelo preparador. A receita do Termux fornece OpenSSL e distribui separadamente as wheels para `ensurepip`. Use os pacotes do próprio ambiente ao reparar uma venv. [Receita do Python](https://github.com/termux/termux-packages/blob/master/packages/python/build.sh) · [Pacote de ensurepip](https://github.com/termux/termux-packages/blob/master/packages/python/python-ensurepip-wheels.subpackage.sh)

Dos sete pacotes comuns, o MarkupSafe contém uma extensão C opcional. A instalação nova pelo inicializador Android solicita a distribuição fonte da versão fixada, permitindo compilação com o Python e a libc Bionic locais. O pacote também oferece implementação em Python se a extensão opcional não compilar. O preparador verifica as importações e confere o binário quando instalado. A venv de Ubuntu ARM64 tem uma ABI diferente. [Código de compilação do MarkupSafe](https://github.com/pallets/markupsafe/blob/3.0.4/setup.py)

O Termux usa a trava POSIX do MOVE. A chave de sessão é publicada de um temporário fechado, sob trava exclusiva própria, com `fsync` e substituição atômica. A receita do Python do Termux pode desativar links físicos. A criação da chave e o provisionamento funcionam sem essa operação. O JSON permanece em UTF-8 e as operações confirmadas são recuperadas em outra execução.

O Android pode suspender a sessão ao alternar aplicativos ou terminar o processo sob pressão de memória. Mantenha a sessão do Termux aberta durante a demonstração. Se a página parar de responder, retorne ao terminal e verifique o processo. Após encerramento, reabra com o inicializador. Para pagamento ou saída com resposta perdida, consulte o ID original da estadia antes de qualquer nova ação. Os arquivos auxiliares de trava podem permanecer em disco. Nenhum serviço permanente ou ajuste de bateria é necessário para iniciar o ensaio. [Comportamento de aplicativos parados no Android](https://developer.android.com/about/versions/15/behavior-changes-all)

Para atualizar, encerre o servidor, preserve uma cópia privada de segurança dos dados e atualize somente o código recebido de fonte autorizada. Se mudar o Python do Termux, confira a venv com o inicializador. Caso fique incompatível, renomeie-a com o servidor parado e abra novamente para criar uma venv nativa. Conserve a pasta privada de dados; a troca de distribuição do Termux ou a desinstalação pode remover os dados do aplicativo.

## Evidências obtidas antes do aceite físico

Foi inspecionado, sem executar, o pacote oficial `python 3.14.10 aarch64` do repositório do Termux. O SHA-256 foi conferido contra o índice de pacotes baixado por HTTPS. A configuração publicada identifica a ABI `cpython-314-aarch64-linux-android`, habilita `flock` e `fsync` e desabilita `link` e `linkat`. Com `readelf`, foram encontrados `EVP_PBE_scrypt` no módulo nativo de hash e `flock` no módulo de bloqueio. O pacote também contém venv, subprocessos e getpass. Essa é evidência estática dos binários Android; a autenticação e a trava ainda precisam ser executadas no telefone e no tablet. [Índice oficial ARM64](https://packages.termux.dev/apt/termux-main/dists/stable/main/binary-aarch64/)

O fonte fixado do MarkupSafe foi compilado em wheel no Ubuntu x86-64. O arquivo produzido destinava-se ao Ubuntu e foi descartado. No ensaio de aplicação, dois inícios em cópia independente, com índice pip desabilitado, permitiram autenticação nos dois papéis. O rastreamento de conexões do inicializador e seus filhos observou somente loopback. A execução com os rádios desligados no Android continua sendo parte do roteiro.

## Roteiro reproduzível de aceite físico

Execute em smartphone e tablet. Registre separadamente a cobertura de Android 15 e 16, modelo, formato do aparelho, versão do Chrome, origem do Termux, data e resultados. Use somente dados fictícios. Os comandos abaixo identificam o ambiente sem coletar IDs de hardware, contas ou segredos.

```sh
/system/bin/getprop ro.build.version.sdk
/system/bin/getprop ro.product.cpu.abi
uname -m
cd "$HOME/MOVE"
.venv/bin/python -V
.venv/bin/python -m pip check
.venv/bin/python -B -m unittest discover -s tests -v
```

| Verificação no aparelho | Evidência de aprovação |
|---|---|
| Primeira instalação | Em cópia limpa, a venv é criada no armazenamento interno, as duas senhas são solicitadas e o login responde em loopback. Registre a versão do Python e o resultado do pip. |
| Gestão, Cliente e autorização | Entre com os dois papéis. Lia vê apenas as próprias estadias. Abrir `/gestao/` com a conta Cliente resulta em acesso negado. |
| Cobrança e comprovante | Na Gestão, consulte AV1 em 1,225 hora e obtenha R$ 6,13. Confirme o pagamento e atualize o Cliente. A vaga 2 continua ocupada. Conclua a saída e confira a liberação, o histórico e o comprovante. AM2 segue ativo. Confira isenção para a moto de Noa. |
| Uso por toque | Em retrato e paisagem, navegue pelo menu, digite a duração com o teclado decimal, revise os dois temas e o foco. Confira legibilidade com o teclado aberto, gestos na borda inferior e a prévia de impressão se disponível. |
| Exclusividade | Com o servidor em execução, em outra sessão de Termux na mesma pasta, execute `MOVE_HISTORICO="$PWD/.move-demonstracao/historico.json" .venv/bin/python -B main.py`. O terminal deve recusar o histórico em uso. |
| Terminal e reabertura | Encerre o servidor com Ctrl+C. Repita o comando anterior, use a opção 3 para consultar ocupação e 4 para salvar e sair. Reabra a demonstração e compare os dados. |
| Execução sem internet | Após a instalação, desconecte os dados móveis e o Wi-Fi. Reabra o Termux e o MOVE, atualize a página pelo loopback, faça login e confirme as leituras. O inicializador reutiliza a mesma venv sem reinstalar os pacotes. |
| Interrupção e recuperação | Em instalação fictícia, com uma operação já persistida, encerre o processo do servidor, reabra o aplicativo Termux e reinicie o MOVE. Confira a estadia original, o faturamento e a possibilidade de adquirir a trava outra vez. |
| Resultado por aparelho | Registre também bloqueios, versão do navegador e comportamento após alternar entre Termux e Chrome. Anote separadamente o que foi aprovado e o que ficou sem execução. |

As regressões exercitam também a disputa entre processos, exclusividade do terminal e recuperação financeira. Elas podem ser repetidas no aparelho com `.venv/bin/python -B -m unittest tests.test_multiplataforma tests.test_inicializacao tests.test_termux -v`. A emulação de toque no Chrome de desktop não substitui o ensaio nativo acima.
