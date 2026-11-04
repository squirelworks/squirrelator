package com.squirelworks.squirrelator.desktop

import com.squirelworks.squirrelator.ui.Translated
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
        assertEquals(Translated(expected, "Rules", "Auto"), engine.translate("print hello", "english", "python"))
        // A second call reuses the same process.
        assertEquals(expected, engine.translate("print hello", "english", "python").text)
    }

    @Test
    fun showsThePipelinesAnswerAndTheSecondOpinion() {
        val ja = engine.translate("バスで学校に行きます。", "japanese", "english")
        assertEquals("Pipeline (alpha)", ja.engine)
        assertTrue(ja.text.startsWith("I go to school by bus."), ja.text)
        val la = engine.translate("I drink water.", "english", "latin")
        assertEquals("Rules", la.engine)
        assertTrue("Second opinion from Pipeline (alpha)" in la.text && "Aquam bibō." in la.text, la.text)
    }

    @Test
    fun keepsUnicode() {
        val out = engine.translate("Grüße, 世界", "english", "english").text
        assertEquals("Grüße, 世界", out)
    }
}
