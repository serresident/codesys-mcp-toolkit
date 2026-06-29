// @OBJECT_ID: d2828cf0-a55e-4108-8a78-43bc321d9b6a
// @DECLARATION
FUNCTION_BLOCK FB_InfluxBuffer
VAR_INPUT
    sMeasurement : STRING(80);   // Measurement name (e.g., 'CEX6')
    sTagKey      : STRING(40);   // Tag name (e.g., 'title')
    sTagValue    : STRING(80);   // Tag value (e.g., 'kolonna_23b')
END_VAR

VAR_OUTPUT
    sBuffer      : STRING(5000); // Resulting string for fbSender
END_VAR

VAR
    iCurrentLen  : INT;          // Current length of sBuffer
END_VAR









// @IMPLEMENTATION
// Initialization: Clear buffer and add Measurement + Tag
// Format: "Measurement,TagKey=TagValue " (note the space at the end)
sBuffer := CONCAT(sMeasurement, ',');
sBuffer := CONCAT(sBuffer, sTagKey);
sBuffer := CONCAT(sBuffer, '=');
sBuffer := CONCAT(sBuffer, sTagValue);
sBuffer := CONCAT(sBuffer, ' '); // Line protocol space between tags and fields

iCurrentLen := LEN(sBuffer);