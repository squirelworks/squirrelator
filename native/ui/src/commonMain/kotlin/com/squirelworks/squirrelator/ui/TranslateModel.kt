package com.squirelworks.squirrelator.ui

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/**
 * What the translate screen shows, kept apart from the drawing so it can be
 * tested without a window.
 */
class TranslateModel(
    private val engine: Engine,
    private val worker: CoroutineDispatcher = Dispatchers.Default,
) {
    var languages by mutableStateOf<List<String>>(emptyList())
        private set
    var from by mutableStateOf("")
    var to by mutableStateOf("")
    var input by mutableStateOf("")
    var output by mutableStateOf("")
        private set
    /** "Auto: translated with Rules", or "" before the first translation. */
    var engineNote by mutableStateOf("")
        private set
    var problem by mutableStateOf<String?>(null)
        private set
    var busy by mutableStateOf(false)
        private set

    val canTranslate: Boolean
        get() = !busy && input.isNotBlank() && from.isNotEmpty() && to.isNotEmpty()

    /** Ask the engine which languages it offers and pick a starting pair. */
    suspend fun load() {
        busy = true
        try {
            val found = withContext(worker) { engine.languages() }
            languages = found
            if (from !in found) from = found.firstOrNull { it == "english" } ?: found.firstOrNull().orEmpty()
            if (to !in found) to = found.firstOrNull { it != from }.orEmpty()
            problem = if (found.isEmpty()) "The translation engine offered no languages." else null
        } catch (e: Exception) {
            problem = "The translation engine didn't start: ${e.message ?: e::class.simpleName}"
        } finally {
            busy = false
        }
    }

    fun swap() {
        val old = from
        from = to
        to = old
    }

    suspend fun translate() {
        if (!canTranslate) return
        busy = true
        problem = null
        try {
            val done = withContext(worker) { engine.translate(input, from, to) }
            output = done.text
            engineNote = "${done.mode}: translated with ${done.engine}"
        } catch (e: Exception) {
            problem = "The translation failed: ${e.message ?: e::class.simpleName}"
        } finally {
            busy = false
        }
    }
}

/** A language id as people read it: "english" becomes "English". */
fun languageLabel(id: String): String = id.replaceFirstChar { it.uppercaseChar() }
