// Locate JSON syntax errors without depending on browser-specific error messages.
function jsonErrorPosition(text) {
  let i = 0;
  const fail = () => { throw i; };
  const ws = () => { while (/[\x20\t\n\r]/.test(text[i] || '\u0000')) i++; };
  function string() {
    if (text[i++] !== '"') { i--; fail(); }
    while (i < text.length) {
      const c = text[i++];
      if (c === '"') return;
      if (c.charCodeAt(0) < 32) { i--; fail(); }
      if (c === '\\') {
        if (text[i] === 'u') {
          i++;
          for (let n = 0; n < 4; n++, i++) if (!/[0-9a-fA-F]/.test(text[i] || 'x')) fail();
        } else if ('"\\/bfnrt'.includes(text[i] || '\u0000')) i++;
        else fail();
      }
    }
    fail();
  }
  function value(depth) {
    if (depth > 500) fail();
    ws();
    if (text[i] === '"') return string();
    if (text[i] === '{' || text[i] === '[') {
      const object = text[i++] === '{', end = object ? '}' : ']';
      ws(); if (text[i] === end) { i++; return; }
      while (true) {
        ws();
        if (object) { string(); ws(); if (text[i] !== ':') fail(); i++; }
        value(depth + 1); ws();
        if (text[i] === end) { i++; return; }
        if (text[i] !== ',') fail();
        i++;
      }
    }
    for (const literal of ['true', 'false', 'null']) {
      if (text.slice(i, i + literal.length) === literal) { i += literal.length; return; }
    }
    const number = text.slice(i).match(/^-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?/);
    if (number) { i += number[0].length; return; }
    fail();
  }
  try { value(0); ws(); if (i !== text.length) fail(); } catch (position) { return Number.isInteger(position) ? position : i; }
  return i;
}
