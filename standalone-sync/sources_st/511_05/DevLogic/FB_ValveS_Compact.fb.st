// @OBJECT_ID: fa77258a-480d-4f24-958d-df1ed5a50eb2
// @DECLARATION
FUNCTION_BLOCK FB_ValveS_Compact
VAR_INPUT
    xMode        : BOOL; 
    xManControl  : BOOL; 
    xAutoControl : BOOL; 
END_VAR

VAR_OUTPUT
    xOutControl  : BOOL; 
END_VAR












// @IMPLEMENTATION
// Компактная реализация в одну строку с помощью SEL
xOutControl := SEL(xMode, xManControl, xAutoControl);