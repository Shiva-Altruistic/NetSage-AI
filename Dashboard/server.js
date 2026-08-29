import express from 'express';
import cors from 'cors';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PROJECT_ROOT = path.resolve(__dirname, '..');

const app = express();
const PORT = 3001;

app.use(cors());
app.use(express.json());

// ---------------------------------------------------------------------------
// CSV & JSON Helpers
// ---------------------------------------------------------------------------

function parseCSV(text) {
  if (!text || !text.trim()) return [];
  const rows = [];
  let row = [];
  let cell = '';
  let inQuotes = false;

  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    const nextChar = text[i + 1];

    if (inQuotes) {
      if (char === '"') {
        if (nextChar === '"') {
          cell += '"';
          i++;
        } else {
          inQuotes = false;
        }
      } else {
        cell += char;
      }
    } else {
      if (char === '"') {
        inQuotes = true;
      } else if (char === ',') {
        row.push(cell.trim());
        cell = '';
      } else if (char === '\r') {
        if (nextChar === '\n') i++;
        row.push(cell.trim());
        cell = '';
        if (row.length > 1 || (row.length === 1 && row[0] !== '')) {
          rows.push(row);
        }
        row = [];
      } else if (char === '\n') {
        row.push(cell.trim());
        cell = '';
        if (row.length > 1 || (row.length === 1 && row[0] !== '')) {
          rows.push(row);
        }
        row = [];
      } else {
        cell += char;
      }
    }
  }
  if (cell || row.length > 0) {
    row.push(cell.trim());
    rows.push(row);
  }

  if (rows.length === 0) return [];
  const headers = rows[0].map((h) => h.trim());
  const result = [];
  for (let r = 1; r < rows.length; r++) {
    const obj = {};
    headers.forEach((h, idx) => {
      obj[h] = rows[r][idx] !== undefined ? rows[r][idx] : '';
    });
    result.push(obj);
  }
  return result;
}

function readCSVFile(filePath) {
  try {
    if (!fs.existsSync(filePath)) return [];
    const content = fs.readFileSync(filePath, 'utf-8');
    return parseCSV(content);
  } catch (err) {
    console.error(`Error reading ${filePath}:`, err);
    return [];
  }
}

function writeCSVFile(filePath, rows) {
  if (!rows || rows.length === 0) return;
  const headers = Object.keys(rows[0]);
  const lines = [headers.join(',')];

  rows.forEach((r) => {
    const vals = headers.map((h) => {
      let val = r[h] !== undefined && r[h] !== null ? String(r[h]) : '';
      if (val.includes(',') || val.includes('"') || val.includes('\n')) {
        val = `"${val.replace(/"/g, '""')}"`;
      }
      return val;
    });
    lines.push(vals.join(','));
  });

  fs.writeFileSync(filePath, lines.join('\n') + '\n', 'utf-8');
}

// ---------------------------------------------------------------------------
// API Endpoints
// ---------------------------------------------------------------------------

// 1. Overview KPIs
app.get('/api/overview', (req, res) => {
  const cases = readCSVFile(path.join(PROJECT_ROOT, 'Dataset', 'cases.csv'));
  const promptComp = readCSVFile(path.join(PROJECT_ROOT, 'Results', 'prompt_comparison.csv'));
  const humanReviews = readCSVFile(path.join(PROJECT_ROOT, 'Results', 'human_review.csv'));
  const evalResults = readCSVFile(path.join(PROJECT_ROOT, 'Results', 'eval_results.csv'));

  const totalCases = cases.length;
  const evaluatedCount = promptComp.length;

  let v1AvgScore = 0;
  let v2AvgScore = 0;
  if (promptComp.length > 0) {
    v1AvgScore =
      promptComp.reduce((acc, r) => acc + (parseFloat(r.V1_score) || 0), 0) /
      promptComp.length;
    v2AvgScore =
      promptComp.reduce((acc, r) => acc + (parseFloat(r.V2_score) || 0), 0) /
      promptComp.length;
  }

  const approvedReviews = humanReviews.filter((r) => r.decision === 'APPROVED').length;
  const modifiedReviews = humanReviews.filter((r) => r.decision === 'MODIFIED').length;
  const rejectedReviews = humanReviews.filter((r) => r.decision === 'REJECTED').length;
  const approvalRate = humanReviews.length
    ? (approvedReviews / humanReviews.length) * 100
    : 0;

  const highRiskCount = humanReviews.filter((r) => r.risk_level === 'High').length;
  const mediumRiskCount = humanReviews.filter((r) => r.risk_level === 'Medium').length;

  // Category counts
  const categoryCounts = {};
  cases.forEach((c) => {
    const tag = c.concept_tag || 'unknown';
    categoryCounts[tag] = (categoryCounts[tag] || 0) + 1;
  });

  // Topologies
  const topologies = [
    { id: 'A', name: 'SOHO Branch', count: 6, devices: 'R1-BR, SW1' },
    { id: 'B', name: 'Campus L3', count: 6, devices: 'SW-CORE, SW-DIST, SW-ACC' },
    { id: 'C', name: 'WAN Edge', count: 6, devices: 'R1 (HQ), R2 (Branch)' },
    { id: 'D', name: 'Internet Edge', count: 6, devices: 'R-EDGE (NAT/PAT/ACL)' },
    { id: 'E', name: 'Wireless LAN', count: 6, devices: 'WLC1, AP1, AP2' },
  ];

  res.json({
    totalCases,
    evaluatedCount,
    v1AvgScore: (v1AvgScore * 100).toFixed(1),
    v2AvgScore: (v2AvgScore * 100).toFixed(1),
    approvalRate: approvalRate.toFixed(1),
    humanReviewsCount: humanReviews.length,
    approvedReviews,
    modifiedReviews,
    rejectedReviews,
    highRiskCount,
    mediumRiskCount,
    categoryCounts,
    topologies,
  });
});

// 2. Cases Explorer
app.get('/api/cases', (req, res) => {
  const cases = readCSVFile(path.join(PROJECT_ROOT, 'Dataset', 'cases.csv'));
  const aiDiags = readCSVFile(path.join(PROJECT_ROOT, 'Results', 'ai_diagnoses.csv'));
  const promptComp = readCSVFile(path.join(PROJECT_ROOT, 'Results', 'prompt_comparison.csv'));
  const humanReviews = readCSVFile(path.join(PROJECT_ROOT, 'Results', 'human_review.csv'));

  const aiLookup = {};
  aiDiags.forEach((d) => (aiLookup[d.case_id] = d));

  const compLookup = {};
  promptComp.forEach((c) => (compLookup[c.case_id] = c));

  const reviewLookup = {};
  humanReviews.forEach((r) => (reviewLookup[r.case_id] = r));

  const enriched = cases.map((c) => {
    const cid = c.case_id;
    const diag = aiLookup[cid] || {};
    const comp = compLookup[cid] || {};
    const rev = reviewLookup[cid] || {};

    return {
      ...c,
      ai_fault: diag.fault || comp.V2_fault || '',
      ai_osi_layer: diag.osi_layer || comp.V2_osi_layer || 0,
      ai_concept_tag: diag.concept_tag || comp.V2_concept_tag || '',
      ai_severity: diag.severity || comp.V2_severity || '',
      ai_confidence: diag.confidence || comp.V2_confidence || '',
      ai_next_command: diag.next_command || comp.V2_next_command || '',
      ai_fix: diag.fix || comp.V2_fix || '',
      v1_score: comp.V1_score ? (parseFloat(comp.V1_score) * 100).toFixed(1) : null,
      v2_score: comp.V2_score ? (parseFloat(comp.V2_score) * 100).toFixed(1) : null,
      human_decision: rev.decision || 'PENDING',
      risk_level: rev.risk_level || 'Low',
      reviewer_notes: rev.reviewer_notes || '',
      approved_fix: rev.approved_fix || '',
    };
  });

  res.json(enriched);
});

// 3. Prompt Comparison Studio
app.get('/api/prompt-comparison', (req, res) => {
  const promptComp = readCSVFile(path.join(PROJECT_ROOT, 'Results', 'prompt_comparison.csv'));
  const cases = readCSVFile(path.join(PROJECT_ROOT, 'Dataset', 'cases.csv'));
  const caseMap = {};
  cases.forEach((c) => (caseMap[c.case_id] = c));

  const enriched = promptComp.map((r) => {
    const c = caseMap[r.case_id] || {};
    const v1 = parseFloat(r.V1_score) || 0;
    const v2 = parseFloat(r.V2_score) || 0;
    const delta = v2 - v1;

    return {
      ...r,
      symptom: c.symptom || '',
      expected_fault: c.expected_fault || '',
      expected_fix: c.expected_fix || '',
      ground_truth_tag: c.concept_tag || '',
      ground_truth_osi: c.osi_layer || '',
      v1_pct: (v1 * 100).toFixed(1),
      v2_pct: (v2 * 100).toFixed(1),
      delta_pct: (delta * 100).toFixed(1),
      winner: delta > 0.005 ? 'V2' : delta < -0.005 ? 'V1' : 'TIE',
    };
  });

  res.json(enriched);
});

// 4. Human Reviews & Sign-offs
app.get('/api/human-reviews', (req, res) => {
  const reviews = readCSVFile(path.join(PROJECT_ROOT, 'Results', 'human_review.csv'));
  res.json(reviews);
});

app.post('/api/human-reviews', (req, res) => {
  const { case_id, decision, notes, approved_fix, override_tag, override_osi } = req.body;
  if (!case_id) {
    return res.status(400).json({ error: 'case_id is required' });
  }

  const reviewPath = path.join(PROJECT_ROOT, 'Results', 'human_review.csv');
  const reviews = readCSVFile(reviewPath);
  const cases = readCSVFile(path.join(PROJECT_ROOT, 'Dataset', 'cases.csv'));
  const caseObj = cases.find((c) => c.case_id === case_id) || {};

  const existingIdx = reviews.findIndex((r) => r.case_id === case_id);
  const timestamp = new Date().toISOString();

  const newRecord = {
    case_id,
    decision: decision || 'APPROVED',
    risk_level: 'Low',
    ai_concept_tag: caseObj.concept_tag || '',
    human_concept_tag: override_tag || caseObj.concept_tag || '',
    ai_osi_layer: caseObj.osi_layer || 0,
    human_osi_layer: override_osi || caseObj.osi_layer || 0,
    ai_severity: caseObj.severity || '',
    human_severity: caseObj.severity || '',
    ai_confidence: 'high',
    agreed_concept: true,
    agreed_osi: true,
    agreed_severity: true,
    ai_fix: approved_fix || caseObj.expected_fix || '',
    approved_fix: approved_fix || caseObj.expected_fix || '',
    reviewer_notes: notes || 'Reviewed via Web Dashboard.',
    reviewer_id: 'WebDashboard-NetEng',
    timestamp,
  };

  if (existingIdx >= 0) {
    reviews[existingIdx] = { ...reviews[existingIdx], ...newRecord };
  } else {
    reviews.push(newRecord);
  }

  writeCSVFile(reviewPath, reviews);
  res.json({ success: true, record: newRecord });
});

// 5. Responsible AI Telemetry
app.get('/api/responsible-ai', (req, res) => {
  const jsonlPath = path.join(PROJECT_ROOT, 'Results', 'responsible_ai_log.jsonl');
  const events = [];

  if (fs.existsSync(jsonlPath)) {
    const lines = fs.readFileSync(jsonlPath, 'utf-8').split('\n');
    for (const l of lines) {
      if (l.trim()) {
        try {
          events.push(JSON.parse(l));
        } catch (e) {}
      }
    }
  }

  const uncertainCases = ['C005', 'C023', 'C030'];
  const uncertainEvents = events.filter((e) => e.is_uncertain_case);
  const hedgedCorrectly = uncertainEvents.filter((e) => e.confidence_appropriate).length;
  const hedgingRate = uncertainEvents.length
    ? ((hedgedCorrectly / uncertainEvents.length) * 100).toFixed(1)
    : '100.0';

  const highRisks = events.filter((e) => e.safety_risk_level === 'High').length;
  const medRisks = events.filter((e) => e.safety_risk_level === 'Medium').length;

  res.json({
    totalEvents: events.length,
    uncertainCasesCount: uncertainEvents.length,
    hedgingRate,
    highRisks,
    medRisks,
    events: events.slice(-20).reverse(), // Last 20 events
  });
});

app.listen(PORT, () => {
  console.log(`[✓] NetSage AI Dashboard API running on http://localhost:${PORT}`);
});
