// Build a KDP-ready .docx from manuscript.md
const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel,
  AlignmentType, BorderStyle,
} = require('docx');

const md = fs.readFileSync('manuscript.md', 'utf8');
const lines = md.split('\n');

// Inline **bold** / *italic* -> TextRun[]
function inlineRuns(text, base = {}) {
  const runs = [];
  const re = /(\*\*([^*]+)\*\*|\*([^*]+)\*)/g;
  let last = 0, m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) runs.push(new TextRun({ text: text.slice(last, m.index), ...base }));
    if (m[2] !== undefined) runs.push(new TextRun({ text: m[2], bold: true, ...base }));
    else runs.push(new TextRun({ text: m[3], italics: true, ...base }));
    last = re.lastIndex;
  }
  if (last < text.length) runs.push(new TextRun({ text: text.slice(last), ...base }));
  if (runs.length === 0) runs.push(new TextRun({ text: '', ...base }));
  return runs;
}

const children = [];
let seenChapter = false; // false while in title-page front matter

for (let raw of lines) {
  const line = raw.replace(/\s+$/,'');
  const t = line.trim();

  if (t === '') continue;                 // blank -> skip (paragraphs are per-line)
  if (t === '---') continue;              // horizontal rules -> omit

  // Headings
  if (t.startsWith('#### ')) {
    children.push(new Paragraph({ heading: HeadingLevel.HEADING_3, children: inlineRuns(t.slice(5)) }));
    continue;
  }
  if (t.startsWith('### ')) {
    const centered = !seenChapter;
    children.push(new Paragraph({
      heading: HeadingLevel.HEADING_2,
      alignment: centered ? AlignmentType.CENTER : undefined,
      children: inlineRuns(t.slice(4)),
    }));
    continue;
  }
  if (t.startsWith('## ')) {
    seenChapter = true;
    children.push(new Paragraph({
      heading: HeadingLevel.HEADING_1,
      pageBreakBefore: true,
      children: inlineRuns(t.slice(3)),
    }));
    continue;
  }
  if (t.startsWith('# ')) {
    children.push(new Paragraph({
      heading: HeadingLevel.TITLE,
      alignment: AlignmentType.CENTER,
      spacing: { before: 480, after: 240 },
      children: inlineRuns(t.slice(2)),
    }));
    continue;
  }

  // Blockquote (tips)
  if (t.startsWith('> ')) {
    children.push(new Paragraph({
      indent: { left: 480, right: 480 },
      spacing: { before: 120, after: 120 },
      border: { left: { style: BorderStyle.SINGLE, size: 18, space: 12, color: 'C8A15A' } },
      children: inlineRuns(t.slice(2), { italics: true }),
    }));
    continue;
  }

  // Checklist item "- [ ] X"
  const chk = t.match(/^-\s*\[[ xX]?\]\s+(.*)$/);
  if (chk) {
    children.push(new Paragraph({
      indent: { left: 360 },
      spacing: { after: 60 },
      children: [ new TextRun({ text: '☐  ' }), ...inlineRuns(chk[1]) ],
    }));
    continue;
  }

  // Bullet list "- X" or "* X"
  const bul = t.match(/^[-*]\s+(.*)$/);
  if (bul) {
    children.push(new Paragraph({ bullet: { level: 0 }, children: inlineRuns(bul[1]) }));
    continue;
  }

  // Numbered "N. X" -> keep number inline as plain paragraph (clean & reliable)
  const num = t.match(/^(\d+)\.\s+(.*)$/);
  if (num) {
    children.push(new Paragraph({
      indent: { left: 360 },
      spacing: { after: 60 },
      children: [ new TextRun({ text: num[1] + '. ', bold: true }), ...inlineRuns(num[2]) ],
    }));
    continue;
  }

  // Normal paragraph
  children.push(new Paragraph({ spacing: { after: 160 }, children: inlineRuns(t) }));
}

const doc = new Document({
  creator: 'CappadociaOps',
  title: 'Cappadocia: The Complete Traveler’s Guide',
  styles: {
    default: {
      document: { run: { font: 'Georgia', size: 24 } }, // 12pt
    },
  },
  sections: [{ children }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync('Cappadocia-Travel-Guide.docx', buf);
  console.log('wrote Cappadocia-Travel-Guide.docx', buf.length, 'bytes,', children.length, 'blocks');
});
