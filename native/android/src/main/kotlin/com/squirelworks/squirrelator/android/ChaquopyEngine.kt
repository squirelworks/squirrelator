package com.squirelworks.squirrelator.android

import android.content.Context
import com.chaquo.python.PyObject
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import com.squirelworks.squirrelator.ui.Engine
import java.io.File
import java.util.zip.ZipInputStream

/**
 * The Python engine, running inside the app through Chaquopy. The first call
 * starts Python and unpacks the bundled language data; both are slow, which
 * is why the screens call this off the main thread.
 */
class ChaquopyEngine(private val context: Context) : Engine {
    private val bridge: PyObject by lazy {
        if (!Python.isStarted()) Python.start(AndroidPlatform(context))
        val module = Python.getInstance().getModule("squirrelator_bridge")
        module.callAttr("setup", unpackData().absolutePath)
        module
    }

    override fun languages(): List<String> =
        bridge.callAttr("languages").asList().map { it.toString() }

    override fun translate(text: String, from: String, to: String): String =
        bridge.callAttr("translate", text, from, to).toString()

    /** Unpack lang-data.zip once per installed version of the app. */
    private fun unpackData(): File {
        val info = context.packageManager.getPackageInfo(context.packageName, 0)
        val dir = File(context.filesDir, "lang-data")
        val stamp = File(dir, ".unpacked")
        val version = info.lastUpdateTime.toString()
        if (stamp.isFile && stamp.readText() == version) return dir

        dir.deleteRecursively()
        dir.mkdirs()
        val root = dir.canonicalPath + File.separator
        context.assets.open("lang-data.zip").use { raw ->
            ZipInputStream(raw.buffered()).use { zip ->
                while (true) {
                    val entry = zip.nextEntry ?: break
                    val out = File(dir, entry.name)
                    check(out.canonicalPath.startsWith(root)) { "Bad path in language data: ${entry.name}" }
                    if (entry.isDirectory) {
                        out.mkdirs()
                    } else {
                        out.parentFile?.mkdirs()
                        out.outputStream().use { zip.copyTo(it) }
                    }
                }
            }
        }
        stamp.writeText(version)
        return dir
    }
}
