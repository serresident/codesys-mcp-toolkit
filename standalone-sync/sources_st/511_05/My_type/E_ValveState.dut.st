// @OBJECT_ID: ccedf3a1-333e-4438-9377-f198f9544b07
// @DECLARATION
{attribute 'qualified_only'}
{attribute 'strict'}
TYPE E_ValveState :
(
    INIT    := 0,   // Инициализация указателей
    IDLE    := 1,   // Ожидание выбора режима
    AUTO    := 2,   // Автоматическое управление
    MANUAL  := 3,   // Ручное управление (HMI)
    FAULT   := 99   // Состояние ошибки (например, Null Pointer)
);
END_TYPE