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
  document.querySelectorAll('[data-submissao]').forEach(form => new ControleSubmissao(form));
  const controle = document.querySelector('[data-senha]');
  if (controle) controle.addEventListener('click', () => {
    const senha = document.getElementById('senha');
    const mostrar = senha.type === 'password';
    senha.type = mostrar ? 'text' : 'password';
    controle.setAttribute('aria-pressed', String(mostrar));
    controle.setAttribute('aria-label', mostrar ? 'Ocultar senha' : 'Mostrar senha');
    const uso = controle.querySelector('use');
    uso.setAttribute('href', uso.getAttribute('href').split('#')[0] + (mostrar ? '#eye-off' : '#eye'));
  });
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
