/*! consumo.js — rastreio de consumo das áreas de membros ZX LAB (HUB e ZX Control).
 * Fonte da verdade: agencia-ia-connect/public/consumo.js. Cada área serve a PRÓPRIA cópia (mesma origem). Spec: docs/superpowers/specs/2026-10-09-consumo-areas-membros-design.md
 *
 * Contexto da área (um dos dois):
 *   HUB:        <div data-consumo-area="hub_formacao|hub_50k"> em volta do player; token do Supabase Auth do HUB
 *   ZX Control: window.ZX_CONSUMO = { area: "zxc_v7", authKey: "v7_zxcontrol_auth" } antes deste script
 *
 * Fala com o player Bunny pelo protocolo player.js (postMessage). Eventos:
 *   open     primeiro play de cada vídeo na página
 *   progress a cada ~30 s de reprodução real (played_s = segundos tocados desde o último progress)
 *   end      vídeo terminou
 * Fila no localStorage, lote de até 50, event_id UUID (o servidor ignora repetidos).
 * Qualquer erro aqui é engolido: o rastreio nunca pode quebrar a área de membros.
 */
(function () {
  "use strict";
  if (window.__zxConsumo) return;
  window.__zxConsumo = true;

  var API = "https://pnfvlszwlumetdjsuktj.supabase.co/functions/v1";
  var HUB_AUTH_KEY = "sb-hjcudhxizemxepffrmbw-auth-token";
  var FILA_KEY = "zx_consumo_fila_v1";
  var TOKEN_KEY = "zx_consumo_tok_v1";
  var FILA_MAX = 500; // limite de armazenamento local; acima disso descarta os mais antigos
  var LOTE = 50; // igual ao LOTE_MAX da Edge consumo-evento
  var PROGRESSO_S = 30;
  var RENOVA_ANTES_S = 600;
  // renova de hora em hora mesmo com o comprovante válido: se o secret for trocado, a perda fica limitada a 1 h
  var RENOVA_MAX_S = 3600;
  var GUID_RE = /mediadelivery\.net\/embed\/\d+\/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/i;
  var ORIGEM_PLAYER = /^https:\/\/([a-z0-9-]+\.)*mediadelivery\.net$/;
  var SESSAO = rnd(16);
  var FETCH_TIMEOUT_MS = 10000; // conexão pendurada não pode travar a fila da página inteira

  function rnd(n) {
    var a = new Uint8Array(n);
    crypto.getRandomValues(a);
    return Array.prototype.map.call(a, function (b) { return ("0" + b.toString(16)).slice(-2); }).join("");
  }
  function uuid() {
    if (crypto.randomUUID) return crypto.randomUUID();
    var h = rnd(16);
    return h.slice(0, 8) + "-" + h.slice(8, 12) + "-4" + h.slice(13, 16) + "-" +
      ((parseInt(h[16], 16) & 3) | 8).toString(16) + h.slice(17, 20) + "-" + h.slice(20, 32);
  }
  function ler(k) { try { return JSON.parse(localStorage.getItem(k) || "null"); } catch (e) { return null; } }
  function gravar(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); return true; } catch (e) { return false; /* cota cheia ou bloqueado */ } }
  function agora() { return Math.floor(Date.now() / 1000); }
  function comTimeout(opts) {
    try {
      if (typeof AbortSignal !== "undefined" && AbortSignal.timeout) opts.signal = AbortSignal.timeout(FETCH_TIMEOUT_MS);
      else if (typeof AbortController !== "undefined") {
        var ac = new AbortController();
        setTimeout(function () { ac.abort(); }, FETCH_TIMEOUT_MS);
        opts.signal = ac.signal;
      }
    } catch (e) { /* navegador sem AbortController */ }
    return opts;
  }

  // ---------- identidade ----------
  function cfgZxc() { var c = window.ZX_CONSUMO; return c && c.area && c.authKey ? c : null; }

  /** { scope, chave, corpo } da identidade atual, ou null se ninguém logado. */
  function identidade() {
    var z = cfgZxc();
    if (z) {
      var a = ler(z.authKey);
      var email = a && a.loggedIn && a.student && typeof a.student.email === "string" ? a.student.email.trim().toLowerCase() : "";
      if (!email) return null;
      return { scope: "zxc", chave: "zxc:" + email, corpo: { scope: "zxc", email: email, area: z.area } };
    }
    var s = ler(HUB_AUTH_KEY);
    var tok = s && (s.access_token || (s.currentSession && s.currentSession.access_token));
    var uid = s && s.user && s.user.id;
    if (!tok || !uid) return null;
    return { scope: "hub", chave: "hub:" + uid, corpo: { scope: "hub", access_token: tok } };
  }

  /** Comprovante guardado ainda serve? Conta pelo relógio local desde que foi recebido (não pela hora absoluta). */
  function valido(t, chave) {
    if (!t || t.chave !== chave || typeof t.em !== "number" || typeof t.ttl !== "number") return false;
    var idade = agora() - t.em;
    return idade >= 0 && idade < Math.min(t.ttl - RENOVA_ANTES_S, RENOVA_MAX_S);
  }

  var pedindo = null;
  /** Comprovante válido para a identidade atual (renova perto do vencimento). */
  function comprovante() {
    var id = identidade();
    if (!id) return Promise.resolve(null);
    var t = ler(TOKEN_KEY);
    if (valido(t, id.chave)) return Promise.resolve({ chave: id.chave, token: t.token });
    if (pedindo) return pedindo;
    pedindo = fetch(API + "/consumo-sessao", comTimeout({
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(id.corpo),
    })).then(function (r) { return r.ok ? r.json() : null; }).then(function (j) {
      if (!j || typeof j.token !== "string" || typeof j.ttl !== "number") return null;
      gravar(TOKEN_KEY, { chave: id.chave, token: j.token, em: agora(), ttl: j.ttl });
      return { chave: id.chave, token: j.token };
    }).catch(function () { return null; }).then(function (r) { pedindo = null; return r; });
    return pedindo;
  }

  // ---------- fila ----------
  /** chave = identidade de quando o vídeo começou a tocar; se mudou de lá pra cá, o acumulado é descartado. */
  function enfileirar(ev, chave) {
    var id = identidade();
    if (!id || (chave && id.chave !== chave)) return false;
    ev.event_id = uuid();
    ev.session_id = SESSAO;
    ev.client_ts = new Date().toISOString();
    ev._k = id.chave;
    var f = ler(FILA_KEY) || [];
    f.push(ev);
    if (f.length > FILA_MAX) f = f.slice(f.length - FILA_MAX);
    return gravar(FILA_KEY, f);
  }

  /** Lote da identidade atual. Eventos de outra identidade ficam na fila até ela voltar (ou o teto FILA_MAX). */
  function lote(chave) {
    var f = (ler(FILA_KEY) || []).filter(function (e) { return e && e._k === chave; });
    return f.slice(0, LOTE);
  }
  /** Tira da fila só os eventos confirmados pelo servidor. */
  function remover(ids) {
    var set = {};
    ids.forEach(function (i) { set[i] = 1; });
    var f = (ler(FILA_KEY) || []).filter(function (e) { return e && !set[e.event_id]; });
    gravar(FILA_KEY, f);
  }
  function corpo(token, evs) {
    return JSON.stringify({
      token: token,
      events: evs.map(function (e) {
        var o = {};
        for (var k in e) if (k !== "_k") o[k] = e[k];
        return o;
      }),
    });
  }

  var enviando = false;
  function enviar() {
    if (enviando) return;
    enviando = true;
    comprovante().then(function (c) {
      if (!c) return;
      var evs = lote(c.chave);
      if (!evs.length) return;
      return fetch(API + "/consumo-evento", comTimeout({
        method: "POST", headers: { "Content-Type": "text/plain" }, body: corpo(c.token, evs), keepalive: true,
      })).then(function (r) {
        // 400 = corpo que o servidor nunca vai aceitar: descarta, senão o lote trava a fila desta identidade
        if (r.ok || r.status === 400) remover(evs.map(function (e) { return e.event_id; }));
      });
    }).catch(function () { /* tenta de novo no próximo ciclo */ }).then(function () { enviando = false; });
  }

  /** Saída da página: sendBeacon com o comprovante guardado. Não tira da fila (o beacon não confirma entrega):
   * o próximo carregamento reenvia e o servidor ignora event_id repetido. */
  function enviarNaSaida() {
    try {
      var id = identidade();
      var t = ler(TOKEN_KEY);
      if (!id || !valido(t, id.chave) || !navigator.sendBeacon) return;
      var evs = lote(id.chave);
      if (!evs.length) return;
      navigator.sendBeacon(API + "/consumo-evento", new Blob([corpo(t.token, evs)], { type: "text/plain" }));
    } catch (e) { /* nada */ }
  }

  // ---------- player ----------
  function areaDe(iframe) {
    var z = cfgZxc();
    if (z) return z.area;
    var el = iframe.closest && iframe.closest("[data-consumo-area]");
    var a = el && el.getAttribute("data-consumo-area");
    return /^hub_(formacao|50k)$/.test(a || "") ? a : null;
  }

  var players = []; // { iframe, key, area, chave, pos, ts, dur, tocado, abriu, pausado }

  function estadoDe(win) {
    for (var i = 0; i < players.length; i++) if (players[i].iframe.contentWindow === win) return players[i];
    return null;
  }

  function registrar(iframe) {
    var m = GUID_RE.exec(iframe.src || "");
    if (!m) return null;
    var key = m[1].toLowerCase();
    for (var i = 0; i < players.length; i++) {
      if (players[i].iframe === iframe) {
        if (players[i].key !== key) {
          fecharProgresso(players[i]);
          // estado desconhecido = não conta até o player avisar "play"
          players[i].key = key; players[i].abriu = false; players[i].pos = null; players[i].dur = null; players[i].pausado = true;
          players[i].chave = null;
        }
        return players[i];
      }
    }
    var p = { iframe: iframe, key: key, area: areaDe(iframe), chave: null, pos: null, ts: 0, dur: null, tocado: 0, abriu: false, pausado: true };
    players.push(p);
    return p;
  }

  function enviarAoPlayer(p, metodo, valor) {
    try {
      var origem = new URL(p.iframe.src).origin;
      p.iframe.contentWindow.postMessage(JSON.stringify({
        context: "player.js", version: "0.0.11", method: metodo, value: valor, listener: "zxc-" + valor,
      }), origem);
    } catch (e) { /* iframe sem janela ainda */ }
  }
  function assinar(p) {
    ["play", "pause", "ended", "timeupdate"].forEach(function (ev) { enviarAoPlayer(p, "addEventListener", ev); });
  }

  function evento(p, tipo, extra) {
    // iframe já removido (troca de aula no React) não tem mais ancestral: vale a área guardada no registro
    var area = (document.contains(p.iframe) && areaDe(p.iframe)) || p.area;
    if (area) p.area = area;
    if (!area) return false;
    var e = { area: area, lesson_key: p.key, event_type: tipo };
    if (p.pos != null) e.position_s = Math.round(p.pos);
    if (p.dur != null && p.dur > 0 && p.dur <= 86400) e.duration_s = Math.round(p.dur);
    if (extra) for (var k in extra) e[k] = extra[k];
    return enfileirar(e, p.chave);
  }

  /** Emite o tocado em partes de até 45 s (teto do servidor); o resto abaixo de 1 s fica para o próximo. */
  function fecharProgresso(p) {
    while (p.tocado >= 1) {
      var n = Math.min(45, Math.round(p.tocado));
      evento(p, "progress", { played_s: n });
      p.tocado -= n;
    }
    if (p.tocado < 0) p.tocado = 0;
  }
  /** Fixa quem está assistindo; troca de login no meio descarta o acumulado do anterior.
   * Devolve false quando ninguém está logado (aí o tempo não conta para ninguém). */
  function fixarChave(p) {
    var id = identidade();
    if (!id) return false;
    if (p.chave !== id.chave) { p.chave = id.chave; p.tocado = 0; }
    return true;
  }

  window.addEventListener("message", function (msg) {
    try {
      if (!ORIGEM_PLAYER.test(msg.origin)) return;
      var d = typeof msg.data === "string" ? JSON.parse(msg.data) : msg.data;
      if (!d || d.context !== "player.js") return;
      var p = estadoDe(msg.source);
      if (!p) {
        varrer();
        p = estadoDe(msg.source);
        if (!p) return;
      }
      var v = d.value || {};
      switch (d.event) {
        case "ready":
          assinar(p);
          break;
        case "play":
          p.pausado = false;
          p.pos = null; // a busca feita com o vídeo pausado não conta como assistida
          fixarChave(p);
          if (!p.abriu) p.abriu = evento(p, "open");
          break;
        case "timeupdate": {
          var s = Number(v.seconds), dur = Number(v.duration);
          if (isFinite(dur) && dur > 0) p.dur = dur;
          if (!isFinite(s)) break;
          // conta segundos de CONTEÚDO tocados (a 2x, 10 s reais valem 20 s de aula). Só avanço contínuo:
          // pausado, volta ou pulo maior que o tempo real decorrido (até 3x de velocidade) não contam.
          var t = Date.now();
          // sem ninguém logado não acumula: o tempo não pode ir para quem logar depois
          if (fixarChave(p) && p.pos != null && !p.pausado) {
            var delta = s - p.pos;
            var real = (t - p.ts) / 1000;
            if (delta > 0 && delta <= Math.max(3, real * 3 + 1)) p.tocado += delta;
          }
          p.pos = s;
          p.ts = t;
          if (!p.abriu && p.tocado > 0) p.abriu = evento(p, "open");
          if (p.tocado >= PROGRESSO_S) fecharProgresso(p);
          break;
        }
        case "pause":
          p.pausado = true;
          fecharProgresso(p);
          enviar();
          break;
        case "ended":
          p.pausado = true;
          fecharProgresso(p);
          evento(p, "end");
          enviar();
          break;
      }
    } catch (e) { /* mensagem de outro formato */ }
  });

  function varrer() {
    try {
      var fs = document.getElementsByTagName("iframe");
      for (var i = 0; i < fs.length; i++) {
        var f = fs[i];
        if (!GUID_RE.test(f.src || "")) continue;
        var novo = !players.some(function (p) { return p.iframe === f; });
        var p = registrar(f);
        // player que já carregou antes deste script não manda "ready" de novo: assina direto
        if (p && novo) assinar(p);
      }
      players = players.filter(function (p) {
        if (document.contains(p.iframe)) return true;
        fecharProgresso(p);
        return false;
      });
    } catch (e) { /* nada */ }
  }

  function iniciar() {
    varrer();
    try {
      // agrupa mutações (contadores da página mudam o DOM a cada segundo)
      var agendado = null;
      new MutationObserver(function () {
        if (agendado) return;
        agendado = setTimeout(function () { agendado = null; varrer(); }, 300);
      }).observe(document.documentElement, {
        childList: true, subtree: true, attributes: true, attributeFilter: ["src"],
      });
    } catch (e) { /* nada */ }
    setInterval(enviar, 20000);
    document.addEventListener("visibilitychange", function () {
      if (document.visibilityState === "hidden") {
        players.forEach(fecharProgresso);
        enviarNaSaida();
      }
    });
    window.addEventListener("pagehide", function () {
      players.forEach(fecharProgresso);
      enviarNaSaida();
    });
    enviar();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", iniciar);
  else iniciar();
})();
