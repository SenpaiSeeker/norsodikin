nsdev = __import__("nsdev")

BinaryCipher = nsdev.encrypt.BinaryCipher
BytesCipher = nsdev.encrypt.BytesCipher
ShiftChipher = nsdev.encrypt.ShiftChipher
cipher = nsdev.encrypt.cipher

LoggerHandler = nsdev.logger.LoggerHandler
SSHUserManager = nsdev.addUser.SSHUserManager

LocalDataBase = nsdev.database.LocalDataBase
MongoDataBase = nsdev.database.MongoDataBase

__version__ = "0.1.dev2"
