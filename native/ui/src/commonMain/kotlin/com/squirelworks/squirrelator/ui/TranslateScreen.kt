package com.squirelworks.squirrelator.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.selection.SelectionContainer
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.input.key.Key
import androidx.compose.ui.input.key.KeyEventType
import androidx.compose.ui.input.key.isCtrlPressed
import androidx.compose.ui.input.key.isMetaPressed
import androidx.compose.ui.input.key.key
import androidx.compose.ui.input.key.onPreviewKeyEvent
import androidx.compose.ui.input.key.type
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.launch

/** The whole app for now: one translate screen, the same on phone and desktop. */
@Composable
fun App(engine: Engine) {
    val model = remember(engine) { TranslateModel(engine) }
    LaunchedEffect(model) { model.load() }
    MaterialTheme(colorScheme = if (isSystemInDarkTheme()) darkColorScheme() else lightColorScheme()) {
        Surface(Modifier.fillMaxSize()) {
            TranslateScreen(model)
        }
    }
}

@Composable
fun TranslateScreen(model: TranslateModel) {
    val scope = rememberCoroutineScope()
    val go: () -> Unit = { scope.launch { model.translate() } }

    // Pad for cutouts, system bars and the on-screen keyboard; keep one
    // readable column on wide windows.
    Box(
        Modifier.fillMaxSize().windowInsetsPadding(WindowInsets.safeDrawing).imePadding(),
        contentAlignment = Alignment.TopCenter,
    ) {
        Column(
            Modifier.widthIn(max = 720.dp).fillMaxWidth()
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Text("squirrelator", style = MaterialTheme.typography.headlineSmall)

            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                LanguagePicker("From", model.from, model.languages, Modifier.weight(1f)) { model.from = it }
                TextButton(onClick = model::swap, enabled = !model.busy) { Text("Swap") }
                LanguagePicker("To", model.to, model.languages, Modifier.weight(1f)) { model.to = it }
            }

            OutlinedTextField(
                value = model.input,
                onValueChange = { model.input = it },
                label = { Text("Text to translate") },
                modifier = Modifier.fillMaxWidth().heightIn(min = 120.dp).onPreviewKeyEvent { e ->
                    // Ctrl+Enter (Cmd+Enter on a Mac) translates from a physical keyboard.
                    val submit = e.type == KeyEventType.KeyDown && e.key == Key.Enter &&
                        (e.isCtrlPressed || e.isMetaPressed)
                    if (submit) go()
                    submit
                },
            )

            Button(onClick = go, enabled = model.canTranslate, modifier = Modifier.fillMaxWidth()) {
                Text(if (model.busy) "Working…" else "Translate")
            }

            model.problem?.let {
                Text(it, color = MaterialTheme.colorScheme.error)
            }

            if (model.output.isNotEmpty()) {
                SelectionContainer {
                    Text(model.output, style = MaterialTheme.typography.bodyLarge)
                }
                Text(
                    model.engineNote,
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}

@Composable
private fun LanguagePicker(
    label: String,
    selected: String,
    options: List<String>,
    modifier: Modifier = Modifier,
    onPick: (String) -> Unit,
) {
    var open by remember { mutableStateOf(false) }
    Box(modifier) {
        OutlinedButton(onClick = { open = true }, modifier = Modifier.fillMaxWidth(), enabled = options.isNotEmpty()) {
            Text(if (selected.isEmpty()) label else "$label: ${languageLabel(selected)}")
        }
        DropdownMenu(expanded = open, onDismissRequest = { open = false }) {
            options.forEach { id ->
                DropdownMenuItem(text = { Text(languageLabel(id)) }, onClick = {
                    onPick(id)
                    open = false
                })
            }
        }
    }
}
