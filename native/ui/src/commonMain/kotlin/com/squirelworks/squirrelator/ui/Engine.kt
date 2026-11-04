package com.squirelworks.squirrelator.ui

/**
 * The translation engine as the screens see it. Each platform supplies one
 * that calls the same Python engine: Chaquopy on Android, a Python process on
 * desktop. Calls may be slow, so the screens make them off the main thread.
 */
interface Engine {
    /** Language ids translate() accepts with its default settings, in menu order. */
    fun languages(): List<String>

    /** The engine's translate() with its defaults. */
    fun translate(text: String, from: String, to: String): String
}
