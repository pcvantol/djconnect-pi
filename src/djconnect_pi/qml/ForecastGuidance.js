.pragma library

// Apple Session Forecast presents Core's quoted queue prose as a list.
// This runs only over already-admitted text and never creates track references.
function split(sectionId, value) {
    if (sectionId !== "guidance" || typeof value !== "string" || value.length > 8192 || /[\r\n]/.test(value))
        return null
    var first = value.indexOf(': “')
    if (first <= 0)
        return null
    var start = first + 2
    var tail = value.slice(start)
    var note = /\. (?=(?:De rode draad zoek ik|Zo ziet de wachtrij|I’ll look for a musical thread|That is the queue|Den musikalischen Faden|So sieht die Warteschlange|Je chercherai le fil musical|Voilà la file actuelle|Buscaré el hilo musical|Así está la cola))/.exec(tail)
    if (!note)
        return null
    var tracks = tail.slice(0, note.index).split(/(?:, | (?:and|en|und|et|y) )(?=“[^“”]+” — )/)
    if (tracks.length > 5 || !tracks.every(function(track) {
        return /^“[^“”]+” — [^“”]+$/.test(track) && track.slice(track.indexOf("” — ") + 4).trim().length > 0
    }))
        return null
    return {intro: value.slice(0, start).replace(/ +$/, ""), tracks: tracks, note: tail.slice(note.index + note[0].length)}
}
