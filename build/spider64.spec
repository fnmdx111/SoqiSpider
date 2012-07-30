# -*- mode: python -*-
a = Analysis([os.path.join(HOMEPATH,'support\\_mountzlib.py'), os.path.join(HOMEPATH,'support\\useUnicode.py'), 'd:\\workspace\\SoqiSpider\\main.py'],
             pathex=['D:\\workspace\\SoqiSpider', 'D:\\Python27\\DLLs', 'D:\\Python27\\Lib', 'D:\\Python27\\Lib', 'C:\\Users\\wo'])
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=1,
          name=os.path.join('build\\pyi.win32\\spider64', 'spider64.exe'),
          debug=False,
          strip=False,
          upx=True,
          console=False )
coll = COLLECT( exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name=os.path.join('dist', 'spider64'))
app = BUNDLE(coll,
             name=os.path.join('dist', 'spider64.app'))
