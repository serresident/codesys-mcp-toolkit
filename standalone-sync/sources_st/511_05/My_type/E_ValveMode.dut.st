// @OBJECT_ID: 49d09f1c-415d-484a-a4ec-69eeeb5b62bd
// @DECLARATION
{attribute 'qualified_only'}
{attribute 'strict'}
TYPE E_ValveMode :
(
    INIT := 0,
    AUTO := 1,
    MANUAL := 2,
    ERROR := 99
) INT; // Указываем базовый тип для совместимости
END_TYPE