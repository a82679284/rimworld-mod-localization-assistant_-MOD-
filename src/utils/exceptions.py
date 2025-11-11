"""
自定义异常类
"""


class RimworldTranslatorError(Exception):
    """基础异常类"""
    pass


class ModNotFoundError(RimworldTranslatorError):
    """MOD 目录不存在"""
    pass


class ModInvalidStructureError(RimworldTranslatorError):
    """MOD 目录结构无效"""
    pass


class XMLParseError(RimworldTranslatorError):
    """XML 解析失败"""
    pass


class FilePermissionError(RimworldTranslatorError):
    """文件权限不足"""
    pass


class DatabaseError(RimworldTranslatorError):
    """数据库操作错误"""
    pass


class TranslationAPIError(RimworldTranslatorError):
    """翻译 API 调用失败"""
    pass


class ConfigurationError(RimworldTranslatorError):
    """配置错误"""
    pass


class ValidationError(RimworldTranslatorError):
    """数据验证失败"""
    pass
