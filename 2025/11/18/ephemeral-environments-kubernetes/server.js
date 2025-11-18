const http = require('http');

const PORT = process.env.PORT || 8080;
const ENV = process.env.ENV || 'unknown';
const PR_NUMBER = process.env.PR_NUMBER || 'N/A';

const server = http.createServer((req, res) => {
  if (req.url === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'healthy' }));
    return;
  }

  if (req.url === '/ready') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ready' }));
    return;
  }

  if (req.url === '/') {
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>PR Environment - ${PR_NUMBER}</title>
        <style>
          body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
          }
          .container {
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
          }
          h1 {
            color: #333;
            margin-top: 0;
          }
          .info {
            background: #f0f0f0;
            padding: 15px;
            border-radius: 4px;
            margin: 20px 0;
          }
          .info-item {
            margin: 10px 0;
          }
          .label {
            font-weight: bold;
            color: #666;
          }
          .value {
            color: #333;
            font-family: monospace;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <h1>🚀 Ephemeral PR Environment</h1>
          <div class="info">
            <div class="info-item">
              <span class="label">PR Number:</span>
              <span class="value">${PR_NUMBER}</span>
            </div>
            <div class="info-item">
              <span class="label">Environment:</span>
              <span class="value">${ENV}</span>
            </div>
            <div class="info-item">
              <span class="label">Status:</span>
              <span class="value">Running</span>
            </div>
          </div>
          <p>This is an ephemeral environment created for PR #${PR_NUMBER}.</p>
          <p>It will be automatically deleted when the PR is closed or merged.</p>
        </div>
      </body>
      </html>
    `);
    return;
  }

  res.writeHead(404, { 'Content-Type': 'text/plain' });
  res.end('Not Found');
});

server.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
  console.log(`Environment: ${ENV}`);
  console.log(`PR Number: ${PR_NUMBER}`);
});

