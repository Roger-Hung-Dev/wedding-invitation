// 唯讀：抽出 v2 分鏡稿的所有標註文字，印出一行 JSON（storyboard-raw/v2）。
// 用法：整段貼進 mcp__pencil-server__execute 的 input（filePath 帶分鏡稿絕對路徑）。
// 只有 Get／Print，不會觸發寫入守門 hook；也絕不可在這段裡加任何寫入函式。
const N = {}, K = {}, TOP = [];
Get(document, (n, c) => {
  const p = c.parentCtx && c.parentCtx.node ? c.parentCtx.node.id : "__root";
  N[n.id] = { id: n.id, name: n.name || "", type: n.type, on: n.enabled !== false,
              text: n.type === "text" ? String(n.content ?? "") : null };
  (K[p] = K[p] || []).push(n.id);
  if (c.depth === 0) TOP.push(n.id);
}, { depth: 30 });
const kids = (id) => (K[id] || []).map((k) => N[k]).filter((n) => n.on);
const find = (id, pred) => {
  for (const ch of kids(id)) { if (pred(ch)) return ch; const r = find(ch.id, pred); if (r) return r; }
  return null;
};
const textOf = (id, name) => { const t = find(id, (n) => n.type === "text" && n.name === name); return t ? t.text : null; };
// 收集 scope 底下所有「{prefix}{key}」列的值（列內名為「值」的文字節點）
const rows = (scope, prefix) => {
  const o = {};
  const walk = (id) => kids(id).forEach((n) => {
    if (n.type !== "text" && n.name.startsWith(prefix)) {
      const v = kids(n.id).find((x) => x.type === "text" && x.name === "值");
      if (v) o[n.name.slice(prefix.length)] = v.text;
    }
    walk(n.id);
  });
  walk(scope);
  return o;
};
const top = (re) => TOP.map((id) => N[id]).filter((n) => n.on && re.test(n.name));
const one = (re) => { const t = top(re); return t.length ? t[0].id : null; };

const ov = one(/^00 /), op = one(/^01 /), ed = one(/^02 /);
const payload = {
  schema: "storyboard-raw/v2",
  tops: TOP.map((id) => N[id].name),
  spec: ov ? rows(ov, "規格-") : {},
  openingParams: op ? rows(op, "參數-") : {},
  endingParams: ed ? rows(ed, "參數-") : {},
  rows: top(/^\d\d 分鏡列/).map((r) => {
    const hd = find(r.id, (n) => n.name === "章節標頭");
    return {
      name: r.name,
      chapter: hd ? (textOf(hd.id, "章名") || "") : "",
      header: hd ? rows(hd.id, "資訊-") : {},
      cards: kids(r.id).filter((n) => n.name.startsWith("鏡-")).map((cd) => ({
        frame: cd.name,
        id: textOf(find(cd.id, (n) => n.name === "標註")?.id ?? cd.id, "鏡號") || "",
        timecode: textOf(cd.id, "時間碼") || "",
        seconds: textOf(cd.id, "秒") || "",
        rows: rows(cd.id, "列-"),
      })),
    };
  }),
};
// 謄寫核對碼：build_storyboard.py 會用同一演算法重算，抄錯任何一個字都會被擋下
const s = JSON.stringify(payload);
let h = 5381;
for (const ch of s) h = (Math.imul(h, 33) + ch.codePointAt(0)) >>> 0;
const cards = payload.rows.reduce((a, r) => a + r.cards.length, 0);
Print(JSON.stringify({ payload, check: { cards, chars: [...s].length, hash: h } }));
