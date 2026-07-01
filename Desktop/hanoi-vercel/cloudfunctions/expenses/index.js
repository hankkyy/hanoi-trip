const http = require('http');
const cloudbase = require('@cloudbase/node-sdk');

const app = cloudbase.init({ env: 'hanoi-d4gj8vd2q1e7a3dc0' });
const db = app.database();
const COLLECTION = 'expenses';

function readBody(req) {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => resolve(body));
    req.on('error', reject);
  });
}

function send(res, code, data) {
  res.writeHead(code, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify(data));
}

const server = http.createServer(async (req, res) => {
  // CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  const url = new URL(req.url, `http://${req.headers.host}`);
  const path = url.pathname;

  try {
    // GET / — list all expenses
    if (req.method === 'GET' && (path === '/' || path === '')) {
      const result = await db.collection(COLLECTION).orderBy('createdAt', 'asc').get();
      return send(res, 200, { success: true, data: result.data });
    }

    // POST / — batch save (replace all)
    if (req.method === 'POST' && (path === '/' || path === '')) {
      const body = await readBody(req);
      const { items } = JSON.parse(body || '{}');

      // Remove all existing
      const existing = await db.collection(COLLECTION).get();
      for (const doc of existing.data) {
        await db.collection(COLLECTION).doc(doc._id).remove();
      }

      // Insert new ones
      if (items && items.length > 0) {
        for (const item of items) {
          await db.collection(COLLECTION).add({
            ...item,
            createdAt: Date.now()
          });
        }
      }

      return send(res, 200, { success: true, count: items ? items.length : 0 });
    }

    // 404
    return send(res, 404, { success: false, error: 'Not found' });

  } catch (e) {
    console.error('Expenses API error:', e);
    return send(res, 500, { success: false, error: e.message });
  }
});

server.listen(9000, () => {
  console.log('Expenses API listening on port 9000');
});
