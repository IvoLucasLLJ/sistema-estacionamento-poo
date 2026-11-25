'use strict';

class ControleTema {
  #sistema = window.matchMedia('(prefers-color-scheme: dark)');
  #preferencia = 'sistema';

  constructor() {
    try {
      this.#preferencia = this.#validar(localStorage.getItem('move.tema'));
    } catch { /* A preferência funciona nesta página mesmo sem armazenamento. */ }
    this.#aplicar();
    this.#sistema.addEventListener('change', () => this.#aplicar());
    window.addEventListener('storage', evento => {
      if (evento.key === 'move.tema' || evento.key === null) {
        this.#preferencia = this.#validar(evento.newValue);
        this.#aplicar();
      }
    });
  }

  #validar(valor) {
    return ['claro', 'escuro'].includes(valor) ? valor : 'sistema';
  }

  #aplicar() {
    const modo = this.#preferencia === 'sistema'
      ? (this.#sistema.matches ? 'escuro' : 'claro') : this.#preferencia;
    document.documentElement.dataset.tema = modo;
    for (const campo of document.querySelectorAll('input[name="tema"]')) {
      campo.checked = campo.value === this.#preferencia;
      if (campo.checked) {
        const opcao = campo.closest('label');
        const botao = campo.closest('details').querySelector('summary');
        const nome = 'Aparência: ' + opcao.textContent.trim();
        botao.setAttribute('aria-label', nome);
        botao.title = nome;
        botao.querySelector('use').setAttribute('href', opcao.querySelector('use').getAttribute('href'));
      }
    }
  }

  conectar() {
    this.#aplicar();
    for (const campo of document.querySelectorAll('input[name="tema"]')) {
      campo.addEventListener('change', () => {
        this.#preferencia = this.#validar(campo.value);
        this.#aplicar();
        try { localStorage.setItem('move.tema', this.#preferencia); } catch { /* opcional */ }
      });
    }
  }
}

class ControleSubmissao {
  #enviando = false;

  constructor(formulario) {
    const botao = formulario.querySelector('button[type="submit"]');
    formulario.addEventListener('submit', evento => {
      if (this.#enviando) {
        evento.preventDefault();
        return;
      }
      this.#enviando = true;
      formulario.setAttribute('aria-busy', 'true');
      botao.disabled = true;
    });
    window.addEventListener('pageshow', () => {
      this.#enviando = false;
      formulario.removeAttribute('aria-busy');
      botao.disabled = false;
    });
  }
}

const temaMove = new ControleTema();
document.addEventListener('DOMContentLoaded', () => {
  temaMove.conectar();
  const menus = document.querySelectorAll('[data-menu-cabecalho]');
  function fecharOutros(evento) {
    for (const menu of menus) {
      if (menu.open && !menu.contains(evento.target)) menu.open = false;
    }
  }
  document.addEventListener('click', fecharOutros);
  document.addEventListener('focusin', fecharOutros);
  document.addEventListener('keydown', evento => {
    const menu = evento.target.closest('[data-menu-cabecalho][open]');
    if (evento.key === 'Escape' && menu) {
      menu.open = false;
      menu.querySelector('summary').focus();
    }
  });
  document.querySelectorAll('[data-submissao]').forEach(form => new ControleSubmissao(form));
  for (const controle of document.querySelectorAll('[data-senha]')) {
    const senha = document.getElementById(controle.getAttribute('aria-controls'));
    const rotulo = senha.labels[0].textContent.trim().toLowerCase();
    controle.addEventListener('click', () => {
      const mostrar = senha.type === 'password';
      senha.type = mostrar ? 'text' : 'password';
      controle.setAttribute('aria-pressed', String(mostrar));
      controle.setAttribute('aria-label', (mostrar ? 'Ocultar ' : 'Mostrar ') + rotulo);
      const uso = controle.querySelector('use');
      uso.setAttribute('href', uso.getAttribute('href').split('#')[0] + (mostrar ? '#eye-off' : '#eye'));
    });
  }
});

document.addEventListener('DOMContentLoaded', () => {
  const menu = document.querySelector('[data-menu]');
  if (menu) {
    menu.parentElement.classList.add('com-menu');
    menu.addEventListener('click', () => {
      menu.setAttribute('aria-expanded', String(menu.getAttribute('aria-expanded') !== 'true'));
    });
  }
  document.querySelector('[data-imprimir]')?.addEventListener('click', () => window.print());
});

document.addEventListener('DOMContentLoaded', () => {
  const mais = document.querySelector('[data-mais]');
  if (!mais) return;
  const destinos = document.getElementById(mais.getAttribute('aria-controls'));
  mais.closest('nav').classList.add('com-mais');
  mais.addEventListener('click', () => {
    mais.setAttribute('aria-expanded', String(mais.getAttribute('aria-expanded') !== 'true'));
  });
  document.addEventListener('keydown', evento => {
    if (evento.key === 'Escape' && mais.getAttribute('aria-expanded') === 'true') {
      mais.setAttribute('aria-expanded', 'false');
      mais.focus();
    }
  });
  function fecharFora(evento) {
    if (!mais.contains(evento.target) && !destinos.contains(evento.target)) {
      mais.setAttribute('aria-expanded', 'false');
    }
  }
  document.addEventListener('click', fecharFora);
  document.addEventListener('focusin', fecharFora);
});
