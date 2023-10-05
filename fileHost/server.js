const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const multer = require('multer');  // Add multer

const app = express();

const BACKUP_DIR = './backups/';
const TARGET_FILE = './target.csv';

// Middleware
app.use(cors());
app.use(bodyParser.json());

const storage = multer.memoryStorage();  // Store the file data in memory
const upload = multer({ storage: storage });



function renameAndBackup() {
    if (fs.existsSync(TARGET_FILE)) {
        const dateStr = new Date().toISOString().replace(/[:.]/g, "-");
        const backupName = `backup-${dateStr}.csv`;

        fs.renameSync(TARGET_FILE, path.join(BACKUP_DIR, backupName));

        // Check and delete backups if there are more than five
        const backups = fs.readdirSync(BACKUP_DIR).sort((a, b) => {
            return fs.statSync(path.join(BACKUP_DIR, b)).mtime - fs.statSync(path.join(BACKUP_DIR, a)).mtime;
        });

        while (backups.length > 5) {
            const oldestBackup = backups.pop();
            fs.unlinkSync(path.join(BACKUP_DIR, oldestBackup));
        }
    }
}

app.get('/download', validateToken, (req, res) => {
    const filePath = path.join(__dirname, 'target.csv');

    if (fs.existsSync(filePath)) {
        res.sendFile(filePath);
    } else {
        res.status(404).send('File not found');
    }
});

function validateToken(req, res, next) {
    const authHeader = req.headers['authorization'];

    if (!authHeader || authHeader !== "Bearer 76cdc8491313c226dd2ffac76e1b544d") {
        return res.status(403).json({ error: "Invalid token" });
    }
    
    next(); // Move on to the actual route handler if the token is valid
}

// Handle new CSV uploads
app.post('/upload', upload.single('file'), (req, res) => {
    if (!req.file || !req.file.buffer) {
        console.log("DEBUG: No file buffer found in request.", req.file);
        return res.status(400).json({ error: 'No file uploaded' });
    }

    const fileData = req.file.buffer.toString();

    renameAndBackup();

    fs.writeFileSync(TARGET_FILE, fileData);
    res.status(200).json({ success: true });
});


app.listen(3000, () => {
    console.log('Server started on port 3000');
});
