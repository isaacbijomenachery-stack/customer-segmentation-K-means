// ── Scatter Canvas ──────────────────────────────────────────────
const canvas = document.getElementById('scatter');
const ctx = canvas.getContext('2d');
let currentView = 'rfm';

const COLORS = ['#6c63ff','#ff6584','#43e97b','#f7971e'];
const LABELS = ['Champions','At-Risk','Potential Loyalists','Hibernating'];

function resize() {
  const rect = canvas.parentElement.getBoundingClientRect();
  canvas.width = rect.width - 80;
  canvas.height = 340;
  draw();
}

// Generate synthetic cluster data
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
  const pw = W - pad.l - pad.r;
  const ph = H - pad.t - pad.b;

  ctx.clearRect(0, 0, W, H);

  // Grid
  ctx.strokeStyle = 'rgba(255,255,255,0.05)';
  ctx.lineWidth = 1;
  for (let i = 0; i <= 5; i++) {
    const x = pad.l + (pw / 5) * i;
    const y = pad.t + (ph / 5) * i;
    ctx.beginPath(); ctx.moveTo(x, pad.t); ctx.lineTo(x, pad.t + ph); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(pad.l + pw, y); ctx.stroke();
  }

  // Axis labels
  ctx.fillStyle = '#8888aa';
  ctx.font = '12px monospace';
  ctx.textAlign = 'center';
  ctx.fillText(xLabel, pad.l + pw / 2, H - 8);
  ctx.save();
  ctx.translate(14, pad.t + ph / 2);
  ctx.rotate(-Math.PI / 2);
  ctx.fillText(yLabel, 0, 0);
  ctx.restore();

  // Centroids
  const centroids = [[0,0],[0,0],[0,0],[0,0]];
  const counts = [0,0,0,0];
  pts.forEach(p => {
    centroids[p.cluster][0] += p.x;
    centroids[p.cluster][1] += p.y;
    counts[p.cluster]++;
  });

  centroids.forEach((c,i)=>{
    c[0]/=counts[i];
    c[1]/=counts[i];
  });

  // Points
  pts.forEach(p => {
    const px = pad.l + p.x * pw;
    const py = pad.t + (1 - p.y) * ph;
    ctx.beginPath();
    ctx.arc(px, py, 4, 0, Math.PI * 2);
    ctx.fillStyle = COLORS[p.cluster] + 'bb';
    ctx.fill();
  });

  // Centroid X
  centroids.forEach((c,i)=>{
    const px = pad.l + c[0] * pw;
    const py = pad.t + (1 - c[1]) * ph;
    ctx.strokeStyle = COLORS[i];
    ctx.lineWidth = 2;
    const s = 10;

    ctx.beginPath();
    ctx.moveTo(px - s, py - s);
    ctx.lineTo(px + s, py + s);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(px + s, py - s);
    ctx.lineTo(px - s, py + s);
    ctx.stroke();
  });
}

function drawElbow() {
  const W = canvas.width, H = canvas.height;
  ctx.clearRect(0, 0, W, H);

  const ks = [1,2,3,4,5,6,7,8];
  const inertia = [14200,9800,7100,4400,4100,3900,3800,3750];

  const maxI = Math.max(...inertia);
  const minI = Math.min(...inertia);

  const pad = {l:60,r:30,t:20,b:50};
  const pw = W - pad.l - pad.r;
  const ph = H - pad.t - pad.b;

  ctx.beginPath();
  ks.forEach((k,i)=>{
    const x = pad.l + (i/(ks.length-1))*pw;
    const y = pad.t + (1 - (inertia[i]-minI)/(maxI-minI))*ph;
    i===0 ? ctx.moveTo(x,y) : ctx.lineTo(x,y);
  });

  ctx.strokeStyle = '#6c63ff';
  ctx.lineWidth = 2;
  ctx.stroke();
}

function draw() {
  if (currentView === 'rfm') {
    drawScatter(rfmPts,'Frequency →','← Recency');
  } else if (currentView === 'spending') {
    drawScatter(spendPts,'Frequency →','← Monetary');
  } else {
    drawElbow();
  }
}

function setView(v) {
  currentView = v;
  draw();
}

window.addEventListener('resize', resize);
resize();