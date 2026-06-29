// @OBJECT_ID: 0f7dc9ff-fcad-4997-a2b3-68e2ac3befdf
// @DECLARATION
METHOD PUBLIC AddReal : BOOL
VAR_INPUT
    sName : STRING(40);
    rVal  : REAL;
END_VAR
VAR
    sFragment : STRING(100);
END_VAR









// @IMPLEMENTATION

// Add comma if not the first field
IF iCurrentLen > (LEN(sMeasurement) + LEN(sTagKey) + LEN(sTagValue) + 3) THEN
    sFragment := ',';
ELSE
    sFragment := '';
END_IF

// Format: Key=Value
sFragment := CONCAT(sFragment, sName);
sFragment := CONCAT(sFragment, '=');
sFragment := CONCAT(sFragment, REAL_TO_STRING(rVal));

// Append to buffer using STU for safety or simple CONCAT
STU.StrConcatA(ADR(sFragment), ADR(sBuffer), SIZEOF(sBuffer));
iCurrentLen := LEN(sBuffer);
AddReal := TRUE;