package com.squirelworks.squirrelator.desktop

import kotlin.test.AfterTest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

/** Runs the real engine through the bridge, the way the desktop app does. */
class PythonProcessEngineTest {
    private val engine = PythonProcessEngine.fromSystemProperties()

    @AfterTest
    fun stop() = engine.close()

    @Test
    fun offersTheDefaultEnginesLanguages() {
        val langs = engine.languages()
        assertTrue("english" in langs, "got $langs")
        assertTrue("python" in langs, "got $langs")
    }

    @Test
    fun translatesLikeTheEngineDoes() {
        // Same answer `python3 -m squirrelator --cli english python 'print hello'` gives.
        val expected = ProcessBuilder("python3", "-c", "from squirrelator import translate; print(translate('print hello', 'english', 'python'), end='')")
            .also { it.environment()["PYTHONPATH"] = System.getProperty("squirrelator.root") }
            .also { it.environment()["SQUIRREL_LANG_DATA"] = System.getProperty("squirrelator.data") }
            .start().inputStream.bufferedReader().readText()
        assertEquals(expected, engine.translate("print hello", "english", "python"))
        // A second call reuses the same process.
        assertEquals(expected, engine.translate("print hello", "english", "python"))
    }

    @Test
    fun keepsUnicode() {
        val out = engine.translate("Grüße, 世界", "english", "english")
        assertEquals("Grüße, 世界", out)
    }
}
