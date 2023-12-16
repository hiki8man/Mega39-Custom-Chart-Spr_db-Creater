add custom chart spr_db info without edit db file by yourself

孩子做着玩的产物，用来给自制谱快速添加spr_db

spr_db 的文件看着结构有点糟心，老实说我不是很理解为什么Sega要那样子设计记录 spr 和 tex

spr_db 文件结构分析：

小端4字节存储

第一部分：统计项目数量

第二部分：项目开始位置

第三部分：统计定义的info总量

第四部分：info开始位置


项目以16字节为长度

第一部分：id

第二部分：对应字符起始位置

第三部分：对应文件名起始位置

第四部分：索引id

info以12字节为长度

第一部分：id

第二部分：对应字符起始位置

第三部分：索引id（第一二位代表index，第三，四位代表项目索引id，第四位00代表spr部分，10代表tex部分）

所有文字都有00隔开
