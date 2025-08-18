from pathlib import Path
from arkparse import AsaSave
import time
from .__manager import Manager
from arkparse.ftp.ark_ftp_client import ArkFtpClient, ArkFile, ArkMap
from arkparse.api import DinoApi, EquipmentApi, StackableApi, StructureApi, PlayerApi, BaseApi

class SaveTracker(Manager):
    def __init__(self, ftp_config: str, map: ArkMap):
        super().__init__(self.__process, "Save tracker", 60)
        self.ftp_config = ftp_config
        self._save: AsaSave = None
        self.map = map
        self._save_is_manually_set: bool = False

        # APIs
        self._dino_api: DinoApi = None
        self._equipment_api: EquipmentApi = None
        self._stackable_api: StackableApi = None
        self._structure_api: StructureApi = None
        self._player_api: PlayerApi = None
        self._base_api: BaseApi = None
        self.ftp_client: ArkFtpClient = None

        self._prev_save_info: ArkFile = None
        self.reconnect()

    @property
    def save(self) -> AsaSave:
        return self._save

    @property
    def dino_api(self) -> DinoApi:
        return self._dino_api
    
    @property
    def equipment_api(self) -> EquipmentApi:
        return self._equipment_api
    
    @property
    def stackable_api(self) -> StackableApi:
        return self._stackable_api
    
    @property
    def structure_api(self) -> StructureApi:
        return self._structure_api
    
    @property
    def player_api(self) -> PlayerApi:
        return self._player_api
    
    @property
    def base_api(self) -> BaseApi:
        return self._base_api

    def stop(self):
        if self.ftp_client:
            self.ftp_client.close()
            self.ftp_client = None

    def disconnect(self):
        if self.ftp_client:
            self.ftp_client.close()
            self.ftp_client = None

    def connect(self):
        self.ftp_client: ArkFtpClient = ArkFtpClient.from_config(self.ftp_config, self.map)
        self.ftp_client.connect()

    def reconnect(self):
        if self.ftp_client:
            self.disconnect()
        self.connect()

    def set_save(self, save: AsaSave):
        self._save = save
        self._save_is_manually_set = True
        self._dino_api = DinoApi(save)
        self._equipment_api = EquipmentApi(save)
        self._stackable_api = StackableApi(save)
        self._structure_api = StructureApi(save)
        self._player_api = PlayerApi(save)
        self._base_api = BaseApi(save, self.map)

    def get_save(self):
        if self._save is None:
            self._print("Save is not set, fetching from FTP...")
            self.__reconfigure()
        return self._save
    
    def put_save(self):
        self._save.store_db(Path.cwd() / "Ragnarok_WP.ark")

        if self.ftp_client is None:
            raise ValueError("FTP client is not connected. Call connect() before uploading the save file.")
        
        self._print("Removing old save file from FTP...")
        self.ftp_client.remove_save_file(self.map)
        self._print("Uploading new save file to FTP...")
        self.ftp_client.upload_save_file(Path.cwd() / "Ragnarok_WP.ark", map=self.map)

        self._print("Save file uploaded successfully.")

    def get_api(self, type: type):
        try:
            if type == DinoApi:
                return self._dino_api
            elif type == EquipmentApi:
                return self._equipment_api
            elif type == StackableApi:
                return self._stackable_api
            elif type == StructureApi:
                return self._structure_api
            elif type == PlayerApi:
                return self._player_api
            elif type == BaseApi:
                return self._base_api
            else:
                raise ValueError(f"Unknown API type: {type}")
        except Exception as e:
            if not "Unknown API type" in str(e):
                self.__reconfigure()
                return self.get_api(type)
            else:
                raise e

        
    def test_process(self):
        self.__process()

    def __init_apis(self, save: AsaSave):
        self._dino_api = DinoApi(save)
        self._equipment_api = EquipmentApi(save)
        self._stackable_api = StackableApi(save)
        self._structure_api = StructureApi(save)
        self._player_api = PlayerApi(save)
        self._base_api = BaseApi(save, self.map)

    def refresh_apis(self):
        self.__init_apis(self._save)

    def __reconfigure(self):
        self.ftp_client = ArkFtpClient.from_config(self.ftp_config, self.map)
        info = self.ftp_client.check_save_file(self.map)
        if len(info) == 0:
            self._print("No save file found on FTP, skipping reconfiguration.")
            return
        self._prev_save_info = self.ftp_client.check_save_file(self.map)[0]
        self._save = AsaSave(contents=self.ftp_client.download_save_file(map=self.map), read_only=False)
        self.__init_apis(self._save)

    def __process(self, _: int = 0):
        if self._save_is_manually_set:
            self._print("Save is manually set, skipping FTP check")
            return
        
        try:
            if self.ftp_client is None:
                self.reconnect()

            save_file_info : ArkFile = self.ftp_client.check_save_file(self.map)[0]
            if self._prev_save_info is None or save_file_info.is_newer_than(self._prev_save_info):
                self._print("New save file detected, downloading...")
                self._prev_save_info = save_file_info

                self._save = AsaSave(contents=self.ftp_client.download_save_file(map=self.map), read_only=False)
                self.__init_apis(self._save)

            self.reconnect()
        except Exception as e:
            self._print(f"Error during save tracking, redownloading save: {e}")
            self.__reconfigure()
