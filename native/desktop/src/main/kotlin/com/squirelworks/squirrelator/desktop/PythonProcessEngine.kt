package com.squirelworks.squirrelator.desktop

import com.squirelworks.squirrelator.ui.Engine
import com.squirelworks.squirrelator.ui.Translated
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.boolean
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import java.io.BufferedReader
import java.io.BufferedWriter
import java.io.File

/**
 * The Python engine in a long-running `python3 squirrelator_bridge.py --serve`
 * process, one JSON line per request. The process starts on the first call.
 */
class PythonProcessEngine(
    private val python: String,
    private val bridge: File,
    private val engineRoot: File,
    private val dataDir: File,
) : Engine, AutoCloseable {
    private var process: Process? = null
    private lateinit var input: BufferedWriter
    private lateinit var output: BufferedReader

    override fun languages(): List<String> =
        call(mapOf("op" to "languages"))["languages"]!!.jsonArray.map { it.jsonPrimitive.content }

    override fun translate(text: String, from: String, to: String): Translated {
        val reply = call(mapOf("op" to "show", "text" to text, "from" to from, "to" to to))
        return Translated(
            reply["text"]!!.jsonPrimitive.content,
            reply["engine"]!!.jsonPrimitive.content,
            reply["mode"]!!.jsonPrimitive.content,
        )
    }

    @Synchronized
    private fun call(request: Map<String, String>): JsonObject {
        val p = process?.takeIf { it.isAlive } ?: start()
        input.write(JsonObject(request.mapValues { JsonPrimitive(it.value) }).toString())
        input.newLine()
        input.flush()
        val line = output.readLine() ?: run {
            val err = p.errorStream.bufferedReader().readText().trim()
            process = null
            error("The Python engine stopped. $err")
        }
        val reply = Json.parseToJsonElement(line).jsonObject
        if (!reply["ok"]!!.jsonPrimitive.boolean) error(reply["error"]?.jsonPrimitive?.content ?: "unknown error")
        return reply
    }

    private fun start(): Process {
        val pb = ProcessBuilder(python, "-u", bridge.absolutePath, "--serve")
        pb.environment()["PYTHONPATH"] = engineRoot.absolutePath
        pb.environment()["SQUIRREL_LANG_DATA"] = dataDir.absolutePath
        pb.environment()["PYTHONIOENCODING"] = "utf-8"
        val p = pb.start()
        input = p.outputStream.bufferedWriter(Charsets.UTF_8)
        output = p.inputStream.bufferedReader(Charsets.UTF_8)
        process = p
        return p
    }

    @Synchronized
    override fun close() {
        process?.let {
            runCatching { input.close() }
            it.destroy()
        }
        process = null
    }

    companion object {
        /** Settings passed by the Gradle build (see desktop/build.gradle.kts). */
        fun fromSystemProperties(): PythonProcessEngine {
            fun prop(name: String) = System.getProperty(name)
                ?: error("Missing -D$name. Run the app with `gradle :desktop:run`.")
            return PythonProcessEngine(
                python = System.getProperty("squirrelator.python")
                    ?: if (System.getProperty("os.name").startsWith("Windows")) "python" else "python3",
                bridge = File(prop("squirrelator.bridge")),
                engineRoot = File(prop("squirrelator.root")),
                dataDir = File(prop("squirrelator.data")),
            )
        }
    }
}
