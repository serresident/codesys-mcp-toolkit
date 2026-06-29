// @OBJECT_ID: 2515430e-378e-4b6e-88dc-ad2a64e06f23
// @DECLARATION
TYPE E_AO_State :
(
    INIT    := 0,       // Проверка готовности указателей
    IDLE    := 1,       // Ожидание и циклическое обновление
    ERROR   := 99       // Ошибка адресации или данных
) INT;
END_TYPE