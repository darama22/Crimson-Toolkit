# 🦎 C2-CHAMELEON
**Adaptive Command & Control Framework**

## 📖 Description

C2-CHAMELEON is a next-generation C2 server that disguises malicious traffic as legitimate protocols. AI-driven channel selection automatically switches between DNS tunneling, HTTPS, and WebSockets based on network monitoring detection.

## ✨ Features

- 🎭 **Protocol Shapeshifting** - DNS, HTTPS, WebSocket channels
- 🤖 **AI Channel Selection** - Automatic evasion logic
- 📡 **Multi-Agent Management** - Control hundreds of implants
- 🔐 **Encrypted Communications** - mTLS + AES-256
- 📊 **TUI Dashboard** - Real-time agent monitoring

## 🚀 Usage

```bash
# Start C2 server
./c2-server --listen 0.0.0.0:8443 --protocol https

# Generate agent
./c2-agent-builder --server c2.example.com --protocol dns

# Connect to dashboard
./c2-client --server localhost:8443
```

## 🛠️ Tech Stack

- **Go** - Server (high concurrency)
- **Rust** - Agent (small binary size)
- **gRPC** - Inter-service communication
- **DNS-over-HTTPS** - Covert channel

## ⚖️ Legal Notice

**Authorized Red Team operations only.** Unauthorized C2 deployment is illegal.

## 📝 Status

⏳ **Planned** - Most complex component, final implementation
