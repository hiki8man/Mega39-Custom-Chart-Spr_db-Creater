from pprint import pprint
import hashlib

def get_hash(string):
    obj = hashlib.shake_256()
    obj.update(string.encode("utf-8"))
    result=int(obj.hexdigest(4),16)
    return result

class Manager:
    def __init__(self):
        self.sprinfo_list = list()
        self.spr_list = list()
        self.spr_infoid_dict = {}
        self.pvtmb = None

    def read_db(self,_file_path):
        with open(_file_path,"rb") as f:
            info_len = f.read(16)
            SpriteSetInfo_list = {"len":int.from_bytes(info_len[0:4],"little"),
                                "start":int.from_bytes(info_len[4:8],"little"),
                                }
            Sprites_list = {"len":int.from_bytes(info_len[8:12],"little"),
                            "start":int.from_bytes(info_len[12:16],"little"),
                            }
            for i in range(SpriteSetInfo_list["len"]):
                f.seek(SpriteSetInfo_list["start"] + i * 16)
                self.add_spr(SpriteSetInfo(f.read(16), f))
                if SpriteSetInfo.max_info_id < self.sprinfo_list[-1].info_id:
                    SpriteSetInfo.max_info_id = self.sprinfo_list[-1].info_id

            for i in range(Sprites_list["len"]):
                f.seek(Sprites_list["start"] + i * 12)
                self.add_spr(Sprites(f.read(12),f))
                
    def write_db(self,_file_path):
        len_sprinfo = len(self.sprinfo_list)
        len_spr = len(self.spr_list)
        sprinfo_start = 16
        spr_start = len_sprinfo * 16 + sprinfo_start
        spr_no_data_lenght = 16 - ((len_spr * 12) % 16)
        str_start = spr_start + (len_spr * 12) + spr_no_data_lenght

        with open(_file_path,"wb+") as f:
            #write head info
            f.write(len_sprinfo.to_bytes(4,byteorder="little"))
            f.write(sprinfo_start.to_bytes(4,byteorder="little"))
            f.write(len_spr.to_bytes(4,byteorder="little"))
            f.write(spr_start.to_bytes(4,byteorder="little"))
            for i in self.sprinfo_list:
                #write sprinfo
                #write id
                f.seek(sprinfo_start)
                f.write(i.id.to_bytes(4,byteorder="little"))
                #write str start point
                f.write(str_start.to_bytes(4,byteorder="little"))
                #write file str start point
                file_str_start = len(i.info_str) + str_start + 1
                f.write(file_str_start.to_bytes(4,byteorder="little"))
                #wrile info id
                f.write(i.info_id.to_bytes(4,byteorder="little"))

                sprinfo_start += 16

                #write str
                f.seek(str_start)
                f.write(i.info_str.encode("UTF-8"))
                f.write(b"\x00")
                f.write(i.file_str.encode("UTF-8"))

                str_start = f.tell() + 1

                #write Sprites and Textures
                temp_list = i.Sprites_list + i.Textures_list
                if len(temp_list) > 0:
                    for k in temp_list:
                        f.seek(spr_start)
                        f.write(k.id.to_bytes(4,byteorder="little"))
                        #write str start point
                        f.write(str_start.to_bytes(4,byteorder="little"))
                        #wrile index
                        f.write(k.index.to_bytes(2,byteorder="little"))
                        #wrile info id
                        info_id = k.info_id
                        if not k.is_spr:
                            #\x00\x00 mean spr
                            #\x00\x10 mean tex
                            info_id += 4096
                        f.write(info_id.to_bytes(2,byteorder="little"))

                        spr_start += 12

                        f.seek(str_start)
                        f.write(k.info_str.encode("UTF-8"))

                        str_start = f.tell() + 1
            file_size = f.tell()
            f.write(b"\x00"*(16 - (file_size%16)))

    def add_spr(self,data):
        print(f"add {data.info_str}")
        if type(data) == SpriteSetInfo:
            self.sprinfo_list.append(data)
            self.spr_infoid_dict[self.sprinfo_list[-1].info_id] = self.sprinfo_list[-1]
            if (self.pvtmb == None and self.sprinfo_list[-1].info_str == "SPR_SEL_PVTMB"):
                self.pvtmb = self.sprinfo_list[-1]

        elif type(data) == Sprites:
            self.spr_list.append(data)
            self.spr_infoid_dict[self.spr_list[-1].info_id].add_spr(self.spr_list[-1])

        else:
            raise ValueError("Error Data！",data)
    
    def check_index(self):
        print("----------------")
        check_list = []
        for i in self.sprinfo_list:
            print(f"check {i.info_str} index......",end="")
            check = i.check_index()
            check_list += check
        print("\nDone!")
        if len(check_list) > 0:
            pprint(f"Crash Error Index:\n{check_list}")
        else:
            print("No Crash Error")

    def check_id(self):
        print("----------------")
        print("Check sprinfo id")
        id_list = []
        same_id_list = []
        for i in self.sprinfo_list:
            print(f"\rcheck {i.info_str} id......",end="")
            id_list.append(i.id)
            if id_list.count(i.id) > 1 and same_id_list.count(i.id) == 0:
                same_id_list.append(i.id)
        print("Done!")
        if len(same_id_list) > 0:
            pprint(f"Same ID:\n{same_id_list}")
        else:
            print("No Same ID")
        
        print("----------------")
        print("Check spr id")
        id_list = []
        same_id_list = []
        for i in self.spr_list:
            print(f"\rcheck {i.info_str} id......",end="")
            id_list.append(i.id)
            if id_list.count(i.id) > 1 and same_id_list.count(i.id) == 0:
                same_id_list.append(i.id)
        print("Done!")
        if len(same_id_list) > 0:
            pprint(f"Same ID:\n{same_id_list}")
        else:
            print("No Same ID")
    
class SpriteSetInfo:
    max_info_id = 0
    def __init__(self,data,file = None):
        self.Sprites_list = list()
        self.Textures_list = list()
        if type(data) == type(dict()):
            self.id = data["id"]
            self.info_str = data["info_str"]
            self.file_str = data["file_str"]
            self.info_id = data["info_id"]
        elif file != None:
            self.id = self.to_int(data[:4])
            self.info_str = self.get_str(file, self.to_int(data[4:8]))
            self.file_str = self.get_str(file, self.to_int(data[8:12]))
            self.info_id = self.to_int(data[12:16])
    
    def get_str(self, file, start):
        file.seek(start)
        get_str = ""
        get_char = ""
        while get_char != b"\x00":
            if get_char != "":
                get_str += get_char.decode("utf-8")
            get_char = file.read(1)
        return get_str

    def to_int(self,int_byte):
        return int.from_bytes(int_byte,"little")
    
    def add_spr(self, data):
        if data.is_spr == True:
            self.Sprites_list.append(data)
        else:
            self.Textures_list.append(data)
    
    def check_index(self):
        wrong_list = []
        for i in self.Textures_list:
            if i.index >= len(self.Sprites_list):
                wrong_list.append(i)
        for i in self.Sprites_list:
            if i.index >= len(self.Sprites_list):
                wrong_list.append(i.info_str)
        return wrong_list

class Sprites:
    def __init__(self,data,file = None):
        if type(data) == type(dict()):
            self.id = data["id"]
            self.info_str = data["info_str"]
            self.index = data["index"]
            self.is_spr = data["is_spr"]
            self.info_id = data["info_id"]
        elif file != None:
            self.id = self.to_int(data[:4])
            self.info_str = self.get_str(file, self.to_int(data[4:8]))
            self.index = int.from_bytes(data[8:10],"little")
            self.get_info_id(data[10:12])
    
    def get_str(self, file, start):
        file.seek(start)
        get_str = ""
        get_char = ""
        while get_char != b"\x00":
            if get_char != "":
                get_str += get_char.decode("utf-8")
            get_char = file.read(1)
        return get_str

    def to_int(self,int_byte):
        return int.from_bytes(int_byte,"little")
    
    def get_info_id(self,data):
        check = data[1]
        if check >= 16:
            self.is_spr = False
            check -= 16
        else:
            self.is_spr = True
        self.info_id = data[0] + (check * 256)

class add_new_custom_chart_spr_db:
    def __init__(self, _pv_id_list,_Manager):
        self.Manager = _Manager
        for pv_id in _pv_id_list:
            self.creat_sprsetinfo(pv_id)
            self.creat_sprinfo(pv_id)
            self.creat_texinfo(pv_id)

    def creat_sprsetinfo(self,_pv_id):
        head_str = f'SPR_SEL_PV{_pv_id:03d}'
        sprsetinfo_dict = {"id":0,
                        "info_str":0,
                        "file_str":0,
                        "info_id":0}
        SpriteSetInfo.max_info_id  += 1
        sprsetinfo_dict["info_str"] = head_str
        sprsetinfo_dict["file_str"] = str(head_str + ".bin").lower()
        sprsetinfo_dict["id"]       = get_hash(head_str)
        sprsetinfo_dict["info_id"]  = SpriteSetInfo.max_info_id
        self.Manager.add_spr(SpriteSetInfo(sprsetinfo_dict))

    def creat_sprinfo(self,_pv_id):
        head_str_list = [f"BG{_pv_id:03d}",
                         f"JK{_pv_id:03d}",
                         f"LOGO{_pv_id:03d}"]
        sprinfo_dict = {"id":0,
                        "info_str":0,
                        "index":0,
                        "is_spr":True,
                        "info_id":0}
        for i in range(3):
            head_str = f'SPR_SEL_PV{_pv_id:03d}_SONG_{head_str_list[i]}'
            sprinfo_dict["info_str"] = head_str
            sprinfo_dict["index"]    = i
            sprinfo_dict["is_spr"]   = True
            sprinfo_dict["id"]       = get_hash(head_str)
            sprinfo_dict["info_id"]  = SpriteSetInfo.max_info_id
            self.Manager.add_spr(Sprites(sprinfo_dict))

    def creat_texinfo(self,_pv_id):
        head_str_list = ["MERGE_BC5COMP_00",
                         "MERGE_BC5COMP_01"]
        sprinfo_dict = {"id":0,
                        "info_str":0,
                        "index":0,
                        "is_spr":False,
                        "info_id":0}
        for i in range(2):
            head_str = f'SPR_SEL_PV{_pv_id:03d}_{head_str_list[i]}'
            sprinfo_dict["info_str"] = head_str
            sprinfo_dict["index"]    = i
            sprinfo_dict["is_spr"]   = False
            sprinfo_dict["id"]       = get_hash(head_str)
            sprinfo_dict["info_id"]  = SpriteSetInfo.max_info_id
            self.Manager.add_spr(Sprites(sprinfo_dict))

class add_pvtmb:
    def __init__(self, _Manager, _pv_list = None):
        self.Manager = _Manager
        self.obj_pvtmb = self.Manager.pvtmb
        if _pv_list == None:
            raise ValueError("pv_list is None！",_pv_list)
        for pv_id in _pv_list:
            self.add_pvtmb_spr(pv_id)
        
        print("SPR_SEL_PVTMB Textures list:")
        for name in self.obj_pvtmb.Textures_list:
            print(name.info_str)
        while True:
            print("\rDo you want to add New SPR_SEL_PVTMB Textures?(Y/N)",end="")
            want_add_pvtmb_tex = input()
            if want_add_pvtmb_tex.upper() != "Y":
                print("\nUser Select:No")
                return
            print("\nUser Select:Yes")
            break
        while True:
            print("How many SPR_SEL_PVTMB Textures you want to add")
            _num = input()
            if self.check_str_is_int(_num):
                self.add_pvtmb_tex(int(_num))
                break
        
    def check_str_is_int(self,_num):
        try:
            _num = int(_num)
            return True
        except:
            return False
        
    def add_pvtmb_spr(self, _pv_id):
        sprinfo_dict = {"id":0,
                        "info_str":0,
                        "index":0,
                        "is_spr":True,
                        "info_id":self.obj_pvtmb.info_id}
        
        sprinfo_dict["info_str"] = f'SPR_SEL_PVTMB_{_pv_id}'
        sprinfo_dict["index"]    = len(self.obj_pvtmb.Sprites_list)
        sprinfo_dict["is_spr"]   = True
        sprinfo_dict["id"]       = get_hash(sprinfo_dict["info_str"])
        sprinfo_dict["info_id"]  = self.obj_pvtmb.info_id

        self.Manager.add_spr(Sprites(sprinfo_dict))

    def add_pvtmb_tex(self,_num):
        sprinfo_dict = {"id":0,
                        "info_str":0,
                        "index":0,
                        "is_spr":False,
                        "info_id":self.obj_pvtmb.info_id}
        
        index_start = len(self.obj_pvtmb.Textures_list)
        index_end   = index_start + _num

        for i in range(index_start , index_end):
            head_str = f'SPRTEX_SEL_PVTMB_MERGE_D5COMP_{i}'
            sprinfo_dict["info_str"] = head_str
            sprinfo_dict["index"]    = i
            sprinfo_dict["is_spr"]   = False
            sprinfo_dict["id"]       = get_hash(head_str)
            sprinfo_dict["info_id"]  = self.obj_pvtmb.info_id
            self.Manager.add_spr(Sprites(sprinfo_dict))

DB = Manager()
print("Read DB......")
DB.read_db("base\\mod_spr_db.bin")
print("Done!")
  
while True:
    print("-"*32)
    print("1.check Index")
    print("2.check ID")
    print('3.Add custom chart spr_db')
    print("4.Load another mod_spr_db.bin")
    print("5.Save you change into mod_spr_db and Exit")
    select = int(input("input number then press enter\n"))
    print("*"*32)
    if select == 1:
        DB.check_index()
    if select == 2:
        DB.check_id()
    if select == 3:
        pv_id_list = []
        while True:
            pv_id = input("input pv_id then press enter to add spr db\nif you don't want add more pv_id then just press enter\n")
            if pv_id == "":
                break
            try:
                pv_id_list.append(int(pv_id))
            except:
                print("Wrong Value!")
        add_new_custom_chart_spr_db(pv_id_list,DB)
        if DB.pvtmb != None:
            add_pvtmb(DB,pv_id_list)
        DB.write_db("output\\mod_spr_db.bin")
        
    if select == 4:
        DB = Manager()
        print("Drop your mod_spr_db.bin in here then press enter")
        DB_path = input()
        DB.read_db(DB_path)
    if select == 5:
        DB.write_db("output\\mod_spr_db.bin")
        break



