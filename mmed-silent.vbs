' ============================================================
' M-MED avtoyuklash
' Uvicorn va ngrok endi Windows xizmati (NSSM) sifatida ishlaydi
' Bu skript faqat auto-deploy va scheduler ni ishga tushiradi
' ============================================================
Set WshShell = CreateObject("WScript.Shell")

' Xizmatlar ishga tushishini kutamiz (ngrok URL hosil bo'lishi uchun)
WScript.Sleep 20000

' Saytni yangilash (ngrok URL ni yozish)
WshShell.Run "cmd /c cd C:\mmed-api && python auto-deploy.py", 0, True

' Telegram kunlik hisobot planировщиki
WshShell.Run "cmd /k cd C:\mmed-api && python scheduler.py", 0, False
