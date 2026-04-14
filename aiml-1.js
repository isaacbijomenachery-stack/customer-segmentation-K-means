const canvas = document.getElementById('scatter');
const ctx = canvas.getContext('2d');
let currentView = 'rfm';

const COLORS = ['#6c63ff','#ff6584','#43e97b','#f7971e'];

// Synthetic Data Generation
function genClusters(view) {
  const pts = [];
  const configs = view === 'rfm' ? [
    { cx: 0.75, cy: 0.8,  spread: 0.1, n: 55 },
    { cx: 0.25, cy: 0.45, spread: 0.1, n: 40 },
    { cx: 0.65, cy: 0.4,  spread: 0.12, n: 50 },
    { cx: 0.2,  cy: 0.2,  spread: 0.08, n: 35 }
  ] : [
    { cx: 0.8,  cy: 0.85, spread: 0.09, n: 55 },
    { cx: 0.35, cy: 0.5,  spread: 0.1,  n: 40 },
    { cx: 0.55, cy: 0.35, spread: 0.11, n: 50 },
    { cx: 0.15, cy: 0.18, spread: 0.07, n: 35 }
  ];
  configs.forEach((c, ci) => {
    for (let i = 0; i < c.n; i++) {
      const angle = Math.random() * 2 * Math.PI;
      const r = Math.random() * c.spread;
      pts.push({ x: c.cx + r * Math.cos(angle), y: c.cy + r * Math.sin(angle), cluster: ci });
    }
  });
  return pts;
}

const rfmPts = genClusters('rfm');
const spendPts = genClusters('spending');

function drawScatter(pts, xLabel, yLabel) {
  const W = canvas.width, H = canvas.height;
  const pad = { l: 50, r: 20, t: 20, b: 40 };
  const pw = W - pad.l - pad.r, ph = H - pad.t - pad.b;

  ctx.clearRect(0, 0, W, H);

  // Draw Points
  pts.forEach(p => {
    const px = pad.l + p.x * pw;
    const py = pad.t + (1 - p.y) * ph;
    ctx.beginPath();
    ctx.arc(px, py, 4, 0, Math.PI * 2);
    ctx.fillStyle = COLORS[p.cluster] + 'bb';
    ctx.fill();
  });
}

function setView(v) {
  currentView = v;
  document.querySelectorAll('.tab').forEach((t, i) => {
    t.classList.toggle('active', ['rfm','spending','elbow'][i] === v);
  });
  draw();
}

function draw() {
  if (currentView === 'rfm') drawScatter(rfmPts, 'Frequency →', '← Recency');
  else if (currentView === 'spending') drawScatter(spendPts, 'Frequency →', '← Monetary');
  // Logic for Elbow drawing omitted for brevity but follows same pattern
}

window.addEventListener('resize', () => {
  canvas.width = canvas.parentElement.clientWidth - 80;
  draw();
});

// Init
canvas.width = canvas.parentElement.clientWidth - 80;
draw();