# -*- coding: utf-8 -*-
# Author:yuzhonghua

import os
import re
import tarfile
import zipfile

from Gastepo.Core.Base.BaseData import OUTPUT_PATH
from Gastepo.Core.Base.CustomException import DotTypeError
from Gastepo.Core.Util.LogUtils import logger


class ZipTool(object):
    '''
    压缩/解压缩工具类
    '''

    def __init__(self):
        pass

    def zip(self, srcpath, zipname):
        '''
        将指定路径下的所有文件zip打包压缩
        :param srcpath:待压缩目录或独立文件
        :param zipname:压缩后zip文件（只需指定文件名且后缀名必须为".zip"，默认均位于OUTPUT_PATH文件目录）
        :return zipname:返回压缩文件绝对路径
        '''
        try:
            initname = re.split(r'[\\|/]', zipname)[-1]
            dot = os.path.splitext(initname)[1]
            if dot == r'.zip':
                zipname = os.path.join(OUTPUT_PATH, initname)
                if os.path.isdir(srcpath) and os.path.exists(srcpath):
                    ziphandler = zipfile.ZipFile(zipname, 'w', zipfile.ZIP_DEFLATED)
                    for rootpath, dirs, files in os.walk(srcpath):
                        for filename in files:
                            ziphandler.write(os.path.join(rootpath, filename))
                            logger.info('文件"{}"已zip压缩成功.'.format(filename))
                        logger.info('全部zip压缩成功, 生成zip压缩文件："{}".'.format(zipname))
                    ziphandler.close()
                    return zipname
                elif os.path.isfile(srcpath) and os.path.exists(srcpath):
                    ziphandler = zipfile.ZipFile(zipname, 'w', zipfile.ZIP_DEFLATED)
                    ziphandler.write(srcpath)
                    logger.info('文件"{}"已zip压缩成功.'.format(re.split(r'[\\|/]', srcpath)[-1]))
                    logger.info('全部zip压缩成功, 生成zip压缩文件："{}".'.format(zipname))
                    ziphandler.close()
                    return zipname
                else:
                    raise FileNotFoundError
            else:
                raise DotTypeError
        except FileNotFoundError:
            logger.exception('文件不存在或其路径非法, 请检查参数路径（其中待压缩目录或独立文件需指定完整路径）.')
        except DotTypeError:
            logger.exception('非法压缩文件后缀名"{}", 请指定".zip"后缀名的压缩文件名称.'.format(dot))

    def unzip(self, zipname, dstpath=OUTPUT_PATH):
        '''
        将指定zip文件解压缩到指定文件夹，并删除源zip压缩文件
        :param zipname: 待解压zip压缩文件（需指定绝对路径）
        :param dstpath: 指定解压路径（层级结构，默认解压缩路径为OUTPUT_PATH文件目录）
        :return dstpath:返回解压缩路径
        '''
        try:
            initname = re.split(r'[\\|/]', zipname)[-1]
            dot = os.path.splitext(initname)[1]
            if os.path.isfile(zipname) and os.path.exists(zipname):
                if dot == r'.zip':
                    ziphandler = zipfile.ZipFile(zipname, 'r')
                    for file in ziphandler.namelist():
                        logger.info('文件"{}"开始unzip解压缩提取.'.format(file))
                    ziphandler.extractall(dstpath)
                    logger.info('压缩文件"{0}"已unzip解压缩成功, 解压路径为："{1}".'.format(initname, dstpath))
                    ziphandler.close()
                    os.remove(zipname)
                    logger.info('压缩文件"{}"已物理删除.'.format(initname))
                    return dstpath
                else:
                    raise DotTypeError
            else:
                raise FileNotFoundError
        except FileNotFoundError:
            logger.exception('文件不存在或其路径非法, 请检查参数路径（其中zip压缩文件需指定绝对路径）.')
        except DotTypeError:
            logger.exception('非法压缩文件后缀名"{}", 请指定".zip"后缀名的压缩文件名称.'.format(dot))

    def tar(self, srcpath, tarname):
        '''
        将指定路径下的所有文件打成tar包并压缩(gzip/bzip2/xz)
        :param srcpath:待压缩目录或独立文件
        :param tarname:tar包压缩后文件名（只需指定文件名，后缀名可为".tar.gz/.tar.bz2/.tar.xz"，默认均位于OUTPUT_PATH文件目录）
        :return tarname:返回压缩文件绝对路径
        '''
        try:
            initname = re.split(r'[\\|/]', tarname)[-1]
            dot = os.path.splitext(initname)[1]
            comtype = dot[1:]
            if dot in [r'.gz', r'.bz2', r'.xz']:
                tarname = os.path.join(OUTPUT_PATH, initname)
                if os.path.isdir(srcpath) and os.path.exists(srcpath):
                    tarhandler = tarfile.open(tarname, "w:{}".format(comtype))
                    for rootpath, dirs, files in os.walk(srcpath):
                        for filename in files:
                            tarhandler.add(os.path.join(rootpath, filename))
                            logger.info('文件"{0}"已{1}压缩成功.'.format(filename, comtype))
                        logger.info('全部{0}压缩成功, 生成压缩文件："{1}".'.format(comtype, tarname))
                    tarhandler.close()
                    return tarname
                elif os.path.isfile(srcpath) and os.path.exists(srcpath):
                    tarhandler = tarfile.open(tarname, "w:{}".format(comtype))
                    tarhandler.add(srcpath)
                    logger.info('文件"{0}"已{1}压缩成功.'.format(re.split(r'[\\|/]', srcpath)[-1], comtype))
                    logger.info('全部{0}压缩成功, 生成压缩文件："{1}".'.format(comtype, tarname))
                    tarhandler.close()
                    return tarname
                else:
                    raise FileNotFoundError
            else:
                raise DotTypeError
        except FileNotFoundError:
            logger.exception('文件不存在或其路径非法, 请检查参数路径（其中待压缩目录或独立文件需指定完整路径）.')
        except DotTypeError:
            logger.exception('非法压缩文件后缀名"{}", 请指定".tar.gz/.tar.bz2/.tar.xz"中任意后缀名的压缩文件名称.'.format(dot))

    def untar(self, tarname, dstpath=OUTPUT_PATH):
        '''
        将指定tar包压缩文件解压缩到指定文件夹，并删除源tar包压缩文件
        :param tarname: 待解压tar包压缩文件（需指定绝对路径）
        :param dstpath: 指定解压路径（层级结构，默认解压缩路径为OUTPUT_PATH文件目录）
        :return dstpath:返回解压缩路径
        '''
        try:
            initname = re.split(r'[\\|/]', tarname)[-1]
            dot = os.path.splitext(initname)[1]
            comtype = dot[1:]
            if os.path.isfile(tarname) and os.path.exists(tarname):
                if dot in [r'.gz', r'.bz2', r'.xz']:
                    tarhandler = tarfile.open(tarname, "r:{}".format(comtype))
                    for file in tarhandler.getnames():
                        logger.info('文件"{0}"开始{1}解压缩提取.'.format(file, comtype))
                    tarhandler.extractall(dstpath)
                    logger.info('压缩文件"{0}"已{1}解压缩成功, 解压路径为："{2}".'.format(initname, comtype, dstpath))
                    tarhandler.close()
                    os.remove(tarname)
                    logger.info('压缩文件"{}"已物理删除.'.format(initname))
                    return dstpath
                else:
                    raise DotTypeError
            else:
                raise FileNotFoundError
        except FileNotFoundError:
            logger.exception('文件不存在或其路径非法, 请检查参数路径（其中压缩文件需指定绝对路径）.')
        except DotTypeError:
            logger.exception('非法压缩文件后缀名"{}", 请指定".tar.gz/.tar.bz2/.tar.xz"中任意后缀名的压缩文件名称.'.format(dot))


comext = ZipTool()
