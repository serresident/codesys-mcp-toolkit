// @OBJECT_ID: 7d4ed387-9382-45d7-b1fe-40ec3c2ade09
// @DECLARATION
PROGRAM InfluxUdpSender
VAR
		fbSender: FB_InfluxUdpSender;
	fbBuf    : FB_InfluxBuffer;
	sendData : STRING(5000); // Data to send
	sIP : STRING :='192.168.150.133'; // InfluxIP
    uiPort : UINT := 8089; // Influx port
	sParam:STRING(200);
END_VAR








// @IMPLEMENTATION
		sendData := 'CEX15,title=aliy2s_app511_abak_101_172 ';

// Initialization (Measurement mariyu Tag set cheyadam)
// =============================================================
fbBuf(sMeasurement:= 'CEX15', sTagKey:= 'title', sTagValue:= 'aliy2s_app511_abak_101_172');

fbBuf.AddReal('rPosValveDiazo',   GVL.gInputRegs.rPosValveDiazo);
fbBuf.AddReal('rPosValveSoda',   GVL.gInputRegs.rPosValveSoda);
fbBuf.AddReal('rPosValveSteam',   GVL.gInputRegs.rPosValveSteam);

fbBuf.AddReal('rPhApp511',   GVL.gInputRegs.rPhApp511);

fbBuf.AddReal('rTempApp511',   GVL.gInputRegs.rTempApp511);

fbBuf.AddReal('WE_1_app_511',   GVL.gInputRegs.WE_1);

fbBuf.AddReal('WE_2_app_511',   GVL.gInputRegs.WE_2);


fbBuf.AddReal('TotalWater_511',   GVL.gInputRegs.IR_TotalWater);

fbBuf.AddReal('TotalSoda_511',   GVL.gInputRegs.IR_TotalSoda);


fbBuf.AddReal('FlowSoda_511',   GVL.gInputRegs.IR_FlowSoda);

fbBuf.AddReal('FlowWater_511',   GVL.gInputRegs.IR_FlowWater);
// Send Data

// =============================================================
fbSender(sSendData:= fbBuf.sBuffer, sIPInflux:= sIP, uiPortInflux:= uiPort);