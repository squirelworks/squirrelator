package com.squirelworks.squirrelator.ui

/**
 * The translation engine as the screens see it. Each platform supplies one
 * that calls the same Python engine: Chaquopy on Android, a Python process on
 * desktop. Calls may be slow, so the screens make them off the main thread.
 */
interface Engine {
    /** Language ids translate() accepts with its default settings, in menu order. */
    fun languages(): List<String>

    /**
     * What the screen shows for a translation under the Auto engine, the same
     * as the desktop GUI (squirrelator.menus.display): the text, with the
     * pipeline's alternatives and alpha label, or the second opinion for
     * Latin and Klingon.
     */
    fun translate(text: String, from: String, to: String): Translated
}

/**
 * A translation as shown: [text], the [engine] that made it ("Rules" or
 * "Pipeline (alpha)"), and the [mode] chosen, "Auto" on every app for now.
 */
data class Translated(val text: String, val engine: String, val mode: String = "Auto")
