package com.squirelworks.squirrelator.ui

import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.runTest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNull
import kotlin.test.assertTrue

private class FakeEngine(
    private val langs: List<String> = listOf("english", "latin", "python"),
    private val fail: Boolean = false,
) : Engine {
    val calls = mutableListOf<Triple<String, String, String>>()
    override fun languages() = if (fail) error("no python") else langs
    override fun translate(text: String, from: String, to: String): Translated {
        calls += Triple(text, from, to)
        return Translated("[$from>$to] $text", if (to == "python") "Rules" else "Pipeline (alpha)")
    }
}

class TranslateModelTest {
    @Test
    fun loadPicksEnglishAndAnotherLanguage() = runTest {
        val model = TranslateModel(FakeEngine(listOf("klingon", "english", "latin")), StandardTestDispatcher(testScheduler))
        model.load()
        assertEquals(listOf("klingon", "english", "latin"), model.languages)
        assertEquals("english", model.from)
        assertEquals("klingon", model.to)
        assertNull(model.problem)
    }

    @Test
    fun translateCallsTheEngineWithThePickedPair() = runTest {
        val engine = FakeEngine()
        val model = TranslateModel(engine, StandardTestDispatcher(testScheduler))
        model.load()
        model.to = "python"
        model.input = "print hello"
        model.translate()
        assertEquals(listOf(Triple("print hello", "english", "python")), engine.calls)
        assertEquals("[english>python] print hello", model.output)
        assertEquals("Auto: translated with Rules", model.engineNote)
        assertFalse(model.busy)
    }

    @Test
    fun blankInputDoesNotCallTheEngine() = runTest {
        val engine = FakeEngine()
        val model = TranslateModel(engine, StandardTestDispatcher(testScheduler))
        model.load()
        model.input = "   "
        assertFalse(model.canTranslate)
        model.translate()
        assertTrue(engine.calls.isEmpty())
    }

    @Test
    fun swapExchangesTheLanguages() = runTest {
        val model = TranslateModel(FakeEngine(), StandardTestDispatcher(testScheduler))
        model.load()
        model.swap()
        assertEquals("latin", model.from)
        assertEquals("english", model.to)
    }

    @Test
    fun aBrokenEngineIsReportedNotThrown() = runTest {
        val model = TranslateModel(FakeEngine(fail = true), StandardTestDispatcher(testScheduler))
        model.load()
        assertTrue(model.problem!!.startsWith("The translation engine didn't start"))
        assertTrue(model.languages.isEmpty())
    }

    @Test
    fun labelsAreCapitalised() {
        assertEquals("English", languageLabel("english"))
        assertEquals("Z80", languageLabel("z80"))
    }
}
