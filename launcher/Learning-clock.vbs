' =============================================================================
' File Name : Learning-clock.vbs
' Artifact  : LearningClock - Silent Launcher
' Author    : javaboy-vk
' Date      : 2026-06-05
' Version   : v3.1
' Purpose:
'   Starts the Learning Clock app without a visible CLI window.
'   Accepts one argument: path to a .properties file.
' Change Log:
'   v3.1 - Add optional launchPython property so VBS-only debugging can stop
'          before starting the Python process.
'   v3.0 - Add optional windowStyle and waitForExit properties so debug
'          launcher output can be shown when troubleshooting breakpoints.
'   v2.9 - Add optional pythonArgs property so debug launchers can start
'          Python through debugpy while normal launch remains silent.
'   v2.8 - Load learning path, Python executable, script path, and log directory
'          from a properties file passed as the only launcher argument.
' =============================================================================

Option Explicit

Dim shell, fso
Dim propertiesPath, propertiesFolder, properties
Dim learningPathName, pythonExe, pythonArgs, pyScriptPath, logDir, windowStyle, waitForExit
Dim launchPython
Dim cmd

Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

If WScript.Arguments.Count <> 1 Then
    MsgBox "Usage:" & vbCrLf & _
        "wscript.exe //nologo Learning-clock.vbs path\to\dev.properties", _
        vbCritical, "Learning Clock"
    WScript.Quit 1
End If

propertiesPath = ResolveArgumentPath(WScript.Arguments(0))

If Not fso.FileExists(propertiesPath) Then
    MsgBox "Properties file was not found:" & vbCrLf & propertiesPath, _
        vbCritical, "Learning Clock"
    WScript.Quit 1
End If

propertiesFolder = fso.GetParentFolderName(propertiesPath)
Set properties = LoadProperties(propertiesPath)

learningPathName = RequiredProperty(properties, "learning-path-name", propertiesPath)
pythonExe = ResolveConfigPath(RequiredProperty(properties, "pythonExe", propertiesPath), propertiesFolder)
pythonArgs = OptionalProperty(properties, "pythonArgs")
pyScriptPath = ResolveConfigPath(RequiredProperty(properties, "pyScriptPath", propertiesPath), propertiesFolder)
logDir = ResolveConfigPath(RequiredProperty(properties, "logDir", propertiesPath), propertiesFolder)
windowStyle = OptionalIntegerProperty(properties, "windowStyle", 0)
waitForExit = OptionalBooleanProperty(properties, "waitForExit", False)
launchPython = OptionalBooleanProperty(properties, "launchPython", True)

If Not fso.FileExists(pythonExe) Then
    MsgBox "Python executable was not found:" & vbCrLf & pythonExe, _
        vbCritical, "Learning Clock"
    WScript.Quit 1
End If

If Not fso.FileExists(pyScriptPath) Then
    MsgBox "Learning Clock Python script was not found:" & vbCrLf & pyScriptPath, _
        vbCritical, "Learning Clock"
    WScript.Quit 1
End If

If Not fso.FolderExists(logDir) Then
    EnsureFolder logDir
End If

shell.CurrentDirectory = propertiesFolder
cmd = Quote(pythonExe)
If Len(pythonArgs) > 0 Then
    cmd = cmd & " " & pythonArgs
End If
cmd = cmd & " " & Quote(pyScriptPath) & _
    " --learning-path " & Quote(learningPathName) & _
    " --log-dir " & Quote(logDir)

If Not launchPython Then
    WScript.Echo "VBS debug mode: Python launch skipped."
    WScript.Echo cmd
    WScript.Quit 0
End If

shell.Run cmd, windowStyle, waitForExit

Function LoadProperties(path)
    Dim result, stream, line, trimmed, separatorIndex, key, value
    Set result = CreateObject("Scripting.Dictionary")
    result.CompareMode = 1

    Set stream = fso.OpenTextFile(path, 1, False)
    Do Until stream.AtEndOfStream
        line = stream.ReadLine
        trimmed = Trim(line)

        If Len(trimmed) > 0 Then
            If Left(trimmed, 1) <> "#" And Left(trimmed, 1) <> ";" Then
                separatorIndex = InStr(trimmed, "=")
                If separatorIndex > 1 Then
                    key = Trim(Left(trimmed, separatorIndex - 1))
                    value = Trim(Mid(trimmed, separatorIndex + 1))
                    result(key) = Unquote(value)
                End If
            End If
        End If
    Loop
    stream.Close

    Set LoadProperties = result
End Function

Function RequiredProperty(propertiesDictionary, key, sourcePath)
    If Not propertiesDictionary.Exists(key) Then
        MsgBox "Required property is missing from:" & vbCrLf & sourcePath & vbCrLf & vbCrLf & key, _
            vbCritical, "Learning Clock"
        WScript.Quit 1
    End If

    RequiredProperty = Trim(propertiesDictionary(key))
    If Len(RequiredProperty) = 0 Then
        MsgBox "Required property is empty in:" & vbCrLf & sourcePath & vbCrLf & vbCrLf & key, _
            vbCritical, "Learning Clock"
        WScript.Quit 1
    End If
End Function

Function OptionalProperty(propertiesDictionary, key)
    OptionalProperty = ""
    If propertiesDictionary.Exists(key) Then
        OptionalProperty = Trim(propertiesDictionary(key))
    End If
End Function

Function OptionalIntegerProperty(propertiesDictionary, key, defaultValue)
    OptionalIntegerProperty = defaultValue
    If propertiesDictionary.Exists(key) Then
        If IsNumeric(Trim(propertiesDictionary(key))) Then
            OptionalIntegerProperty = CInt(Trim(propertiesDictionary(key)))
        End If
    End If
End Function

Function OptionalBooleanProperty(propertiesDictionary, key, defaultValue)
    Dim rawValue
    OptionalBooleanProperty = defaultValue
    If propertiesDictionary.Exists(key) Then
        rawValue = LCase(Trim(propertiesDictionary(key)))
        OptionalBooleanProperty = rawValue = "true" Or rawValue = "1" Or rawValue = "yes"
    End If
End Function

Function ResolveArgumentPath(path)
    If IsAbsolutePath(path) Then
        ResolveArgumentPath = fso.GetAbsolutePathName(path)
    Else
        ResolveArgumentPath = fso.GetAbsolutePathName( _
            fso.BuildPath(fso.GetParentFolderName(WScript.ScriptFullName), path))
    End If
End Function

Function ResolveConfigPath(path, baseFolder)
    If IsAbsolutePath(path) Then
        ResolveConfigPath = fso.GetAbsolutePathName(path)
    Else
        ResolveConfigPath = fso.GetAbsolutePathName(fso.BuildPath(baseFolder, path))
    End If
End Function

Function IsAbsolutePath(path)
    IsAbsolutePath = False
    If Len(path) >= 3 Then
        If Mid(path, 2, 1) = ":" Then
            IsAbsolutePath = True
        End If
    End If
    If Left(path, 2) = "\\" Then
        IsAbsolutePath = True
    End If
End Function

Sub EnsureFolder(path)
    Dim parentFolder
    If fso.FolderExists(path) Then
        Exit Sub
    End If

    parentFolder = fso.GetParentFolderName(path)
    If Len(parentFolder) > 0 Then
        EnsureFolder parentFolder
    End If

    If Not fso.FolderExists(path) Then
        fso.CreateFolder(path)
    End If
End Sub

Function Quote(value)
    Quote = """" & value & """"
End Function

Function Unquote(value)
    Dim result
    result = Trim(value)
    If Len(result) >= 2 Then
        If Left(result, 1) = """" And Right(result, 1) = """" Then
            result = Mid(result, 2, Len(result) - 2)
        End If
    End If
    Unquote = result
End Function
