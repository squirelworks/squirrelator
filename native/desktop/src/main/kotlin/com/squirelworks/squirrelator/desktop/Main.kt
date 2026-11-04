package com.squirelworks.squirrelator.desktop

import androidx.compose.ui.window.Window
import androidx.compose.ui.window.application
import com.squirelworks.squirrelator.ui.App

fun main() {
    val engine = PythonProcessEngine.fromSystemProperties()
    application {
        Window(onCloseRequest = { engine.close(); exitApplication() }, title = "squirrelator") {
            App(engine)
        }
    }
}
