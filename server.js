const express = require('express');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 3000;
// Allow overriding the target user via environment variable
const USER = process.env.TARGET_USER || 'j.p_morgan_trading';
const POSTS_FILE = path.join(__dirname, `${USER}_threads.json`);

// Serve static files from the frontend directory
app.use(express.static(path.join(__dirname, 'frontend')));

app.get('/api/posts', (req, res) => {
  fs.readFile(POSTS_FILE, 'utf8', (err, data) => {
    if (err) {
      if (err.code === 'ENOENT') {
        return res.json([]); // No posts yet
      }
      console.error('Error reading posts:', err);
      return res.status(500).json({ error: 'Failed to load posts' });
    }
    try {
      const posts = JSON.parse(data);
      res.json(posts);
    } catch (e) {
      console.error('Error parsing posts:', e);
      res.status(500).json({ error: 'Failed to parse posts' });
    }
  });
});

app.listen(PORT, () => {
  console.log(`Server listening on port ${PORT}`);
});
