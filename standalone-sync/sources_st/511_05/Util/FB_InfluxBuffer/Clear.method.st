// @OBJECT_ID: 5ef3d038-d9c2-4048-9196-bfdb9bff4938
// @DECLARATION
METHOD Clear : BOOL
VAR_INPUT
END_VAR









// @IMPLEMENTATION
// Очистка буфера для нового измерения
sBuffer := CONCAT(sMeasurement, ',');
sBuffer := CONCAT(sBuffer, sTagKey);
sBuffer := CONCAT(sBuffer, '=');
sBuffer := CONCAT(sBuffer, sTagValue);
sBuffer := CONCAT(sBuffer, ' ');

iCurrentLen := LEN(sBuffer);
Clear := TRUE;