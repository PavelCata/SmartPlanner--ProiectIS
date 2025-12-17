class Config:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.SECRET_KEY = "cheie-super-secreta"
            cls._instance.SQLALCHEMY_DATABASE_URI = (
                "mysql+pymysql://root:PriPjtJXaqEoaCKNgFsYJOLfAuhyRejJ@nozomi.proxy.rlwy.net:17751/railway"
            )
            cls._instance.SQLALCHEMY_TRACK_MODIFICATIONS = False
            cls._instance.DARK_MODE = False
        return cls._instance