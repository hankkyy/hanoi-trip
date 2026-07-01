const http = require('http');
const cloudbase = require('@cloudbase/node-sdk');

const app = cloudbase.init({
  env: 'hanoi-d4gj8vd2q1e7a3dc0',
  region: 'ap-shanghai'
});

const db = app.database();

const PORT = process.env.PORT || 9000;

function json(res, data, statusCode = 200) {
  res.writeHead(statusCode, {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type'
  });
  res.end(JSON.stringify(data));
}

const server = http.createServer(async (req, res) => {
  // CORS preflight
  if (req.method === 'OPTIONS') {
    res.writeHead(204, {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
      'Access-Control-Max-Age': '86400'
    });
    res.end();
    return;
  }

  const url = new URL(req.url, `http://${req.headers.host}`);
  const route = url.pathname;

  try {
    // GET /itinerary
    if (route === '/itinerary' && req.method === 'GET') {
      const result = await db.collection('itinerary')
        .orderBy('day', 'asc')
        .orderBy('sortOrder', 'asc')
        .limit(100)
        .get();
      return json(res, { success: true, data: result.data });
    }

    // GET /checklist
    if (route === '/checklist' && req.method === 'GET') {
      const result = await db.collection('checklist')
        .orderBy('id', 'asc')
        .limit(20)
        .get();
      return json(res, { success: true, data: result.data });
    }

    // POST /checklist/:docId
    const match = route.match(/^\/checklist\/(.+)$/);
    if (match && req.method === 'POST') {
      const docId = match[1];
      let body = '';
      req.on('data', chunk => body += chunk);
      await new Promise(resolve => req.on('end', resolve));
      const { done } = JSON.parse(body);
      const result = await db.collection('checklist').doc(docId).update({ done });
      return json(res, { success: true, updated: result.updated });
    }

    // GET /bucket-list
    if (route === '/bucket-list' && req.method === 'GET') {
      const result = await db.collection('bucket_list')
        .orderBy('sort', 'asc')
        .limit(100)
        .get();
      return json(res, { success: true, data: result.data });
    }

    // POST /bucket-list/:docId
    const blMatch = route.match(/^\/bucket-list\/(.+)$/);
    if (blMatch && req.method === 'POST') {
      const docId = blMatch[1];
      let body = '';
      req.on('data', chunk => body += chunk);
      await new Promise(resolve => req.on('end', resolve));
      const { done } = JSON.parse(body);
      const result = await db.collection('bucket_list').doc(docId).update({ done });
      return json(res, { success: true, updated: result.updated });
    }

    // GET /expenses
    if (route === '/expenses' && req.method === 'GET') {
      const result = await db.collection('expenses')
        .orderBy('createdAt', 'asc')
        .limit(200)
        .get();
      return json(res, { success: true, data: result.data });
    }

    // POST /expenses (batch save: replace all)
    if (route === '/expenses' && req.method === 'POST') {
      let body = '';
      req.on('data', chunk => body += chunk);
      await new Promise(resolve => req.on('end', resolve));
      const { items } = JSON.parse(body || '{}');

      // Remove all existing
      const existing = await db.collection('expenses').get();
      const removeTasks = existing.data.map(doc =>
        db.collection('expenses').doc(doc._id).remove()
      );
      await Promise.all(removeTasks);

      // Insert new ones
      if (items && items.length > 0) {
        const addTasks = items.map(item =>
          db.collection('expenses').add({ ...item, createdAt: Date.now() })
        );
        await Promise.all(addTasks);
      }

      return json(res, { success: true, count: items ? items.length : 0 });
    }

    // 404
    json(res, { success: false, error: 'Not found' }, 404);

  } catch (err) {
    json(res, { success: false, error: err.message }, 500);
  }
});

server.listen(PORT, () => {
  console.log(`API server running on port ${PORT}`);
});
