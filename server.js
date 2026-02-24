const express = require('express');
const path = require('path');
const fs = require('fs');
const app = express();

const PORT = process.env.PORT || 8080;

// Serve static files
app.use(express.static(__dirname));

// Root path serves index.html
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

// Special endpoint for /install
app.get('/install', (req, res) => {
    res.sendFile(path.join(__dirname, 'install'));
});

// Fallback for any HTML files
app.get('/:file.html', (req, res) => {
    const filePath = path.join(__dirname, req.params.file + '.html');
    if (fs.existsSync(filePath)) {
        res.sendFile(filePath);
    } else {
        res.status(404).send('Not found');
    }
});

app.listen(PORT, () => {
    console.log(`EMInstaller running on port ${PORT}`);
});
