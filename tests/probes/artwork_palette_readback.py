import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from PySide6.QtCore import QMetaObject, QObject, QUrl, Slot, qInstallMessageHandler
from PySide6.QtGui import QColor, QGuiApplication, QImage
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest

from djconnect_pi.artwork_palette import displayed_artwork_tint

app=QGuiApplication([]);messages=[];qInstallMessageHandler(lambda k,c,m:messages.append(m))
class Backend(QObject):
 def __init__(self):super().__init__();self.values=[]
 @Slot(QImage,result=str)
 def sampleArtworkTint(self,image):
  assert image.width()==32 and image.height()==32
  value=displayed_artwork_tint(image);self.values.append(value);return value
b=Backend();secondBackend=Backend();paths=[]
workspace=TemporaryDirectory(prefix='pi-palette-readback-')
for color in ['red','blue']:
 im=QImage(16,16,QImage.Format_ARGB32);im.fill(QColor(color));p=Path(workspace.name)/(color+'.png');assert im.save(str(p));paths.append(p.as_uri())
e=QQmlApplicationEngine();e.rootContext().setContextProperty('djconnect',b);e.rootContext().setContextProperty('djconnect2',secondBackend);q=Path.cwd()/'src/djconnect_pi/qml'
e.loadData(('''import QtQuick
import "'''+q.as_uri()+'''"
Window {id:root;visible:true;width:100;height:100
 property string picture:"'''+paths[0]+'''"
 property string lease:"original"
 property bool admitted:true
 property bool secondActive:false
 property var glassStyle:GlassStyle
 Image {id:art;anchors.fill:parent;source:root.picture;cache:false;retainWhileLoading:false}
 Image {id:otherImage;width:16;height:16;source:"'''+paths[1]+'''"}
 ArtworkPalette {objectName:"otherPalette";backend:djconnect2;imageItem:otherImage;active:root.secondActive}
 ArtworkPalette {id:palette;objectName:"palette";backend:djconnect;imageItem:art;leaseKey:root.lease;admissionCheck:function(){return root.admitted}}
}''').encode(),QUrl.fromLocalFile(str(q/'ActualPaletteFences.qml')))
assert e.rootObjects(),messages
window=e.rootObjects()[0];assert isinstance(window,QQuickWindow);window.setWidth(int(sys.argv[1]));window.setHeight(int(sys.argv[2]));palette=window.findChild(QObject,'palette')
def wait_for(predicate, label):
    # Readback is asynchronous. Bound actual completion, not an arbitrary frame delay.
    for _ in range(100):
        if predicate(): return
        QTest.qWait(20)
    raise AssertionError((label,messages,b.values))
wait_for(lambda: palette.property('tint')=='#ff0000', 'initial readback')
assert palette.property('tint')=='#ff0000' and b.values==['#ff0000'],(messages,b.values)
# Force one real asynchronous readback, then revoke before any GUI event can apply it.
window.setProperty('lease','new-profile');QMetaObject.invokeMethod(palette,'sample');assert palette.property('pending')
window.setProperty('secondActive',True);other=window.findChild(QObject,'otherPalette');QMetaObject.invokeMethod(other,'sample');assert not other.property('pending')
window.setProperty('admitted',False);assert palette.property('tint')=='' and palette.property('sampledTint')==''
QTest.qWait(120);assert b.values==['#ff0000'] and palette.property('tint')==''
wait_for(lambda: secondBackend.values==['#0000ff'],'second queued image');window.setProperty('secondActive',False)
# A fresh current image gets a new sample; an old readback cannot paint the new lease.
window.setProperty('picture',paths[1]);window.setProperty('lease','latest');window.setProperty('admitted',True)
assert palette.property('tint')=='';wait_for(lambda: palette.property('tint')=='#0000ff','fresh blue readback')
assert palette.property('tint')=='#0000ff' and b.values==['#ff0000','#0000ff'],(messages,b.values)
window.setProperty('picture','');assert palette.property('tint')=='';QTest.qWait(80);assert palette.property('sampledTint')==''
# Hiding/active withdrawal is synchronous and cannot resurrect a saved sample.
window.setProperty('picture',paths[0]);wait_for(lambda: palette.property('tint')=='#ff0000','source restored');assert palette.property('tint')=='#ff0000'
palette.setProperty('active',False);assert palette.property('sampledTint')=='' and palette.property('tint')==''
palette.setProperty('active',True);assert palette.property('tint')=='';wait_for(lambda: palette.property('tint')=='#ff0000','active restored')
style=window.property('glassStyle');style.setProperty('awake',False);assert palette.property('sampledTint')=='' and palette.property('tint')==''
style.setProperty('awake',True);assert palette.property('tint')=='';wait_for(lambda: palette.property('tint')=='#ff0000','awake restored')
window.setProperty('lease','closing');QMetaObject.invokeMethod(palette,'sample');assert palette.property('pending')
window.close();assert palette.property('tint')=='';e.deleteLater();QTest.qWait(60)
assert not messages,messages
print(json.dumps({'one_live_broker_readback_and_sibling_isolation':True,'real_32pixel_readback':True,'revoked_pending_callback_no_slot_call':True,'fresh_lease_and_source_fence':True,'source_clear_no_resurrection':True,'active_withdrawal':True,'idle_withdrawal_no_saved_tint_restore':True,'close_during_pending':True,'qml_errors':messages}))
