from ...core.parser import parse_product
from ...core.matcher import compare_products
tracked=parse_product("ToolPRO Auto Diagnostic Scanner OBD2 and CAN")
cases=[
("ToolPRO Auto Diagnostic Scanner OBD2 and CAN","EXACT"),
("Kincrome Automotive Diagnostic Code Reader","POSSIBLE"),
("Foxwell ET2707 OBDII Diagnostic Scanner","POSSIBLE"),
("ToolPRO Auto Diagnostic Scanner","POSSIBLE"),
("Foxwell Advanced OBDII Code Reader ET3010","POSSIBLE"),
("Kincrome Auto Diagnostic Scanner OBD2 and CAN","POSSIBLE"),
("Gator Dash Cam Hard Wire Kit OBD2","REJECT"),
("Aerpro Universal OBD2 Port Lock - AOBDLK","REJECT"),
("Thinkware OBD-II Plug & Play Power Harness For Thinkware Dash Cams - OBDTH01E","REJECT"),
("Foxwell OBD to BMW 20 Pin Connector - ET8000-01","REJECT"),
]
passed=0
for title,want in cases:
    got=compare_products(tracked,parse_product(title)).classification
    print(("PASS" if got==want else "FAIL"),want,got,title)
    passed += got==want
print(f"DIAGNOSTIC SCANNER MATCHING: {passed}/{len(cases)} passed")
raise SystemExit(0 if passed==len(cases) else 1)
