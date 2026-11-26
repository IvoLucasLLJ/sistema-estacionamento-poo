"""Mutação pontual em cópias descartáveis. A seleção precisa passar antes da mutação."""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

RAIZ = Path(__file__).resolve().parents[1]
FIN = 'qualidade_10a5.QualidadeTests.test_nove_combinacoes_com_oraculo_decimal_nas_fronteiras'
VINC = 'estadias.EstadiasTests.test_rejeita_vinculos_invalidos_e_conflitantes'
PAGO = 'service.ServiceTests.test_cada_escrita_recuperavel_e_consultas_sem_gravar'
MASTER = 'contexto_acesso.ContextoAcessoTests.test_master_inicia_na_gestao_alterna_para_lia_e_encerra_os_dois_portais'
WEB = 'web.WebTests.'
CASOS = [
    ('model/carro.py', '= 10', '= 11', FIN), ('model/moto.py', '= 5', '= 6', FIN),
    ('model/caminhao.py', '= 20', '= 21', FIN), ('model/cliente_vip.py', '/ 2', '/ 4', FIN),
    ('model/cliente_mensalista.py', 'return 0', 'return tarifa_base', FIN),
    ('model/estadia.py', 'rounding=ROUND_HALF_UP', "rounding='ROUND_DOWN'", FIN),
    ('model/vaga.py', 'if self.ocupada:', 'if not self.ocupada:', 'nucleo.NucleoTests.test_duplicidade_ocupacao_e_reentrada'),
    ('model/estacionamento.py', 'is not cliente:', 'is cliente:', VINC),
    ('model/estacionamento.py', 'sum(centavos)', '2 * sum(centavos)', PAGO),
    ('model/estadia.py', 'self.pagamento = cobranca', 'self.pagamento = None', PAGO),
    ('service/representacoes.py', 'if recebido != esperado:', 'if recebido == esperado:', PAGO),
    ('web/contas.py', 'self._demonstracao and papel', 'False and papel', MASTER),
    ('web/seguranca.py', 'if papel is not None and g.identidade.papel != papel:', 'if papel is not None:', MASTER),
    ('web/seguranca.py', "or dados['cliente_id'] != g.identidade.cliente_id:", "or dados['cliente_id'] is not None:",
     WEB+'test_recurso_pessoal_autoriza_pelo_evento_da_entrada'),
    ('web/seguranca.py', 'if not esperado or not hmac.compare_digest', 'if esperado or not hmac.compare_digest',
     WEB+'test_csrf_login_logout_e_rotacao'),
    ('web/revisoes.py', 'if consumir:', 'if True:', 'gestao.GestaoTests.test_revisao_pertence_a_sessao_e_a_operacao_e_expira'),
    ('web/seguranca.py', "int(agora()) + current_app", "int(agora()) - current_app", MASTER),
    ('web/contas.py', 'self.contas.ativar(reserva)', 'return', 'cadastro_pessoal.CadastroPessoalTests.test_cadastro_login_categoria_e_titularidade_do_homonimo'),
    ('persistence/exclusividade.py', 'if self._reserva is None:', 'if self._reserva is not None:',
     'multiplataforma.MultiplataformaTests.test_bloqueio_persiste_ao_substituir_json_e_libera_apos_saida_ou_morte'),
]


def executar(raiz, teste):
    return subprocess.run([sys.executable, '-B', '-m', 'unittest', 'tests.test_' + teste],
                          cwd=raiz, capture_output=True, timeout=60, text=True)


def campanha():
    resultado = []
    with TemporaryDirectory() as tmp:
        copia = Path(tmp)
        for pasta in ('controller','model','persistence','repository','service','view','web','tests'):
            shutil.copytree(RAIZ/pasta, copia/pasta, ignore=shutil.ignore_patterns('__pycache__'))
        for nome in ('main.py','iniciar_move.py','requirements.txt'):
            shutil.copy(RAIZ/nome, copia/nome)
        controles = {teste: executar(copia, teste).returncode for teste in sorted({c[3] for c in CASOS})}
        for modulo, anterior, novo, teste in CASOS:
            arquivo = copia/modulo
            original = arquivo.read_text(encoding='utf-8')
            estado = 'inválido'
            try:
                if not controles[teste] and original.count(anterior) == 1:
                    alterado = original.replace(anterior, novo)
                    compile(alterado, modulo, 'exec')
                    arquivo.write_text(alterado, encoding='utf-8')
                    proc = executar(copia, teste)
                    if not proc.returncode:
                        estado = 'sobrevivente'
                    elif re.search(r'Ran [1-9]\d* tests? in', proc.stderr) and 'FAILED (' in proc.stderr:
                        estado = 'detectado'
            except subprocess.TimeoutExpired:
                estado = 'timeout'
            finally:
                arquivo.write_text(original, encoding='utf-8')
            resultado.append(dict(arquivo=modulo, alvo=anterior, teste=teste, resultado=estado))
    return resultado


if __name__ == '__main__':
    print(json.dumps(campanha(), ensure_ascii=False, indent=2))
