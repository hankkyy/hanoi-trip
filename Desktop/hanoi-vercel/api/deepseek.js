// ═══════════════════════════════════════════════
// Vercel API: /api/deepseek
//   代理 DeepSeek API 调用，解决微信小程序 wx.request
//   长连接易被中断的问题。Vercel 服务端超时 60s，
//   足够承载 10-20s 的 AI 响应。
// ═══════════════════════════════════════════════

// Vercel 环境变量中配置 DEEPSEEK_API_KEY
const DEEPSEEK_API_KEY = process.env.DEEPSEEK_API_KEY || '';
const DEEPSEEK_API_URL = 'https://api.deepseek.com/v1/chat/completions';

export default async function handler(req, res) {
  // CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { systemPrompt, userContent, apiKey } = req.body || {};

  if (!userContent) {
    return res.status(400).json({ success: false, error: '缺少内容' });
  }

  // 优先用服务器环境变量，其次用客户端传入的 key
  const key = DEEPSEEK_API_KEY || apiKey || '';

  if (!key) {
    return res.status(400).json({ success: false, error: 'API Key 未配置' });
  }

  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 55000); // 55s，留 5s 余量

    const response = await fetch(DEEPSEEK_API_URL, {
      method: 'POST',
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${key}`
      },
      body: JSON.stringify({
        model: 'deepseek-chat',
        messages: [
          { role: 'system', content: systemPrompt || '你是一个专业的旅行攻略解析助手。' },
          { role: 'user', content: userContent }
        ],
        temperature: 0.3,
        max_tokens: 4096,
        response_format: { type: 'json_object' }
      })
    });

    clearTimeout(timeout);

    if (!response.ok) {
      const errText = await response.text();
      console.error('DeepSeek API error:', response.status, errText);
      return res.status(200).json({
        success: false,
        error: `DeepSeek API 错误 (${response.status})`
      });
    }

    const data = await response.json();

    if (data.error) {
      return res.status(200).json({
        success: false,
        error: `DeepSeek: ${data.error.message || '未知错误'}`
      });
    }

    const content = data.choices[0].message.content;

    // 尝试解析 JSON（处理可能的 markdown 包裹）
    let parsed;
    try {
      parsed = JSON.parse(content);
    } catch (e) {
      const match = content.match(/```(?:json)?\s*([\s\S]*?)```/);
      if (match) {
        parsed = JSON.parse(match[1].trim());
      } else {
        const objMatch = content.match(/\{[\s\S]*\}/);
        if (objMatch) {
          parsed = JSON.parse(objMatch[0]);
        } else {
          return res.status(200).json({ success: false, error: 'AI 返回格式异常' });
        }
      }
    }

    return res.status(200).json({ success: true, data: parsed });

  } catch (err) {
    console.error('deepseek proxy error:', err.message);
    return res.status(200).json({
      success: false,
      error: err.name === 'AbortError' ? 'AI 请求超时，请重试' : '代理请求失败: ' + err.message
    });
  }
}
