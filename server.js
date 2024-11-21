const express = require('express');
const path = require('path');
const app = express();

// Serve static files from the Next.js app
app.use('/_next', express.static(path.join(__dirname, 'frontend/.next')));
app.use(express.static(path.join(__dirname, 'frontend/public')));

// Handle all requests
app.get('*', (req, res) => {
    const nextPath = path.join(__dirname, 'frontend/.next/server/pages');
    
    // Try to serve the specific page, fallback to index
    const pagePath = path.join(nextPath, `${req.path}.html`);
    const indexPath = path.join(nextPath, 'index.html');
    
    if (require('fs').existsSync(pagePath)) {
        res.sendFile(pagePath);
    } else {
        res.sendFile(indexPath);
    }
});

const port = process.env.PORT || 3000;
app.listen(port, () => console.log(`Server running on port ${port}`));