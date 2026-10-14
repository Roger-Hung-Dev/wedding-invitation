// 開場影片剪接樣式：字卡、轉場的「唯一一份」實作（2026-10-12）。
// 展示頁（Artifact）、render-settings mod 的動態預覽、正式剪接的逐格截圖（render_edit.py）都載入這一份，
// 所以預覽看到的就是成品。樣式清單、配色、字型在 catalog.json；這裡的 CAPTIONS／TRANSITIONS 鍵名要和 catalog 的 id 一致。
//
// 用法：
//   const p = EditStyles.player(容器元素, catalog, program, settings)
//   p.renderAt(t)        畫出第 t 秒（不等影片，用在播放）
//   await p.seek(t)      畫出第 t 秒並等影片跳到那一格（用在逐格截圖、拖時間軸）
//   p.play() / p.pause() / p.duration / p.update(settings)
// program：{ shots: [{ id, label, src, dur（鏡內秒數）, in_s（選填：影片開頭要跳過的秒數＝頭尾多做的）, cap: [標題, 內容], cue: [進場秒, 退場秒或 null] }] }
//   program 最上層可加 "caption_hold": "until_next"：退場秒空白的字卡跨鏡留到下一張字卡進場前（先退完、空 0.15 秒，新的才進；最後一張留到片尾）
// settings：{ caption_style, font, palette, layout, transition, transition_s, caption_speed, title_size }
(function () {
  const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
  const ease = (x) => 1 - Math.pow(1 - clamp(x), 3);
  const back = (x) => { x = clamp(x); const c = 1.7; return 1 + (c + 1) * Math.pow(x - 1, 3) + c * Math.pow(x - 1, 2); };
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  const CSS = `
  .es-stage { position: relative; width: 100%; aspect-ratio: 16 / 9; overflow: hidden; background: #d6d6d6; container-type: inline-size }
  .es-layer { position: absolute; inset: 0; overflow: hidden }
  .es-layer video { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover }
  /* col 版面：影片原樣鋪滿（不平移、不縮放），左 40% 由字卡底色蓋住 → 影片區剛好是原片 x 40%～100%（film.json caption_safe 左 0.4）。
     2026-10-13 拿掉原本的 translateX(18%)：它把原片右邊 18% 推出畫面，構圖在 70%～80% 的人被切掉 */
  .es-colbg { position: absolute; left: 0; top: 0; bottom: 0; width: 40%; background: var(--cap-bg) }
  .es-stage:not(.col) .es-colbg { display: none }
  .es-cap { position: absolute; z-index: 60; left: 4.5%; top: 50%; width: 32%; transform: translateY(-50%); display: grid; gap: 1.2cqw; font-family: var(--cap-font) }
  .es-stage:not(.col) .es-cap { left: 4%; width: 40% }
  .es-cap .t { font-weight: 700; font-size: var(--title-size); line-height: 1.15; color: var(--cap-title); justify-self: start; transform-origin: 30% 50%; white-space: pre-wrap }
  .es-cap .b { font-size: calc(var(--title-size) * .5); color: var(--cap-text); line-height: 1.45 }
  .es-stage:not(.col) .es-cap .t, .es-stage:not(.col) .es-cap .b { text-shadow: 0 .15cqw .6cqw rgba(0,0,0,.35) }
  .es-cap.stamp .t { border: .35cqw solid currentColor; border-radius: .6cqw; padding: .3cqw 1.2cqw }
  .es-cap.card .box { background: var(--cap-card); border-radius: 1.2cqw; padding: 1.6cqw 2cqw; box-shadow: 0 .6cqw 2cqw rgba(0,0,0,.18); display: grid; gap: 1cqw }
  .es-caret { display: inline-block; width: .25cqw; height: 1em; background: currentColor; vertical-align: -0.12em; margin-left: .2cqw }
  .es-flash, .es-black { position: absolute; inset: 0; pointer-events: none; opacity: 0 }
  .es-flash { background: #fff } .es-black { background: #000 }
  .es-pillar { position: absolute; top: -5%; bottom: -5%; width: 16%; left: 130%; transform: translateX(-50%); pointer-events: none;
    background: linear-gradient(90deg, rgba(0,0,0,0) 0, #5b4a43 12%, #7a665d 45%, #4a3c36 85%, rgba(0,0,0,0) 100%) }`;

  // ── 字卡：ti＝進場後幾秒、to＝退場後幾秒（還沒退場為 null）、sp＝速度倍率。回傳這一格的 HTML 與樣式 ──
  const CAPTIONS = {
    stamp(txt, ti, sp) {
      const d = 0.42 / sp, p = clamp(ti / d);
      const sc = p < 0.55 ? 1.8 + (0.92 - 1.8) * ease(p / 0.55) : 0.92 + 0.08 * ease((p - 0.55) / 0.45);
      const q = clamp((ti - 0.3 / sp) / (0.4 / sp));
      return { html: `<div class="t">${esc(txt[0])}</div><div class="b">${esc(txt[1])}</div>`,
        t: `transform: rotate(${-9 + 6 * ease(p)}deg) scale(${sc}); opacity:${clamp(p * 3)}`,
        b: `opacity:${q}; transform: translateY(${(1 - ease(q)) * 1.2}cqw)` };
    },
    type(txt, ti, sp) {
      const cps = 11 * sp, [a, b] = txt, n = Math.floor(ti * cps), nb = Math.floor((ti - a.length / cps - 0.25) * cps);
      const caret = `<span class="es-caret" style="opacity:${Math.floor(ti * 2.2) % 2 === 0 ? 1 : 0}"></span>`;
      return { html: `<div class="t">${esc(a.slice(0, n))}${n < a.length ? caret : ""}</div><div class="b">${esc(b.slice(0, Math.max(0, nb)))}${n >= a.length ? caret : ""}</div>` };
    },
    card(txt, ti, sp) {
      const p = clamp(ti / (0.55 / sp));
      return { html: `<div class="box" style="transform: translateX(${(1 - back(p)) * -120}%)"><div class="t">${esc(txt[0])}</div><div class="b">${esc(txt[1])}</div></div>` };
    },
    soft(txt, ti, sp) {
      const p = clamp(ti / (0.9 / sp)), q = clamp((ti - 0.35 / sp) / (0.9 / sp));
      return { html: `<div class="t">${esc(txt[0])}</div><div class="b">${esc(txt[1])}</div>`,
        // 字距拉開改用橫向放大（2026-10-12）：letter-spacing 會改變排版寬度，長標題進場時先斷成兩行再縮回一行；transform 不影響排版
        t: `filter: blur(${(1 - ease(p)) * 1.2}cqw); letter-spacing:0.06em; transform: scaleX(${1 + (1 - ease(p)) * 0.3}); opacity:${ease(p)}`,
        b: `filter: blur(${(1 - ease(q)) * 0.8}cqw); opacity:${ease(q)}` };
    },
  };
  // 退場（劇本：人一起步，舊字就滑出）
  const CAPTION_OUT = {
    soft: (p) => `filter: blur(${p * 1.2}cqw); opacity:${1 - p}`,
    card: (p) => `transform: translate(${-p * 120}%, -50%)`,
    _: (p) => `transform: translate(${-p * 30}%, -50%); opacity:${1 - p}`,
  };

  function drawCaption(el, style, txt, ti, to, sp) {
    el.className = "es-cap " + style;
    if (ti < 0 || (to !== null && to > 0.5 / sp)) { el.innerHTML = ""; el.style.cssText = "opacity:0"; return; }
    const r = (CAPTIONS[style] || CAPTIONS.stamp)(txt, ti, sp);
    el.innerHTML = r.html;
    if (r.t) el.querySelector(".t").style.cssText = r.t;
    if (r.b) el.querySelector(".b").style.cssText = r.b;
    el.style.cssText = to !== null && to > 0 ? (CAPTION_OUT[style] || CAPTION_OUT._)(ease(to / (0.5 / sp))) : "";
  }

  // ── 轉場：p＝轉場進度 0～1；A＝前一段、B＝後一段的圖層。overlap 的轉場兩段同時在播，其他的在接點換 ──
  const TRANSITIONS = {
    cut: () => ({}),
    dissolve: (p) => ({ aOp: 1 - p, bOp: p }),
    push: (p) => ({ aTf: `translateX(${-ease(p) * 100}%)`, bTf: `translateX(${(1 - ease(p)) * 100}%)` }),
    scroll: (p) => ({ aTf: `translateX(${-p * 100}%)`, bTf: `translateX(${(1 - p) * 100}%)` }),
    pillar: (p) => { const x = 115 - p * 140; return { pillar: x, aClip: `inset(0 ${clamp(100 - x, 0, 100)}% 0 0)` }; },
    flash: (p) => ({ flash: 1 - Math.abs(p * 2 - 1) }),
    black: (p) => ({ black: 1 - Math.abs(p * 2 - 1) }),
  };

  function player(root, catalog, program, settings) {
    if (!document.getElementById("es-css")) { const s = document.createElement("style"); s.id = "es-css"; s.textContent = CSS; document.head.appendChild(s); }
    const st = document.createElement("div"); st.className = "es-stage col"; root.appendChild(st);
    const shots = program.shots.map((sh, i) => {
      const layer = document.createElement("div"); layer.className = "es-layer"; layer.style.zIndex = 10 + program.shots.length - i;
      const v = document.createElement("video"); v.src = sh.src; v.muted = true; v.playsInline = true; v.preload = "auto";
      layer.appendChild(v); st.appendChild(layer);
      return { ...sh, layer, v };
    });
    const colbg = document.createElement("div"); colbg.className = "es-colbg"; colbg.style.zIndex = 50; st.appendChild(colbg);
    const pillar = document.createElement("div"); pillar.className = "es-pillar"; pillar.style.zIndex = 40; st.appendChild(pillar);
    // 字卡的圖層順序寫在 CSS（.es-cap 的 z-index）：drawCaption 每格會重設 style，寫在 style 會被清掉
    shots.forEach((sh) => { sh.cap_el = document.createElement("div"); sh.cap_el.className = "es-cap"; st.appendChild(sh.cap_el); });
    const flash = document.createElement("div"); flash.className = "es-flash"; flash.style.zIndex = 70; st.appendChild(flash);
    const black = document.createElement("div"); black.className = "es-black"; black.style.zIndex = 70; st.appendChild(black);
    let S = settings, starts = [], playing = false;

    function layout() {
      const pal = catalog.palettes.find((x) => x.id === S.palette) || catalog.palettes[0];
      const font = catalog.fonts.find((x) => x.id === S.font) || catalog.fonts[0];
      st.style.setProperty("--cap-bg", pal.bg); st.style.setProperty("--cap-title", pal.title); st.style.setProperty("--cap-text", pal.text);
      st.style.setProperty("--cap-card", pal.card); st.style.setProperty("--cap-font", font.stack); st.style.setProperty("--title-size", S.title_size + "cqw");
      st.classList.toggle("col", S.layout === "col");
      const tr = catalog.transitions.find((x) => x.id === S.transition) || {};
      starts = []; let t0 = 0;
      shots.forEach((sh, i) => { starts.push(t0); t0 += sh.dur - (i < shots.length - 1 && tr.overlap ? S.transition_s : 0); });
      api.duration = starts[starts.length - 1] + shots[shots.length - 1].dur;
      api.joints = starts.slice(1).map((s) => (tr.overlap ? s + S.transition_s / 2 : s));
    }

    function state(t) {
      const d = S.transition_s, tr = catalog.transitions.find((x) => x.id === S.transition) || {};
      const fx = TRANSITIONS[S.transition] || TRANSITIONS.cut;
      const out = shots.map(() => ({ op: 0, tf: "", clip: "none" }));
      let fl = 0, bk = 0, pil = 130;
      shots.forEach((sh, i) => { const l = t - starts[i]; if (l >= 0 && l < sh.dur) out[i].op = 1; });
      for (let j = 0; j < shots.length - 1; j++) {
        const s = starts[j + 1];
        if (tr.overlap) {
          if (t < s || t > s + d) continue;
          const r = fx(clamp((t - s) / d));
          out[j].op = r.aOp ?? 1; out[j + 1].op = r.bOp ?? 1; out[j].tf = r.aTf || ""; out[j + 1].tf = r.bTf || "";
          out[j].clip = r.aClip || "none"; if (r.pillar !== undefined) pil = r.pillar;
        } else if (Math.abs(t - s) <= d / 2) {
          const r = fx(clamp((t - (s - d / 2)) / d)); fl = Math.max(fl, r.flash || 0); bk = Math.max(bk, r.black || 0);
        }
      }
      return { out, fl, bk, pil };
    }

    // 字卡跨鏡留著（program.caption_hold＝"until_next"，2026-10-12 使用者：左欄不要空掉）：
    // 退場秒空白的字卡留到「下一張有字的字卡進場」前退完，最後一張留到片尾；退場寫成數字的照舊。
    // 2026-10-12 導演端：舊字卡退場（0.5 秒）和新字卡進場同時發生會疊在左欄同一個位置 → 舊的提早退場，退完留 CAP_GAP 秒空白新的才進（新的進場秒不變）
    // 沒寫 caption_hold＝舊行為：退場空白的字卡在這一鏡畫面消失時一起消失
    const CAP_GAP = 0.15;
    const hasCap = (sh) => sh.cap && String(sh.cap[0] || "").trim() !== "";
    function holdOut(i) {
      const outDur = 0.5 / (S.caption_speed || 1), gin = starts[i] + shots[i].cue[0];
      for (let j = i + 1; j < shots.length; j++)
        if (hasCap(shots[j])) return Math.max(gin + outDur, starts[j] + shots[j].cue[0] - outDur - CAP_GAP);
      return api.duration;
    }

    function draw(t) {
      const z = state(t), hold = program.caption_hold === "until_next";
      shots.forEach((sh, i) => {
        const o = z.out[i]; sh.layer.style.opacity = o.op; sh.layer.style.transform = o.tf; sh.layer.style.clipPath = o.clip;
        const l = t - starts[i], [ci, co] = sh.cue;
        if (!hasCap(sh)) { drawCaption(sh.cap_el, S.caption_style, sh.cap, -1, null, S.caption_speed); return; }
        if (hold && co === null) {                       // 用整支片的時間算：進場＝這一鏡的進場秒，退場＝下一張字卡進場
          const gin = starts[i] + ci, gout = holdOut(i);
          drawCaption(sh.cap_el, S.caption_style, sh.cap, t - gin, t >= gout && gout < api.duration ? t - gout : null, S.caption_speed);
          return;
        }
        const visible = o.op > 0 || (l >= 0 && l < sh.dur);
        drawCaption(sh.cap_el, S.caption_style, sh.cap, visible ? l - ci : -1, co !== null && l >= co ? l - co : null, S.caption_speed);
      });
      flash.style.opacity = z.fl; black.style.opacity = z.bk; pillar.style.left = z.pil + "%";
    }

    // 影片裡要跳過的開頭（in_s＝完整渲染頭尾多做的秒數）：鏡內第 0 秒＝影片第 in_s 秒；dur 是鏡內長度
    function localOf(i, t) { const a = shots[i].in_s || 0; return a + clamp(t - starts[i], 0, shots[i].dur - 0.001); }
    function syncVideos(t, hard) {
      shots.forEach((sh, i) => {
        const l = t - starts[i], on = l >= 0 && l < sh.dur;
        if (!on || !playing) { if (!sh.v.paused) sh.v.pause(); }
        else if (sh.v.paused) sh.v.play().catch(() => {});
        if (on || hard) { const want = localOf(i, t); if (Math.abs(sh.v.currentTime - want) > (playing ? 0.25 : 0.01)) sh.v.currentTime = want; }
      });
    }

    const api = {
      stage: st, duration: 0, joints: [],
      update(s) { S = { ...S, ...s }; layout(); },
      renderAt(t) { syncVideos(t, false); draw(t); },
      async seek(t) {
        playing = false;
        await Promise.all(shots.map((sh, i) => new Promise((res) => {
          const want = localOf(i, t);
          const ready = () => (sh.v.readyState >= 2 ? res() : sh.v.addEventListener("loadeddata", res, { once: true }));
          sh.v.pause();
          // 影片已經停在那一格時瀏覽器不會發 seeked（2026-10-12 縮圖卡在第二張），只等資料載好
          if (Math.abs(sh.v.currentTime - want) < 0.001) return ready();
          sh.v.addEventListener("seeked", ready, { once: true }); sh.v.currentTime = want;
        })));
        draw(t);
        await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
      },
      play() { playing = true; }, pause() { playing = false; shots.forEach((sh) => sh.v.pause()); },
      get playing() { return playing; },
    };
    layout();
    return api;
  }

  window.EditStyles = { player, CAPTION_IDS: Object.keys(CAPTIONS), TRANSITION_IDS: Object.keys(TRANSITIONS) };
})();
