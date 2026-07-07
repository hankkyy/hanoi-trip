// ═══════════════════════════════════════════════
// Vercel API: /api/fetch-url
//   代理抓取 URL 内容，返回纯文本
//   用于 Trippo 小程序的 AI 智能导入
// ═══════════════════════════════════════════════

export default async function handler(req, res) {
  // CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST' && req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const url = req.method === 'POST' ? (req.body?.url || req.query?.url) : req.query?.url;

  if (!url) {
    return res.status(400).json({ error: 'Missing url parameter' });
  }

  // 验证 URL 格式
  try {
    new URL(url);
  } catch (e) {
    return res.status(400).json({ error: 'Invalid URL' });
  }

  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 8000);

    const response = await fetch(url, {
      signal: controller.signal,
      headers: {
        'User-Agent': 'Mozilla/5.0 (compatible; TrippoBot/1.0)',
        'Accept': 'text/html,application/xhtml+xml,text/plain,*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
      },
      redirect: 'follow'
    });

    clearTimeout(timeout);

    const html = await response.text();

    // 清理 HTML → 纯文本
    const text = cleanHtml(html);

    return res.status(200).json({
      success: true,
      text: text,
      length: text.length,
      sourceUrl: url
    });

  } catch (err) {
    console.error('fetch-url error:', err.message);
    return res.status(200).json({
      success: false,
      error: err.name === 'AbortError' ? '抓取超时，请尝试文字模式' : '抓取失败: ' + err.message,
      sourceUrl: url
    });
  }
}

function cleanHtml(html) {
  if (!html) return '';

  return html
    .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '')
    .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '')
    .replace(/<noscript[^>]*>[\s\S]*?<\/noscript>/gi, '')
    .replace(/<head[^>]*>[\s\S]*?<\/head>/gi, '')
    .replace(/<header[^>]*>[\s\S]*?<\/header>/gi, '')
    .replace(/<footer[^>]*>[\s\S]*?<\/footer>/gi, '')
    .replace(/<nav[^>]*>[\s\S]*?<\/nav>/gi, '')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#x27;/g, "'")
    .replace(/&#(\d+);/g, '')
    .replace(/&[a-z]+;/gi, '')
    .replace(/\s+/g, ' ')
    .trim()
    .substring(0, 30000);
}
