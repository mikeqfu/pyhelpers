'Adapted from the answers and comments at https://stackoverflow.com/questions/1858195/

if WScript.Arguments.Count < 3 Then
    WScript.Echo "Usage: xlsx2csv.vbs <xlsx/xls pathname> <csv pathname> <worksheet number (starting from 1)>"
    Wscript.Quit
End If

csv_format = 6

Set objFSO = CreateObject("Scripting.FileSystemObject")

src_file = objFSO.GetAbsolutePathName(Wscript.Arguments.Item(0))
dest_file = objFSO.GetAbsolutePathName(WScript.Arguments.Item(1))
worksheet_number = CInt(WScript.Arguments.Item(2))

Dim oExcel
Set oExcel = CreateObject("Excel.Application")

Dim oBook
Set oBook = oExcel.Workbooks.Open(src_file)
oBook.Worksheets(worksheet_number).Activate

oBook.SaveAs dest_file, csv_format

oBook.Close False
oExcel.Quit