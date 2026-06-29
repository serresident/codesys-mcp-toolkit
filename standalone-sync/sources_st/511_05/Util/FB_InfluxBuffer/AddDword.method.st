// @OBJECT_ID: a5b3bcec-b63f-42e1-9ad1-aa88a7512f3d
// @DECLARATION
METHOD PUBLIC AddDWord : BOOL
VAR_INPUT
    sName : STRING(40);
    dwVal : DWORD;
END_VAR
VAR
    sFragment : STRING(100);
    sTemp     : STRING(20);
END_VAR









// @IMPLEMENTATION

// Add comma if not the first field
IF iCurrentLen > (LEN(sMeasurement) + LEN(sTagKey) + LEN(sTagValue) + 3) THEN
    sFragment := ',';
ELSE
    sFragment := '';
END_IF

// Format: Key=Value (DWORD преобразуется в UDINT для строки)
sFragment := CONCAT(sFragment, sName);
sFragment := CONCAT(sFragment, '=');

// Convert DWORD to string
sTemp := DWORD_TO_STRING(dwVal);
sFragment := CONCAT(sFragment, sTemp);

// Append to buffer
STU.StrConcatA(ADR(sFragment), ADR(sBuffer), SIZEOF(sBuffer));
iCurrentLen := LEN(sBuffer);
AddDWord := TRUE;