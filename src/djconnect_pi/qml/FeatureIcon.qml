import QtQuick
import "BrandTheme.js" as BrandTheme

Canvas {
        id: menuIcon
        property string iconName: "more"
        property color iconColor: BrandTheme.colors.text
        property real strokeWidth: 2.4

        DJSessionMenuSymbol {
            anchors.fill: parent
            visible: menuIcon.iconName === "session"
            iconColor: menuIcon.iconColor
        }
        implicitWidth: 32
        implicitHeight: 32
        onIconNameChanged: requestPaint()
        onIconColorChanged: requestPaint()
        onStrokeWidthChanged: requestPaint()
        onPaint: {
            var ctx = getContext("2d")
            var w = width
            var h = height
            var s = Math.min(w, h)
            var x = (w - s) / 2
            var y = (h - s) / 2
            function px(v) { return x + v * s / 32 }
            function py(v) { return y + v * s / 32 }
            function line(x1, y1, x2, y2) {
                ctx.beginPath()
                ctx.moveTo(px(x1), py(y1))
                ctx.lineTo(px(x2), py(y2))
                ctx.stroke()
            }
            function circle(cx, cy, r, fill) {
                ctx.beginPath()
                ctx.arc(px(cx), py(cy), r * s / 32, 0, Math.PI * 2)
                if (fill) ctx.fill()
                else ctx.stroke()
            }
            function roundRect(x0, y0, ww, hh, rr) {
                ctx.beginPath()
                ctx.moveTo(px(x0 + rr), py(y0))
                ctx.lineTo(px(x0 + ww - rr), py(y0))
                ctx.quadraticCurveTo(px(x0 + ww), py(y0), px(x0 + ww), py(y0 + rr))
                ctx.lineTo(px(x0 + ww), py(y0 + hh - rr))
                ctx.quadraticCurveTo(px(x0 + ww), py(y0 + hh), px(x0 + ww - rr), py(y0 + hh))
                ctx.lineTo(px(x0 + rr), py(y0 + hh))
                ctx.quadraticCurveTo(px(x0), py(y0 + hh), px(x0), py(y0 + hh - rr))
                ctx.lineTo(px(x0), py(y0 + rr))
                ctx.quadraticCurveTo(px(x0), py(y0), px(x0 + rr), py(y0))
                ctx.closePath()
                ctx.stroke()
            }
            function star(cx, cy, r) {
                ctx.beginPath()
                for (var i = 0; i < 8; i++) {
                    var a = -Math.PI / 2 + i * Math.PI / 4
                    var radius = i % 2 === 0 ? r : r * 0.42
                    var sx = px(cx) + Math.cos(a) * radius * s / 32
                    var sy = py(cy) + Math.sin(a) * radius * s / 32
                    if (i === 0) ctx.moveTo(sx, sy)
                    else ctx.lineTo(sx, sy)
                }
                ctx.closePath()
                ctx.fill()
            }

            ctx.clearRect(0, 0, w, h)
            ctx.strokeStyle = menuIcon.iconColor
            ctx.fillStyle = menuIcon.iconColor
            ctx.lineWidth = menuIcon.strokeWidth
            ctx.lineCap = "round"
            ctx.lineJoin = "round"

            function waveform() {
                var heights = [8, 16, 24, 12, 20, 8]
                for (var b = 0; b < heights.length; b++) line(6 + b * 4, 16 - heights[b] / 2, 6 + b * 4, 16 + heights[b] / 2)
            }
            function microphone() {
                roundRect(12, 5, 8, 14, 4)
                ctx.beginPath(); ctx.arc(px(16), py(16), 8 * s / 32, 0, Math.PI); ctx.stroke()
                line(16, 24, 16, 28); line(12, 28, 20, 28)
            }
            if (iconName === "waveform" || iconName === "mood_groove" || iconName === "presence_talkative") {
                waveform()
            } else if (iconName === "mood_chill") {
                ctx.beginPath(); ctx.moveTo(px(19), py(5))
                ctx.bezierCurveTo(px(5), py(3), px(3), py(25), px(18), py(27))
                ctx.bezierCurveTo(px(23), py(27), px(27), py(23), px(27), py(20))
                ctx.bezierCurveTo(px(13), py(25), px(9), py(11), px(19), py(5)); ctx.fill()
            } else if (iconName === "mood_energy") {
                ctx.beginPath(); ctx.moveTo(px(19),py(3));ctx.lineTo(px(7),py(18));ctx.lineTo(px(15),py(18))
                ctx.lineTo(px(12),py(29));ctx.lineTo(px(26),py(13));ctx.lineTo(px(18),py(13));ctx.closePath();ctx.fill()
            } else if (iconName === "mood_party") {
                ctx.beginPath();ctx.moveTo(px(5),py(27));ctx.lineTo(px(11),py(12));ctx.lineTo(px(22),py(23));ctx.closePath();ctx.stroke()
                line(14, 9, 17, 5);line(20, 13, 26, 10);line(23, 19, 28, 19)
                circle(24, 5, 1.4, true);circle(9, 6, 1.4, true);circle(27, 26, 1.4, true)
            } else if (iconName === "presence_music_only") {
                line(17, 5, 17, 24);line(17,5,25,8);circle(13,24,4,true)
            } else if (iconName === "presence_occasional") {
                roundRect(5,7,22,16,4);line(11,23,9,27)
            } else if (iconName === "presence_balanced") {
                roundRect(4,6,16,13,3);line(9,19,7,23);roundRect(13,13,15,12,3);line(22,25,25,28)
            } else if (iconName === "presence_presenter" || iconName === "persona_festival_dj") {
                microphone()
            } else if (iconName === "persona_home_dj") {
                line(4,15,16,5);line(16,5,28,15);line(8,13,8,27);line(8,27,24,27);line(24,27,24,13)
                line(13,27,13,19);line(13,19,19,19);line(19,19,19,27)
            } else if (iconName === "persona_radio_dj") {
                roundRect(4,10,24,17,3);line(7,10,23,4);circle(21,19,4,false);line(8,16,13,16);line(8,21,13,21)
            } else if (iconName === "persona_club_dj") {
                circle(16,16,11,false);circle(16,16,3,false);line(19,8,24,13);line(8,19,13,24)
            } else if (iconName === "session_persona") {
                circle(16,16,11,false);circle(16,12,3.5,false)
                ctx.beginPath();ctx.arc(px(16),py(24),7*s/32,Math.PI,Math.PI*2);ctx.stroke()
            } else if (iconName === "search") {
                circle(14, 14, 8, false); line(20, 20, 27, 27)
            } else if (iconName === "send") {
                line(5, 14, 28, 4); line(28, 4, 19, 28); line(19, 28, 14, 19)
                line(14, 19, 5, 14); line(14, 19, 28, 4)
            } else if (iconName === "history") {
                ctx.beginPath(); ctx.arc(px(16), py(16), 10, -Math.PI * 0.8, Math.PI * 0.8); ctx.stroke()
                line(8, 5, 7, 12); line(7, 12, 13, 11)
                line(16, 10, 16, 16); line(16, 16, 21, 19)
            } else if (iconName === "persona") {
                circle(16, 11, 4, false)
                ctx.beginPath(); ctx.arc(px(16), py(26), 9 * s / 32, Math.PI, Math.PI * 2); ctx.stroke()
            } else if (iconName === "voice") {
                line(6, 13, 11, 13); line(11, 13, 17, 8); line(17, 8, 17, 24)
                line(17, 24, 11, 19); line(11, 19, 6, 19); line(6, 19, 6, 13)
                ctx.beginPath(); ctx.arc(px(18), py(16), 6 * s / 32, -1, 1); ctx.stroke()
                ctx.beginPath(); ctx.arc(px(18), py(16), 10 * s / 32, -1, 1); ctx.stroke()
            } else if (iconName === "music") {
                line(13, 10, 13, 23)
                line(13, 10, 22, 7)
                line(22, 7, 22, 19)
                circle(10, 23, 3.2, true)
                circle(19, 19, 3.2, true)
            } else if (iconName === "control") {
                line(8, 10, 24, 10); circle(13, 10, 3, false)
                line(8, 16, 24, 16); circle(20, 16, 3, false)
                line(8, 22, 24, 22); circle(11, 22, 3, false)
            } else if (iconName === "chat") {
                roundRect(6, 8, 14, 11, 3)
                line(11, 19, 9, 23)
                roundRect(13, 13, 13, 10, 3)
                line(21, 23, 24, 26)
            } else if (iconName === "queue") {
                ctx.beginPath()
                ctx.moveTo(px(6), py(7)); ctx.lineTo(px(10), py(9.5)); ctx.lineTo(px(6), py(12)); ctx.closePath(); ctx.fill()
                line(13, 9.5, 26, 9.5)
                line(7, 16, 26, 16)
                line(7, 22.5, 26, 22.5)
            } else if (iconName === "more") {
                circle(9, 16, 2.2, true); circle(16, 16, 2.2, true); circle(23, 16, 2.2, true)
            } else if (iconName === "playlists") {
                line(10, 7, 22, 7); line(8, 10, 24, 10)
                roundRect(7, 12, 18, 13, 2)
            } else if (iconName === "musicdna") {
                ctx.beginPath()
                ctx.moveTo(px(8), py(8))
                ctx.bezierCurveTo(px(24), py(8), px(8), py(24), px(24), py(24))
                ctx.moveTo(px(24), py(8))
                ctx.bezierCurveTo(px(8), py(8), px(24), py(24), px(8), py(24))
                ctx.stroke()
                line(10, 13, 22, 13)
                line(10, 19, 22, 19)
            } else if (iconName === "trackInsight") {
                ctx.beginPath()
                ctx.moveTo(px(5), py(17))
                ctx.lineTo(px(8), py(17))
                ctx.bezierCurveTo(px(9), py(12), px(10.5), py(12), px(11.5), py(17))
                ctx.lineTo(px(13.2), py(22))
                ctx.lineTo(px(15.3), py(8))
                ctx.lineTo(px(18.1), py(24))
                ctx.lineTo(px(20.2), py(14))
                ctx.bezierCurveTo(px(21.4), py(17), px(22.4), py(17), px(24), py(17))
                ctx.lineTo(px(27), py(17))
                ctx.stroke()
                line(5, 25, 27, 25)
            } else if (iconName === "discover") {
                line(9, 23, 22, 10)
                line(19.5, 7.5, 24.5, 12.5)
                line(17.8, 9.2, 22.8, 14.2)
                star(9, 9, 3.2)
                star(24, 22, 2.5)
                star(14, 14, 1.8)
            } else if (iconName === "heart") {
                ctx.beginPath()
                ctx.moveTo(px(16), py(25))
                ctx.bezierCurveTo(px(7), py(19), px(5), py(13), px(8.5), py(9.5))
                ctx.bezierCurveTo(px(11.5), py(6.5), px(15), py(8.5), px(16), py(11))
                ctx.bezierCurveTo(px(17), py(8.5), px(20.5), py(6.5), px(23.5), py(9.5))
                ctx.bezierCurveTo(px(27), py(13), px(25), py(19), px(16), py(25))
                ctx.closePath()
                ctx.stroke()
            } else if (iconName === "mood") {
                circle(16, 16, 10, false)
                circle(12, 13, 1.4, true)
                circle(20, 13, 1.4, true)
                ctx.beginPath()
                ctx.arc(px(16), py(17), 5, Math.PI * 0.15, Math.PI * 0.85)
                ctx.stroke()
            } else if (iconName === "gamepad") {
                ctx.beginPath()
                ctx.moveTo(px(8), py(20))
                ctx.quadraticCurveTo(px(10), py(12), px(14), py(14))
                ctx.lineTo(px(18), py(14))
                ctx.quadraticCurveTo(px(22), py(12), px(24), py(20))
                ctx.quadraticCurveTo(px(25), py(25), px(21), py(23))
                ctx.lineTo(px(18), py(20))
                ctx.lineTo(px(14), py(20))
                ctx.lineTo(px(11), py(23))
                ctx.quadraticCurveTo(px(7), py(25), px(8), py(20))
                ctx.stroke()
                line(11, 18, 15, 18); line(13, 16, 13, 20)
                circle(20, 17, 1.2, true); circle(23, 20, 1.2, true)
            } else if (iconName === "settings") {
                circle(16, 16, 5, false)
                for (var i = 0; i < 8; i++) {
                    var a = i * Math.PI / 4
                    line(16 + Math.cos(a) * 8, 16 + Math.sin(a) * 8, 16 + Math.cos(a) * 11, 16 + Math.sin(a) * 11)
                }
            } else if (iconName === "document") {
                roundRect(8, 4, 16, 24, 2)
                line(12, 11, 20, 11); line(12, 16, 20, 16); line(12, 21, 17, 21)
            } else if (iconName === "privacy") {
                ctx.beginPath(); ctx.moveTo(px(16), py(4)); ctx.lineTo(px(26), py(8)); ctx.lineTo(px(25), py(18)); ctx.quadraticCurveTo(px(23), py(25), px(16), py(29)); ctx.quadraticCurveTo(px(9), py(25), px(7), py(18)); ctx.lineTo(px(6), py(8)); ctx.closePath(); ctx.stroke()
                line(16, 11, 16, 21)
            } else if (iconName === "back") {
                line(20, 7, 11, 16); line(11, 16, 20, 25)
            } else if (iconName === "logs") {
                roundRect(9, 6, 13, 18, 2)
                line(13, 11, 18, 11); line(13, 16, 17, 16)
                circle(21, 22, 3.5, false); line(23.5, 24.5, 26, 27)
            } else if (iconName === "trash") {
                line(10, 11, 22, 11)
                line(13, 11, 13.8, 25)
                line(18.2, 25, 19, 11)
                line(12, 11, 12.8, 25)
                line(19.2, 25, 20, 11)
                line(14, 8, 18, 8)
                line(15, 6, 17, 6)
                roundRect(11, 11, 10, 15, 1.5)
            } else if (iconName === "info") {
                circle(16, 16, 10, false)
                line(16, 15, 16, 22); circle(16, 10.5, 1.2, true)
            } else if (iconName === "globe") {
                circle(16, 16, 11, false)
                line(5, 16, 27, 16)
                ctx.beginPath(); ctx.moveTo(px(8), py(9)); ctx.quadraticCurveTo(px(16), py(13), px(24), py(9)); ctx.stroke()
                ctx.beginPath(); ctx.moveTo(px(8), py(23)); ctx.quadraticCurveTo(px(16), py(19), px(24), py(23)); ctx.stroke()
                ctx.beginPath(); ctx.moveTo(px(16), py(5)); ctx.bezierCurveTo(px(8), py(10), px(8), py(22), px(16), py(27)); ctx.stroke()
                ctx.beginPath(); ctx.moveTo(px(16), py(5)); ctx.bezierCurveTo(px(24), py(10), px(24), py(22), px(16), py(27)); ctx.stroke()
            } else if (iconName === "end") {
                ctx.strokeStyle = BrandTheme.colors.danger
                circle(16, 16, 10, false)
                line(12, 12, 20, 20); line(20, 12, 12, 20)
            } else if (iconName === "refresh") {
                ctx.beginPath(); ctx.arc(px(16), py(17), s * 0.28, -Math.PI * 0.65, Math.PI * 1.1); ctx.stroke()
                line(19, 5, 23, 10); line(23, 10, 17, 11)

            }
        }

}
